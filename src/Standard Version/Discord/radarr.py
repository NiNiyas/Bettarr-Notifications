#!/usr/bin/python3

import datetime
import json
import os
import random
import sys

import requests

import config
from addons import ratings_radarr
from helpers import colors
from helpers import log
from helpers import retry
from helpers.size import convert_size

discord_headers = {'content-type': 'application/json'}

eventtype = os.environ.get('radarr_eventtype')


def initialize():
    required_variables = [config.radarr_discord_url, config.radarr_url, config.radarr_key,
                          config.moviedb_key, config.tmdb_country]
    for variable in required_variables:
        if variable == "":
            print("Required variables not set.. Exiting!")
            log.log.error("Please set required variables in script_config.py")
            sys.exit(1)
        else:
            continue


def utc_now_iso():
    utcnow = datetime.datetime.utcnow()
    return utcnow.isoformat()


def test_message():
    testmessage = {
        'content': '**Bettarr Notification for Discord Radarr AIO test message.\nThank you for using the script!**'}
    sender = requests.post(config.radarr_discord_url, headers=discord_headers, json=testmessage)
    if sender.status_code == 204:
        log.log.info("Successfully sent test notification to Discord.")
        sys.exit(0)
    else:
        log.log.error(
            "Error occured when trying to send test notification to Discord. Please open an issue with the below contents.")
        log.log.error("-------------------------------------------------------")
        log.log.error(sender.content)
        log.log.error(json.dumps(testmessage, sort_keys=True, indent=4, separators=(',', ': ')))
        log.log.error("-------------------------------------------------------")
        log.log.info(json.dumps(testmessage, sort_keys=True, indent=4, separators=(',', ': ')))
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
        log.log.info("Trailer not Found. Using 'Never Gonna Give You Up'.")
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
        log.log.info("Couldn't fetch providers from TMDb. Defaulting to US. Fetching from mdblist.")
        try:
            for x in ratings_radarr.mdblist_data['streams']:
                stream = (x['name'])
                providers.append(stream)
        except (KeyError, TypeError, IndexError):
            log.log.info("Error fetching stream data from mdblist.")
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

    # Discord Message Format
    message = {
        'username': config.radarr_discord_user,
        'content': "Grabbed **{} ({})** from **{}**".format(media_title, year, release_indexer),
        'embeds': [
            {
                'description': '**Overview**\n{}\n\n**Ratings**\n{}'.format(overview, ratings_radarr.ratings),
                'author': {
                    'name': 'Radarr',
                    'url': config.radarr_url,
                    'icon_url': config.radarr_icon
                },
                'title': '{}'.format(media_title),
                'footer': {
                    "icon_url": config.radarr_icon,
                    'text': "{} | {}".format(media_title, year)
                },
                'timestamp': utc_now_iso(),
                'color': random.choice(colors.colors),
                'url': '{}movie/{}'.format(config.radarr_url, tmdb_id),
                'image': {
                    'url': poster_path
                },
                'fields': [
                    {
                        "name": "Size",
                        "value": "{}".format(convert_size(int(release_size))),
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
                        "value": "{}".format(ratings_radarr.certification),
                        "inline": True
                    },
                    {
                        "name": 'Genre(s)',
                        "value": genres,
                        "inline": False
                    },
                    {
                        "name": 'Cast',
                        "value": actors,
                        "inline": False
                    },
                    {
                        "name": 'Director(s)',
                        "value": directors,
                        "inline": False
                    },
                    {
                        "name": "Available On ({})".format(country_code),
                        "value": "{}".format(watch_on),
                        "inline": False
                    },
                    {
                        "name": "Trailer",
                        "value": "[Youtube]({})".format(trailer_link),
                        "inline": False
                    },
                    {
                        "name": 'View Details',
                        "value": "[IMDb]({}) | [TMDB]({}) | [Trakt]({}) | [MovieChat]({})".format(imdb_url,
                                                                                                  tmdb_url,
                                                                                                  trakt_url,
                                                                                                  moviechat),
                        "inline": False
                    },
                ],
            },
        ]
    }

    # Send notification
    sender = requests.post(config.radarr_discord_url, headers=discord_headers, json=message, timeout=60)
    if sender.status_code == 204:
        log.log.info("Successfully sent grab notification to Discord.")
        sys.exit(0)
    else:
        log.log.error(
            "Error occured when trying to send grab notification to Discord. Please open an issue with the below contents.")
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

    # Poster
    try:
        poster_path = moviedb_api['poster_path']
        poster_path = 'https://image.tmdb.org/t/p/original' + poster_path
    except (KeyError, TypeError, IndexError):
        poster_path = 'https://i.imgur.com/GoqfZJe.jpg'

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

    # Upgrade
    if is_upgrade == 'True':
        content = 'Upgraded **{}** ({})'.format(media_title, year)
    else:
        content = 'Downloaded **{}** ({})'.format(media_title, year)

    # Discord Message Format
    message = {
        'username': config.radarr_discord_user,
        'content': "{}".format(content),
        'embeds': [
            {
                'description': "{}\n{}".format("**Overview**", overview),
                'author': {
                    'name': 'Radarr',
                    'url': config.radarr_url,
                    'icon_url': config.radarr_icon
                },
                'title': '{}'.format(media_title),
                'footer': {
                    'text': "{}".format(scene_name),
                    "icon_url": config.radarr_icon
                },
                'timestamp': utc_now_iso(),
                'color': random.choice(colors.colors),
                'url': '{}movie/{}'.format(config.radarr_url, tmdb_id),
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
                        "name": 'Release Date',
                        "value": release,
                        "inline": True
                    },
                    {
                        "name": 'Trailer',
                        "value": "[{}]({})".format("Youtube", trailer_link),
                        "inline": True
                    },
                    {
                        "name": 'Physical Release Date',
                        "value": physical_release,
                        "inline": False
                    },
                    {
                        "name": 'Genre',
                        "value": genres,
                        "inline": False

                    }
                ],
            },
        ]
    }

    # Send notification
    sender = requests.post(config.radarr_discord_url, headers=discord_headers, json=message)
    if sender.status_code == 204:
        log.log.info("Successfully sent import notification to Discord.")
        sys.exit(0)
    else:
        log.log.error(
            "Error occured when trying to send import notification to Discord. Please open an issue with the below contents.")
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
        'content': "**An error has occured on Radarr.**",
        'username': config.radarr_discord_user,
        'embeds': [
            {
                'author': {
                    'name': config.radarr_discord_user,
                    'url': config.radarr_url,
                    'icon_url': config.radarr_icon
                },
                "footer": {
                    "icon_url": config.radarr_icon,
                    "text": "Radarr"
                },
                'timestamp': utc_now_iso(),
                'color': random.choice(colors.colors),
                'fields': [
                    {
                        "name": 'Error Level',
                        "value": issue_level,
                        "inline": False
                    },
                    {
                        "name": 'Error Type',
                        "value": issue_type,
                        "inline": False
                    },
                    {
                        "name": 'Error Message',
                        "value": issue_message,
                        "inline": False
                    },
                    {
                        "name": 'Wiki Link',
                        "value": '[View Wiki]({})'.format(wiki_link),
                        "inline": False
                    },
                    {
                        "name": 'Visit Radarr',
                        "value": '[Radarr]({})'.format(config.radarr_url),
                        "inline": False
                    },
                ],
            },
        ]
    }

    sender = requests.post(config.radarr_health_url, headers=discord_headers, json=message)
    if sender.status_code == 204:
        log.log.info("Successfully sent health notification to Discord.")
        sys.exit(0)
    else:
        log.log.error(
            "Error occured when trying to send health notification to Discord. Please open an issue with the below contents.")
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
