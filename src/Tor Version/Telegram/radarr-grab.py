import datetime
import json
import logging
import os
import sys

import humanize
import requests
from torpy.http.requests import TorRequests

import script_config

# Set up the log folder and file
dir = os.path.join(os.path.dirname(sys.argv[0]))
os.chdir(dir)
if not os.path.exists('Logs'):
    os.mkdir('Logs')
log_filename = os.path.join(os.path.dirname(sys.argv[0]), 'Logs/radarr-grab-tor-telegram.log')
logging.basicConfig(
    filename=log_filename,
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s'
)
log = logging.getLogger('Radarr')

# Was getting error : https://github.com/psf/requests/issues/3391#issuecomment-231990544
sess = requests.Session()
adapter = requests.adapters.HTTPAdapter(max_retries=20)
sess.mount('http://', adapter)

# Ratings
imdb_id = os.environ.get('radarr_movie_imdbid')
if not imdb_id:
    imdb_id = 'tt0120915'
mdblist = sess.get('https://mdblist.com/api/?apikey={}&i={}'.format(script_config.mdbapi, imdb_id))
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

# Get Event Type
eventtype = os.environ.get('radarr_eventtype')

url = 'https://api.telegram.org/bot{}/sendMessage'.format(script_config.bot_id)

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
    media_title = 'Unknown'
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

try:
    overview = radarr_data['overview']
except:
    overview = 'Unknown'

try:
    release = moviedb_api_data['movie_results'][0]['release_date']
    release = datetime.datetime.strptime(release, "%Y-%m-%d").strftime("%B %d, %Y")
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

# Telegram Message Format
message = {
    "chat_id": script_config.chat_id,
    "parse_mode": "HTML",
    "text": "Grabbed New Movie - <b>{}</b> ({}) from <i>{}</i>"
            "\n\n<strong>Overview</strong> \n{}"
            "\n\n<b>IMDB</b> - {} ⭐| <b>Metacritic</b> - {} | <b>Rotten Tomatoes</b> - {} 🍅\n<b>TMDb</b> - {} | <b>Trakt</b> - {} "
            "\n\n<b>Release Date</b> - {}"
            "\n<b>Quality</b> - {}"
            "\n<b>Release Group</b> - {}"
            "\n<b>Download Client</b> - {}"
            "\n<b>Size</b> - {}"
            "\n<b>Genre</b> - {}"
            "\n<a href='{}'>&#8204;</a>"
        .format(
        media_title, year,
        release_indexer, overview,
        imdb_rating, metacritic, rottentomatoes, tmdb_rating, trakt_rating, release, quality, release_group,
        download_client,
        humanize.naturalsize(release_size), genres, poster_path),
    "reply_markup": {
        "inline_keyboard": [[
            {
                "text": "Trailer",
                "url": trailer_link
            },
            {
                "text": "IMDb",
                "url": imdb_url
            },
            {
                "text": "TMDB",
                "url": tmdb_url
            },
            {
                "text": "MovieChat",
                "url": moviechat
            },
            {
                "text": "Trakt",
                "url": trakt_url
            }]
        ]
    }

}

# Log json
log.info(json.dumps(message, sort_keys=True, indent=4, separators=(',', ': ')))

# Send notification
sender = requests.post(url, json=message)
if eventtype == 'Test':
    print("Successfully sent test notification")
else:
    print("Successfully sent notification to Telegram.")
