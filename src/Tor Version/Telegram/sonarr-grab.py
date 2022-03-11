#!/usr/bin/python3

import json
import logging
import os
import re
import sys

import humanize
import requests
from torpy.http.requests import TorRequests

import script_config

headers = {
    "Accept-Encoding": "gzip, deflate",
    "Accept-Language": "en-US,en;q=0.9",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.85 Safari/537.36 Edg/90.0.818.49"
}

# Set up the log folder and file
folder = os.path.join(os.path.dirname(sys.argv[0]))
os.chdir(folder)
if not os.path.exists('Logs'):
    os.mkdir('Logs')
log_filename = os.path.join(os.path.dirname(sys.argv[0]), 'Logs/sonarr-grab-tor-telegram.log')
logging.basicConfig(
    filename=log_filename,
    level=logging.ERROR,
    format='[%(asctime)s] %(levelname)s - %(message)s'
)
log = logging.getLogger('Sonarr')

tgurl = 'https://api.telegram.org/bot{}/sendMessage'.format(script_config.sonarr_botid)

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

    testmessage = {
        "chat_id": script_config.chat_id,
        "text": "Bettarr Notification for Telegram Sonarr Grab event test message.\nThank you for using the script!"
    }

    # Send test notification
    if eventtype == 'Test':
        sender = requests.post(tgurl, data=testmessage)
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

    # Telegram Message Format
    message = {
        "chat_id": script_config.chat_id,
        "parse_mode": "HTML",
        "text": "Grabbed <b>{}</b>: <i>S{}E{}</i> - <b>{}</b> from <i>{}</i>"
                "\n\n<strong>Overview</strong> \n{}"
                "\n\n<strong>Ratings</strong> \n"
                "<i>IMDB</i>: {} \n<i>Metacritic</i>: {} \n<i>Rotten Tomatoes</i>: {} \n<i>Trakt</i>: {} \n<i>TMDb</i>: {} \n<i>LetterBoxd</i>: {}"
                "\n\n<strong>File Details</strong>\n"
                "<i>Episode</i>: S{}E{}"
                "\n<i>Release Group</i>: {}"
                "\n<i>Quality</i>: {}"
                "\n<i>Size</i>: {}"
                "\n\n<strong>Show Details</strong>"
                "\n<i>Content Rating</i>: {}"
                "\n<i>Network</i>: {}"
                "\n<i>Genre(s)</i>: {}"
                "\n<i>Available On ({})</i>: {}"
                "\n<a href='{}'>&#8204;</a>"
            .format(
            media_title, season, episode, episode_title,
            release_indexer, overview, imdb_rating, metacritic, rottentomatoes, trakt_rating, tmdb_rating, letterboxd,
            season, episode, release_group, quality,
            (humanize.naturalsize(size)), content_rating, network, genres, country_code, watch_on, banner),
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
                    "text": "TVDb",
                    "url": tvdb_url
                },
                {
                    "text": "TMDb",
                    "url": tmdb_url
                },
                {
                    "text": "Trakt",
                    "url": trakt_url
                },

                {
                    "text": "TVmaze",
                    "url": tvmaze_url
                }]
            ]
        }

    }

    # Send notification
    sender = requests.post(tgurl, json=message)
    log.info(json.dumps(message, sort_keys=True, indent=4, separators=(',', ': ')))
    print("Successfully sent notification to Telegram.")


# Call main
main()
