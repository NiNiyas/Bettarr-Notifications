import datetime
import json
import logging
import os
import sys

import humanize
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from torpy.http.requests import TorRequests

import script_config

discord_headers = {'content-type': 'application/json'}
headers = {
    "Accept-Encoding": "gzip, deflate",
    "Accept-Language": "en-US,en;q=0.9",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.85 Safari/537.36 Edg/90.0.818.49"
}

# Set up the log folder and file
dir = os.path.join(os.path.dirname(sys.argv[0]))
os.chdir(dir)
if not os.path.exists('Logs'):
    os.mkdir('Logs')
log_filename = os.path.join(os.path.dirname(sys.argv[0]), 'Logs/radarr-grab-tor-discord.log')
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


# From https://www.peterbe.com/plog/best-practice-with-retries-with-requests
def requests_retry_session(
        retries=5,
        backoff_factor=0.3,
        status_forcelist=(500, 502, 504),
        session=None,
):
    session = session or requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session


# Ratings
imdb_id = os.environ.get('radarr_movie_imdbid')
if not imdb_id:
    imdb_id = 'tt0120915'
mdblist = requests_retry_session().get('https://mdblist.com/api/?apikey={}&i={}&m=movie'.format(script_config.mdbapi, imdb_id),
                                       headers=headers)
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

# TMDb ID
tmdb_id = os.environ.get('radarr_movie_tmdbid')
if not tmdb_id:
    tmdb_id = '1893'

# Get variables from Radarr
eventtype = os.environ.get('radarr_eventtype')

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
except TypeError:
    # Send a generic poster if there is not one for this movie
    poster_path = 'https://i.imgur.com/GoqfZJe.jpg'

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

# Discord Message Format
message = {
    'username': script_config.radarr_discord_user,
    'content': 'Grabbed **{}** *({})* from **{}**\n**IMDb**: {} | **Metacritic**: {} | **Rotten Tomatoes**: {} | **TMDb**: {} | **Trakt**: {}'.format(
        media_title,
        year,
        release_indexer,
        imdb_rating,
        metacritic, rottentomatoes, tmdb_rating, trakt_rating),
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
                "icon_url": script_config.radarr_icon,
                'text': "{}".format(media_title)
            },
            'timestamp': utc_now_iso(),
            'color': 15158332,
            'url': '{}movie/{}'.format(script_config.radarr_url, tmdb_id),
            'image': {
                'url': poster_path
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
                    "name": 'Download Client',
                    "value": download_client,
                    "inline": True
                },
                {
                    "name": 'Genre',
                    "value": genres,
                    "inline": True
                },
                {
                    "name": "Trailer",
                    "value": "[{}]({})".format("Youtube", trailer_link),
                    "inline": True
                },
                {
                    "name": "Size",
                    "value": "{}".format(humanize.naturalsize(release_size)),
                    "inline": True
                },
                {
                    "name": 'Release Group',
                    "value": "{}".format(release_group),
                    "inline": True
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

# Logging
log.info(json.dumps(message, sort_keys=True, indent=4, separators=(',', ': ')))

if eventtype == 'Test':
    print("Successfully sent test notification")
else:
    print("Successfully sent notification to Discord.")
