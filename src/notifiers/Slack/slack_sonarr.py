import json

import config
import requests
from helpers import funcs, ratings, sonarr_envs, omdb
from loguru import logger as log
from requests import RequestException

HEADERS = {"content-type": "application/json"}


def sonarr_test():
    test = {
        "channel": config.SLACK_CHANNEL,
        "text": "*Bettarr Notifications for Sonarr test message. Thank you for using the script!*"}

    try:
        sender = requests.post(config.SONARR_SLACK_WEBHOOK, headers=HEADERS, json=test, timeout=60)
        if sender.status_code == 200:
            log.success("Successfully sent test notification to Slack.")
        else:
            log.error(
                "Error occured when trying to send test notification to Slack. Please open an issue with the below contents.")
            log.error("-------------------------------------------------------")
            log.error(f"Status code: {sender.status_code}")
            log.error(f"Status body: {sender.content}")
            log.error(json.dumps(test, sort_keys=True, indent=4, separators=(",", ": ")))
            log.error("-------------------------------------------------------")
    except RequestException as e:
        log.error(e)
        log.error("Error occured when trying to send test notification to Slack.")


def sonarr_grab():
    skyhook = requests.get(f"http://skyhook.sonarr.tv/v1/tvdb/shows/en/{sonarr_envs.tvdb_id}").json()
    slug = skyhook["slug"]
    season = funcs.format_season_episode(sonarr_envs.season, sonarr_envs.episode)[0]
    episode = funcs.format_season_episode(sonarr_envs.season, sonarr_envs.episode)[1]

    title = f"{sonarr_envs.media_title}: S{season}E{episode} - {sonarr_envs.episode_title}"
    if len(title) >= 204:
        title = title[:150]
        title += '...'

    try:
        cast = f"<{funcs.get_seriescast(sonarr_envs.tvdb_id, sonarr_envs.imdb_id)[0][0]}|{funcs.get_seriescast(sonarr_envs.tvdb_id, sonarr_envs.imdb_id)[1][0]}>, <{funcs.get_seriescast(sonarr_envs.tvdb_id, sonarr_envs.imdb_id)[0][1]}|{funcs.get_seriescast(sonarr_envs.tvdb_id, sonarr_envs.imdb_id)[1][1]}>, <{funcs.get_seriescast(sonarr_envs.tvdb_id, sonarr_envs.imdb_id)[0][2]}|{funcs.get_seriescast(sonarr_envs.tvdb_id, sonarr_envs.imdb_id)[1][2]}>"
    except (KeyError, TypeError, IndexError, Exception):
        try:
            cast = f"<{funcs.get_seriescast(sonarr_envs.tvdb_id, sonarr_envs.imdb_id)[0][0]}|{funcs.get_seriescast(sonarr_envs.tvdb_id, sonarr_envs.imdb_id)[1][0]}>"
        except (KeyError, TypeError, IndexError, Exception):
            cast = "Unknown"

    message = {
        "channel": config.SLACK_CHANNEL,
        "text": f"Grabbed *{sonarr_envs.media_title}* - *S{season}E{episode}* - *{sonarr_envs.episode_title}* from *{sonarr_envs.release_indexer}*.",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"Grabbed *{sonarr_envs.media_title}* - *S{season}E{episode}* - *{sonarr_envs.episode_title}* from *{sonarr_envs.release_indexer}*.{ratings.mdblist_tv()[5]}",
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
                    "text": f"```{funcs.get_sonarr_overview(sonarr_envs.tvdb_id, sonarr_envs.imdb_id)[1]}```"
                }
            },
            {
                "type": "image",
                "image_url": funcs.get_posterseries(sonarr_envs.tvdb_id, sonarr_envs.imdb_id),
                "alt_text": "poster"
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Episode*\nS{season}E{episode}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Quality*\n{sonarr_envs.quality}",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Size*\n{funcs.convert_size(int(sonarr_envs.size))}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Download Client*\n{sonarr_envs.download_client}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Release Group*\n{sonarr_envs.release_group}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Content Rating*\n{funcs.get_sonarr_contentrating(skyhook)}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Network*\n{funcs.get_sonarr_network(skyhook)}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Genre(s)*\n{funcs.get_sonarrgenres(skyhook)}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Available On ({funcs.get_tv_watch_providers(sonarr_envs.tvdb_id, sonarr_envs.imdb_id)[1]})*\n{funcs.get_tv_watch_providers(sonarr_envs.tvdb_id, sonarr_envs.imdb_id)[0]}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*View Details*\n<{funcs.get_sonarr_links(sonarr_envs.tvdb_id, sonarr_envs.imdb_id, skyhook, slug)[3]}|IMDb> | <{funcs.get_sonarr_links(sonarr_envs.tvdb_id, sonarr_envs.imdb_id, skyhook, slug)[0]}|TheTVDB> | <{funcs.get_sonarr_links(sonarr_envs.tvdb_id, sonarr_envs.imdb_id, skyhook, slug)[4]}|TheMovieDb> | <{funcs.get_sonarr_links(sonarr_envs.tvdb_id, sonarr_envs.imdb_id, skyhook, slug)[2]}|Trakt> | <{funcs.get_sonarr_links(sonarr_envs.tvdb_id, sonarr_envs.imdb_id, skyhook, slug)[1]}|TVmaze>"

                    }
                ]
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Cast*\n{cast}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Director*\n<{funcs.get_seriescrew(sonarr_envs.tvdb_id, sonarr_envs.imdb_id)[0]}|{funcs.get_seriescrew(sonarr_envs.tvdb_id, sonarr_envs.imdb_id)[1]}>"
                    }
                    ,
                    {
                        "type": "mrkdwn",
                        "text": f"*Awards*\n{omdb.omdb_sonarr(sonarr_envs.imdb_id)}"
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
                        "url": f"{config.SONARR_URL}series/{slug}"
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Open Sonarr"
                        },
                        "url": config.SONARR_URL
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Trailer"
                        },
                        "url": funcs.get_sonarr_trailer()
                    }
                ]
            }
        ]
    }

    if funcs.get_tv_watch_providers(sonarr_envs.tvdb_id, sonarr_envs.imdb_id)[0] == "None":
        del message['blocks'][5]['fields'][8]

    if cast == "Unknown":
        del message['blocks'][6]['fields'][0]

    if omdb.omdb_sonarr(sonarr_envs.imdb_id) == "N/A":
        del message['blocks'][6]['fields'][2]

    if funcs.get_seriescrew(sonarr_envs.tvdb_id, sonarr_envs.imdb_id)[1] == "Unknown":
        del message['blocks'][6]['fields'][1]

    if sonarr_envs.release_group == "":
        del message['blocks'][5]['fields'][4]

    if funcs.get_sonarr_contentrating(skyhook) == "Unknown":
        del message['blocks'][5]['fields'][5]

    try:
        sender = requests.post(config.SONARR_SLACK_WEBHOOK, headers=HEADERS, json=message, timeout=60)
        if sender.status_code == 200:
            log.success("Successfully sent grab notification to Slack.")
        else:
            log.error(
                "Error occured when trying to send grab notification to Slack. Please open an issue with the below contents.")
            log.error("-------------------------------------------------------")
            log.error(f"Status code: {sender.status_code}")
            log.error(f"Status body: {sender.content}")
            log.error(json.dumps(message, sort_keys=True, indent=4, separators=(",", ": ")))
            log.error("-------------------------------------------------------")
    except RequestException as e:
        log.error(e)
        log.error("Error occured when trying to send grab notification to Slack.")


def sonarr_import():
    skyhook = requests.get(f'http://skyhook.sonarr.tv/v1/tvdb/shows/en/{sonarr_envs.tvdb_id}').json()
    slug = skyhook["slug"]
    season = funcs.format_season_episode(sonarr_envs.import_season, sonarr_envs.import_episode)[0]
    episode = funcs.format_season_episode(sonarr_envs.import_season, sonarr_envs.import_episode)[1]

    if sonarr_envs.is_upgrade == "True":
        content = f'Upgraded *{sonarr_envs.media_title}* - *S{season}E{episode}* - *{sonarr_envs.import_episode_title}*.'
    else:
        content = f'Downloaded *{sonarr_envs.media_title}* - *S{season}E{episode}* - *{sonarr_envs.import_episode_title}*.'

    message = {
        "channel": config.SLACK_CHANNEL,
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
                    "text": funcs.get_sonarr_episodeoverview(season, episode,
                                                             sonarr_envs.tvdb_id, sonarr_envs.imdb_id)[1]
                },
                "accessory": {
                    "type": "image",
                    "image_url": funcs.get_posterseries(sonarr_envs.tvdb_id, sonarr_envs.imdb_id),
                    "alt_text": "Poster"
                }
            },
            {
                "type": "image",
                "image_url": funcs.get_sonarr_episodesample(sonarr_envs.tvdb_id, sonarr_envs.imdb_id, season, episode,
                                                            skyhook),
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
                        "text": f"*Episode*\nS{season}E{episode}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Quality*\n{sonarr_envs.import_quality}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Content Rating*\n{funcs.get_sonarr_contentrating(skyhook)}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Network*\n{funcs.get_sonarr_network(skyhook)}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Genre(s)*\n{funcs.get_sonarrgenres(skyhook)}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Air Date*\n{sonarr_envs.delete_air_date} UTC"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Release Name*\n`{sonarr_envs.scene_name}`"
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
                        "url": f"{config.SONARR_URL}series/{slug}"
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Open Sonarr"
                        },
                        "url": config.SONARR_URL
                    }
                ]
            }
        ]
    }

    if sonarr_envs.delete_air_date == "":
        del message['blocks'][5]['fields'][5]

    if funcs.get_sonarr_episodeoverview(season, episode, sonarr_envs.tvdb_id, sonarr_envs.imdb_id)[1] == "":
        del message['blocks'][1]
        del message['blocks'][1]

    if sonarr_envs.scene_name == "":
        del message['blocks'][5]['fields'][6]

    if funcs.get_sonarr_contentrating(skyhook) == "Unknown":
        del message['blocks'][5]['fields'][2]

    try:
        sender = requests.post(config.SONARR_SLACK_WEBHOOK, headers=HEADERS, json=message, timeout=60)
        if sender.status_code == 200:
            log.success("Successfully sent import notification to Slack.")
        else:
            log.error(
                "Error occured when trying to send import notification to Slack. Please open an issue with the below contents.")
            log.error("-------------------------------------------------------")
            log.error(f"Status code: {sender.status_code}")
            log.error(f"Status body: {sender.content}")
            log.error(json.dumps(message, sort_keys=True, indent=4, separators=(",", ": ")))
            log.error("-------------------------------------------------------")
    except RequestException as e:
        log.error(e)
        log.error("Error occured when trying to send import notification to Slack.")


def sonarr_health():
    message = {
        "channel": config.SLACK_CHANNEL,
        "text": "An issue has occured on Sonarr.",
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "Sonarr"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*An issue has occured on Sonarr.*"
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
                        "text": f"*Error Level*\n{sonarr_envs.issue_level}",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Error Type*\n{sonarr_envs.issue_type}",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Error Message*\n{sonarr_envs.issue_message}",
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
                            "text": "Visit Sonarr"

                        },
                        "style": "primary",
                        "url": config.SONARR_URL
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Wiki Link"
                        },
                        "url": sonarr_envs.wiki_link
                    }
                ]
            }
        ]
    }

    try:
        sender = requests.post(config.SONARR_HEALTH_SLACK_WEBHOOK, headers=HEADERS, json=message, timeout=60)
        if sender.status_code == 200:
            log.success("Successfully sent health notification to Slack.")
        else:
            log.error(
                "Error occured when trying to send health notification to Slack. Please open an issue with the below contents.")
            log.error("-------------------------------------------------------")
            log.error(f"Status code: {sender.status_code}")
            log.error(f"Status body: {sender.content}")
            log.error(json.dumps(message, sort_keys=True, indent=4, separators=(",", ": ")))
            log.error("-------------------------------------------------------")
    except RequestException as e:
        log.error(e)
        log.error("Error occured when trying to send health notification to Slack.")


def sonarr_delete_episode():
    skyhook = requests.get(f'http://skyhook.sonarr.tv/v1/tvdb/shows/en/{sonarr_envs.tvdb_id}').json()
    slug = skyhook['slug']
    season = funcs.format_season_episode(sonarr_envs.delete_season, sonarr_envs.delete_episode)[0]
    episode = funcs.format_season_episode(sonarr_envs.delete_season, sonarr_envs.delete_episode)[1]

    message = {
        "channel": config.SLACK_CHANNEL,
        "text": f"Deleted *{sonarr_envs.media_title}* - *S{season}E{episode}* - *{sonarr_envs.delete_episode_name}*.",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"Deleted *{sonarr_envs.media_title}* - *S{season}E{episode}* - *{sonarr_envs.delete_episode_name}*.",
                }
            },
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "File Location"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"```{sonarr_envs.episode_path}```"
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
                        "text": f"*Series name*\n{sonarr_envs.media_title}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Episode name*\n{sonarr_envs.delete_episode_name}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Season*\n{season}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Episode*\n{episode}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Quality*\n{sonarr_envs.delete_quality}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Release Group*\n`{sonarr_envs.delete_release_group}`",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*File name*\n`{sonarr_envs.scene_name}`"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Air Date*\n{sonarr_envs.delete_air_date} UTC"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*View Details*\n<{funcs.get_sonarr_links(sonarr_envs.tvdb_id, sonarr_envs.imdb_id, skyhook, slug)[3]}|IMDb> | <{funcs.get_sonarr_links(sonarr_envs.tvdb_id, sonarr_envs.imdb_id, skyhook, slug)[0]}|TheTVDB> | <{funcs.get_sonarr_links(sonarr_envs.tvdb_id, sonarr_envs.imdb_id, skyhook, slug)[4]}|TheMovieDb> | <{funcs.get_sonarr_links(sonarr_envs.tvdb_id, sonarr_envs.imdb_id, skyhook, slug)[2]}|Trakt> | <{funcs.get_sonarr_links(sonarr_envs.tvdb_id, sonarr_envs.imdb_id, skyhook, slug)[1]}|TVmaze>"

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
                        "url": f"{config.SONARR_URL}series/{slug}"
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Open Sonarr"
                        },
                        "url": config.SONARR_URL
                    }
                ]
            }
        ]
    }

    if sonarr_envs.scene_name == "":
        del message['blocks'][4]['fields'][6]

    if sonarr_envs.delete_release_group == "":
        del message['blocks'][4]['fields'][5]

    try:
        sender = requests.post(config.SONARR_MISC_SLACK_WEBHOOK, headers=HEADERS, json=message, timeout=60)
        if sender.status_code == 200:
            log.success("Successfully sent delete episode notification to Slack.")
        else:
            log.error(
                "Error occured when trying to send delete episode notification to Slack. Please open an issue with the below contents.")
            log.error("-------------------------------------------------------")
            log.error(f"Status code: {sender.status_code}")
            log.error(f"Status body: {sender.content}")
            log.error(json.dumps(message, sort_keys=True, indent=4, separators=(",", ": ")))
            log.error("-------------------------------------------------------")
    except RequestException as e:
        log.error(e)
        log.error("Error occured when trying to send delete episode notification to Slack.")


def sonarr_delete_series():
    skyhook = requests.get(f'http://skyhook.sonarr.tv/v1/tvdb/shows/en/{sonarr_envs.tvdb_id}').json()
    slug = skyhook['slug']

    message = {
        "channel": config.SLACK_CHANNEL,
        "text": f"Deleted *{sonarr_envs.media_title}* from Sonarr.",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"Deleted *{sonarr_envs.media_title}* from Sonarr.",
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Series name*\n{sonarr_envs.media_title}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Path*\n`{sonarr_envs.series_path}`"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*View Details*\n<{funcs.get_sonarr_links(sonarr_envs.tvdb_id, sonarr_envs.imdb_id, skyhook, slug)[3]}|IMDb> | <{funcs.get_sonarr_links(sonarr_envs.tvdb_id, sonarr_envs.imdb_id, skyhook, slug)[0]}|TheTVDB> | <{funcs.get_sonarr_links(sonarr_envs.tvdb_id, sonarr_envs.imdb_id, skyhook, slug)[4]}|TheMovieDb> | <{funcs.get_sonarr_links(sonarr_envs.tvdb_id, sonarr_envs.imdb_id, skyhook, slug)[2]}|Trakt> | <{funcs.get_sonarr_links(sonarr_envs.tvdb_id, sonarr_envs.imdb_id, skyhook, slug)[1]}|TVmaze>"

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
                            "text": "Open Sonarr"
                        },
                        "url": config.SONARR_URL
                    },
                ]
            }
        ]
    }

    try:
        sender = requests.post(config.SONARR_MISC_SLACK_WEBHOOK, headers=HEADERS, json=message, timeout=60)
        if sender.status_code == 200:
            log.success("Successfully sent delete series notification to Slack.")
        else:
            log.error(
                "Error occured when trying to send delete series notification to Slack. Please open an issue with the below contents.")
            log.error("-------------------------------------------------------")
            log.error(f"Status code: {sender.status_code}")
            log.error(f"Status body: {sender.content}")
            log.error(json.dumps(message, sort_keys=True, indent=4, separators=(",", ": ")))
            log.error("-------------------------------------------------------")
    except RequestException as e:
        log.error(e)
        log.error("Error occured when trying to send delete series notification to Slack.")


def sonarr_update():
    message = {
        "text": f"Sonarr has ben updated to `{sonarr_envs.new_version}`.",
        "blocks": [
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Old version*\n`{sonarr_envs.old_version}`"
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
                            "text": "Open Sonarr"
                        },
                        "url": config.SONARR_URL
                    },
                ]
            }
        ]
    }

    try:
        sender = requests.post(config.SONARR_MISC_SLACK_WEBHOOK, headers=HEADERS, json=message, timeout=60)
        if sender.status_code == 200:
            log.success("Successfully sent app update notification to Slack.")
        else:
            log.error(
                "Error occured when trying to send app update notification to Slack. Please open an issue with the below contents.")
            log.error("-------------------------------------------------------")
            log.error(f"Status code: {sender.status_code}")
            log.error(f"Status body: {sender.content}")
            log.error(json.dumps(message, sort_keys=True, indent=4, separators=(",", ": ")))
            log.error("-------------------------------------------------------")
    except RequestException as e:
        log.error(e)
        log.error("Error occured when trying to send app update notification to Slack.")
