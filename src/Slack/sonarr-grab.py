import json
import logging
import os
import re
import sys
import time

import humanize
import requests

import script_config

slack_headers = {'content-type': 'application/json'}

# Set up the log folder and file
dir = os.path.join(os.path.dirname(sys.argv[0]))
os.chdir(dir)
if not os.path.exists('Logs'):
    os.mkdir('Logs')
log_filename = os.path.join(os.path.dirname(sys.argv[0]), 'Logs/sonarr-grab-slack.log')
logging.basicConfig(
    filename=log_filename,
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s'
)
log = logging.getLogger('Sonarr')

# Ratings
imdb_id = os.environ.get('sonarr_series_imdbid')
if not imdb_id:
    imdb_id = 'tt0944947'

mdblist = requests.get('https://mdblist.com/api/?apikey={}&i={}&m=show'.format(script_config.mdbapi, imdb_id))
mdblist_data = mdblist.json()

# IMDb
try:
    imdb_rating = mdblist_data['ratings'][0]['value']
except:
    log.info("Error fetching rating from mdblist")
    imdb_rating = 'None'

# Metacritic
try:
    metacritic = mdblist_data['ratings'][1]['value']
except:
    log.info("Error fetching rating from mdblist")
    metacritic = 'None'

# Trakt
try:
    trakt_rating = mdblist_data['ratings'][2]['value']
except:
    log.info("Error fetching rating from mdblist")
    trakt_rating = 'None'

# TMDb Rating
try:
    tmdb_rating = mdblist_data['ratings'][5]['value']
except:
    log.info("Error fetching rating from mdblist")
    tmdb_rating = 'None'

# Rotten Tomatoes
try:
    rottentomatoes = mdblist_data['ratings'][3]['value']
except:
    log.info("Error fetching rating from mdblist")
    rottentomatoes = 'None'


def main():
    # Get/set ENV variables. More info on 'https://github.com/Sonarr/Sonarr/wiki/Custom-Post-Processing-Scripts'
    eventtype = os.environ.get('sonarr_eventtype')

    season = os.environ.get('sonarr_release_seasonnumber')

    episode = os.environ.get('sonarr_release_episodenumbers')

    tvdb_id = os.environ.get('sonarr_series_tvdbid')
    if not tvdb_id:
        tvdb_id = '370998'

    size = os.environ.get('sonarr_release_size')
    if not size:
        size = '5454554445'

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
    try:
        tmdb = ('https://api.themoviedb.org/3/find/{}?api_key={}&language=en&external_source=tvdb_id').format(tvdb_id,
                                                                                                              script_config.moviedb_key)
        get_tmdb = requests.get(tmdb).json()
        tmdb_id = get_tmdb['tv_results'][0]['id']
    except:
        log.error("Tvdb id not found. Grabbing from IMDB")
        tmdb = ('https://api.themoviedb.org/3/find/{}?api_key={}&language=en&external_source=imdb_id').format(imdb_id,
                                                                                                              script_config.moviedb_key)
        get_tmdb = requests.get(tmdb).json()
        tmdb_id = get_tmdb['tv_results'][0]['id']

    # Season poster, if it fails, falls back to series banner
    try:
        banner_url = ('https://api.themoviedb.org/3/tv/{}/season/{}/images?api_key={}&language=en').format(tmdb_id,
                                                                                                           season,
                                                                                                           script_config.moviedb_key)
        banner_data = requests.get(banner_url).json()
        banner = banner_data['posters'][0]['file_path']
        banner = 'https://image.tmdb.org/t/p/original' + banner
    except:
        # Series banner
        log.error("Couldn't fetch season banner. Falling back to series banner")
        try:
            banner = skyhook_data['images'][0]['url']
        except:
            banner = 'http://gearr.scannain.com/wp-content/uploads/2015/02/noposter.jpg'

    # View Details
    tvdb_url = 'https://thetvdb.com/series/' + title_slug

    tvmaze_id = skyhook_data['tvMazeId']

    tvmaze_url = 'https://www.tvmaze.com/shows/' + str(tvmaze_id)

    trakt_url = 'https://trakt.tv/search/tvdb/' + tvdb_id + '?id_type=show'

    imdb_url = ('https://www.imdb.com/title/' + str(imdb_id))

    tmdb_url = 'https://www.themoviedb.org/tv/' + str(tmdb_id)

    try:
        trailer_link = mdblist_data['trailer']
    except:
        log.error("Couldn't find trailer. Using default")
        trailer_link = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ&ab'

    # Series Overview
    series = ('https://api.themoviedb.org/3/tv/{}?api_key={}&language=en').format(tmdb_id,
                                                                                  script_config.moviedb_key)
    series_data = requests.get(series).json()
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

    # Slack Message Format
    message = {
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Grabbed *{}*: _S{}E{}_ - *{}* from _{}_\n*IMDb*: {} | *Metascore*: {} | *Rotten Tomatoes*: {} | *Trakt*: {} | *TMDb*: {}".format(
                        media_title, season, episode, episode_title, release_indexer, imdb_rating, metacritic,
                        rottentomatoes, trakt_rating, tmdb_rating)
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
                        "text": "*Episode*\nS{}E{}".format(season, episode)
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*Quality*\n{}".format(quality),
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*Size*\n{}".format(humanize.naturalsize(size))
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*Network*\n{}".format(network)
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*Genre*\n{}".format(genres)
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*Release Group*\n{}".format(release_group)
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*Content Rating*\n{}".format(content_rating)
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*View Details:*\n<{}|IMDb> | <{}|The TVDB> | <{}|TMDb> | <{}|Trakt> | <{}|TVmaze>".format(
                            imdb_url,
                            tvdb_url,
                            tmdb_url,
                            trakt_url, tvmaze_url)

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

    # Logging
    log.info(json.dumps(message, sort_keys=True, indent=4, separators=(',', ': ')))

    log.info("Sleeping for 20 seconds before sending notifications")
    time.sleep(20)

    # Send notification
    sender = requests.post(script_config.sonarr_slack_url, headers=slack_headers, json=message)


# Call main
main()
