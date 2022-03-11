#!/usr/bin/python3

import datetime
import json
import os
import sys

from helpers.size import convert_size
from helpers import logging
import requests

import config
from helpers import retry
from addons import ratings_radarr

tg_url = 'https://api.telegram.org/bot{}/sendMessage'.format(config.radarr_botid)
tg_health = 'https://api.telegram.org/bot{}/sendMessage'.format(config.radarr_error_botid)

eventtype = os.environ.get('radarr_eventtype')


def initialize():
    required_variables = [config.chat_id, config.radarr_botid, config.radarr_url,
                          config.radarr_key, config.moviedb_key,
                          config.tmdb_country]
    for variable in required_variables:
        if variable == "":
            print("Required variables not set.. Exiting!")
            logging.log.error("Please set required variables in script_config.py")
            sys.exit(1)
        else:
            continue


def test_message():
    testmessage = {
        "chat_id": config.chat_id,
        "parse_mode": "HTML",
        "disable_notification": config.silent,
        "text": "<b>Bettarr Notification for Telegram Radarr AIO test message.\nThank you for using the script!</b>"
    }
    sender = requests.post(tg_url, json=testmessage)
    if sender.status_code == 200:
        print("Successfully sent test notification to Telegram.")
        logging.log.info(json.dumps(testmessage, sort_keys=True, indent=4, separators=(',', ': ')))
        sys.exit(0)
    else:
        print(
            "Error occured when trying to send test notification to Telegram. Please open an issue with the below contents.")
        print("-------------------------------------------------------")
        print(sender.content)
        logging.log.error(json.dumps(testmessage, sort_keys=True, indent=4, separators=(',', ': ')))
        print("-------------------------------------------------------")
        logging.log.info(json.dumps(testmessage, sort_keys=True, indent=4, separators=(',', ': ')))
        sys.exit(1)


def grab():
    imdb_id = os.environ.get('radarr_movie_imdbid')

    movie_id = os.environ.get('radarr_movie_id')

    media_title = os.environ.get('radarr_movie_title')

    quality = os.environ.get('radarr_release_quality')

    download_client = os.environ.get('radarr_download_client')

    release_indexer = os.environ.get('radarr_release_indexer')

    release_size = os.environ.get('radarr_release_size')

    release_group = os.environ.get('radarr_release_releasegroup')
    if release_group == "":
        release_group = "Unknown"

    tmdb_id = os.environ.get('radarr_movie_tmdbid')

    year = os.environ.get('radarr_movie_year')

    # Service URLs
    imdb_url = 'https://www.imdb.com/title/' + imdb_id

    tmdb_url = 'https://www.themoviedb.org/movie/' + tmdb_id

    moviechat = 'https://moviechat.org/' + imdb_id

    trakt_url = 'https://trakt.tv/search/tmdb/' + tmdb_id + '?id_type=movie'

    # Radarr API
    radarr = requests.get('{}api/v3/movie/{}?apikey={}'.format(config.radarr_url, movie_id, config.radarr_key))
    radarr = radarr.json()

    # Trailer
    try:
        trailer_link = 'https://www.youtube.com/watch?v={}'.format(radarr['youTubeTrailerId'])
    except (KeyError, TypeError, IndexError):
        logging.log.info("Trailer not Found. Using 'Never Gonna Give You Up'.")
        trailer_link = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ&ab'

    # Overview
    try:
        overview = radarr['overview']
    except (KeyError, TypeError, IndexError):
        overview = 'Unknown'

    if len(overview) >= 300:
        overview = overview[:250]
        overview += '...'

    # Genres
    try:
        genres_data = radarr['genres']
        genres = str(genres_data)[1:-1]
        genres = genres.replace("'", "")
    except (KeyError, TypeError, IndexError):
        genres = 'Unknown'

    # TMDB API
    moviedb_api = retry.requests_retry_session().get(
        'https://api.themoviedb.org/3/movie/{}?api_key={}'.format(tmdb_id,
                                                               config.moviedb_key), timeout=60)
    moviedb_api = moviedb_api.json()

    # Cast and Crew
    crew = retry.requests_retry_session().get(
        'https://api.themoviedb.org/3/movie/{}/credits?api_key={}'.format(tmdb_id, config.moviedb_key), timeout=60)
    crew = crew.json()

    cast = []
    for x in crew['cast']:
        cast.append(x['original_name'])
        cast = cast[:3]

    actors = str(cast)[1:-1]
    actors = actors.replace("'", "")
    if not actors:
        actors = "None"

    director = []
    for x in crew['crew']:
        if x['job'] == "Director":
            director.append(x['original_name'])

    directors = str(director)[1:-1]
    directors = directors.replace("'", "")
    if not directors:
        directors = "None"

    # Powered by JustWatch and/or mdblist
    providers = []
    try:
        country_code = config.tmdb_country
        justwatch = retry.requests_retry_session().get(
            'https://api.themoviedb.org/3/movie/{}/watch/providers?api_key={}'.format(tmdb_id,
                                                                                   config.moviedb_key))
        tmdbProviders = justwatch.json()
        for p in tmdbProviders["results"][country_code]['flatrate']:
            providers.append(p['provider_name'])
    except (KeyError, TypeError, IndexError):
        country_code = "US"
        logging.log.info("Couldn't fetch providers from TMDb. Defaulting to US. Fetching from mdblist.")
        try:
            for x in ratings_radarr.mdblist_data['streams']:
                stream = (x['name'])
                providers.append(stream)
        except (KeyError, TypeError, IndexError):
            logging.log.info("Error fetching stream data from mdblist.")
            stream = "None"
            providers.append(stream)

    watch_on = str(providers)[1:-1]
    watch_on = watch_on.replace("'", "")
    if not watch_on:
        watch_on = 'None'

    # Release Date
    try:
        release = moviedb_api['release_date']
        release = datetime.datetime.strptime(release, "%Y-%m-%d").strftime("%B %d, %Y")
    except (KeyError, TypeError, IndexError):
        release = 'Unknown'

    # Get Poster from TMDB
    try:
        poster_path = moviedb_api['poster_path']
        poster_path = 'https://image.tmdb.org/t/p/original' + poster_path
    except (KeyError, TypeError, IndexError):
        # Send a generic poster if there is not one for this movie
        poster_path = 'https://i.imgur.com/GoqfZJe.jpg'

    # Telegram Message Format
    message = {
        "chat_id": config.chat_id,
        "parse_mode": "HTML",
        "disable_notification": config.silent,
        "text": "Grabbed <b>{}</b> ({}) from <i>{}</i>"
                "\n\n<strong>Overview</strong> \n{}"
                "\n\n<strong>Ratings</strong>\n{}"
                "\n\n<strong>File Details</strong>"
                "\n<i>Release Group</i>: {}"
                "\n<i>Quality</i>: {}"
                "\n<i>Download Client</i>: {}"
                "\n<i>Size</i>: {}"
                "\n\n<strong>Movie Details</strong>"
                "\n<i>Release Date</i>: {}"
                "\n<i>Content Rating</i>: {}"
                "\n<i>Genre(s)</i>: {}"
                "\n<i>Cast(s)</i>: {}"
                "\n<i>Director(s)</i>: {}"
                "\n<i>Available On ({})</i>: {}"
                "\n<a href='{}'>&#8204;</a>".format(media_title, year, release_indexer, overview,
                                                    ratings_radarr.ratings,
                                                    release_group, quality, download_client,
                                                    convert_size(int(release_size)),
                                                    release, ratings_radarr.certification, genres, actors, directors,
                                                    country_code,
                                                    watch_on, poster_path),
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

    # Send notification
    sender = requests.post(tg_url, json=message, timeout=60)
    if sender.status_code == 200:
        print("Successfully sent grab notification to Telegram.")
        logging.log.info(json.dumps(message, sort_keys=True, indent=4, separators=(',', ': ')))
        sys.exit(0)
    else:
        print(
            "Error occured when trying to send grab notification to Telegram. Please open an issue with the below contents.")
        print("-------------------------------------------------------")
        print(sender.content)
        logging.log.error(json.dumps(message, sort_keys=True, indent=4, separators=(',', ': ')))
        print("-------------------------------------------------------")
        logging.log.info(json.dumps(message, sort_keys=True, indent=4, separators=(',', ': ')))
        sys.exit(1)


def import_():
    tmdb_id = os.environ.get('radarr_movie_tmdbid')

    movie_id = os.environ.get('radarr_movie_id')

    media_title = os.environ.get('radarr_movie_title')

    quality = os.environ.get('radarr_moviefile_quality')

    scene_name = os.environ.get('radarr_moviefile_scenename')

    is_upgrade = os.environ.get('radarr_isupgrade')

    year = os.environ.get('radarr_movie_year')

    # Radarr API
    radarr = requests.get('{}api/v3/movie/{}?apikey={}'.format(config.radarr_url, movie_id, config.radarr_key))
    radarr = radarr.json()

    # Trailer
    try:
        trailer_link = 'https://www.youtube.com/watch?v={}'.format(radarr['youTubeTrailerId'])
    except (KeyError, TypeError, IndexError):
        logging.log.info("Trailer not Found. Using 'Never Gonna Give You Up'.")
        trailer_link = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ&ab'

    # Overview
    try:
        overview = radarr['overview']
    except (KeyError, TypeError, IndexError):
        overview = 'Unknown'

    # Genres
    try:
        genres_data = radarr['genres']
        genres = str(genres_data)[1:-1]
        genres = genres.replace("'", "")
    except (KeyError, TypeError, IndexError):
        genres = 'Unknown'

    # Physical release date
    try:
        physical_release = radarr['physicalRelease']
        physical_release = datetime.datetime.strptime(physical_release, "%Y-%m-%dT%H:%M:%SZ").strftime("%B %d, %Y")
    except (KeyError, TypeError, IndexError):
        physical_release = 'Unknown'

    # TMDB API
    moviedb_api = retry.requests_retry_session().get(
        'https://api.themoviedb.org/3/movie/{}?api_key={}'.format(tmdb_id,
                                                               config.moviedb_key), timeout=60)
    moviedb_api = moviedb_api.json()

    # Release Date
    try:
        release = moviedb_api['release_date']
        release = datetime.datetime.strptime(release, "%Y-%m-%d").strftime("%B %d, %Y")
    except (KeyError, TypeError, IndexError):
        release = 'Unknown'

    # Backdrop
    try:
        banner_data = retry.requests_retry_session().get(
            'https://api.themoviedb.org/3/movie/{}/images?api_key={}&language=en'.format(tmdb_id,
                                                                                      config.moviedb_key),
            timeout=60).json()
        banner = banner_data['backdrops'][0]['file_path']
        banner = 'https://image.tmdb.org/t/p/original' + banner
    except (KeyError, TypeError, IndexError):
        banner_url = moviedb_api['backdrop_path']
        try:
            banner = 'https://image.tmdb.org/t/p/original' + banner_url
        except (KeyError, TypeError, IndexError):
            logging.log.info("Error retrieving backdrop. Defaulting to generic banner.")
            banner = 'https://i.imgur.com/IMQb6ia.png'

    # Upgrade
    if is_upgrade == 'True':
        content = 'Upgraded <b>{}</b> ({})'.format(media_title, year)
    else:
        content = 'Downloaded <b>{}</b> ({})'.format(media_title, year)

    # Telegram Message Format
    message = {
        "chat_id": config.chat_id,
        "disable_notification": config.silent,
        "parse_mode": "HTML",
        "text": "{}"
                "\n\n<b>Overview</b>\n{}"
                "\n\n<strong>File Details</strong>"
                "\n<b>Quality</b>: {}"
                "\n<b>Release Name</b>: {}"
                "\n\n<strong>Movie Details</strong>"
                "\n<b>Release Date</b>: {}"
                "\n<b>Physical Release</b>: {}"
                "\n<b>Genre(s)</b>: {}"
                "\n<a href='{}'>&#8204;</a>".format(content, overview, quality, scene_name, release,
                                                    physical_release,
                                                    genres, banner),
        "reply_markup": {
            "inline_keyboard": [[
                {
                    "text": "Trailer",
                    "url": trailer_link
                },
                {
                    "text": "View Movie on Radarr",
                    "url": '{}movie/{}'.format(config.radarr_url, tmdb_id),
                }]
            ]
        }
    }

    # Send notification
    sender = requests.post(tg_url, json=message)
    if sender.status_code == 200:
        print("Successfully sent import notification to Telegram.")
        logging.log.info(json.dumps(message, sort_keys=True, indent=4, separators=(',', ': ')))
        sys.exit(0)
    else:
        print(
            "Error occured when trying to send import notification to Telegram. Please open an issue with the below contents.")
        print("-------------------------------------------------------")
        print(sender.content)
        logging.log.error(json.dumps(message, sort_keys=True, indent=4, separators=(',', ': ')))
        print("-------------------------------------------------------")
        logging.log.info(json.dumps(message, sort_keys=True, indent=4, separators=(',', ': ')))
        sys.exit(1)


def health():
    issue_level = os.environ.get('radarr_health_issue_level')

    issue_type = os.environ.get('radarr_health_issue_type')

    issue_message = os.environ.get('radarr_health_issue_message')

    wiki_link = os.environ.get('radarr_health_issue_wiki')

    message = {
        "chat_id": config.error_channel,
        "parse_mode": "HTML",
        "text": "An error has occured on Radarr"
                "\n\n<b>Error Level</b> - {}"
                "\n\n<b>Error Type</b> - {}"
                "\n<b>Error Message</b> - {}".format(issue_level, issue_type, issue_message),
        "reply_markup": {
            "inline_keyboard": [[
                {
                    "text": "Visit Radarr",
                    "url": config.radarr_url
                },
                {
                    "text": "Visit Wiki",
                    "url": wiki_link
                }]
            ]
        }

    }

    sender = requests.post(tg_health, json=message)
    if sender.status_code == 200:
        print("Successfully sent health notification to Telegram.")
        logging.log.info(json.dumps(message, sort_keys=True, indent=4, separators=(',', ': ')))
        sys.exit(0)
    else:
        print(
            "Error occured when trying to send health notification to Telegram. Please open an issue with the below contents.")
        print("-------------------------------------------------------")
        print(sender.content)
        logging.log.error(json.dumps(message, sort_keys=True, indent=4, separators=(',', ': ')))
        print("-------------------------------------------------------")
        logging.log.info(json.dumps(message, sort_keys=True, indent=4, separators=(',', ': ')))
        sys.exit(1)


if eventtype == "Test":
    initialize()
    test_message()

if eventtype == "Grab":
    initialize()
    grab()

if eventtype == "Download":
    initialize()
    import_()

if eventtype == "HealthIssue":
    initialize()
    health()
