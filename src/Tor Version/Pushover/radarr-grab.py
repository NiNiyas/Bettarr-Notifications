#!/usr/bin/python3

import datetime
import json
import logging
import os
import sys
import shutil

import humanize
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
log_filename = os.path.join(os.path.dirname(sys.argv[0]), 'Logs/radarr-grab-tor-pushover.log')
logging.basicConfig(
    filename=log_filename,
    level=logging.ERROR,
    format='[%(asctime)s] %(levelname)s - %(message)s'
)
log = logging.getLogger('Radarr')

# Ratings
imdb_id = os.environ.get('radarr_movie_imdbid')
if not imdb_id:
    log.error("Radarr didn't have movie's IMDb id. Defaulting to Star Wars: Episode I - The Phantom Menace.")
    imdb_id = 'tt0120915'
mdblist = requests.get(
    'https://mdblist.com/api/?apikey={}&i={}&m=movie'.format(script_config.mdbapi, imdb_id),
    headers=headers)
mdblist_data = mdblist.json()

# IMDb
try:
    imdb_rating = mdblist_data['ratings'][0]['value']
except:
    log.error("Error fetching IMDb rating from mdblist.")
    imdb_rating = 'None'

# Metacritic
try:
    metacritic = mdblist_data['ratings'][1]['value']
except:
    log.error("Error fetching Metacritic rating from mdblist.")
    metacritic = 'None'

# Trakt
try:
    trakt_rating = mdblist_data['ratings'][3]['value']
except:
    log.error("Error fetching Trakt rating from mdblist.")
    trakt_rating = 'None'

# TMDb Rating
try:
    tmdb_rating = mdblist_data['ratings'][6]['value']
except:
    log.error("Error fetching TMDb rating from mdblist.")
    tmdb_rating = 'None'

# Rotten Tomatoes
try:
    rottentomatoes = mdblist_data['ratings'][4]['value']
except:
    log.error("Error fetching Tomatoes rating from mdblist.")
    rottentomatoes = 'None'

# LetterBoxd
try:
    letterboxd = mdblist_data['ratings'][7]['value']
except:
    log.error("Error fetching LetterBoxd rating from mdblist.")
    letterboxd = 'None'

# Certification
try:
    certification = mdblist_data['certification']
except:
    certification = 'None'

# TMDb ID
tmdb_id = os.environ.get('radarr_movie_tmdbid')
if not tmdb_id:
    tmdb_id = '1893'

# More info on https://wiki.servarr.com/radarr/custom-scripts
eventtype = os.environ.get('radarr_eventtype')

# Pushover Test Message Format
testmessage = {
    "html": 1,
    "token": script_config.push_radarr,
    "user": script_config.push_user,
    "message": "Bettarr Notification for Pushover Radarr Grab event test message.\nThank you for using the script!"
}

# Send test notification
if eventtype == 'Test':
    sender = requests.post(push_api, data=testmessage)
    log.info(json.dumps(testmessage, sort_keys=True, indent=4, separators=(',', ': ')))
    print("Successfully sent test notification.")
    sys.exit(0)

movie_id = os.environ.get('radarr_movie_id')

media_title = os.environ.get('radarr_movie_title')

quality = os.environ.get('radarr_release_quality')

download_client = os.environ.get('radarr_download_client')

release_indexer = os.environ.get('radarr_release_indexer')

release_size = os.environ.get('radarr_release_size')

release_group = os.environ.get('radarr_release_releasegroup')

year = os.environ.get('radarr_movie_year')

# Get Radarr data
radarr_api_url = '{}api/v3/movie/{}?apikey={}'.format(script_config.radarr_url, movie_id, script_config.radarr_key)
radarr = requests.get(radarr_api_url)
radarr_data = radarr.json()

# Get trailer link from Radarr
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

# Powered by JustWatch and/or mdblist
providers = []
country_code = script_config.tmdb_country
with TorRequests() as tor_requests:

    with tor_requests.get_session(retries=10) as sess:
        try:
            justwatch = sess.get('https://api.themoviedb.org/3/movie/{}/watch/providers?api_key={}'.format(tmdb_id,
                                                                                                           script_config.moviedb_key))
            tmdbProviders = justwatch.json()
            for p in tmdbProviders["results"][country_code]['flatrate']:
                providers.append(p['provider_name'])
        except:
            log.error("Couldn't fetch providers from TMDb. Defaulting to US")
        try:
            for x in mdblist_data['streams']:
                stream = (x['name'])
                providers.append(stream)
        except:
            stream = "None"

watch_on = str(providers)[1:-1]
watch_on = watch_on.replace("'", "")
if not watch_on:
    watch_on = 'None'

# Overview
try:
    overview = radarr_data['overview']
except:
    overview = 'Unknown'

if len(overview) >= 200:
    overview = overview[:150]
    overview += '...'

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

# Get Poster from TMDB
poster_path = moviedb_api_data['movie_results'][0]['poster_path']
try:
    poster_path = 'https://image.tmdb.org/t/p/original' + poster_path
except:
    # Send a generic poster if there is not one for this movie
    poster_path = 'https://i.imgur.com/GoqfZJe.jpg'

if not os.path.exists('Images'):
    os.mkdir('Images')
response = requests.get(poster_path, stream=True)
filename = poster_path.split("/")[-1]
file_path = os.path.join('Images', filename)
# From https://towardsdatascience.com/how-to-download-an-image-using-python-38a75cfa21c
if response.status_code == 200:
    response.raw.decode_content = True
    with open(file_path, 'wb') as f:
        shutil.copyfileobj(response.raw, f)
    print('Poster successfully downloaded.')
else:
    print('Error retrieving poster.')

# Pushover Grab Message Format
message = {
    "html": "1",
    "token": script_config.push_radarr,
    "user": script_config.push_user,
    "message": "Grabbed <b>{}</b> ({}) from <i>{}</i>"
               "\n\n<strong>Overview</strong> \n{}"
               "\n\n<strong>Ratings</strong>"
               "\n<i>IMDB</i>: {} \n<i>Metacritic</i>: {}\n<i>Rotten Tomatoes</i>: {} \n<i>TMDb</i>: {} \n<i>Trakt</i>: {} \n<i>LetterBoxd</i>: {}"
               "\n\n<strong>File Details</strong>"
               "\n<i>Release Group</i>: {}"
               "\n<i>Quality</i>: {}"
               "\n<i>Download Client</i>: {}"
               "\n<i>Size</i>: {}"
               "\n\n<strong>Movie Details</strong>"
               "\n<i>Release Date</i>: {}"
               "\n<i>Content Rating</i>: {}"
               "\n<i>Genre(s)</i>: {}"
               "\n<i>Available On ({})</i>: {}"
               "\n<i>Trailer</i>: <a href={}>Youtube</a>"
        .format(media_title, year, release_indexer, overview, imdb_rating, metacritic, rottentomatoes, tmdb_rating,
                trakt_rating,
                letterboxd, release_group, quality, download_client, humanize.naturalsize(release_size),
                release, certification, genres, country_code, watch_on, trailer_link)
}

# Send grab notification
if eventtype == 'Grab':
    try:
        sender = requests.post(push_api, data=message,
                               files={"attachment": (file_path, open(file_path, "rb"), "image/jpeg")})
    except:
        sender = requests.post(push_api, data=message)
    print("Successfully sent notification to Pushover.")

# Removing Image
os.remove(file_path)
log.info("Removed poster image. If you want to keep it, comment or remove line 264.")

# Logging
log.info(json.dumps(message, sort_keys=True, indent=4, separators=(',', ': ')))
