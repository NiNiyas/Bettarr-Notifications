import json
import logging
import os
import re
import sys

import humanize
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from torpy.http.requests import TorRequests

import script_config

headers = {
    "Accept-Encoding": "gzip, deflate",
    "Accept-Language": "en-US,en;q=0.9",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.85 Safari/537.36 Edg/90.0.818.49"
}

# Set up the log folder and file
dir = os.path.join(os.path.dirname(sys.argv[0]))
os.chdir(dir)
if not os.path.exists('Logs'):
    os.mkdir('Logs')
log_filename = os.path.join(os.path.dirname(sys.argv[0]), 'Logs/sonarr-grab-tor-telegram.log')
logging.basicConfig(
    filename=log_filename,
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s'
)
log = logging.getLogger('Sonarr')

tgurl = 'https://api.telegram.org/bot{}/sendMessage'.format(script_config.bot_id)


# From https://www.peterbe.com/plog/best-practice-with-retries-with-requests
def requests_retry_session(
        retries=5,
        backoff_factor=0.3,
        status_forcelist=(500, 502, 504),
        session=None,
):
    session = session or requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session


# Ratings
imdb_id = os.environ.get('sonarr_series_imdbid')
if not imdb_id:
    imdb_id = 'tt0944947'

mdblist = requests_retry_session().get('https://mdblist.com/api/?apikey={}&i={}&m=show'.format(script_config.mdbapi, imdb_id),
                                       headers=headers)
mdblist_data = mdblist.json()

# IMDb
try:
    imdb_rating = mdblist_data['ratings'][0]['value']
except:
    log.info("Error fetching rating from mdblist")
    imdb_rating = 'None'

# Metacritic
try:
    metacritic = mdblist_data['ratings'][1]['value']
except:
    log.info("Error fetching rating from mdblist")
    metacritic = 'None'

# Trakt
try:
    trakt_rating = mdblist_data['ratings'][2]['value']
except:
    log.info("Error fetching rating from mdblist")
    trakt_rating = 'None'

# TMDb Rating
try:
    tmdb_rating = mdblist_data['ratings'][5]['value']
except:
    log.info("Error fetching rating from mdblist")
    tmdb_rating = 'None'

# Rotten Tomatoes
try:
    rottentomatoes = mdblist_data['ratings'][3]['value']
except:
    log.info("Error fetching rating from mdblist")
    rottentomatoes = 'None'


def main():
    # Get/set ENV variables. More info on 'https://github.com/Sonarr/Sonarr/wiki/Custom-Post-Processing-Scripts'
    eventtype = os.environ.get('sonarr_eventtype')

    season = os.environ.get('sonarr_release_seasonnumber')

    episode = os.environ.get('sonarr_release_episodenumbers')

    tvdb_id = os.environ.get('sonarr_series_tvdbid')
    if not tvdb_id:
        tvdb_id = '121361'

    size = os.environ.get('sonarr_release_size')
    if not size:
        size = '5454554445'

    release_group = os.environ.get('sonarr_release_releasegroup')

    media_title = os.environ.get('sonarr_series_title')

    episode_title = os.environ.get('sonarr_release_episodetitles')

    quality = os.environ.get('sonarr_release_quality')

    release_indexer = os.environ.get('sonarr_release_indexer')

    # Get show information from skyhook
    skyhook_url = 'http://skyhook.sonarr.tv/v1/tvdb/shows/en/{}'.format(tvdb_id)
    skyhook_data = requests.get(skyhook_url).json()
    title_slug = skyhook_data['slug']

    # TMDb ID
    with TorRequests() as tor_requests:
        with tor_requests.get_session(retries=10) as sess:
            try:
                tmdb = ('https://api.themoviedb.org/3/find/{}?api_key={}&language=en&external_source=tvdb_id').format(
                    tvdb_id,
                    script_config.moviedb_key)
                get_tmdb = sess.get(tmdb, headers=headers, timeout=60).json()
                tmdb_id = get_tmdb['tv_results'][0]['id']
            except:
                with tor_requests.get_session(retries=10) as sess:
                    tmdb = (
                        'https://api.themoviedb.org/3/find/{}?api_key={}&language=en&external_source=imdb_id').format(
                        imdb_id,
                        script_config.moviedb_key)
                    get_tmdb = sess.get(tmdb, headers=headers, timeout=60).json()
                    tmdb_id = get_tmdb['tv_results'][0]['id']

    # Season poster, if it fails, falls back to series banner
    with TorRequests() as tor_requests:
        with tor_requests.get_session(retries=10) as sess:
            try:
                banner_url = ('https://api.themoviedb.org/3/tv/{}/season/{}/images?api_key={}&language=en').format(
                    tmdb_id,
                    season,
                    script_config.moviedb_key)
                banner_data = sess.get(banner_url, headers=headers, timeout=60).json()
                banner = banner_data['posters'][0]['file_path']
                banner = 'https://image.tmdb.org/t/p/original' + banner
            except:
                # Series banner
                log.info("Couldn't fetch season banner. Falling back to series banner")
                try:
                    banner = skyhook_data['images'][0]['url']
                except:
                    banner = 'http://gearr.scannain.com/wp-content/uploads/2015/02/noposter.jpg'

    # View Details
    tvdb_url = 'https://thetvdb.com/series/' + title_slug

    try:
        tvmaze_id = skyhook_data['tvMazeId']
    except Exception as e:
        log.info("TVMaze id not found. Using GOT. Error: {}".format(e))
        tvmaze_id = '82'

    tvmaze_url = 'https://www.tvmaze.com/shows/' + str(tvmaze_id)

    trakt_url = 'https://trakt.tv/search/tvdb/' + tvdb_id + '?id_type=show'

    imdb_url = ('https://www.imdb.com/title/' + str(imdb_id))

    tmdb_url = 'https://www.themoviedb.org/tv/' + str(tmdb_id)

    # Trailer
    try:
        trailer_link = mdblist_data['trailer']
        if trailer_link is None:
            log.info("Trailer not Found. Using 'Never Gonna Give You Up'.")
            trailer_link = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ&ab'
    except KeyError:
        log.info("Trailer not Found. Using 'Never Gonna Give You Up'.")
        trailer_link = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ&ab'

    # Series Overview
    with TorRequests() as tor_requests:
        with tor_requests.get_session(retries=10) as sess:
            series = ('https://api.themoviedb.org/3/tv/{}?api_key={}&language=en').format(tmdb_id,
                                                                                          script_config.moviedb_key)
            series_data = sess.get(series, headers=headers, timeout=60).json()
            overview = series_data['overview']

    # Formatting Season and Episode
    if len(str(season)) == 1:
        season = '0{}'.format(season)
    if len(str(episode)) == 1:
        episode = '0{}'.format(episode)

    # Content Rating
    try:
        content_rating = skyhook_data['contentRating']
    except:
        content_rating = 'Unknown'

    # Network
    try:
        network = skyhook_data['network']
    except:
        network = 'Unknown'

    # Genre
    try:
        genres = json.dumps(skyhook_data['genres'])
        genres = re.sub(r'[?|$|.|!|:|/|\]|\[|\"]', r'', genres)
    except:
        genres = 'Unknown'

    # Telegram Message Format
    message = {
        "chat_id": script_config.chat_id,
        "parse_mode": "HTML",
        "text": "Grabbed - <b>{}</b>: <i>S{}E{}</i> - <b>{}</b> from <i>{}</i>"
                "\n\n<b>Overview</b> \n{}"
                "\n\n<b>IMDB</b> - {} ???| <b>Metacritic</b> - {} | <b>Rotten Tomatoes</b> - {} ????\n<b>Trakt</b> - {} | <b>TMDb</b> - {} "
                "\n\n<b>Episode</b> - S{}E{}"
                "\n<b>Quality</b> - {}"
                "\n<b>Size</b> - {}"
                "\n<b>Network</b> - {}"
                "\n<b>Genre</b> - {}"
                "\n<b>Release Group</b> - {}"
                "\n<b>Content Rating</b> - {}"
                "\n<a href='{}'>&#8204;</a>"
            .format(
            media_title, season, episode, episode_title,
            release_indexer, overview,
            imdb_rating, metacritic, rottentomatoes, trakt_rating, tmdb_rating, season, episode, quality,
            (humanize.naturalsize(size)),
            network, genres,
            release_group, content_rating, banner),
        "reply_markup": {
            "inline_keyboard": [[
                {
                    "text": "Trailer",
                    "url": trailer_link
                },
                {
                    "text": "IMDb",
                    "url": imdb_url
                },
                {
                    "text": "TVDb",
                    "url": tvdb_url
                },
                {
                    "text": "TMDb",
                    "url": tmdb_url
                },
                {
                    "text": "Trakt",
                    "url": trakt_url
                },

                {
                    "text": "TVmaze",
                    "url": tvmaze_url
                }]
            ]
        }

    }

    # Send notification
    sender = requests.post(tgurl, json=message)

    # Logging
    log.info(json.dumps(message, sort_keys=True, indent=4, separators=(',', ': ')))

    if eventtype == "Test":
        print("Successfully sent test notification.")
    else:
        print("Successfully sent notification to Telegram.")


# Call main
main()
