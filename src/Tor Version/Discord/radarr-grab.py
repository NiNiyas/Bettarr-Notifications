#!/usr/bin/python3

import datetime
import json
import logging
import os
import sys
import random

import humanize
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
log_filename = os.path.join(os.path.dirname(sys.argv[0]), 'Logs/radarr-grab-tor-discord.log')
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

# Get variables from Radarr
eventtype = os.environ.get('radarr_eventtype')

# Discord Test Message Format
testmessage = {
    'content': 'Bettarr Notification for Discord Radarr Grab event test message.\nThank you for using the script!'}

# Send test notification
if eventtype == 'Test':
    requests.post(script_config.radarr_discord_url, headers=discord_headers, json=testmessage)
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

# Service URLs
imdb_url = 'https://www.imdb.com/title/' + imdb_id

tmdb_url = 'https://www.themoviedb.org/movie/' + tmdb_id

moviechat = 'https://moviechat.org/' + imdb_id

trakt_url = 'https://trakt.tv/search/tmdb/' + tmdb_id + '?id_type=movie'

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

# Powered by JustWatch and/or mdblist
with TorRequests() as tor_requests:
    providers = []
    with tor_requests.get_session(retries=10) as sess:
        try:
            justwatch = sess.get('https://api.themoviedb.org/3/movie/{}/watch/providers?api_key={}'.format(tmdb_id,
                                                                                                           script_config.moviedb_key))
            tmdbProviders = justwatch.json()
            country_code = script_config.tmdb_country
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

# Discord Message Format
message = {
    'username': script_config.radarr_discord_user,
    'embeds': [
        {
            'description': 'Grabbed **{}** *({})* from **{}**\n\n**Ratings**\n**IMDb**: {} | **Metacritic**: {} | **Rotten Tomatoes**: {} | **TMDb**: {} | **Trakt**: {} | **LetterBoxd**: {}\n\n**Overview**\n{}'.format(
                media_title,
                year,
                release_indexer,
                imdb_rating,
                metacritic, rottentomatoes, tmdb_rating, trakt_rating, letterboxd, overview),
            'author': {
                'name': 'Radarr',
                'url': script_config.radarr_url,
                'icon_url': script_config.radarr_icon
            },
            'title': '{}'.format(media_title),
            'footer': {
                "icon_url": script_config.radarr_icon,
                'text': "{}".format(media_title)
            },
            'timestamp': utc_now_iso(),
            'color': random.choice(colors),
            'url': '{}movie/{}'.format(script_config.radarr_url, tmdb_id),
            'image': {
                'url': poster_path
            },
            'fields': [
                {
                    "name": "Size",
                    "value": "{}".format(humanize.naturalsize(release_size)),
                    "inline": True
                },
                {
                    "name": 'Quality',
                    "value": quality,
                    "inline": True
                },
                {
                    "name": 'Download Client',
                    "value": download_client,
                    "inline": True
                },
                {
                    "name": 'Release Group',
                    "value": "{}".format(release_group),
                    "inline": True
                },
                {
                    "name": 'Release Date',
                    "value": release,
                    "inline": True
                },
                {
                    "name": "Content Rating",
                    "value": "{}".format(certification),
                    "inline": True
                },
                {
                    "name": 'Genre(s)',
                    "value": genres,
                    "inline": False
                },
                {
                    "name": "Available On ({})".format(country_code),
                    "value": "{}".format(watch_on),
                    "inline": False
                },
                {
                    "name": "Trailer",
                    "value": "[{}]({})".format("Youtube", trailer_link),
                    "inline": False
                },
                {
                    "name": 'View Details',
                    "value": "[{}]({}) | [{}]({}) | [{}]({}) | [{}]({})".format("IMDb", imdb_url, "TMDb", tmdb_url,
                                                                                "Trakt",
                                                                                trakt_url, "MovieChat", moviechat),
                    "inline": False
                },
            ],
        },
    ]
}

# Send notification
sender = requests.post(script_config.radarr_discord_url, headers=discord_headers, json=message)
log.info(json.dumps(message, sort_keys=True, indent=4, separators=(',', ': ')))
print("Successfully sent notification to Discord.")
