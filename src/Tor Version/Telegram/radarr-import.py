import json
import logging
import os
import sys
from datetime import datetime

import requests
from torpy.http.requests import TorRequests

import script_config

headers = {
    "Accept-Encoding": "gzip, deflate",
    "Accept-Language": "en-US,en;q=0.9",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.85 Safari/537.36 Edg/90.0.818.49"
}

tgurl = 'https://api.telegram.org/bot{}/sendMessage'.format(script_config.bot_id)

# Set up the log folder and file
dir = os.path.join(os.path.dirname(sys.argv[0]))
os.chdir(dir)
if not os.path.exists('Logs'):
    os.mkdir('Logs')
log_filename = os.path.join(os.path.dirname(sys.argv[0]), 'Logs/radarr-import-tor-telegram.log')
logging.basicConfig(
    filename=log_filename,
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s'
)
log = logging.getLogger('Radarr')

# IMDb ID
imdb_id = os.environ.get('radarr_movie_imdbid')
if not imdb_id:
    imdb_id = 'tt0120915'

# TMDB ID
tmdb_id = os.environ.get('radarr_movie_tmdbid')
if not tmdb_id:
    tmdb_id = '11'

# Get Radarr variables
eventtype = os.environ.get('radarr_eventtype')

movie_id = os.environ.get('radarr_movie_id')

media_title = os.environ.get('radarr_movie_title')

quality = os.environ.get('radarr_moviefile_quality')

scene_name = os.environ.get('radarr_moviefile_scenename')

is_upgrade = os.environ.get('radarr_isupgrade')

# Get Radarr data
radarr_api_url = '{}api/v3/movie/{}?apikey={}'.format(script_config.radarr_url, movie_id, script_config.radarr_key)
radarr = requests.get(radarr_api_url)
radarr_data = radarr.json()

if eventtype == 'Test':
    TEST_MODE = True
else:
    TEST_MODE = False

if not TEST_MODE:
    try:
        year = os.environ.get('radarr_movie_year')
    except:
        year = "Unknown"

if TEST_MODE:
    media_title = 'Unknown'
    year = 'Unknown'

# Get Trailer Link from Radarr
try:
    trailer_link = 'https://www.youtube.com/watch?v={}'.format(radarr_data['youTubeTrailerId'])
    if trailer_link is None:
        log.info("Trailer not Found. Using 'Never Gonna Give You Up'.")
        trailer_link = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ&ab'
except KeyError:
    log.info("Trailer not Found. Using 'Never Gonna Give You Up'.")
    trailer_link = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ&ab'

# Get data from TMDB
with TorRequests() as tor_requests:
    with tor_requests.get_session(retries=10) as sess:
        moviedb_api_url = 'https://api.themoviedb.org/3/find/{}?api_key={}&external_source=imdb_id'.format(imdb_id,
                                                                                                           script_config.moviedb_key)
        moviedb_api = sess.get(moviedb_api_url, headers=headers, timeout=60)
        moviedb_api_data = moviedb_api.json()

# Overview
try:
    overview = radarr_data['overview']
except:
    overview = 'Unknown'

# Physical Release Date
try:
    physical_release = radarr_data['physicalRelease']
    physical_release = datetime.strptime(physical_release, "%Y-%m-%dT%H:%M:%SZ").strftime("%B %d, %Y")
except:
    physical_release = 'Unknown'

# Release Date
try:
    release = moviedb_api_data['movie_results'][0]['release_date']
    release = datetime.strptime(release, "%Y-%m-%d").strftime("%B %d, %Y")
except:
    release = 'Unknown'

# Genres
try:
    genres_data = radarr_data['genres']
    genres = str(genres_data)[1:-1]
    genres = genres.replace("'", "")
except:
    genres = 'Unknown'

# Upgrade
if is_upgrade == 'True':
    content = 'Upgraded Movie - <b>{}</b>'.format(media_title)
    is_upgrade = 'Yes'
else:
    content = 'New movie downloaded - <b>{}</b>'.format(media_title)
    is_upgrade = 'No'

# Backdrop
with TorRequests() as tor_requests:
    with tor_requests.get_session(retries=10) as sess:
        try:
            banner_url = ('https://api.themoviedb.org/3/movie/{}/images?api_key={}&language=en').format(tmdb_id,
                                                                                                        script_config.moviedb_key)

            banner_data = sess.get(banner_url, headers=headers, timeout=60).json()
            banner = banner_data['backdrops'][0]['file_path']
            banner = 'https://image.tmdb.org/t/p/original' + banner
        except:
            # Falling back to Poster
            log.info("Backdrop not found. Falling back to movie poster.")
            banner_url = moviedb_api_data['movie_results'][0]['poster_path']
            try:
                banner = 'https://image.tmdb.org/t/p/original' + banner_url
            except:
                log.info("Banner not found. Falling back to generic banner.")
                banner = 'https://stratnor.com/wp-content/themes/stratnor/images/no-image.png'

# Telegram Message Format
message = {
    "chat_id": script_config.chat_id,
    "parse_mode": "HTML",
    "text": "{}"
            "\n\n<b>Overview</b>\n{}"
            "\n\n<b>Quality</b> - {}"
            "\n<b>Release Date</b> - {}"
            "\n<b>Physical Release</b> - {}"
            "\n<b>Upgraded?</b> - {}"
            "\n<b>Genre</b> - {}"
            "\n<b>Release Name</b> - {}"
            "\n<a href='{}'>&#8204;</a>".format(content, overview, quality, release, physical_release, is_upgrade,
                                                genres, scene_name, banner),
    "reply_markup": {
        "inline_keyboard": [[
            {
                "text": "Trailer",
                "url": trailer_link
            },
            {
                "text": "View Movie on Radarr",
                "url": '{}movie/{}'.format(script_config.radarr_url, tmdb_id),
            }]
        ]
    }

}

# Send notification
sender = requests.post(tgurl, json=message)

# Logging
log.info(json.dumps(message, sort_keys=True, indent=4, separators=(',', ': ')))

if eventtype == 'Test':
    print("Successfully sent test notification")
else:
    print("Successfully sent notification to Telegram.")
