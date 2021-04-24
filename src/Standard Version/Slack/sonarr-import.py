import json
import logging
import os
import re
import sys

import requests

import script_config

slack_headers = {'content-type': 'application/json'}

# Set up the log folder and file
dir = os.path.join(os.path.dirname(sys.argv[0]))
os.chdir(dir)
if not os.path.exists('Logs'):
    os.mkdir('Logs')
log_filename = os.path.join(os.path.dirname(sys.argv[0]), 'Logs/sonarr-import-slack.log')
logging.basicConfig(
    filename=log_filename,
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s'
)
log = logging.getLogger('Sonarr')


def main():
    # Getting variables from Sonarr
    eventtype = os.environ.get('sonarr_eventtype')

    season = os.environ.get('sonarr_episodefile_seasonnumber')

    episode = os.environ.get('sonarr_episodefile_episodenumbers')

    tvdb_id = os.environ.get('sonarr_series_tvdbid')
    if not tvdb_id:
        tvdb_id = '71663'

    scene_name = os.environ.get('sonarr_episodefile_scenename')

    media_title = os.environ.get('sonarr_series_title')

    episode_title = os.environ.get('sonarr_episodefile_episodetitles')

    quality = os.environ.get('sonarr_episodefile_quality')

    is_upgrade = os.environ.get('sonarr_isupgrade')

    if eventtype == 'Test':
        log.info('Sonarr script test succeeded.')
        sys.exit(0)

    # Get show information from skyhook
    get_skyhook = requests.get(script_config.skyhook_url + str(tvdb_id))

    skyhook_data = get_skyhook.json()

    title_slug = skyhook_data['slug']

    imdb_id = os.environ.get('sonarr_series_imdbid')
    if not imdb_id:
        imdb_id = 'tt0096697'

    # Getting TMDb ID
    try:
        tmdb = ('https://api.themoviedb.org/3/find/{}?api_key={}&language=en&external_source=tvdb_id').format(tvdb_id,
                                                                                                              script_config.moviedb_key)
        get_tmdb = requests.get(tmdb).json()
        tmdb_id = get_tmdb['tv_results'][0]['id']
    except:
        # Getting TMDb ID from IMDb id when TVDB id is not found
        log.info("Error when grabbing TMDb ID using TVDB ID. Using IMDb ID")
        tmdb = ('https://api.themoviedb.org/3/find/{}?api_key={}&language=en&external_source=imdb_id').format(imdb_id,
                                                                                                              script_config.moviedb_key)
        get_tmdb = requests.get(tmdb).json()
        tmdb_id = get_tmdb['tv_results'][0]['id']

    # Thumbnail
    try:
        thumbnail_url = ('https://api.themoviedb.org/3/tv/{}/images?api_key={}&language=en').format(tmdb_id,
                                                                                                    script_config.moviedb_key)
        thumbnail_data = requests.get(thumbnail_url).json()
        thumbnail = thumbnail_data['posters'][0]['file_path']
        thumbnail = 'https://image.tmdb.org/t/p/original' + thumbnail
    except:
        log.info("Series poster not found on tmdb. Fetching from skyhook.")
        try:
            thumbnail = skyhook_data['images'][0]['url']
        except:
            thumbnail = 'http://gearr.scannain.com/wp-content/uploads/2015/02/noposter.jpg'

    # Episode Sample
    try:
        episode_sample = (
            'https://api.themoviedb.org/3/tv/{}/season/{}/episode/{}/images?api_key={}').format(tmdb_id, season,
                                                                                                episode,
                                                                                                script_config.moviedb_key)
        episode_data = requests.get(episode_sample).json()
        sample = episode_data['stills'][0]['file_path']
        sample = 'https://image.tmdb.org/t/p/original' + sample
    except:
        # Series banner when episode sample is not found
        log.info("Could not fetch episode sample. Falling back to series poster.")
        try:
            sample = skyhook_data['images'][0]['url']
        except:
            log.info("Couldn't fetch poster from skyhook. Falling back to generic.")
            sample = 'http://gearr.scannain.com/wp-content/uploads/2015/02/noposter.jpg'

    # Adding 0 to Season and Episode
    if len(str(season)) == 1:
        season = '0{}'.format(season)

    if len(str(episode)) == 1:
        episode = '0{}'.format(episode)

    # Checking if the file is a upgrade
    if is_upgrade == 'True':
        content = 'Upgraded Episode - *{}*: _S{}E{}_ - *{}*'.format(media_title, season, episode, episode_title)
        is_upgrade = 'Yes'

    else:
        content = 'New episode downloaded - *{}*: _S{}E{}_ - *{}*'.format(media_title, season, episode, episode_title)
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

    # Episode Overview
    try:
        episode_url = ('https://api.themoviedb.org/3/tv/{}/season/{}/episode/{}?api_key={}&language=en').format(tmdb_id,
                                                                                                                season,
                                                                                                                episode,
                                                                                                                script_config.moviedb_key)
        episode_data = requests.get(episode_url).json()
        overview = episode_data['overview']
        if overview == (""):
            series = ('https://api.themoviedb.org/3/tv/{}?api_key={}&language=en').format(tmdb_id,
                                                                                          script_config.moviedb_key)
            series_data = requests.get(series).json()
            overview = series_data['overview']

    except:
        # Series Overview when Episode overview is not found
        log.info("Couldn't fetch episode overview. Falling back to series overview.")
        series = ('https://api.themoviedb.org/3/tv/{}?api_key={}&language=en').format(tmdb_id,
                                                                                      script_config.moviedb_key)
        series_data = requests.get(series).json()
        overview = series_data['overview']

    # Slack Message Format
    message = {
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
                        "text": "*Quality*\n{}".format(quality)
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*Content Rating*\n{}".format(content_rating)
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*Upgraded?*\n{}".format(is_upgrade)
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

    log.info(json.dumps(message, sort_keys=True, indent=4, separators=(',', ': ')))

    # Send notification
    sender = requests.post(script_config.sonarr_slack_url, headers=slack_headers, json=message)
    if eventtype == "Test":
        print("Successfully sent test notification.")
    else:
        print("Successfully sent notification to Slack.")


# Call main
main()
