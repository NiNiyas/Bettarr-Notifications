import datetime
import json
import math
import os
import re
import shutil

import config
import requests
from helpers import ratings
from loguru import logger as log
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

dir_path = os.path.dirname(os.path.realpath(__file__))

colors = ['65405', '15484425', '16270516', '1529855', '14399755', '10947666', '7376755', '1752220', '1146986',
          '3066993', '2067276', '3447003', '2123412', '10181046', '7419530', '15277667',
          '11342935', '15844367', '12745742', '15105570', '11027200', '15158332', '10038562', '9807270', '9936031',
          '8359053', '12370112', '3426654', '2899536', '16776960', '16777215',
          '5793266', '10070709', '2895667', '2303786', '5763719', '16705372', '15418782', '15548997', '16777215',
          '2303786']


def convert_size(size_bytes):
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return "%s %s" % (s, size_name[i])


def utc_now_iso():
    utcnow = datetime.datetime.utcnow()
    return utcnow.isoformat()


def requests_retry_session(retries=3, backoff_factor=0.2, status_forcelist=(500, 502, 504), session=None):
    session = session or requests.Session()
    retry = Retry(total=retries, read=retries, connect=retries, backoff_factor=backoff_factor,
                  status_forcelist=status_forcelist)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('https://', adapter)
    return session


def get_radarr_trailer(radarr):
    try:
        trailer_link = f'https://www.youtube.com/watch?v={radarr["youTubeTrailerId"]}'
    except (KeyError, TypeError, IndexError, Exception):
        trailer_link = "https://www.youtube.com/watch?v=dQw4w9WgXcQ&ab"
        log.warning("Trailer not Found. Using 'Never Gonna Give You Up'.")

    return trailer_link


def get_radarr_links(imdb_id, tmdb_id):
    try:
        imdb_url = "https://www.imdb.com/title/" + imdb_id
        tmdb_url = "https://www.themoviedb.org/movie/" + tmdb_id
        moviechat = "https://moviechat.org/" + imdb_id
        trakt_url = "https://trakt.tv/search/tmdb/" + tmdb_id + '?id_type=movie'
    except Exception:
        imdb_url = "https://www.imdb.com"
        tmdb_url = "https://www.themoviedb.org"
        moviechat = "https://moviechat.org/"
        trakt_url = "https://trakt.tv/"

    return imdb_url, tmdb_url, trakt_url, moviechat


def get_radarr_overview(radarr):
    try:
        overview = radarr["overview"]
    except (KeyError, TypeError, IndexError, Exception):
        log.warning("Error getting overview from Radarr.")
        overview = "Unknown"

    if len(overview) >= 300:
        overview = overview[:250]
        overview += "..."

    discord_overview = f"**Overview**\n{overview}"
    slack_overview = f"{overview}"
    html_overview = overview[:100]
    html_overview += "..."

    return discord_overview, slack_overview, html_overview


def get_radarr_genres(radarr):
    try:
        genres_data = radarr["genres"]
        genres = str(genres_data)[1:-1]
        genres = genres.replace("'", "")
    except (KeyError, TypeError, IndexError, Exception):
        log.warning("Error getting genres from Radarr.")
        genres = "Unknown"

    return genres


def radarr_tmdb_api(tmdb_id):
    moviedb_api = requests_retry_session().get(
        f'https://{config.TMDB_URL}/3/movie/{tmdb_id}?api_key={config.TMDB_APIKEY}', timeout=60)
    moviedb_api = moviedb_api.json()

    return moviedb_api


def get_movie_cast(tmdb_id):
    crew = requests_retry_session().get(
        f'https://{config.TMDB_URL}/3/movie/{tmdb_id}/credits?api_key={config.TMDB_APIKEY}',
        timeout=60)
    crew = crew.json()
    cast = []
    cast_url = []
    for x in crew['cast']:
        cast.append(x['original_name'])
        cast = cast[:3]

    for actors in cast:
        actors_url = f'https://www.themoviedb.org/search?query={actors}'
        actors_url = actors_url.replace(" ", "+")
        cast_url.append(actors_url)

    return cast_url, cast


def get_movie_crew(tmdb_id):
    crew = requests_retry_session().get(
        f'https://{config.TMDB_URL}/3/movie/{tmdb_id}/credits?api_key={config.TMDB_APIKEY}',
        timeout=60)
    crew = crew.json()
    directors = []
    director_url = []
    for x in crew['crew']:
        if x['job'] == "Director":
            directors.append(x['original_name'])

    for director in directors:
        actors_url = f'https://www.themoviedb.org/search?query={director}'
        actors_url = actors_url.replace(" ", "+")
        director_url.append(actors_url)

    return director_url, directors


def get_movie_watch_providers(tmdb_id, imdb_id):
    providers = []
    try:
        country_code = config.TMDB_COUNTRY_CODE
        justwatch = requests_retry_session().get(
            f'https://{config.TMDB_URL}/3/movie/{tmdb_id}/watch/providers?api_key={config.TMDB_APIKEY}')
        tmdbproviders = justwatch.json()
        for p in tmdbproviders["results"][country_code]['flatrate']:
            providers.append(p['provider_name'])
    except (KeyError, TypeError, IndexError, Exception):
        country_code = "US"
        log.warning("Couldn't fetch providers from TMDb. Fetching from mdblist.")
        try:
            mdblist = requests.get(f'https://mdblist.com/api/?apikey={config.MDBLIST_APIKEY}&i={imdb_id}').json()
            for x in {mdblist['streams']}:
                stream = (x['name'])
                providers.append(stream)
        except (KeyError, TypeError, IndexError, Exception):
            log.warning("Error fetching stream data from mdblist.")
            stream = "None"
            providers.append(stream)

    watch_on = str(providers)[1:-1]
    watch_on = watch_on.replace("'", "")
    if not watch_on:
        watch_on = "None"

    return watch_on, country_code


def get_radarr_releasedate(tmdb_id):
    try:
        release = radarr_tmdb_api(tmdb_id)["release_date"]
        release = datetime.datetime.strptime(release, "%Y-%m-%d").strftime("%B %d, %Y")
    except (KeyError, TypeError, IndexError, Exception):
        log.warning("Error getting release date from TMDB.")
        release = "Unknown"

    return release


def get_radarr_physicalrelease(radarr):
    try:
        physical_release = radarr['physicalRelease']
        physical_release = datetime.datetime.strptime(physical_release, "%Y-%m-%dT%H:%M:%SZ").strftime("%B %d, %Y")
    except (KeyError, TypeError, IndexError, Exception):
        physical_release = 'Unknown'

    return physical_release


def get_radarr_backdrop(tmdb_id):
    try:
        banner_data = requests_retry_session().get(
            f'https://{config.TMDB_URL}/3/movie/{tmdb_id}/images?api_key={config.TMDB_APIKEY}&language=en',
            timeout=60).json()
        banner = banner_data['backdrops'][0]['file_path']
        banner = 'https://image.tmdb.org/t/p/original' + banner
    except (KeyError, TypeError, IndexError, Exception):
        try:
            banner_url = radarr_tmdb_api(tmdb_id)['backdrop_path']
            banner = 'https://image.tmdb.org/t/p/original' + banner_url
        except (KeyError, TypeError, IndexError, Exception):
            log.warning("Error retrieving backdrop. Defaulting to generic banner.")
            banner = 'https://i.imgur.com/IMQb6ia.png'

    return banner


def get_radarrposter(tmdb_id):
    try:
        poster_path = radarr_tmdb_api(tmdb_id)['poster_path']
        poster_path = "https://image.tmdb.org/t/p/original" + poster_path
    except (KeyError, TypeError, IndexError, Exception):
        log.warning("Error getting poster from TMDB.")
        poster_path = "https://i.imgur.com/GoqfZJe.jpg"

    return poster_path


def get_pushover_radarrposter(tmdb_id):
    poster_path = get_radarrposter(tmdb_id)

    if not os.path.exists(f"{dir_path}/images"):
        os.mkdir(f"{dir_path}/images")
    response = requests_retry_session().get(poster_path, stream=True)
    filename = poster_path.split("/")[-1]
    file_path = os.path.join(f"{dir_path}/images", filename)
    if response.status_code == 200:
        response.raw.decode_content = True
        with open(file_path, 'wb') as f:
            shutil.copyfileobj(response.raw, f)
        log.debug('Pushover poster for radarr downloaded successfully.')
    else:
        log.warning('Error downloading pushover poster for radarr.')

    return file_path


def get_pushover_radarrstill(tmdb_id):
    still = get_radarr_backdrop(tmdb_id)
    if not os.path.exists(f"{dir_path}/images"):
        os.mkdir(f"{dir_path}/images")
    response = requests_retry_session().get(still, stream=True)
    filename = still.split("/")[-1]
    file_path = os.path.join(f"{dir_path}/images", filename)
    if response.status_code == 200:
        response.raw.decode_content = True
        with open(file_path, 'wb') as f:
            shutil.copyfileobj(response.raw, f)
        log.debug('Pushover still downloaded successfully.')
    else:
        log.warning('Error downloading pushover still.')

    return file_path


#########################################################################
#                                                                       #
#                          SONARR SECTION                               #
#                                                                       #
#########################################################################
def get_sonarr_contentrating(skyhook):
    try:
        content_rating = skyhook['contentRating']
    except (KeyError, TypeError, IndexError, Exception):
        content_rating = ratings.mdblist_tv()[1]

        if content_rating == "":
            content_rating = "Unknown"

    return content_rating


def get_sonarr_network(skyhook):
    try:
        network = skyhook["network"]
    except (KeyError, TypeError, IndexError, Exception):
        network = "Unknown"

    return network


def get_sonarrgenres(skyhook):
    try:
        genres = json.dumps(skyhook["genres"])
        genres = re.sub(r'[?|$|.|!|:|/|\]|\[|\"]', r'', genres)
    except (KeyError, TypeError, IndexError, Exception):
        genres = "Unknown"

    return genres


def sonarr_tmdbapi(tvdb_id, imdb_id):
    try:
        tmdb = requests_retry_session().get(
            f'https://{config.TMDB_URL}/3/find/{tvdb_id}?api_key={config.TMDB_APIKEY}&language=en&external_source=tvdb_id',
            timeout=60).json()
        tmdb_id = tmdb['tv_results'][0]['id']
    except (KeyError, TypeError, IndexError, Exception):
        tmdb = requests_retry_session().get(
            f'https://{config.TMDB_URL}/3/find/{imdb_id}?api_key={config.TMDB_APIKEY}&language=en&external_source=imdb_id',
            timeout=60).json()
        tmdb_id = tmdb['tv_results'][0]['id']

    return tmdb_id


def get_seriescast(tvdb_id, imdb_id):
    try:
        crew = requests.get(
            f"https://{config.TMDB_URL}/3/tv/{sonarr_tmdbapi(tvdb_id, imdb_id)}/credits?api_key={config.TMDB_APIKEY}",
            timeout=60)
        crew = crew.json()
        cast = []
        cast_url = []

        for x in crew['cast']:
            cast.append(x['original_name'])
            cast = cast[:3]

        for actors in cast:
            actors_url = f"https://www.themoviedb.org/search?query={actors}"
            actors_url = actors_url.replace(" ", "+")
            cast_url.append(actors_url)
    except (KeyError, TypeError, IndexError, Exception):
        cast = []
        cast_url = []

    return cast_url, cast


def get_seriescrew(tvdb_id, imdb_id):
    try:
        crew = requests.get(
            f"https://{config.TMDB_URL}/3/tv/{sonarr_tmdbapi(tvdb_id, imdb_id)}/credits?api_key={config.TMDB_APIKEY}",
            timeout=60)
        crew = crew.json()
        directors = []
        director_url = []
        for x in crew['crew']:
            if x['job'] == "Director":
                directors.append(x['original_name'])

        for director in directors:
            actors_url = f"https://www.themoviedb.org/search?query={director}"
            actors_url = actors_url.replace(" ", "+")
            director_url.append(actors_url)
    except (KeyError, TypeError, IndexError, Exception):
        directors = []
        director_url = []

    if not directors:
        directors = "Unknown"

    return director_url, directors


def get_posterseries(tvdb_id, imdb_id):
    try:
        poster_path = requests.get(
            f"https://{config.TMDB_URL}/3/tv/{sonarr_tmdbapi(tvdb_id, imdb_id)}?api_key={config.TMDB_APIKEY}&language=en-US",
            timeout=60).json()
        poster = poster_path['poster_path']
        poster = "https://image.tmdb.org/t/p/original/" + poster
    except (KeyError, TypeError, IndexError, Exception):
        poster = 'http://gearr.scannain.com/wp-content/uploads/2015/02/noposter.jpg'

    return poster


def get_pushover_sonarrposter(tvdb_id, imdb_id):
    poster = get_posterseries(tvdb_id, imdb_id)
    if not os.path.exists(f"{dir_path}/images"):
        os.mkdir(f"{dir_path}/images")
    response = requests_retry_session().get(poster, stream=True)
    filename = poster.split("/")[-1]
    file_path = os.path.join(f"{dir_path}/images", filename)
    if response.status_code == 200:
        response.raw.decode_content = True
        with open(file_path, 'wb') as f:
            shutil.copyfileobj(response.raw, f)
        log.debug('Pushover poster for sonarr downloaded successfully.')
    else:
        log.warning('Error downloading pushover poster for sonarr.')

    return file_path


def get_sonarr_links(tvdb_id, imdb_id, skyhook, slug):
    try:
        tvdb_url = 'https://thetvdb.com/series/' + slug

        try:
            tvmaze_id = skyhook['tvMazeId']
        except (KeyError, TypeError, IndexError, Exception):
            tvmaze_id = "Unknown"

        tvmaze_url = 'https://www.tvmaze.com/shows/' + str(tvmaze_id)

        trakt_url = 'https://trakt.tv/search/tvdb/' + tvdb_id + '?id_type=show'

        imdb_url = 'https://www.imdb.com/title/' + str(imdb_id)

        tmdb_url = 'https://www.themoviedb.org/tv/' + str(sonarr_tmdbapi(tvdb_id, imdb_id))
    except Exception:
        tvdb_url = "https://thetvdb.com"
        tvmaze_url = "https://www.tvmaze.com"
        trakt_url = "https://trakt.tv"
        imdb_url = "https://www.imdb.com"
        tmdb_url = "https://www.themoviedb.org"

    return tvdb_url, tvmaze_url, trakt_url, imdb_url, tmdb_url


def get_tv_watch_providers(tvdb_id, imdb_id):
    providers = []
    try:
        country_code = config.TMDB_COUNTRY_CODE
        justwatch = requests_retry_session().get(
            f'https://{config.TMDB_URL}/3/tv/{sonarr_tmdbapi(tvdb_id, imdb_id)}/watch/providers?api_key={config.TMDB_APIKEY}')
        tmdbproviders = justwatch.json()
        for p in tmdbproviders["results"][country_code]['flatrate']:
            providers.append(p['provider_name'])
    except (KeyError, TypeError, IndexError, Exception):
        country_code = "US"
        log.warning("Couldn't fetch providers from TMDb. Fetching from mdblist.")
        try:
            mdblist = requests.get(f'https://mdblist.com/api/?apikey={config.MDBLIST_APIKEY}&i={imdb_id}&m=show').json()
            for x in {mdblist['streams']}:
                stream = (x['name'])
                providers.append(stream)
        except (KeyError, TypeError, IndexError, Exception):
            log.warning("Error fetching stream data from mdblist.")
            stream = "None"
            providers.append(stream)

    watch_on = str(providers)[1:-1]
    watch_on = watch_on.replace("'", "")
    if not watch_on:
        watch_on = "None"

    return watch_on, country_code


def get_sonarr_trailer():
    try:
        trailer_link = ratings.mdblist_tv()[2]
    except (KeyError, TypeError, IndexError, Exception):
        log.warning("Trailer not Found. Using 'Never Gonna Give You Up'.")
        trailer_link = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ&ab'

    return trailer_link


def get_sonarr_overview(tvdb_id, imdb_id):
    try:
        series = requests_retry_session().get(
            f'https://{config.TMDB_URL}/3/tv/{sonarr_tmdbapi(tvdb_id, imdb_id)}?api_key={config.TMDB_APIKEY}&language=en',
            timeout=20).json()
        overview = series["overview"]
        if overview == "":
            overview = ""
    except (KeyError, TypeError, IndexError, Exception):
        overview = ""

    if len(overview) >= 300:
        overview = overview[:250]
        overview += '...'

    discord_overview = f"**Overview**\n{overview}"
    slack_overview = overview
    html_overview = overview[:100]
    html_overview += "..."

    return discord_overview, slack_overview, html_overview


def format_season_episode(season, episode):
    try:
        if len(str(season)) == 1:
            season = f"0{season}"
    except (KeyError, TypeError, IndexError, Exception):
        season = "Unknown"

    try:
        if len(str(episode)) == 1:
            episode = f"0{episode}"
    except (KeyError, TypeError, IndexError, Exception):
        episode = "Unknown"

    return season, episode


def get_sonarr_episodesample(tvdb_id, imdb_id, season, episode, skyhook):
    try:
        episode_data = requests_retry_session().get(
            f'https://{config.TMDB_URL}/3/tv/{sonarr_tmdbapi(tvdb_id, imdb_id)}/season/{season}/episode/{episode}/images?api_key={config.TMDB_APIKEY}&language=en',
            timeout=20).json()
        sample = episode_data['stills'][0]['file_path']
        sample = 'https://image.tmdb.org/t/p/original' + sample
    except (KeyError, TypeError, IndexError, Exception):
        try:
            sp = requests_retry_session().get(
                f'https://{config.TMDB_URL}/3/tv/{sonarr_tmdbapi(tvdb_id, imdb_id)}/images?api_key={config.TMDB_APIKEY}&language=en',
                timeout=20).json()
            poster = sp['posters'][0]['file_path']
            sample = 'https://image.tmdb.org/t/p/original' + poster
        except (KeyError, TypeError, IndexError, Exception):
            sample = skyhook['images'][0]['url']

    return sample


def get_pushover_sonarrstill(tvdb_id, imdb_id, season, episode, skyhook):
    sample = get_sonarr_episodesample(tvdb_id, imdb_id, season, episode, skyhook)
    if not os.path.exists('Images'):
        os.mkdir('Images')
    response = requests_retry_session().get(sample, stream=True)
    filename = sample.split("/")[-1]
    file_path = os.path.join('Images', filename)
    if response.status_code == 200:
        response.raw.decode_content = True
        with open(file_path, 'wb') as f:
            shutil.copyfileobj(response.raw, f)
        log.debug('Pushover still for sonarr downloaded successfully.')
    else:
        log.warning('Error downloading pushover still for sonarr.')

    return file_path


def get_sonarr_episodeoverview(season, episode, tvdb_id, imdb_id):
    try:
        episode_data = requests_retry_session().get(
            f'https://{config.TMDB_URL}/3/tv/{sonarr_tmdbapi(tvdb_id, imdb_id)}/season/{season}/episode/{episode}?api_key={config.TMDB_APIKEY}&language=en',
            timeout=60).json()
        overview = episode_data['overview']
    except (KeyError, TypeError, IndexError, Exception):
        log.warning("Couldn't fetch episode overview. Falling back to series overview.")
        series = f'https://{config.TMDB_URL}/3/tv/{sonarr_tmdbapi(tvdb_id, imdb_id)}?api_key={config.TMDB_APIKEY}&language=en'
        series_data = requests_retry_session().get(series, timeout=20).json()
        overview = series_data['overview']

    if len(overview) >= 300:
        overview = overview[:250]
        overview += '...'

    discord_overview = f"**Overview**\n{overview}"
    slack_overview = overview
    html_overview = overview[:100]
    html_overview += "..."

    return discord_overview, slack_overview, html_overview
