#!/usr/bin/python3

import datetime
import json
import os
import random
import re
import sys

import requests

import config
from addons import ratings_sonarr
from helpers import colors
from helpers import log
from helpers import retry
from helpers.size import convert_size

discord_headers = {'content-type': 'application/json'}

eventtype = os.environ.get('sonarr_eventtype')


def initialize():
    required_variables = [config.sonarr_discord_url, config.sonarr_url, config.moviedb_key,
                          config.tmdb_country]
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
        'content': '**Bettarr Notification for Discord Sonarr AIO test message.\nThank you for using the script!**'}
    sender = requests.post(config.sonarr_discord_url, headers=discord_headers, json=testmessage)
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
    title_slug = skyhook['slug']

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
    except (KeyError, IndexError, TypeError):
        try:
            poster = skyhook['images'][0]['url']
        except (KeyError, IndexError, TypeError):
            poster = 'http://gearr.scannain.com/wp-content/uploads/2015/02/noposter.jpg'

    # View Details
    tvdb_url = 'https://thetvdb.com/series/' + title_slug

    try:
        tvmaze_id = skyhook['tvMazeId']
    except (KeyError, TypeError, IndexError):
        tvmaze_id = '82'

    tvmaze_url = 'https://www.tvmaze.com/shows/' + str(tvmaze_id)

    trakt_url = 'https://trakt.tv/search/tvdb/' + tvdb_id + '?id_type=show'

    imdb_url = 'https://www.imdb.com/title/' + str(imdb_id)

    tmdb_url = 'https://www.themoviedb.org/tv/' + str(tmdb_id)

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
        log.log.info("Couldn't fetch providers from TMDb. Defaulting to US")
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
        log.log.info("Trailer not Found. Using 'Never Gonna Give You Up'.")
        trailer_link = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ&ab'

    # Series Overview
    series = retry.requests_retry_session().get(
        'https://api.themoviedb.org/3/tv/{}?api_key={}&language=en'.format(tmdb_id,
                                                                        config.moviedb_key),
        timeout=20).json()
    overview = series['overview']

    if len(overview) >= 300:
        overview = overview[:250]
        overview += '...'

    # Formatting Season and Episode
    if len(str(season)) == 1:
        season = '0{}'.format(season)
    if len(str(episode)) == 1:
        episode = '0{}'.format(episode)

    # Discord Message Format
    message = {
        "username": config.sonarr_discord_user,
        'content': "Grabbed **{}** *S{}E{}* - **{}** from *{}*".format(media_title, season,
                                                                       episode, episode_title,
                                                                       release_indexer),
        "embeds": [
            {
                "description": '**Overview**\n{}\n\n**Ratings**\n{}'.format(overview, ratings_sonarr.ratings),
                "author": {
                    "name": "Sonarr",
                    "url": config.sonarr_url,
                    "icon_url": config.sonarr_icon
                },
                "title": "{}: S{}E{} - {}".format(media_title, season, episode, episode_title),
                "color": random.choice(colors.colors),
                "timestamp": utc_now_iso(),
                "footer": {
                    "icon_url": config.sonarr_icon,
                    "text": "{}".format(media_title)
                },
                "url": "{}series/{}".format(config.sonarr_url, title_slug),
                "image": {
                    "url": poster
                },
                "fields": [
                    {
                        "name": "Episode",
                        "value": "S{}E{}".format(season, episode),
                        "inline": True
                    },
                    {
                        "name": "Quality",
                        "value": quality,
                        "inline": True
                    },
                    {
                        "name": "Size",
                        "value": "{}".format(convert_size(int(size))),
                        "inline": True
                    },
                    {
                        "name": 'Download Client',
                        "value": download_client,
                        "inline": True
                    },
                    {
                        "name": "Release Group",
                        "value": release_group,
                        "inline": True
                    },
                    {
                        "name": "Network",
                        "value": "{}".format(network),
                        "inline": True
                    },
                    {
                        "name": "Content Rating",
                        "value": content_rating,
                        "inline": False
                    },
                    {
                        "name": "Genre(s)",
                        "value": genres,
                        "inline": False
                    },
                    {
                        "name": "Cast",
                        "value": actors,
                        "inline": False
                    },
                    {
                        "name": "Director(s)",
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
                        "name": "View Details",
                        "value": "[IMDb]({}) | [TheTVDB]({}) | [TMDB]({}) | [Trakt]({}) | [TVmaze]({})".format(
                            imdb_url,
                            tvdb_url,
                            tmdb_url,
                            trakt_url,
                            tvmaze_url),
                        "inline": False
                    }
                ],
            },
        ]
    }

    # Send notification
    sender = requests.post(config.sonarr_discord_url, headers=discord_headers, json=message)
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
    title_slug = skyhook['slug']

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

    # Thumbnail
    try:
        thumbnail_url = 'https://api.themoviedb.org/3/tv/{}/images?api_key={}&language=en'.format(tmdb_id,
                                                                                               config.moviedb_key)
        thumbnail_data = retry.requests_retry_session().get(thumbnail_url, timeout=20).json()
        thumbnail = thumbnail_data['posters'][0]['file_path']
        thumbnail = 'https://image.tmdb.org/t/p/original' + thumbnail
    except (KeyError, TypeError, IndexError):
        try:
            thumbnail = skyhook['images'][0]['url']
        except (KeyError, TypeError, IndexError):
            thumbnail = 'http://gearr.scannain.com/wp-content/uploads/2015/02/noposter.jpg'

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
        # Series Overview when Episode overview is not found
        log.log.info("Couldn't fetch episode overview. Falling back to series overview.")
        series = 'https://api.themoviedb.org/3/tv/{}?api_key={}&language=en'.format(tmdb_id,
                                                                                 config.moviedb_key)
        series_data = retry.requests_retry_session().get(series, timeout=20).json()
        overview = series_data['overview']

    if len(overview) >= 300:
        overview = overview[:250]
        overview += '...'

    # Formatting Season and Episode
    if len(str(season)) == 1:
        season = '0{}'.format(season)

    if len(str(episode)) == 1:
        episode = '0{}'.format(episode)

    # Checking if the file is a upgrade
    if is_upgrade == 'True':
        content = 'Upgraded **{}** - *S{}E{} - {}*'.format(media_title, season, episode, episode_title)
    else:
        content = 'Downloaded **{}** - *S{}E{} - {}*'.format(media_title, season, episode, episode_title)

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

    # Discord Message Format
    message = {
        "username": config.sonarr_discord_user,
        "content": "{}".format(content),
        "embeds": [
            {
                "description": "{}\n{}".format("**Overview**", overview),
                "author": {
                    "name": "Sonarr",
                    "url": config.sonarr_url,
                    "icon_url": config.sonarr_icon
                },
                "title": "{}: S{}E{} - {}".format(media_title, season, episode, episode_title),
                "color": random.choice(colors.colors),
                "footer": {
                    "icon_url": config.sonarr_icon,
                    "text": "{}".format(scene_name)
                },
                "timestamp": utc_now_iso(),
                "url": "{}series/{}".format(config.sonarr_url, title_slug),
                "thumbnail": {
                    "url": thumbnail
                },
                "image": {
                    "url": sample
                },
                "fields": [
                    {
                        "name": "Quality",
                        "value": quality,
                        "inline": True
                    },
                    {
                        "name": "Episode",
                        "value": "S{}E{}".format(season, episode),
                        "inline": True
                    },
                    {
                        "name": "Content Rating",
                        "value": content_rating,
                        "inline": True
                    },
                    {
                        "name": "Network",
                        "value": network,
                        "inline": False
                    },
                    {
                        "name": "Genre",
                        "value": genres,
                        "inline": False
                    }
                ],
            },
        ]
    }

    # Send notification
    sender = requests.post(config.sonarr_discord_url, headers=discord_headers, json=message)
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
    issue_level = os.environ.get('sonarr_health_issue_level')

    issue_type = os.environ.get('sonarr_health_issue_type')

    issue_message = os.environ.get('sonarr_health_issue_message')

    wiki_link = os.environ.get('sonarr_health_issue_wiki')

    message = {
        'username': config.sonarr_discord_user,
        'embeds': [
            {
                'author': {
                    'name': config.sonarr_discord_user,
                    'url': config.sonarr_url,
                    'icon_url': config.sonarr_icon
                },
                "footer": {
                    "icon_url": config.sonarr_icon,
                    "text": "Sonarr"
                },
                'description': "**An error has occured on Sonarr.**",
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
                        "value": '[{}]({})'.format("View Wiki", wiki_link),
                        "inline": False
                    },
                    {
                        "name": 'Visit Sonarr',
                        "value": '[{}]({})'.format("Sonarr", config.sonarr_url),
                        "inline": False
                    },
                ],
            },
        ]
    }

    sender = requests.post(config.sonarr_health_url, headers=discord_headers, json=message)
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


def delete_episode():
    series_title = os.environ.get('sonarr_series_title')

    tvdb_id = os.environ.get('sonarr_series_tvdbid')

    imdb_id = os.environ.get('sonarr_series_imdbid')

    episode_path = os.environ.get('sonarr_episodefile_path')

    season = os.environ.get('sonarr_episodefile_seasonnumber')

    air_date = os.environ.get('sonarr_episodefile_episodeairdatesutc')

    quality = os.environ.get('sonarr_episodefile_quality')

    episode_title = os.environ.get('sonarr_episodefile_episodetitles')

    episode = os.environ.get('sonarr_episodefile_episodenumbers')

    release_group = os.environ.get('sonarr_episodefile_releasegroup')
    if release_group is None:
        release_group = "Unknown"

    scene_name = os.environ.get('sonarr_episodefile_scenename')
    if scene_name is None:
        scene_name = "Unknown"

    # Formatting Season and Episode
    if len(str(season)) == 1:
        season = '0{}'.format(season)

    if len(str(episode)) == 1:
        episode = '0{}'.format(episode)

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

    skyhook = retry.requests_retry_session().get('http://skyhook.sonarr.tv/v1/tvdb/shows/en/{}'.format(tvdb_id)).json()
    title_slug = skyhook['slug']

    tvdb_url = 'https://thetvdb.com/series/' + title_slug

    try:
        tvmaze_id = os.environ.get('sonarr_series_tvmazeid')
    except (KeyError, TypeError, IndexError):
        tvmaze_id = '82'

    tvmaze_url = 'https://www.tvmaze.com/shows/' + str(tvmaze_id)

    trakt_url = 'https://trakt.tv/search/tvdb/' + tvdb_id + '?id_type=show'

    imdb_url = 'https://www.imdb.com/title/' + str(imdb_id)

    tmdb_url = 'https://www.themoviedb.org/tv/' + str(tmdb_id)

    message = {
        'username': config.sonarr_discord_user,
        'content': f"Deleted **{series_title}** - **S{season}E{episode}** - **{episode_title}**",
        'embeds': [
            {
                'author': {
                    'name': config.sonarr_discord_user,
                    'url': config.sonarr_url,
                    'icon_url': config.sonarr_icon
                },
                "footer": {
                    "icon_url": config.sonarr_icon,
                    "text": "Sonarr"
                },
                'timestamp': utc_now_iso(),
                'title': f"Deleted **{series_title}** - **S{season}E{episode}** - **{episode_title}**",
                'description': f"**File location**\n```{episode_path}```",
                'color': random.choice(colors.colors),
                'fields': [
                    {
                        "name": 'Series name',
                        "value": series_title,
                        "inline": False
                    },
                    {
                        "name": 'Episode name',
                        "value": episode_title,
                        "inline": False
                    },
                    {
                        "name": 'Season no.',
                        "value": season,
                        "inline": True
                    },
                    {
                        "name": 'Episode no.',
                        "value": episode,
                        "inline": True
                    },
                    {
                        "name": 'Quality',
                        "value": quality,
                        "inline": True
                    },
                    {
                        "name": 'Release Group',
                        "value": release_group,
                        "inline": False
                    },
                    {
                        "name": 'File name',
                        "value": scene_name,
                        "inline": False
                    },
                    {
                        "name": 'Aired on',
                        "value": f'{air_date} UTC',
                        "inline": False
                    },
                    {
                        "name": "View Details",
                        "value": "[IMDb]({}) | [TheTVDB]({}) | [TMDB]({}) | [Trakt]({}) | [TVmaze]({})".format(
                            imdb_url,
                            tvdb_url,
                            tmdb_url,
                            trakt_url,
                            tvmaze_url),
                        "inline": False
                    },
                    {
                        "name": 'Visit Sonarr',
                        "value": '[{}]({})'.format("Sonarr", config.sonarr_url),
                        "inline": False
                    },
                ],
            },
        ]
    }

    sender = requests.post(config.sonarr_discord_url, headers=discord_headers, json=message)
    if sender.status_code == 204:
        log.log.info("Successfully sent episode deleted notification to Discord.")
        sys.exit(0)
    else:
        log.log.error(
            "Error occured when trying to send episode deleted notification to Discord. Please open an issue with the below contents.")
        log.log.error("-------------------------------------------------------")
        log.log.error(sender.content)
        log.log.error(json.dumps(message, sort_keys=True, indent=4, separators=(',', ': ')))
        log.log.error("-------------------------------------------------------")
        sys.exit(1)


def series_delete():
    series_title = os.environ.get('sonarr_series_title')

    tvdb_id = os.environ.get('sonarr_series_tvdbid')

    imdb_id = os.environ.get('sonarr_series_imdbid')

    deleted_files = os.environ.get('Sonarr_Series_DeletedFiles')
    if deleted_files == "False":
        deleted_files = "None"

    path = os.environ.get('Sonarr_Series_Path')

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

    skyhook = retry.requests_retry_session().get('http://skyhook.sonarr.tv/v1/tvdb/shows/en/{}'.format(tvdb_id)).json()
    title_slug = skyhook['slug']

    tvdb_url = 'https://thetvdb.com/series/' + title_slug

    try:
        tvmaze_id = os.environ.get('sonarr_series_tvmazeid')
    except (KeyError, TypeError, IndexError):
        tvmaze_id = '82'

    tvmaze_url = 'https://www.tvmaze.com/shows/' + str(tvmaze_id)

    trakt_url = 'https://trakt.tv/search/tvdb/' + tvdb_id + '?id_type=show'

    imdb_url = 'https://www.imdb.com/title/' + str(imdb_id)

    tmdb_url = 'https://www.themoviedb.org/tv/' + str(tmdb_id)

    message = {
        'username': config.sonarr_discord_user,
        'content': f"Deleted **{series_title}** from Sonarr.",
        'embeds': [
            {
                'author': {
                    'name': config.sonarr_discord_user,
                    'url': config.sonarr_url,
                    'icon_url': config.sonarr_icon
                },
                "footer": {
                    "icon_url": config.sonarr_icon,
                    "text": "Sonarr"
                },
                'timestamp': utc_now_iso(),
                'title': f"Deleted `{series_title} from Sonarr.`",
                'description': f"**Files**\n```{deleted_files}```",
                'color': random.choice(colors.colors),
                'fields': [
                    {
                        "name": 'Series name',
                        "value": series_title,
                        "inline": False
                    },
                    {
                        "name": 'Path',
                        "value": path,
                        "inline": False
                    },
                    {
                        "name": "View Details",
                        "value": "[IMDb]({}) | [TheTVDB]({}) | [TMDB]({}) | [Trakt]({}) | [TVmaze]({})".format(
                            imdb_url,
                            tvdb_url,
                            tmdb_url,
                            trakt_url,
                            tvmaze_url),
                        "inline": False
                    },
                    {
                        "name": 'Visit Sonarr',
                        "value": '[{}]({})'.format("Sonarr", config.sonarr_url),
                        "inline": False
                    },
                ],
            },
        ]
    }

    sender = requests.post(config.sonarr_discord_url, headers=discord_headers, json=message)
    if sender.status_code == 204:
        log.log.info("Successfully sent series deleted notification to Discord.")
        sys.exit(0)
    else:
        log.log.error(
            "Error occured when trying to send series deleted notification to Discord. Please open an issue with the below contents.")
        log.log.error("-------------------------------------------------------")
        log.log.error(sender.content)
        log.log.error(json.dumps(message, sort_keys=True, indent=4, separators=(',', ': ')))
        log.log.error("-------------------------------------------------------")
        sys.exit(1)


def app_update():
    update_message = os.environ.get('Sonarr_Update_Message')

    if len(update_message) >= 250:
        update_message = update_message[:200]
        update_message += '...'

    new_version = os.environ.get('Sonarr_Update_NewVersion')

    old_version = os.environ.get('Sonarr_Update_PreviousVersion')

    message = {
        'username': config.sonarr_discord_user,
        'content': f"A new update `({new_version})` is available for Sonarr.",
        'embeds': [
            {
                'author': {
                    'name': config.sonarr_discord_user,
                    'url': config.sonarr_url,
                    'icon_url': config.sonarr_icon
                },
                "footer": {
                    "icon_url": config.sonarr_icon,
                    "text": "Sonarr"
                },
                'timestamp': utc_now_iso(),
                'title': f"A new update `({new_version})` is available for Sonarr.",
                'description': f"**Notes**\n```{update_message}```",
                'color': random.choice(colors.colors),
                'fields': [
                    {
                        "name": 'New version',
                        "value": new_version,
                        "inline": False
                    },
                    {
                        "name": 'Old version',
                        "value": old_version,
                        "inline": False
                    },
                ],
            },
        ]
    }

    sender = requests.post(config.sonarr_discord_url, headers=discord_headers, json=message)
    if sender.status_code == 204:
        log.log.info("Successfully sent application update notification to Discord.")
        sys.exit(0)
    else:
        log.log.error(
            "Error occured when trying to send application update notification to Discord. Please open an issue with the below contents.")
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

if eventtype == "EpisodeFileDelete":
    initialize()
    delete_episode()

if eventtype == "ApplicationUpdate":
    initialize()
    app_update()

if eventtype == "SeriesDelete":
    initialize()
    series_delete()
