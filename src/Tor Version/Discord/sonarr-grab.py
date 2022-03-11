#!/usr/bin/python3

import json
import logging
import os
import re
import sys
import random
from datetime import datetime

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
log_filename = os.path.join(os.path.dirname(sys.argv[0]), 'Logs/sonarr-grab-tor-discord.log')
logging.basicConfig(
    filename=log_filename,
    level=logging.ERROR,
    format='[%(asctime)s] %(levelname)s - %(message)s'
)
log = logging.getLogger('Sonarr')


# Footer Timestamp
def utc_now_iso():
    utcnow = datetime.utcnow()
    return utcnow.isoformat()


# Ratings
imdb_id = os.environ.get('sonarr_series_imdbid')
if not imdb_id:
    log.error("Sonarr didn't have show's IMDb id. Defaulting to GOT.")
    imdb_id = 'tt0944947'

mdblist = requests.get(
    'https://mdblist.com/api/?apikey={}&i={}&m=show'.format(script_config.mdbapi, imdb_id),
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


def main():
    # More info on https://wiki.servarr.com/sonarr/custom-scripts
    eventtype = os.environ.get('sonarr_eventtype')

    # Discord Test Message Format
    testmessage = {
        'content': 'Bettarr Notification for Discord Sonarr Grab event test message.\nThank you for using the script!'}

    # Send test notification
    if eventtype == 'Test':
        requests.post(script_config.sonarr_discord_url, headers=discord_headers, json=testmessage)
        log.info(json.dumps(testmessage, sort_keys=True, indent=4, separators=(',', ': ')))
        print("Successfully sent test notification.")
        sys.exit(0)

    season = os.environ.get('sonarr_release_seasonnumber')

    episode = os.environ.get('sonarr_release_episodenumbers')

    tvdb_id = os.environ.get('sonarr_series_tvdbid')

    size = os.environ.get('sonarr_release_size')

    release_group = os.environ.get('sonarr_release_releasegroup')

    media_title = os.environ.get('sonarr_series_title')

    episode_title = os.environ.get('sonarr_release_episodetitles')

    quality = os.environ.get('sonarr_release_quality')

    release_indexer = os.environ.get('sonarr_release_indexer')

    download_client = os.environ.get('sonarr_download_client')

    # Get show information from skyhook
    skyhook_url = 'http://skyhook.sonarr.tv/v1/tvdb/shows/en/{}'.format(tvdb_id)
    skyhook_data = requests.get(skyhook_url).json()
    title_slug = skyhook_data['slug']

    # TMDb ID
    with TorRequests() as tor_requests:
        with tor_requests.get_session(retries=10) as sess:
            try:
                tmdb = 'https://api.themoviedb.org/3/find/{}?api_key={}&language=en&external_source=tvdb_id'.format(
                    tvdb_id,
                    script_config.moviedb_key)
                get_tmdb = sess.get(tmdb, headers=headers, timeout=60).json()
                tmdb_id = get_tmdb['tv_results'][0]['id']
            except:
                with tor_requests.get_session(retries=10) as sess:
                    tmdb = (
                        'https://api.themoviedb.org/3/find/{}?api_key={}&language=en&external_source=imdb_id').format(
                        imdb_id,
                        script_config.moviedb_key)
                    get_tmdb = sess.get(tmdb, headers=headers, timeout=60).json()
                    tmdb_id = get_tmdb['tv_results'][0]['id']

    # Season poster, if it fails, falls back to series banner
    with TorRequests() as tor_requests:
        with tor_requests.get_session(retries=10) as sess:
            try:
                banner_url = 'https://api.themoviedb.org/3/tv/{}/season/{}/images?api_key={}&language=en'.format(
                    tmdb_id,
                    season,
                    script_config.moviedb_key)
                banner_data = sess.get(banner_url, headers=headers, timeout=60).json()
                banner = banner_data['posters'][0]['file_path']
                banner = 'https://image.tmdb.org/t/p/original' + banner
            except:
                # Series banner
                log.info("Couldn't fetch season banner. Falling back to series banner")
                try:
                    banner = skyhook_data['images'][0]['url']
                except:
                    banner = 'http://gearr.scannain.com/wp-content/uploads/2015/02/noposter.jpg'

    # View Details
    tvdb_url = 'https://thetvdb.com/series/' + title_slug

    try:
        tvmaze_id = skyhook_data['tvMazeId']
    except Exception as e:
        log.info("TVMaze id not found. Using GOT. Error: {}".format(e))
        tvmaze_id = '82'

    tvmaze_url = 'https://www.tvmaze.com/shows/' + str(tvmaze_id)

    trakt_url = 'https://trakt.tv/search/tvdb/' + tvdb_id + '?id_type=show'

    imdb_url = ('https://www.imdb.com/title/' + str(imdb_id))

    tmdb_url = 'https://www.themoviedb.org/tv/' + str(tmdb_id)

    # Powered by JustWatch and/or mdblist
    providers = []
    country_code = script_config.tmdb_country
    with TorRequests() as tor_requests:
        with tor_requests.get_session(retries=10) as sess:
            try:
                justwatch = sess.get('https://api.themoviedb.org/3/tv/{}/watch/providers?api_key={}'.format(tmdb_id,
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

    # Trailer
    try:
        trailer_link = mdblist_data['trailer']
        if trailer_link is None:
            log.info("Trailer not Found. Using 'Never Gonna Give You Up'.")
            trailer_link = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ&ab'
    except:
        log.info("Trailer not Found. Using 'Never Gonna Give You Up'.")
        trailer_link = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ&ab'

    # Series Overview
    with TorRequests() as tor_requests:
        with tor_requests.get_session(retries=10) as sess:
            series = 'https://api.themoviedb.org/3/tv/{}?api_key={}&language=en'.format(tmdb_id,
                                                                                        script_config.moviedb_key)
            series_data = sess.get(series, headers=headers, timeout=60).json()
            overview = series_data['overview']

    # Formatting Season and Episode
    if len(str(season)) == 1:
        season = '0{}'.format(season)
    if len(str(episode)) == 1:
        episode = '0{}'.format(episode)

    # Content Rating
    try:
        content_rating = skyhook_data['contentRating']
    except:
        content_rating = 'Unknown'

    # Network
    try:
        network = skyhook_data['network']
    except:
        network = 'Unknown'

    # Genre
    try:
        genres = json.dumps(skyhook_data['genres'])
        genres = re.sub(r'[?|$|.|!|:|/|\]|\[|\"]', r'', genres)
    except:
        genres = 'Unknown'

    # Discord Message Format
    message = {
        "username": script_config.sonarr_discord_user,
        "embeds": [
            {
                "description": 'Grabbed **{}** *S{}E{}* - **{}** from *{}*\n\n**Ratings**\n**IMDb**: {} | **Metascore**: {} | **Rotten Tomatoes**: {} '
                               '| **Trakt**: {} | **TMDb**: {} | **LetterBoxd**: {}\n\n**Overview**\n{}'
                    .format(
                    media_title, season,
                    episode, episode_title,
                    release_indexer,
                    imdb_rating,
                    metacritic, rottentomatoes, trakt_rating, tmdb_rating, letterboxd, overview),
                "author": {
                    "name": "Sonarr",
                    "url": script_config.sonarr_url,
                    "icon_url": script_config.sonarr_icon
                },
                "title": "{}: S{}E{} - {}".format(media_title, season, episode, episode_title),
                "color": random.choice(colors),
                "timestamp": utc_now_iso(),
                "footer": {
                    "icon_url": script_config.sonarr_icon,
                    "text": "{}".format(media_title)
                },
                "url": "{}series/{}".format(script_config.sonarr_url, title_slug),
                "image": {
                    "url": banner
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
                        "value": "{}".format(humanize.naturalsize(size)),
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
                        "name": "Genre",
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
                        "name": "View Details",
                        "value": "[{}]({}) | [{}]({}) | [{}]({}) | [{}]({}) | [{}]({})".format("IMDb", imdb_url,
                                                                                               "TVDb",
                                                                                               tvdb_url,
                                                                                               "TMDb",
                                                                                               tmdb_url, "Trakt",
                                                                                               trakt_url,
                                                                                               "TVmaze",
                                                                                               tvmaze_url),
                        "inline": False
                    }
                ],
            },
        ]
    }

    # Send notification
    sender = requests.post(script_config.sonarr_discord_url, headers=discord_headers, json=message)
    log.info(json.dumps(message, sort_keys=True, indent=4, separators=(',', ': ')))
    print("Successfully sent notification to Discord.")


# Call main
main()
