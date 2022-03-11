#!/usr/bin/python3

import json
import logging
import os
import shutil
import sys
import datetime

import requests
from torpy.http.requests import TorRequests

import script_config

headers = {
    "Accept-Encoding": "gzip, deflate",
    "Accept-Language": "en-US,en;q=0.9",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.85 Safari/537.36 Edg/90.0.818.49"
}

push_api = 'https://api.pushover.net/1/messages.json'

# Set up the log folder and file
folder = os.path.join(os.path.dirname(sys.argv[0]))
os.chdir(folder)
if not os.path.exists('Logs'):
    os.mkdir('Logs')
log_filename = os.path.join(os.path.dirname(sys.argv[0]), 'Logs/radarr-import-tor-pushover.log')
logging.basicConfig(
    filename=log_filename,
    level=logging.ERROR,
    format='[%(asctime)s] %(levelname)s - %(message)s'
)
log = logging.getLogger('Radarr')

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

# Get Radarr variables
eventtype = os.environ.get('radarr_eventtype')

# Pushover Test Message Format
testmessage = {
    "html": 1,
    "token": script_config.push_radarr,
    "user": script_config.push_user,
    "message": "Bettarr Notification for Pushover Radarr Import event test message.\nThank you for using the script!"
}

# Send test notification
if eventtype == 'Test':
    sender = requests.post(push_api, data=testmessage)
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

if len(overview) >= 200:
    overview = overview[:150]
    overview += '...'

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
    content = 'Upgraded: <b>{}</b> ({})'.format(media_title, year)
    is_upgrade = 'Yes'
else:
    content = 'New movie downloaded: <b>{}</b> ({})'.format(media_title, year)
    is_upgrade = 'No'

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

if not os.path.exists('Images'):
    os.mkdir('Images')
response = requests.get(banner, stream=True)
filename = banner.split("/")[-1]
file_path = os.path.join('Images', filename)
# From https://towardsdatascience.com/how-to-download-an-image-using-python-38a75cfa21c
if response.status_code == 200:
    response.raw.decode_content = True
    with open(file_path, 'wb') as f:
        shutil.copyfileobj(response.raw, f)
    print('Poster successfully downloaded.')
else:
    print('Error retrieving poster.')

# Pushover Message Format
message = {
    "html": "1",
    "token": script_config.push_radarr,
    "user": script_config.push_user,
    "message": "{}"
               "\n\n<b>Overview</b>\n{}"
               "\n\n<strong>File Details</strong>"
               "\n<b>Quality</b>: {}"
               "\n<b>Release Name</b>: {}"
               "\n<b>Upgraded?</b>: {}"
               "\n\n<strong>Movie Details</strong>"
               "\n<b>Release Date</b>: {}"
               "\n<b>Physical Release</b>: {}"
               "\n<b>Genre(s)</b>: {}"
        .format(content, overview, quality, scene_name, is_upgrade, release, physical_release,
                genres)
}

# Send notification
if eventtype == 'Download':
    try:
        sender = requests.post(push_api, data=message,
                               files={"attachment": (file_path, open(file_path, "rb"), "image/jpeg")})
    except:
        sender = requests.post(push_api, data=message)

    print("Successfully sent notification to Pushover.")

# Removing Image
os.remove(file_path)
log.info("Removed poster image. If you want to keep it, comment or remove line 203.")
