#!/usr/bin/python3

import datetime
import json
import os
import sys

from helpers.size import convert_size
from helpers import log
import requests

import config
from helpers import retry
from addons import ratings_radarr

slack_headers = {'content-type': 'application/json'}

eventtype = os.environ.get('radarr_eventtype')


def initialize():
    required_variables = [config.radarr_slack_url, config.radarr_url, config.radarr_key,
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
        'text': '*Bettarr Notification for Slack Radarr AIO test message.*\n*Thank you for using the script!*'}
    sender = requests.post(config.radarr_slack_url, headers=slack_headers, json=testmessage)
    if sender.status_code == 200:
        log.log.info("Successfully sent test notification to Slack.")
        sys.exit(0)
    else:
        log.log.error(
            "Error occured when trying to send test notification to Slack. Please open an issue with the below contents.")
        log.log.error("-------------------------------------------------------")
        log.log.error(sender.content)
        log.log.error(json.dumps(testmessage, sort_keys=True, indent=4, separators=(',', ': ')))
        log.log.error("-------------------------------------------------------")
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

    # Slack Message Format
    message = {
        "text": "Grabbed *{}* ({}) from *{}*".format(media_title, year, release_indexer),
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Grabbed *{}* ({}) from *{}*\n\n*Ratings*\n{}".format(media_title, year, release_indexer,
                                                                                ratings_radarr.ratings)
                }
            },
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "Overview"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": overview
                }
            },
            {
                "type": "image",
                "image_url": poster_path,
                "alt_text": "Poster"
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": "*Quality*\n{}".format(quality)
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*Size*\n{}".format(convert_size(int(release_size))),
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*Download Client*\n{}".format(download_client)
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*Release Group*\n{}".format(release_group)
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*Genre(s)*\n{}".format(genres)
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*Release Date*\n{}".format(release)
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*Available On ({})*\n{}".format(country_code, watch_on)
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*Trailer*\n<{}|Youtube>".format(trailer_link)
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*View Details*\n<{}|IMDb> | <{}|TMDb> | <{}|Trakt> | <{}|MovieChat>".format(imdb_url,
                                                                                                             tmdb_url,
                                                                                                             trakt_url,
                                                                                                             moviechat)
                    }
                ]
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": "*Cast*\n{}".format(actors)
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*Director(s)*\n{}".format(directors)
                    },
                ]
            },
            {
                "type": "divider"
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "View Movie on Radarr",
                        },
                        "style": "primary",
                        "url": "{}movie/{}".format(config.radarr_url, tmdb_id)
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Go to Radarr",
                        },
                        "url": config.radarr_url
                    }
                ]
            }
        ]
    }

    # Send notification
    sender = requests.post(config.radarr_slack_url, headers=slack_headers, json=message, timeout=60)
    if sender.status_code == 200:
        log.log.info("Successfully sent grab notification to Slack.")
        sys.exit(0)
    else:
        log.log.error(
            "Error occured when trying to send grab notification to Slack. Please open an issue with the below contents.")
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
        content = 'Upgraded *{} ({})*'.format(media_title, year)
    else:
        content = 'Downloaded *{} ({})*'.format(media_title, year)

    # Slack Message Format
    message = {
        "text": content,
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": content
                }
            },
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "Overview"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": overview
                },
                "accessory": {
                    "type": "image",
                    "image_url": poster_path,
                    "alt_text": "Poster"
                }
            },
            {
                "type": "image",
                "image_url": banner,
                "alt_text": "Banner"
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": "*Quality*\n{}".format(quality)
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*Release Date*\n{}".format(release)
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*Physical Release Date*\n{}".format(physical_release)
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*Genre*\n{}".format(genres)
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*Release Name*\n{}".format(scene_name)
                    },

                ]
            },
            {
                "type": "divider"
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "View Movie on Radarr"

                        },
                        "style": "primary",
                        "url": "{}movie/{}".format(config.radarr_url, tmdb_id)
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Go to Radarr"
                        },
                        "url": config.radarr_url
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Trailer"
                        },
                        "url": trailer_link
                    }
                ]
            }
        ]
    }

    # Send notification
    sender = requests.post(config.radarr_slack_url, headers=slack_headers, json=message)
    if sender.status_code == 200:
        log.log.info("Successfully sent import notification to Slack.")
        sys.exit(0)
    else:
        log.log.error(
            "Error occured when trying to send import notification to Slack. Please open an issue with the below contents.")
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
        "text": "An issue has occured on Radarr.",
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "Radarr"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "An error has occured on Radarr."
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": "*Error Level*\n{}".format(issue_level),
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*Error Type*\n{}".format(issue_type),
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*Error Message*\n{}".format(issue_message),
                    }
                ]
            },
            {
                "type": "divider"
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Visit Radarr"

                        },
                        "style": "primary",
                        "url": config.radarr_url
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Wiki Link"
                        },
                        "url": wiki_link
                    }
                ]
            }
        ]
    }

    sender = requests.post(config.slack_radarr_health_url, headers=slack_headers, json=message)
    if sender.status_code == 200:
        log.log.info("Successfully sent health notification to Slack.")
        sys.exit(0)
    else:
        log.log.error(
            "Error occured when trying to send health notification to Slack. Please open an issue with the below contents.")
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
