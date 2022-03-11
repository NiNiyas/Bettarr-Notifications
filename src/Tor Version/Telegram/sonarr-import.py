#!/usr/bin/python3

import json
import logging
import os
import re
import sys

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
log_filename = os.path.join(os.path.dirname(sys.argv[0]), 'Logs/sonarr-import-tor-telegram.log')
logging.basicConfig(
    filename=log_filename,
    level=logging.ERROR,
    format='[%(asctime)s] %(levelname)s - %(message)s'
)
log = logging.getLogger('Sonarr')

tgurl = 'https://api.telegram.org/bot{}/sendMessage'.format(script_config.sonarr_botid)


def main():
    # More info on https://wiki.servarr.com/sonarr/custom-scripts
    eventtype = os.environ.get('sonarr_eventtype')

    testmessage = {
        "chat_id": script_config.chat_id,
        "text": "Bettarr Notification for Telegram Sonarr Import event test message.\nThank you for using the script!"
    }

    # Send test notification
    if eventtype == 'Test':
        sender = requests.post(tgurl, data=testmessage)
        log.info(json.dumps(testmessage, sort_keys=True, indent=4, separators=(',', ': ')))
        print("Successfully sent test notification.")
        sys.exit(0)

    season = os.environ.get('sonarr_episodefile_seasonnumber')

    episode = os.environ.get('sonarr_episodefile_episodenumbers')

    tvdb_id = os.environ.get('sonarr_series_tvdbid')

    scene_name = os.environ.get('sonarr_episodefile_scenename')

    media_title = os.environ.get('sonarr_series_title')

    episode_title = os.environ.get('sonarr_episodefile_episodetitles')

    quality = os.environ.get('sonarr_episodefile_quality')

    is_upgrade = os.environ.get('sonarr_isupgrade')

    # Get show information from skyhook
    get_skyhook = requests.get(script_config.skyhook_url + str(tvdb_id))
    skyhook_data = get_skyhook.json()
    title_slug = skyhook_data['slug']
    imdb_id = os.environ.get('sonarr_series_imdbid')
    if not imdb_id:
        imdb_id = 'tt0944947'

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
                    get_tmdb = sess.get(tmdb).json()
                    tmdb_id = get_tmdb['tv_results'][0]['id']

    # Episode Sample
    with TorRequests() as tor_requests:
        with tor_requests.get_session(retries=10) as sess:
            try:
                episode_sample = (
                    'https://api.themoviedb.org/3/tv/{}/season/{}/episode/{}/images?api_key={}').format(tmdb_id, season,
                                                                                                        episode,
                                                                                                        script_config.moviedb_key)
                episode_data = sess.get(episode_sample, headers=headers, timeout=60).json()
                sample = episode_data['stills'][0]['file_path']
                sample = 'https://image.tmdb.org/t/p/original' + sample
            except:
                # Season poster when episode sample is not found
                log.info("Could not fetch episode sample. Falling back to series poster.")
                with tor_requests.get_session(retries=10) as sess:
                    try:
                        season_poster = 'https://api.themoviedb.org/3/tv/{}/season/{}/images?api_key={}'.format(
                            tmdb_id, season, script_config.moviedb_key)
                        sp = sess.get(season_poster, headers=headers, timeout=60).json()
                        poster = sp['poster'][0]['file_path']
                        sample = 'https://image.tmdb.org/t/p/original' + poster
                    except:
                        sample = skyhook_data['images'][0]['url']

    # Episode Overview
    with TorRequests() as tor_requests:
        with tor_requests.get_session(retries=10) as sess:
            try:
                episode_url = 'https://api.themoviedb.org/3/tv/{}/season/{}/episode/{}?api_key={}&language=en'.format(
                    tmdb_id,
                    season,
                    episode,
                    script_config.moviedb_key)
                episode_data = sess.get(episode_url, headers=headers, timeout=60).json()
                overview = episode_data['overview']
                if overview == "":
                    with tor_requests.get_session(retries=10) as sess:
                        series = 'https://api.themoviedb.org/3/tv/{}?api_key={}&language=en'.format(tmdb_id,
                                                                                                    script_config.moviedb_key)
                        series_data = sess.get(series, headers=headers, timeout=60).json()
                        overview = series_data['overview']
            except:
                # Series Overview when Episode overview is not found
                log.info("Couldn't fetch episode overview. Falling back to series overview.")
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

    # Checking if the file is a upgrade
    if is_upgrade == 'True':
        content = 'Upgraded Episode: <b>{}</b>: <i>S{}E{}</i> - <b>{}</b>'.format(media_title, season, episode,
                                                                                  episode_title)
        is_upgrade = 'Yes'

    else:
        content = 'New episode downloaded: <b>{}</b>: <i>S{}E{}</i> - <b>{}</b>'.format(media_title, season, episode,
                                                                                        episode_title)
        is_upgrade = 'No'

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

    # Genres
    try:
        genres = json.dumps(skyhook_data['genres'])
        genres = re.sub(r'[?|$|.|!|:|/|\]|\[|\"]', r'', genres)
    except:
        genres = 'Unknown'

    # Telegram Message Format
    message = {
        "chat_id": script_config.chat_id,
        "parse_mode": "HTML",
        "text": "{}"
                "\n\n<b>Overview</b>\n{}"
                "\n\n<strong>File Details</strong>"
                "\n<b>Episode</b>: S{}E{}"
                "\n<b>Quality</b>: {}"
                "\n<b>Upgraded?</b>: {}"
                "\n<b>Release Name</b>: {}"
                "\n\n<strong>Show Details</strong>"
                "\n<b>Content Rating</b>: {}"
                "\n<b>Genre</b>: {}"
                "\n<b>Network</b>: {}"
                "\n<a href='{}'>&#8204;</a>".format(content, overview, season, episode, quality, is_upgrade,
                                                    scene_name, content_rating, genres, network, sample),
        "reply_markup": {
            "inline_keyboard": [[
                {
                    "text": "View Series on Sonarr",
                    "url": "{}series/{}".format(script_config.sonarr_url, title_slug)
                },
                {
                    "text": "Open Sonarr",
                    "url": "{}".format(script_config.sonarr_url),
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
