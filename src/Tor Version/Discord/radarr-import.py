import datetime
import json
import logging
import os
import sys

import requests
from torpy.http.requests import TorRequests

import script_config

discord_headers = {'content-type': 'application/json'}

# Set up the log folder and file
dir = os.path.join(os.path.dirname(sys.argv[0]))
os.chdir(dir)
if not os.path.exists('Logs'):
    os.mkdir('Logs')
log_filename = os.path.join(os.path.dirname(sys.argv[0]), 'Logs/radarr-import-tor-discord.log')
logging.basicConfig(
    filename=log_filename,
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s'
)
log = logging.getLogger('Radarr')


# Footer Timestamp
def utc_now_iso():
    utcnow = datetime.datetime.utcnow()
    return utcnow.isoformat()


# IMDb ID
imdb_id = os.environ.get('radarr_movie_imdbid')
if not imdb_id:
    imdb_id = 'tt0120915'

# TMDB ID
tmdb_id = os.environ.get('radarr_movie_tmdbid')
if not tmdb_id:
    tmdb_id = '1893'

# Get Radarr event type
eventtype = os.environ.get('radarr_eventtype')

if eventtype == 'Test':
    TEST_MODE = True
else:
    TEST_MODE = False

# Get Radarr variables
movie_id = os.environ.get('radarr_movie_id')

media_title = os.environ.get('radarr_movie_title')

quality = os.environ.get('radarr_moviefile_quality')

scene_name = os.environ.get('radarr_moviefile_scenename')

is_upgrade = os.environ.get('radarr_isupgrade')

# Service URLs
imdb_url = 'https://www.imdb.com/title/' + imdb_id

# Get Radarr data
radarr_api_url = '{}api/v3/movie/{}?apikey={}'.format(script_config.radarr_url, movie_id, script_config.radarr_key)

radarr = requests.get(radarr_api_url)

radarr_data = radarr.json()

if not TEST_MODE:
    year = radarr_data['year']

if TEST_MODE:
    scene_name = 'Unknown'
    year = 'Unknown'

# Get Trailer Link from Radarr
trailer_link = 'https://www.youtube.com/watch?v={}'.format(radarr_data['youTubeTrailerId'])
if not trailer_link:
    log.info("Trailer not found. Using 'Never Gonna Give You Up'")
    trailer_link = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ&ab'

# Get data from TMDB
with TorRequests() as tor_requests:
    with tor_requests.get_session() as sess:
        moviedb_api_url = 'https://api.themoviedb.org/3/find/{}?api_key={}&external_source=imdb_id'.format(imdb_id,
                                                                                                           script_config.moviedb_key)
        moviedb_api = sess.get(moviedb_api_url)
        moviedb_api_data = moviedb_api.json()

# Overview
try:
    overview = radarr_data['overview']
except:
    overview = 'Unknown'

# Physical Release Date
try:
    physical_release = radarr_data['physicalRelease']
    physical_release = datetime.datetime.strptime(physical_release, "%Y-%m-%dT%H:%M:%SZ").strftime("%B %d, %Y")
except:
    physical_release = 'Unknown'

# Release Date
try:
    release = moviedb_api_data['movie_results'][0]['release_date']
    release = datetime.datetime.strptime(release, "%Y-%m-%d").strftime("%B %d, %Y")
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
    content = 'Upgraded Movie - **{}**'.format(media_title)
    is_upgrade = 'Yes'

else:
    content = 'New movie downloaded - **{}**'.format(media_title)
    is_upgrade = 'No'

# Get Poster from TMDB
poster_path = moviedb_api_data['movie_results'][0]['poster_path']
try:
    poster_path = 'https://image.tmdb.org/t/p/original' + poster_path
except TypeError:
    # Send a generic poster if there is not one for this movie
    poster_path = 'https://i.imgur.com/GoqfZJe.jpg'

# Backdrop
with TorRequests() as tor_requests:
    with tor_requests.get_session() as sess:
        try:
            banner_url = ('https://api.themoviedb.org/3/movie/{}/images?api_key={}&language=en').format(tmdb_id,
                                                                                                        script_config.moviedb_key)

            banner_data = sess.get(banner_url).json()
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

# Discord Message Format
message = {
    'username': script_config.radarr_discord_user,
    'content': content,
    'embeds': [
        {
            'author': {
                'name': 'Radarr HD',
                'url': script_config.radarr_url,
                'icon_url': script_config.radarr_icon
            },
            'title': '{}'.format(media_title),
            'description': "{}\n{}".format("**Overview**", overview),
            'footer': {
                'text': "{}".format(scene_name),
                "icon_url": script_config.radarr_icon

            },
            'timestamp': utc_now_iso(),
            'color': 3394662,
            'url': '{}movie/{}'.format(script_config.radarr_url, tmdb_id),
            'image': {
                'url': banner
            },
            "thumbnail": {
                "url": poster_path
            },
            'fields': [
                {
                    "name": 'Quality',
                    "value": quality,
                    "inline": True
                },
                {
                    "name": 'Release Date',
                    "value": release,
                    "inline": True
                },
                {
                    "name": 'Physical Release Date',
                    "value": physical_release,
                    "inline": True
                },
                {
                    "name": "Upgraded?",
                    "value": is_upgrade,
                    "inline": True
                },
                {
                    "name": 'Trailer',
                    "value": "[{}]({})".format("Youtube", trailer_link),
                    "inline": True
                },
                {
                    "name": 'Genre',
                    "value": genres,
                    "inline": True

                }
            ],
        },
    ]
}

# Log json
log.info(json.dumps(message, sort_keys=True, indent=4, separators=(',', ': ')))

# Send notification
sender = requests.post(script_config.radarr_discord_url, headers=discord_headers, json=message)
if eventtype == 'Test':
    print("Successfully sent test notification")
else:
    print("Successfully sent notification to Discord.")
