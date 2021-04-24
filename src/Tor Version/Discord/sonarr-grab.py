import json
import logging
import os
import re
import sys
from datetime import datetime

import humanize
import requests
from torpy.http.requests import TorRequests

import script_config

discord_headers = {'content-type': 'application/json'}

# Set up the log folder and file
dir = os.path.join(os.path.dirname(sys.argv[0]))
os.chdir(dir)
if not os.path.exists('Logs'):
    os.mkdir('Logs')
log_filename = os.path.join(os.path.dirname(sys.argv[0]), 'Logs/sonarr-grab-tor-discord.log')
logging.basicConfig(
    filename=log_filename,
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s'
)
log = logging.getLogger('Sonarr')

# Was getting error : https://github.com/psf/requests/issues/3391#issuecomment-231990544
sess = requests.Session()
adapter = requests.adapters.HTTPAdapter(max_retries=20)
sess.mount('http://', adapter)


# Footer Timestamp
def utc_now_iso():
    utcnow = datetime.utcnow()
    return utcnow.isoformat()


# Ratings
imdb_id = os.environ.get('sonarr_series_imdbid')
if not imdb_id:
    imdb_id = 'tt0944947'

mdblist = sess.get('https://mdblist.com/api/?apikey={}&i={}&m=show'.format(script_config.mdbapi, imdb_id))
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
        size = '545455455'

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
        with tor_requests.get_session() as sess:
            try:
                tmdb = ('https://api.themoviedb.org/3/find/{}?api_key={}&language=en&external_source=tvdb_id').format(
                    tvdb_id,
                    script_config.moviedb_key)
                get_tmdb = sess.get(tmdb).json()
                tmdb_id = get_tmdb['tv_results'][0]['id']
            except:
                with tor_requests.get_session() as sess:
                    log.info("TVDb id not found. Grabbing from IMDB")
                    tmdb = (
                        'https://api.themoviedb.org/3/find/{}?api_key={}&language=en&external_source=imdb_id').format(
                        imdb_id,
                        script_config.moviedb_key)
                    get_tmdb = sess.get(tmdb).json()
                    tmdb_id = get_tmdb['tv_results'][0]['id']

    # Season poster, if it fails, falls back to series banner
    with TorRequests() as tor_requests:
        with tor_requests.get_session() as sess:
            try:
                banner_url = ('https://api.themoviedb.org/3/tv/{}/season/{}/images?api_key={}&language=en').format(
                    tmdb_id,
                    season,
                    script_config.moviedb_key)
                banner_data = sess.get(banner_url).json()
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
        print("Trailer not Found. Using 'Never Gonna Give You Up'.")
        trailer_link = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ&ab'

    # API Used
    api_used = mdblist_data['apiused']
    log.info("API Used:" + str(api_used))

    # Series Overview
    with TorRequests() as tor_requests:
        with tor_requests.get_session() as sess:
            series = ('https://api.themoviedb.org/3/tv/{}?api_key={}&language=en').format(tmdb_id,
                                                                                          script_config.moviedb_key)
            series_data = sess.get(series).json()
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

    # Discord Message Format
    message = {
        "username": script_config.sonarr_discord_user,
        "content": 'Grabbed **{}** *S{}E{}* - **{}** from *{}*\n**IMDb**: {} | **Metascore**: {} | **Rotten Tomatoes**: {} | **Trakt**: {} | **TMDb**: {}'.format(
            media_title, season,
            episode, episode_title,
            release_indexer,
            imdb_rating,
            metacritic, rottentomatoes, trakt_rating, tmdb_rating),

        "embeds": [
            {
                "author": {
                    "name": "Sonarr HD",
                    "url": script_config.sonarr_url,
                    "icon_url": script_config.sonarr_icon
                },
                "title": "{}: S{}E{} - {}".format(media_title, season, episode, episode_title),
                "description": "{}\n{}".format("**Overview**", overview),
                "color": 15158332,
                "timestamp": utc_now_iso(),
                "footer": {
                    "icon_url": script_config.sonarr_icon,
                    "text": "{}".format(media_title)
                },
                "url": "{}series/{}".format(script_config.sonarr_url, title_slug),
                "image": {
                    "url": banner
                },
                "fields": [
                    {
                        "name": "Episode",
                        "value": "S{}E{}".format(season, episode),
                        "inline": True
                    },
                    {
                        "name": "Quality",
                        "value": quality,
                        "inline": True
                    },
                    {
                        "name": "Size",
                        "value": "{}".format(humanize.naturalsize(size)),
                        "inline": True
                    },
                    {
                        "name": "Network",
                        "value": "{}".format(network),
                        "inline": True
                    },
                    {
                        "name": "Release Group",
                        "value": release_group,
                        "inline": True
                    },
                    {
                        "name": "Genre",
                        "value": genres,
                        "inline": True
                    },
                    {
                        "name": "Trailer",
                        "value": "[{}]({})".format("Youtube", trailer_link),
                        "inline": True
                    },
                    {
                        "name": "Content Rating",
                        "value": content_rating,
                        "inline": False
                    },
                    {
                        "name": "View Details",
                        "value": "[{}]({}) | [{}]({}) | [{}]({}) | [{}]({}) | [{}]({})".format("IMDb", imdb_url,
                                                                                               "The TVDB",
                                                                                               tvdb_url,
                                                                                               "TMDb",
                                                                                               tmdb_url, "Trakt",
                                                                                               trakt_url,
                                                                                               "TVmaze",
                                                                                               tvmaze_url),
                        "inline": False
                    }
                ],
            },
        ]
    }

    # Logging
    log.info(json.dumps(message, sort_keys=True, indent=4, separators=(',', ': ')))

    # Send notification
    sender = requests.post(script_config.sonarr_discord_url, headers=discord_headers, json=message)
    if eventtype == "Test":
        print("Successfully sent test notification.")
    else:
        print("Successfully sent notification to Discord.")


# Call main
main()
