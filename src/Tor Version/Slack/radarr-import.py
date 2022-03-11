#!/usr/bin/python3

import datetime
import json
import logging
import os
import sys

import requests
from torpy.http.requests import TorRequests

import script_config

slack_headers = {'content-type': 'application/json'}
headers = {
    "Accept-Encoding": "gzip, deflate",
    "Accept-Language": "en-US,en;q=0.9",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.85 Safari/537.36 Edg/90.0.818.49"
}

# Set up the log folder and file
folder = os.path.join(os.path.dirname(sys.argv[0]))
os.chdir(folder)
if not os.path.exists('Logs'):
    os.mkdir('Logs')
log_filename = os.path.join(os.path.dirname(sys.argv[0]), 'Logs/radarr-import-tor-slack.log')
logging.basicConfig(
    filename=log_filename,
    level=logging.ERROR,
    format='[%(asctime)s] %(levelname)s - %(message)s'
)
log = logging.getLogger('Radarr')

# IMDB ID
imdb_id = os.environ.get('radarr_movie_imdbid')
if not imdb_id:
    log.error("Radarr didn't have movie's IMDb id. Defaulting to Star Wars: Episode I - The Phantom Menace.")
    imdb_id = 'tt0120915'

# TMDb ID
tmdb_id = os.environ.get('radarr_movie_tmdbid')
if not tmdb_id:
    log.error("Radarr didn't have movie's TMDb id. Defaulting to Star Wars: Episode I - The Phantom Menace.")
    tmdb_id = '1893'

# Get ENV variables.
eventtype = os.environ.get('radarr_eventtype')
testmessage = {
    'text': 'Bettarr Notification for Slack Radarr Import event test message.\nThank you for using the script!'}

# Send test notification
if eventtype == 'Test':
    requests.post(script_config.radarr_slack_url, headers=slack_headers, json=testmessage)
    log.info(json.dumps(testmessage, sort_keys=True, indent=4, separators=(',', ': ')))
    print("Successfully sent test notification.")
    sys.exit(0)

movie_id = os.environ.get('radarr_movie_id')

media_title = os.environ.get('radarr_movie_title')

quality = os.environ.get('radarr_moviefile_quality')

scene_name = os.environ.get('radarr_moviefile_scenename')

is_upgrade = os.environ.get('radarr_isupgrade')

year = os.environ.get('radarr_movie_year')

# Get Radarr data
radarr_api_url = '{}api/v3/movie/{}?apikey={}'.format(script_config.radarr_url, movie_id, script_config.radarr_key)
radarr = requests.get(radarr_api_url)
radarr_data = radarr.json()

# Get Trailer Link from Radarr
try:
    trailer_link = 'https://www.youtube.com/watch?v={}'.format(radarr_data['youTubeTrailerId'])
    if trailer_link is None:
        log.info("Trailer not Found. Using 'Never Gonna Give You Up'.")
        trailer_link = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ&ab'
except:
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
    physical_release = datetime.datetime.strptime(physical_release, "%Y-%m-%dT%H:%M:%SZ").strftime("%B %d, %Y")
except:
    physical_release = 'Unknown'

# Release Date
try:
    release = moviedb_api_data['movie_results'][0]['release_date']
    release = datetime.datetime.strptime(release, "%Y-%m-%d").strftime("%B %d, %Y")
except:
    release = 'Unknown'

# Genre
try:
    genres_data = radarr_data['genres']
    genres = str(genres_data)[1:-1]
    genres = genres.replace("'", "")
except:
    genres = 'Unknown'

# Upgrade
if is_upgrade == 'True':
    content = 'Upgraded Movie: *{}* ({})'.format(media_title, year)
    is_upgrade = 'Yes'
else:
    content = 'New movie downloaded: *{}* ({})'.format(media_title, year)
    is_upgrade = 'No'

# Get Poster from TMDB
poster_path = moviedb_api_data['movie_results'][0]['poster_path']
try:
    poster_path = 'https://image.tmdb.org/t/p/original' + poster_path
except:
    # Send a generic poster if there is not one for this movie
    poster_path = 'https://i.imgur.com/GoqfZJe.jpg'

# Backdrop
with TorRequests() as tor_requests:
    with tor_requests.get_session(retries=10) as sess:
        try:
            banner_url = 'https://api.themoviedb.org/3/movie/{}/images?api_key={}&language=en'.format(tmdb_id,
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
                banner = 'https://i.imgur.com/IMQb6ia.png'

    # Slack Message Format
message = {
    "text": content,
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
                    "text": "*Upgraded?*\n{}".format(is_upgrade)
                },
                {
                    "type": "mrkdwn",
                    "text": "*Release Name*\n{}".format(scene_name)
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
                    "text": "*Genre*\n{}".format(genres)
                },

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
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Trailer"
                    },
                    "url": trailer_link
                }
            ]
        }
    ]
}

# Send notification
sender = requests.post(script_config.radarr_slack_url, headers=slack_headers, json=message)
log.info(json.dumps(message, sort_keys=True, indent=4, separators=(',', ': ')))
print("Successfully sent notification to Slack.")
