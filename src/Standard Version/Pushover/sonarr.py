#!/usr/bin/python3

import json
import os
import re
import shutil
import sys

from helpers.size import convert_size
from helpers import logging
import requests

import config
from helpers import retry
from addons import ratings_sonarr

push_url = "https://api.pushover.net/1/messages.json"

eventtype = os.environ.get('sonarr_eventtype')


def initialize():
    required_variables = [config.push_user, config.push_sonarr, config.moviedb_key,
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
        "html": 1,
        "token": config.push_sonarr,
        "user": config.push_user,
        "sound": config.push_sound,
        "priority": config.push_priority,
        "device": config.push_device,
        "retry": 60,
        "expire": 3600,
        "message": "<b>Bettarr Notification for Pushover Sonarr AIO test message.\nThank you for using the script!</b>"
    }
    sender = requests.post(push_url, json=testmessage)
    if sender.status_code == 200:
        print("Successfully sent test notification to Pushover.")
        logging.log.info(json.dumps(testmessage, sort_keys=True, indent=4, separators=(',', ': ')))
        sys.exit(0)
    else:
        print(
            "Error occured when trying to send test notification to Pushover. Please open an issue with the below contents.")
        print("-------------------------------------------------------")
        print(sender.content)
        logging.log.error(json.dumps(testmessage, sort_keys=True, indent=4, separators=(',', ': ')))
        print("-------------------------------------------------------")
        logging.log.info(json.dumps(testmessage, sort_keys=True, indent=4, separators=(',', ': ')))
        sys.exit(1)


def grab():
    imdb_id = os.environ.get('sonarr_series_imdbid')

    season = os.environ.get('sonarr_release_seasonnumber')

    episode = os.environ.get('sonarr_release_episodenumbers')

    tvdb_id = os.environ.get('sonarr_series_tvdbid')

    size = os.environ.get('sonarr_release_size')

    release_group = os.environ.get('sonarr_release_releasegroup')
    if release_group == "":
        release_group = "Unknown"

    media_title = os.environ.get('sonarr_series_title')

    episode_title = os.environ.get('sonarr_release_episodetitles')

    quality = os.environ.get('sonarr_release_quality')

    release_indexer = os.environ.get('sonarr_release_indexer')

    download_client = os.environ.get('sonarr_download_client')

    # Get show information from skyhook
    skyhook = retry.requests_retry_session().get('http://skyhook.sonarr.tv/v1/tvdb/shows/en/{}'.format(tvdb_id)).json()

    # Content Rating
    try:
        content_rating = skyhook['contentRating']
    except (KeyError, TypeError, IndexError):
        try:
            content_rating = ratings_sonarr.certification
        except (KeyError, TypeError, IndexError):
            content_rating = "Unkown"

    # Network
    try:
        network = skyhook['network']
    except (KeyError, TypeError, IndexError):
        network = 'Unknown'

    # Genres
    try:
        genres = json.dumps(skyhook['genres'])
        genres = re.sub(r'[?|$|.|!|:|/|\]|\[|\"]', r'', genres)
    except (KeyError, TypeError, IndexError):
        genres = 'Unknown'

    # TMDb ID
    try:
        tmdb = retry.requests_retry_session().get(
            'https://api.themoviedb.org/3/find/{}?api_key={}&language=en&external_source=tvdb_id'.format(
                tvdb_id,
                config.moviedb_key), timeout=20).json()
        tmdb_id = tmdb['tv_results'][0]['id']
    except (KeyError, TypeError, IndexError):
        tmdb = retry.requests_retry_session().get(
            'https://api.themoviedb.org/3/find/{}?api_key={}&language=en&external_source=imdb_id'.format(
                imdb_id,
                config.moviedb_key), timeout=20).json()
        tmdb_id = tmdb['tv_results'][0]['id']

    # Cast and Crew
    crew = retry.requests_retry_session().get(
        'https://api.themoviedb.org/3/tv/{}/credits?api_key={}'.format(tmdb_id, config.moviedb_key), timeout=60)
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

    # Poster
    try:
        poster = retry.requests_retry_session().get(
            'https://api.themoviedb.org/3/tv/{}/season/{}/images?api_key={}&language=en'.format(
                tmdb_id,
                season,
                config.moviedb_key), timeout=20).json()
        poster = poster['posters'][0]['file_path']
        poster = 'https://image.tmdb.org/t/p/original' + poster
    except (KeyError, TypeError, IndexError):
        try:
            poster = skyhook['images'][0]['url']
        except (KeyError, TypeError, IndexError):
            poster = 'http://gearr.scannain.com/wp-content/uploads/2015/02/noposter.jpg'

    # Downloading Poster
    if not os.path.exists('Images'):
        os.mkdir('Images')
    response = retry.requests_retry_session().get(poster, stream=True)
    filename = poster.split("/")[-1]
    file_path = os.path.join('Images', filename)
    if response.status_code == 200:
        response.raw.decode_content = True
        with open(file_path, 'wb') as f:
            shutil.copyfileobj(response.raw, f)
        print('Poster successfully downloaded.')
    else:
        print('Error retrieving poster.')

    # Powered by JustWatch and/or mdblist
    country_code = config.tmdb_country
    providers = []
    try:
        justwatch = retry.requests_retry_session().get(
            'https://api.themoviedb.org/3/tv/{}/watch/providers?api_key={}'.format(tmdb_id,
                                                                                config.moviedb_key))
        tmdbProviders = justwatch.json()
        for p in tmdbProviders["results"][country_code]['flatrate']:
            providers.append(p['provider_name'])
    except (KeyError, TypeError, IndexError):
        logging.log.info("Couldn't fetch providers from TMDb. Defaulting to US")
        try:
            for x in ratings_sonarr.mdblist_data['streams']:
                stream = (x['name'])
                providers.append(stream)
        except (KeyError, TypeError, IndexError):
            stream = "None"
            providers.append(stream)

    watch_on = str(providers)[1:-1]
    watch_on = watch_on.replace("'", "")
    if not watch_on:
        watch_on = 'None'

    # Trailer
    try:
        trailer_link = ratings_sonarr.trailer
    except (KeyError, TypeError, IndexError):
        logging.log.info("Trailer not Found. Using 'Never Gonna Give You Up'.")
        trailer_link = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ&ab'

    # Series Overview
    series = retry.requests_retry_session().get(
        'https://api.themoviedb.org/3/tv/{}?api_key={}&language=en'.format(tmdb_id,
                                                                        config.moviedb_key),
        timeout=20).json()
    overview = series['overview']

    if len(overview) >= 250:
        overview = overview[:200]
        overview += '...'

    # Formatting Season and Episode
    if len(str(season)) == 1:
        season = '0{}'.format(season)
    if len(str(episode)) == 1:
        episode = '0{}'.format(episode)

    # Pushover Message Format
    message = {
        "html": 1,
        "token": config.push_sonarr,
        "user": config.push_user,
        "sound": config.push_sound,
        "priority": config.push_priority,
        "device": config.push_device,
        "retry": 60,
        "expire": 3600,
        "message": "Grabbed <b>{}</b>: <i>S{}E{}</i> - <b>{}</b> from <i>{}</i>"
                   "\n\n<strong>Overview</strong> \n{}"
                   "\n\n<strong>Ratings</strong>\n{}"
                   "\n\n<strong>File Details</strong>"
                   "\n<i>Episode</i>: S{}E{}"
                   "\n<i>Release Group</i>: {}"
                   "\n<i>Quality</i>: {}"
                   "\n<i>Size</i>: {}"
                   "\n<i>Download Client</i>: {}"
                   "\n\n<strong>Show Details</strong>"
                   "\n<i>Content Rating</i>: {}"
                   "\n<i>Network</i>: {}"
                   "\n<i>Genre(s)</i>: {}"
                   "\n<i>Cast</i>: {}"
                   "\n<i>Director(s)</i>: {}"
                   "\n<i>Available On ({})</i>: {}"
                   "\n<i>Trailer</pre>: <a href={}>Youtube</a>".format(media_title, season, episode, episode_title,
                                                                       release_indexer, overview,
                                                                       ratings_sonarr.ratings,
                                                                       season, episode, release_group, quality,
                                                                       (convert_size(int(size))), download_client,
                                                                       content_rating,
                                                                       network, genres, actors, directors, country_code,
                                                                       watch_on,
                                                                       trailer_link)
    }

    # Send notification
    try:
        sender = requests.post(push_url, data=message,
                               files={"attachment": (file_path, open(file_path, "rb"), "image/jpeg")})
    except:
        sender = requests.post(push_url, data=message)

    if sender.status_code == 200:
        print("Successfully sent grab notification to Pushover.")
        logging.log.info(json.dumps(message, sort_keys=True, indent=4, separators=(',', ': ')))
        sys.exit(0)
    else:
        print(
            "Error occured when trying to send grab notification to Pushover. Please open an issue with the below contents.")
        print("-------------------------------------------------------")
        print(sender.content)
        print("-------------------------------------------------------")
        logging.log.info(json.dumps(message, sort_keys=True, indent=4, separators=(',', ': ')))
        sys.exit(1)


def import_():
    season = os.environ.get('sonarr_episodefile_seasonnumber')

    episode = os.environ.get('sonarr_episodefile_episodenumbers')

    tvdb_id = os.environ.get('sonarr_series_tvdbid')

    scene_name = os.environ.get('sonarr_episodefile_scenename')

    media_title = os.environ.get('sonarr_series_title')

    episode_title = os.environ.get('sonarr_episodefile_episodetitles')

    quality = os.environ.get('sonarr_episodefile_quality')

    is_upgrade = os.environ.get('sonarr_isupgrade')

    # Get show information from skyhook
    skyhook = retry.requests_retry_session().get('http://skyhook.sonarr.tv/v1/tvdb/shows/en/{}'.format(tvdb_id)).json()

    imdb_id = os.environ.get('sonarr_series_imdbid')
    if not imdb_id:
        imdb_id = 'tt0944947'

    # TMDb ID
    try:
        tmdb = retry.requests_retry_session().get(
            'https://api.themoviedb.org/3/find/{}?api_key={}&language=en&external_source=tvdb_id'.format(
                tvdb_id,
                config.moviedb_key), timeout=20).json()
        tmdb_id = tmdb['tv_results'][0]['id']
    except (KeyError, TypeError, IndexError):
        tmdb = retry.requests_retry_session().get(
            'https://api.themoviedb.org/3/find/{}?api_key={}&language=en&external_source=imdb_id'.format(
                imdb_id,
                config.moviedb_key)).json()
        tmdb_id = tmdb['tv_results'][0]['id']

    # Episode Sample
    try:
        episode_data = retry.requests_retry_session().get(
            'https://api.themoviedb.org/3/tv/{}/season/{}/episode/{}/images?api_key={}'.format(tmdb_id, season,
                                                                                            episode,
                                                                                            config.moviedb_key),
            timeout=20).json()
        sample = episode_data['stills'][0]['file_path']
        sample = 'https://image.tmdb.org/t/p/original' + sample
    except (KeyError, TypeError, IndexError):
        try:
            sp = retry.requests_retry_session().get(
                'https://api.themoviedb.org/3/tv/{}/images?api_key={}&language=en'.format(tmdb_id,
                                                                                       config.moviedb_key),
                timeout=20).json()
            poster = sp['posters'][0]['file_path']
            sample = 'https://image.tmdb.org/t/p/original' + poster
        except (KeyError, TypeError, IndexError):
            sample = skyhook['images'][0]['url']

    # Downloading Poster
    if not os.path.exists('Images'):
        os.mkdir('Images')
    response = retry.requests_retry_session().get(sample, stream=True)
    filename = sample.split("/")[-1]
    file_path = os.path.join('Images', filename)
    if response.status_code == 200:
        response.raw.decode_content = True
        with open(file_path, 'wb') as f:
            shutil.copyfileobj(response.raw, f)
        print('Poster successfully downloaded.')
    else:
        print('Error retrieving poster.')

    # Episode Overview
    try:
        episode_data = retry.requests_retry_session().get(
            'https://api.themoviedb.org/3/tv/{}/season/{}/episode/{}?api_key={}&language=en'.format(
                tmdb_id,
                season,
                episode,
                config.moviedb_key), timeout=20).json()
        overview = episode_data['overview']
        if overview == "":
            series = 'https://api.themoviedb.org/3/tv/{}?api_key={}&language=en'.format(tmdb_id,
                                                                                     config.moviedb_key)
            series_data = retry.requests_retry_session().get(series, timeout=20).json()
            overview = series_data['overview']
    except (KeyError, TypeError, IndexError):
        logging.log.info("Couldn't fetch episode overview. Falling back to series overview.")
        series = 'https://api.themoviedb.org/3/tv/{}?api_key={}&language=en'.format(tmdb_id,
                                                                                 config.moviedb_key)
        series_data = retry.requests_retry_session().get(series, timeout=20).json()
        overview = series_data['overview']

    if len(overview) >= 250:
        overview = overview[:200]
        overview += '...'

    # Formatting Season and Episode
    if len(str(season)) == 1:
        season = '0{}'.format(season)

    if len(str(episode)) == 1:
        episode = '0{}'.format(episode)

    # Checking if the file is a upgrade
    if is_upgrade == 'True':
        content = 'Upgraded <b>{}</b> - <i>S{}E{}</i> - <b>{}</b>'.format(media_title, season, episode, episode_title)
    else:
        content = 'Downloaded <b>{}</b> - <i>S{}E{}</i> - <b>{}</b>'.format(media_title, season, episode, episode_title)

    # Content Rating
    try:
        content_rating = skyhook['contentRating']
    except (KeyError, TypeError, IndexError):
        try:
            content_rating = ratings_sonarr.certification
        except (KeyError, TypeError, IndexError):
            content_rating = "Unkown"

    # Network
    try:
        network = skyhook['network']
    except (KeyError, TypeError, IndexError):
        network = 'Unknown'

    # Genres
    try:
        genres = json.dumps(skyhook['genres'])
        genres = re.sub(r'[?|$|.|!|:|/|\]|\[|\"]', r'', genres)
    except (KeyError, TypeError, IndexError):
        genres = 'Unknown'

    # Pushover Message Format
    message = {
        "html": 1,
        "token": config.push_sonarr,
        "user": config.push_user,
        "sound": config.push_sound,
        "priority": config.push_priority,
        "device": config.push_device,
        "retry": 60,
        "expire": 3600,
        "message": "{}"
                   "\n\n<b>Overview</b>\n{}"
                   "\n\n<strong>File Details</strong>"
                   "\n<b>Episode</b>: S{}E{}"
                   "\n<b>Quality</b>: {}"
                   "\n<b>Release Name</b>: {}"
                   "\n\n<strong>Show Details</strong>"
                   "\n<b>Content Rating</b>: {}"
                   "\n<b>Genre</b>: {}"
                   "\n<b>Network</b>: {}".format(content, overview, season, episode, quality,
                                                 scene_name, content_rating, genres, network)
    }

    # Send notification
    try:
        sender = requests.post(push_url, data=message,
                               files={"attachment": (file_path, open(file_path, "rb"), "image/jpeg")})
    except:
        sender = requests.post(push_url, data=message)

    if sender.status_code == 200:
        print("Successfully sent import notification to Pushover.")
        logging.log.info(json.dumps(message, sort_keys=True, indent=4, separators=(',', ': ')))
        sys.exit(0)
    else:
        print(
            "Error occured when trying to send import notification to Pushover. Please open an issue with the below contents.")
        print("-------------------------------------------------------")
        print(sender.content)
        logging.log.error(json.dumps(message, sort_keys=True, indent=4, separators=(',', ': ')))
        print("-------------------------------------------------------")
        logging.log.info(json.dumps(message, sort_keys=True, indent=4, separators=(',', ': ')))
        sys.exit(1)


def health():
    issue_level = os.environ.get('sonarr_health_issue_level')

    issue_type = os.environ.get('sonarr_health_issue_type')

    issue_message = os.environ.get('sonarr_health_issue_message')

    wiki_link = os.environ.get('sonarr_health_issue_wiki')

    message = {
        "html": 1,
        "token": config.push_error,
        "user": config.push_user,
        "sound": config.push_sound,
        "priority": config.push_priority,
        "device": config.push_device,
        "retry": 60,
        "expire": 3600,
        "message": "An error has occured on Sonarr"
                   "\n<b>Error Level</b> - {}"
                   "\n<b>Error Type</b> - {}"
                   "\n<b>Error Message</b> - {}"
                   "\n<b>Visit Wiki</b> - <a href={}>Here</a>".format(issue_level, issue_type, issue_message, wiki_link)
    }

    sender = requests.post(push_url, json=message)
    if sender.status_code == 200:
        print("Successfully sent health notification to Pushover.")
        logging.log.info(json.dumps(message, sort_keys=True, indent=4, separators=(',', ': ')))
        sys.exit(0)
    else:
        print(
            "Error occured when trying to send health notification to Pushover. Please open an issue with the below contents.")
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
