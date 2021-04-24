import json
import logging
import os
import sys
from datetime import datetime

import requests

import script_config

slack_headers = {'content-type': 'application/json'}

# Set up the log folder and file
dir = os.path.join(os.path.dirname(sys.argv[0]))
os.chdir(dir)
if not os.path.exists('Logs'):
    os.mkdir('Logs')
log_filename = os.path.join(os.path.dirname(sys.argv[0]), 'Logs/radarr-import-slack.log')
logging.basicConfig(
    filename=log_filename,
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s'
)
log = logging.getLogger('Radarr')

# IMDB ID
imdb_id = os.environ.get('radarr_movie_imdbid')
if not imdb_id:
    imdb_id = 'tt0120915'

# TMDb ID
tmdb_id = os.environ.get('radarr_movie_tmdbid')
if not tmdb_id:
    tmdb_id = '11'

# Get Event Type
eventtype = os.environ.get('radarr_eventtype')

if eventtype == 'Test':
    TEST_MODE = True
else:
    TEST_MODE = False

# Get ENV variables
movie_id = os.environ.get('radarr_movie_id')
if not movie_id:
    movie_id = '10'

media_title = os.environ.get('radarr_movie_title')

quality = os.environ.get('radarr_moviefile_quality')

scene_name = os.environ.get('radarr_moviefile_scenename')

is_upgrade = os.environ.get('radarr_isupgrade')

release_size = os.environ.get('radarr_release_size')
if not release_size:
    release_size = '5146516114'

# Service URLs
imdb_url = 'https://www.imdb.com/title/' + imdb_id

# Get Radarr data
radarr_api_url = '{}api/v3/movie/{}?apikey={}'.format(script_config.radarr_url, movie_id, script_config.radarr_key)
radarr = requests.get(radarr_api_url)
radarr_data = radarr.json()

if not TEST_MODE:
    year = os.environ.get('radarr_movie_year')

if TEST_MODE:
    media_title = 'Unknown'
    year = 'Unknown'

# Get Trailer Link from Radarr
try:
    trailer_link = 'https://www.youtube.com/watch?v={}'.format(radarr_data['youTubeTrailerId'])
except:
    trailer_link = 'None'

# Get data from TMDB
moviedb_api_url = 'https://api.themoviedb.org/3/find/{}?api_key={}&external_source=imdb_id'.format(imdb_id,
                                                                                                   script_config.moviedb_key)
moviedb_api = requests.get(moviedb_api_url)
moviedb_api_data = moviedb_api.json()
radarr_id = moviedb_api_data['movie_results'][0]['id']

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

# Upgrade or not
if is_upgrade == 'True':
    content = 'Upgraded Movie - *{}*'.format(media_title)
    is_upgrade = 'Yes'

else:
    content = 'New movie downloaded - *{}*'.format(media_title)
    is_upgrade = 'No'

# Genre
try:
    genres_data = radarr_data['genres']
    genres = str(genres_data)[1:-1]
    genres = genres.replace("'", "")
except:
    genres = 'Unknown'

# Get Poster from TMDB
poster_path = moviedb_api_data['movie_results'][0]['poster_path']
try:
    poster_path = 'https://image.tmdb.org/t/p/original' + poster_path
except TypeError:
    # Send a generic poster if there is not one for this movie
    poster_path = 'https://i.imgur.com/GoqfZJe.jpg'

# Backdrop
try:
    banner_url = ('https://api.themoviedb.org/3/movie/{}/images?api_key={}&language=en').format(tmdb_id,
                                                                                                script_config.moviedb_key)

    banner_data = requests.get(banner_url).json()
    banner = banner_data['backdrops'][0]['file_path']
    banner = 'https://image.tmdb.org/t/p/original' + banner
except:
    # Falling back to Poster
    log.info("Backdrop not found. Falling back to movie poster.")
    banner_url = moviedb_api_data['movie_results'][0]['poster_path']
    try:
        banner = 'https://image.tmdb.org/t/p/original' + banner_url
    except TypeError:
        # Send a generic poster if there is not one for this movie
        log.info("Banner not found. Falling back to generic banner.")
        banner = 'https://stratnor.com/wp-content/themes/stratnor/images/no-image.png'

    # Slack Message Format
message = {
    "blocks": [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": content
            }
        },
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "Overview"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": overview
            },
            "accessory": {
                "type": "image",
                "image_url": poster_path,
                "alt_text": "Poster"
            }
        },
        {
            "type": "image",
            "image_url": banner,
            "alt_text": "Banner"
        },
        {
            "type": "divider"
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": "*Quality*\n{}".format(quality)
                },
                {
                    "type": "mrkdwn",
                    "text": "*Release Date*\n{}".format(release)
                },
                {
                    "type": "mrkdwn",
                    "text": "*Physical Release Date*\n{}".format(physical_release)
                },
                {
                    "type": "mrkdwn",
                    "text": "*Upgraded?*\n{}".format(is_upgrade)
                },
                {
                    "type": "mrkdwn",
                    "text": "*Genre*\n{}".format(genres)
                },
                {
                    "type": "mrkdwn",
                    "text": "*Release Name*\n{}".format(scene_name)
                },
                {
                    "type": "mrkdwn",
                    "text": "*Trailer:*\n<{}|Youtube>".format(trailer_link)
                }
            ]
        },
        {
            "type": "divider"
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "View Movie on Radarr"

                    },
                    "style": "primary",
                    "url": "{}movie/{}".format(script_config.radarr_url, tmdb_id)
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Go to Radarr"
                    },
                    "url": script_config.radarr_url
                }
            ]
        }
    ]
}

# Log json
log.info(json.dumps(message, sort_keys=True, indent=4, separators=(',', ': ')))

# Send notification
sender = requests.post(script_config.radarr_slack_url, headers=slack_headers, json=message)
if eventtype == "Test":
    print("Successfully sent test notification.")
else:
    print("Successfully sent notification to Slack.")
