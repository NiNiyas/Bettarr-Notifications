import json
import logging
import os
import sys
import time
from datetime import datetime

import humanize
import requests
import script_config

slack_headers = {'content-type': 'application/json'}

# Set up the log folder and file
dir = os.path.join(os.path.dirname(sys.argv[0]))
os.chdir(dir)
if not os.path.exists('Logs'):
    os.mkdir('Logs')
log_filename = os.path.join(os.path.dirname(sys.argv[0]), 'Logs/radarr-grab-slack.log')
logging.basicConfig(
    filename=log_filename,
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s'
)
log = logging.getLogger('Radarr')

# Ratings
imdb_id = os.environ.get('radarr_movie_imdbid')
if not imdb_id:
    imdb_id = 'tt0076759'
mdblist = requests.get('https://mdblist.com/api/?apikey={}&i={}'.format(script_config.mdbapi, imdb_id))
mdblist_data = mdblist.json()

# IMDb
imdb_rating = mdblist_data['ratings'][0]['value']

# Metacritic
metacritic = mdblist_data['ratings'][1]['value']

# Trakt
trakt_rating = mdblist_data['ratings'][2]['value']

# TMDb Rating
tmdb_rating = mdblist_data['ratings'][5]['value']

# Rotten Tomatoes
rottentomatoes = mdblist_data['ratings'][3]['value']

# TMDb ID
tmdb_id = os.environ.get('radarr_movie_tmdbid')
if not tmdb_id:
    tmdb_id = '475430'

# Get Event Type
eventtype = os.environ.get('radarr_eventtype')

if eventtype == 'Test':
    TEST_MODE = True
else:
    TEST_MODE = False

# Get variables from Radarr
movie_id = os.environ.get('radarr_movie_id')

media_title = os.environ.get('radarr_movie_title')

quality = os.environ.get('radarr_release_quality')

download_client = os.environ.get('radarr_download_client')

release_indexer = os.environ.get('radarr_release_indexer')

release_size = os.environ.get('radarr_release_size')
if not release_size:
    release_size = '5146516114'

release_group = os.environ.get('radarr_release_releasegroup')

# Service URLs
imdb_url = 'https://www.imdb.com/title/' + imdb_id

tmdb_url = 'https://www.themoviedb.org/movie/' + tmdb_id

moviechat = 'https://moviechat.org/' + imdb_id

trakt_url = 'https://trakt.tv/search/tmdb/' + tmdb_id + '?id_type=movie'

# Get Radarr data
radarr_api_url = '{}api/v3/movie/{}?apikey={}'.format(script_config.radarr_url, movie_id, script_config.radarr_key)

radarr = requests.get(radarr_api_url)

radarr_data = radarr.json()

if not TEST_MODE:
    year = os.environ.get('radarr_movie_year')

if TEST_MODE:
    media_title = 'TEST'
    year = "TEST"

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

try:
    release = moviedb_api_data['movie_results'][0]['release_date']
    release = datetime.strptime(release, "%Y-%m-%d").strftime("%B %d, %Y")
except:
    release = 'Unknown'

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

    # Slack Message Format
message = {
    "blocks": [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "Grabbed New Movie - *{}* ({}) from *{}*\n*IMDb*: {} | *Metascore*: {} | *Rotten Tomatoes*: {} | *TMDb*: {} | *Trakt*: {}".format(
                    media_title, year, release_indexer, imdb_rating, metacritic, rottentomatoes, tmdb_rating, trakt_rating)
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
            }
        },
        {
            "type": "image",
            "image_url": poster_path,
            "alt_text": "Poster"
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
                    "text": "*Size*\n{}".format(humanize.naturalsize(release_size)),
                },
                {
                    "type": "mrkdwn",
                    "text": "*Release Group*\n{}".format(release_group)
                },
                {
                    "type": "mrkdwn",
                    "text": "*Genre*\n{}".format(genres)
                },
                {
                    "type": "mrkdwn",
                    "text": "*Download Client*\n{}".format(download_client)
                },
                {
                    "type": "mrkdwn",
                    "text": "*Trailer*\n<{}|Youtube>".format(trailer_link)
                },
                {
                    "type": "mrkdwn",
                    "text": "*View Details*\n<{}|IMDb> | <{}|TMDb> | <{}|Trakt> | <{}|MovieChat>".format(imdb_url,
                                                                                                          tmdb_url,
                                                                                                          trakt_url,
                                                                                                          moviechat)
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
                        "text": "View Movie on Radarr",

                    },
                    "style": "primary",
                    "url": "{}movie/{}".format(script_config.radarr_url, tmdb_id)
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Go to Radarr",
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
log.info("Sleeping for 20 seconds before sending notifications")
time.sleep(20)
sender = requests.post(script_config.radarr_slack_url, headers=slack_headers, json=message)
