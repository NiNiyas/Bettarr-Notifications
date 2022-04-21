#!/usr/bin/python3

import datetime
import json
import os
import shutil
import sys

from helpers.size import convert_size
from helpers import log
import requests

import config
from helpers import retry
from addons import ratings_radarr

push_url = "https://api.pushover.net/1/messages.json"

eventtype = os.environ.get('radarr_eventtype')


def initialize():
    required_variables = [config.push_user, config.push_radarr, config.radarr_url,
                          config.radarr_key,
                          config.moviedb_key, config.tmdb_country]
    for variable in required_variables:
        if variable == "":
            print("Required variables not set.. Exiting!")
            log.log.error("Please set required variables in script_config.py")
            sys.exit(1)
        else:
            continue


def test_message():
    testmessage = {
        "html": 1,
        "token": config.push_radarr,
        "user": config.push_user,
        "sound": config.push_sound,
        "priority": config.push_priority,
        "device": config.push_device,
        "retry": 60,
        "expire": 3600,
        "message": "<b>Bettarr Notification for Pushover Radarr AIO event test message.\nThank you for using the script!</b>"
    }
    sender = requests.post(push_url, json=testmessage)
    if sender.status_code == 200:
        log.log.info("Successfully sent test notification to Pushover.")
        sys.exit(0)
    else:
        log.log.error(
            "Error occured when trying to send test notification to Pushover. Please open an issue with the below contents.")
        log.log.error("-------------------------------------------------------")
        log.log.error(sender.content)
        log.log.error(json.dumps(testmessage, sort_keys=True, indent=4, separators=(',', ': ')))
        log.log.error("-------------------------------------------------------")
        sys.exit(1)


def grab():
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

    # Radarr API
    radarr = requests.get('{}api/v3/movie/{}?apikey={}'.format(config.radarr_url, movie_id, config.radarr_key))
    radarr = radarr.json()

    # Trailer
    try:
        trailer_link = 'https://www.youtube.com/watch?v={}'.format(radarr['youTubeTrailerId'])
    except (KeyError, TypeError, IndexError):
        log.log.info("Trailer not Found. Using 'Never Gonna Give You Up'.")
        trailer_link = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ&ab'

    # Overview
    try:
        overview = radarr['overview']
    except (KeyError, TypeError, IndexError):
        overview = 'Unknown'

    if len(overview) >= 250:
        overview = overview[:200]
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
    country_code = config.tmdb_country
    providers = []
    try:
        justwatch = retry.requests_retry_session().get(
            'https://api.themoviedb.org/3/movie/{}/watch/providers?api_key={}'.format(tmdb_id,
                                                                                config.moviedb_key))
        tmdbProviders = justwatch.json()
        for p in tmdbProviders["results"][country_code]['flatrate']:
            providers.append(p['provider_name'])
    except (KeyError, TypeError, IndexError):
        log.log.info("Couldn't fetch providers from TMDb. Defaulting to US")
        try:
            for x in ratings_radarr.mdblist_data['streams']:
                stream = (x['name'])
                providers.append(stream)
        except (KeyError, TypeError, IndexError):
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

    if not os.path.exists('Images'):
        os.mkdir('Images')
    response = retry.requests_retry_session().get(poster_path, stream=True)
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

    # Pushover Message Format
    message = {
        "html": 1,
        "token": config.push_radarr,
        "user": config.push_user,
        "sound": config.push_sound,
        "priority": config.push_priority,
        "device": config.push_device,
        "retry": 60,
        "expire": 3600,
        "message": "Grabbed <b>{}</b> ({}) from <i>{}</i>"
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
                   "\n<i>Cast</i>: {}"
                   "\n<i>Director(s)</i>: {}"
                   "\n<i>Available On ({})</i>: {}"
                   "\n<i>Trailer</i>: <a href={}>Youtube</a>".format(media_title, year, release_indexer, overview,
                                                                     ratings_radarr.ratings, release_group, quality,
                                                                     download_client,
                                                                     convert_size(int(release_size)),
                                                                     release, ratings_radarr.certification, genres,
                                                                     actors, directors,
                                                                     country_code, watch_on, trailer_link)
    }

    # Send notification
    try:
        sender = requests.post(push_url, data=message,
                               files={"attachment": (file_path, open(file_path, "rb"), "image/jpeg")})
    except:
        sender = requests.post(push_url, data=message)

    if sender.status_code == 200:
        log.log.info("Successfully sent grab notification to Pushover.")
        sys.exit(0)
    else:
        log.log.error(
            "Error occured when trying to send grab notification to Pushover. Please open an issue with the below contents.")
        log.log.error("-------------------------------------------------------")
        log.log.error(sender.content)
        log.log.error(json.dumps(message, sort_keys=True, indent=4, separators=(',', ': ')))
        log.log.error("-------------------------------------------------------")
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
        log.log.info("Trailer not Found. Using 'Never Gonna Give You Up'.")
        trailer_link = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ&ab'

    # Overview
    try:
        overview = radarr['overview']
    except (KeyError, TypeError, IndexError):
        overview = 'Unknown'

    if len(overview) >= 250:
        overview = overview[:200]
        overview += '...'

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
            log.log.info("Error retrieving backdrop. Defaulting to generic banner.")
            banner = 'https://i.imgur.com/IMQb6ia.png'

    if not os.path.exists('Images'):
        os.mkdir('Images')
    response = retry.requests_retry_session().get(banner, stream=True)
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

    # Upgrade
    if is_upgrade == 'True':
        content = 'Upgraded <b>{}</b> ({})'.format(media_title, year)
    else:
        content = 'Downloaded <b>{}</b> ({})'.format(media_title, year)

    # Pushover Message Format
    message = {
        "html": 1,
        "token": config.push_radarr,
        "user": config.push_user,
        "sound": config.push_sound,
        "priority": config.push_priority,
        "device": config.push_device,
        "retry": 60,
        "expire": 3600,
        "message": "{}"
                   "\n\n<b>Overview</b>\n{}"
                   "\n\n<strong>File Details</strong>"
                   "\n<b>Quality</b>: {}"
                   "\n<b>Release Name</b>: {}"
                   "\n\n<strong>Movie Details</strong>"
                   "\n<b>Release Date</b>: {}"
                   "\n<b>Physical Release</b>: {}"
                   "\n<b>Trailer</b>: <a href={}>Youtube</a>"
                   "\n<b>Genre(s)</b>: {}".format(content, overview, quality, scene_name, release,
                                                  physical_release, trailer_link, genres)
    }

    # Send notification
    try:
        sender = requests.post(push_url, data=message,
                               files={"attachment": (file_path, open(file_path, "rb"), "image/jpeg")})
    except:
        sender = requests.post(push_url, data=message)

    if sender.status_code == 200:
        log.log.info("Successfully sent import notification to Pushover.")
        sys.exit(0)
    else:
        log.log.error(
            "Error occured when trying to send import notification to Pushover. Please open an issue with the below contents.")
        log.log.error("-------------------------------------------------------")
        log.log.error(sender.content)
        log.log.error(json.dumps(message, sort_keys=True, indent=4, separators=(',', ': ')))
        log.log.error("-------------------------------------------------------")
        sys.exit(1)


def health():
    issue_level = os.environ.get('radarr_health_issue_level')

    issue_type = os.environ.get('radarr_health_issue_type')

    issue_message = os.environ.get('radarr_health_issue_message')

    wiki_link = os.environ.get('radarr_health_issue_wiki')

    message = {
        "user": config.push_user,
        "token": config.push_error,
        "html": 1,
        "message": "An error has occured on Radarr"
                   "\n<b>Error Level</b> - {}"
                   "\n<b>Error Type</b> - {}"
                   "\n<b>Error Message</b> - {}"
                   "\n<b>Visit Wiki</b> - <a href={}>Here</a>".format(issue_level, issue_type, issue_message, wiki_link)
    }

    sender = requests.post(push_url, json=message)
    if sender.status_code == 200:
        log.log.info("Successfully sent health notification to Pushover.")
        sys.exit(0)
    else:
        log.log.error(
            "Error occured when trying to send health notification to Pushover. Please open an issue with the below contents.")
        log.log.error("-------------------------------------------------------")
        log.log.error(sender.content)
        log.log.error(json.dumps(message, sort_keys=True, indent=4, separators=(',', ': ')))
        log.log.error("-------------------------------------------------------")
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
