import json
import logging
import os
import re
import sys
from datetime import datetime

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

# Set up the log folder and file
dir = os.path.join(os.path.dirname(sys.argv[0]))
os.chdir(dir)
if not os.path.exists('Logs'):
    os.mkdir('Logs')
log_filename = os.path.join(os.path.dirname(sys.argv[0]), 'Logs/sonarr-import-tor-discord.log')
logging.basicConfig(
    filename=log_filename,
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s'
)
log = logging.getLogger('Sonarr')


# Discord Footer Timestamp
def utc_now_iso():
    utcnow = datetime.utcnow()
    return utcnow.isoformat()


def main():
    # Getting variables from Sonarr
    eventtype = os.environ.get('sonarr_eventtype')

    season = os.environ.get('sonarr_episodefile_seasonnumber')

    episode = os.environ.get('sonarr_episodefile_episodenumbers')

    tvdb_id = os.environ.get('sonarr_series_tvdbid')
    if not tvdb_id:
        tvdb_id = '121361'

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
                tmdb = ('https://api.themoviedb.org/3/find/{}?api_key={}&language=en&external_source=tvdb_id').format(
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
                thumbnail_url = ('https://api.themoviedb.org/3/tv/{}/images?api_key={}&language=en').format(tmdb_id,
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
                episode_url = ('https://api.themoviedb.org/3/tv/{}/season/{}/episode/{}?api_key={}&language=en').format(
                    tmdb_id,
                    season,
                    episode,
                    script_config.moviedb_key)
                episode_data = sess.get(episode_url, headers=headers, timeout=60).json()
                overview = episode_data['overview']
                if overview == "":
                    with tor_requests.get_session(retries=10) as sess:
                        series = ('https://api.themoviedb.org/3/tv/{}?api_key={}&language=en').format(tmdb_id,
                                                                                                      script_config.moviedb_key)
                        series_data = sess.get(series, headers=headers, timeout=60).json()
                        overview = series_data['overview']
            except:
                # Series Overview when Episode overview is not found
                log.info("Couldn't fetch episode overview. Falling back to series overview.")
                with tor_requests.get_session(retries=10) as sess:
                    series = ('https://api.themoviedb.org/3/tv/{}?api_key={}&language=en').format(tmdb_id,
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
        content = 'Upgraded Episode - **{}**: *S{}E{}* - **{}**'.format(media_title, season, episode, episode_title)
        is_upgrade = 'Yes'

    else:
        content = 'New episode downloaded - **{}**: *S{}E{}* - **{}**'.format(media_title, season, episode,
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

    # Discord Message Format
    message = {
        "username": script_config.sonarr_discord_user,
        "content": content,
        "embeds": [
            {
                "author": {
                    "name": "Sonarr HD",
                    "url": script_config.sonarr_url,
                    "icon_url": script_config.sonarr_icon
                },
                "title": "{}: S{}E{} - {}".format(media_title, season, episode, episode_title),
                "description": "{}\n{}".format("**Overview**", overview),
                "color": 3394662,
                "footer": {
                    "icon_url": script_config.sonarr_icon,
                    "text": "{}".format(scene_name)
                },
                "timestamp": utc_now_iso(),
                "url": "{}series/{}".format(script_config.sonarr_url, title_slug),
                "thumbnail": {
                    "url": thumbnail
                },
                "image": {
                    "url": sample
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
                        "name": "Content Rating",
                        "value": content_rating,
                        "inline": True
                    },
                    {
                        "name": "Upgraded?",
                        "value": is_upgrade,
                        "inline": True
                    },
                    {
                        "name": "Network",
                        "value": network,
                        "inline": True
                    },
                    {
                        "name": "Genre",
                        "value": genres,
                        "inline": True
                    }
                ],
            },
        ]
    }

    # Send notification
    sender = requests.post(script_config.sonarr_discord_url, headers=discord_headers, json=message)

    # Logging
    log.info(json.dumps(message, sort_keys=True, indent=4, separators=(',', ': ')))

    if eventtype == "Test":
        print("Successfully sent test notification.")
    else:
        print("Successfully sent notification to Discord.")


# Call main
main()
