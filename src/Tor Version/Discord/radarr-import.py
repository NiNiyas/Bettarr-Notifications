#!/usr/bin/python3

import datetime
import json
import logging
import os
import sys
import random

import requests
from torpy.http.requests import TorRequests

import script_config

discord_headers = {'content-type': 'application/json'}
headers = {
    "Accept-Encoding": "gzip, deflate",
    "Accept-Language": "en-US,en;q=0.9",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.85 Safari/537.36 Edg/90.0.818.49"
}

colors = ['65405', '15484425', '16270516', '1529855', '14399755', '10947666', '7376755', '1752220', '1146986',
          '3066993', '2067276', '3447003', '2123412', '10181046', '7419530', '15277667',
          '11342935', '15844367', '12745742', '15105570', '11027200', '15158332', '10038562', '9807270', '9936031',
          '8359053', '12370112', '3426654', '2899536', '16776960', '16777215',
          '5793266', '10070709', '2895667', '2303786', '5763719', '16705372', '15418782', '15548997', '16777215',
          '2303786']

# Set up the log folder and file
folder = os.path.join(os.path.dirname(sys.argv[0]))
os.chdir(folder)
if not os.path.exists('Logs'):
    os.mkdir('Logs')
log_filename = os.path.join(os.path.dirname(sys.argv[0]), 'Logs/radarr-import-tor-discord.log')
logging.basicConfig(
    filename=log_filename,
    level=logging.ERROR,
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
    log.error("Radarr didn't have movie's IMDb id. Defaulting to Star Wars: Episode I - The Phantom Menace.")
    imdb_id = 'tt0120915'

# TMDB ID
tmdb_id = os.environ.get('radarr_movie_tmdbid')
if not tmdb_id:
    log.error("Radarr didn't have movie's TMDb id. Defaulting to Star Wars: Episode I - The Phantom Menace.")
    tmdb_id = '1893'

# Get Radarr variables.
eventtype = os.environ.get('radarr_eventtype')

# Discord Test Message Format
testmessage = {
    'content': 'Bettarr Notification for Discord Radarr Import event test message.\nThank you for using the script!'}

# Send test notification
if eventtype == 'Test':
    requests.post(script_config.radarr_discord_url, headers=discord_headers, json=testmessage)
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

# Genres
try:
    genres_data = radarr_data['genres']
    genres = str(genres_data)[1:-1]
    genres = genres.replace("'", "")
except:
    genres = 'Unknown'

# Upgrade
if is_upgrade == 'True':
    content = 'Upgraded Movie: **{}** ({})'.format(media_title, year)
    is_upgrade = 'Yes'
else:
    content = 'New movie downloaded: **{}** ({})'.format(media_title, year)
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
            log.error("Error retrieving backdrop. Defaulting to movie poster.")
            banner_url = moviedb_api_data['movie_results'][0]['poster_path']
            try:
                banner = 'https://image.tmdb.org/t/p/original' + banner_url
            except:
                log.error("Error retrieving backdrop and poster. Defaulting to generic banner.")
                banner = 'https://i.imgur.com/IMQb6ia.png'

# Discord Message Format
message = {
    'username': script_config.radarr_discord_user,
    'embeds': [
        {
            'description': "{}\n\n{}\n{}".format(content, "**Overview**", overview),
            'author': {
                'name': 'Radarr',
                'url': script_config.radarr_url,
                'icon_url': script_config.radarr_icon
            },
            'title': '{}'.format(media_title),
            'footer': {
                'text': "{}".format(scene_name),
                "icon_url": script_config.radarr_icon
            },
            'timestamp': utc_now_iso(),
            'color': random.choice(colors),
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
                    "name": "Upgraded?",
                    "value": is_upgrade,
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
                    "name": 'Genre',
                    "value": genres,
                    "inline": True

                },
                {
                    "name": 'Trailer',
                    "value": "[{}]({})".format("Youtube", trailer_link),
                    "inline": True
                }
            ],
        },
    ]
}

# Send notification
sender = requests.post(script_config.radarr_discord_url, headers=discord_headers, json=message)
log.info(json.dumps(message, sort_keys=True, indent=4, separators=(',', ': ')))
print("Successfully sent notification to Discord.")
