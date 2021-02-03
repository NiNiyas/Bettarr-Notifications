import json
import logging
import os
import re
import sys
import time

import humanize
import requests

import script_config

# Set up the log folder and file
dir = os.path.join(os.path.dirname(sys.argv[0]))
os.chdir(dir)
if not os.path.exists('Logs'):
    os.mkdir('Logs')
log_filename = os.path.join(os.path.dirname(sys.argv[0]), 'Logs/sonarr-grab-telegram.log')
logging.basicConfig(
    filename=log_filename,
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s'
)
log = logging.getLogger('Sonarr')

# Ratings
imdb_id = os.environ.get('sonarr_series_imdbid')
if not imdb_id:
    imdb_id = 'tt0944947'

mdblist = requests.get('https://mdblist.com/api/?apikey={}&i={}&m=show'.format(script_config.mdbapi, imdb_id))
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

    url = 'https://api.telegram.org/bot{}/sendMessage'.format(script_config.bot_id)

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
    try:
        tmdb = ('https://api.themoviedb.org/3/find/{}?api_key={}&language=en&external_source=tvdb_id').format(tvdb_id,
                                                                                                              script_config.moviedb_key)
        get_tmdb = requests.get(tmdb).json()
        tmdb_id = get_tmdb['tv_results'][0]['id']
    except:
        log.error("Tvdb id not found. Grabbing from IMDB")
        tmdb = ('https://api.themoviedb.org/3/find/{}?api_key={}&language=en&external_source=imdb_id').format(imdb_id,
                                                                                                              script_config.moviedb_key)
        get_tmdb = requests.get(tmdb).json()
        tmdb_id = get_tmdb['tv_results'][0]['id']
        print(tmdb_id)

    # Season poster, if it fails, falls back to series banner
    try:
        banner_url = ('https://api.themoviedb.org/3/tv/{}/season/{}/images?api_key={}&language=en').format(tmdb_id,
                                                                                                           season,
                                                                                                           script_config.moviedb_key)
        banner_data = requests.get(banner_url).json()
        banner = banner_data['posters'][0]['file_path']
        banner = 'https://image.tmdb.org/t/p/original' + banner
    except:
        # Series banner
        log.error("Couldn't fetch season banner. Falling back to series banner")
        try:
            banner = skyhook_data['images'][0]['url']
        except:
            banner = 'http://gearr.scannain.com/wp-content/uploads/2015/02/noposter.jpg'

    # View Details
    tvdb_url = 'https://thetvdb.com/series/' + title_slug

    tvmaze_id = skyhook_data['tvMazeId']

    tvmaze_url = 'https://www.tvmaze.com/shows/' + str(tvmaze_id)

    trakt_url = 'https://trakt.tv/search/tvdb/' + tvdb_id + '?id_type=show'

    imdb_url = ('https://www.imdb.com/title/' + str(imdb_id))

    tmdb_url = 'https://www.themoviedb.org/tv/' + str(tmdb_id)

    try:
        trailer_link = mdblist_data['trailer']
    except:
        log.error("Couldn't find trailer. Using default")
        trailer_link = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ&ab'

    # Series Overview

    series = ('https://api.themoviedb.org/3/tv/{}?api_key={}&language=en').format(tmdb_id,
                                                                                  script_config.moviedb_key)
    series_data = requests.get(series).json()
    overview = series_data['overview']

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
                "\n\n<b>IMDB</b> - {} ⭐| <b>Metacritic</b> - {} | <b>Rotten Tomatoes</b> - {} 🍅\n<b>Trakt</b> - {} | <b>TMDb</b> - {} "
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
                    "text": "The TVDB",
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

    # Log json
    log.info(json.dumps(message, sort_keys=True, indent=4, separators=(',', ': ')))

    # Send notification
    log.info("Sleeping for 30 seconds before sending notifications")
    time.sleep(30)
    sender = requests.post(url, json=message)


# Call main
main()
