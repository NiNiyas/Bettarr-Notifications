#!/usr/bin/python3

import json
import logging
import os
import re
import sys

import requests
from torpy.http.requests import TorRequests

import script_config

slack_headers = {'content-type': 'application/json'}
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
log_filename = os.path.join(os.path.dirname(sys.argv[0]), 'Logs/sonarr-import-tor-slack.log')
logging.basicConfig(
    filename=log_filename,
    level=logging.ERROR,
    format='[%(asctime)s] %(levelname)s - %(message)s'
)
log = logging.getLogger('Sonarr')


def main():
    # More info on https://wiki.servarr.com/sonarr/custom-scripts
    eventtype = os.environ.get('sonarr_eventtype')

    # Slack Test Message Format
    testmessage = {
        'text': 'Bettarr Notification for Slack Sonarr Import event test message.\nThank you for using the script!'}

    # Send test notification
    if eventtype == 'Test':
        requests.post(script_config.radarr_slack_url, headers=slack_headers, json=testmessage)
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

    # Thumbnail
    with TorRequests() as tor_requests:
        with tor_requests.get_session(retries=10) as sess:
            try:
                thumbnail_url = 'https://api.themoviedb.org/3/tv/{}/images?api_key={}&language=en'.format(tmdb_id,
                                                                                                          script_config.moviedb_key)
                thumbnail_data = sess.get(thumbnail_url, headers=headers, timeout=60).json()
                thumbnail = thumbnail_data['posters'][0]['file_path']
                thumbnail = 'https://image.tmdb.org/t/p/original' + thumbnail
            except:
                log.info("Series poster not found on tmdb. Fetching from skyhook.")
                try:
                    thumbnail = skyhook_data['images'][0]['url']
                except:
                    thumbnail = 'http://gearr.scannain.com/wp-content/uploads/2015/02/noposter.jpg'

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

    # Adding 0 to Season and Episode
    if len(str(season)) == 1:
        season = '0{}'.format(season)

    if len(str(episode)) == 1:
        episode = '0{}'.format(episode)

    # Checking if the file is a upgrade
    if is_upgrade == 'True':
        content = 'Upgraded _S{}E{}_ of *{}*'.format(season, episode, media_title)
        is_upgrade = 'Yes'
    else:
        content = 'Downloaded _S{}E{}_ of *{}*'.format(season, episode, media_title)
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
                    "image_url": thumbnail,
                    "alt_text": "Banner"
                }
            },
            {
                "type": "image",
                "image_url": sample,
                "alt_text": "Sample"
            },

            {
                "type": "divider"
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": "*Episode*\nS{}E{}".format(season, episode)
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*Upgraded?*\n{}".format(is_upgrade)
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*Quality*\n{}".format(quality)
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*Content Rating*\n{}".format(content_rating)
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*Genre*\n{}".format(genres)
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*Network*\n{}".format(network)
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*Release Name*\n{}".format(scene_name)
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
                            "text": "View Series on Sonarr"

                        },
                        "style": "primary",
                        "url": "{}series/{}".format(script_config.sonarr_url, title_slug)
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Open Sonarr"
                        },
                        "url": script_config.sonarr_url
                    }
                ]
            }
        ]
    }

    # Send notification
    sender = requests.post(script_config.sonarr_slack_url, headers=slack_headers, json=message)
    log.info(json.dumps(message, sort_keys=True, indent=4, separators=(',', ': ')))
    print("Successfully sent notification to Slack.")


# Call main
main()
