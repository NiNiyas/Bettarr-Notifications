import json

import config
import requests
from helpers import funcs, ratings, radarr_envs
from loguru import logger as log
from requests import RequestException

HEADERS = {"content-type": "application/json"}


def radarr_test():
    test = {
        "channel": config.SLACK_CHANNEL,
        "text": "*Bettarr Notifications for Radarr test message. Thank you for using the script!*"}

    try:
        sender = requests.post(config.RADARR_SLACK_WEBHOOK, headers=HEADERS, json=test)
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


def radarr_grab():
    radarr = requests.get(f"{config.RADARR_URL}api/v3/movie/{radarr_envs.movie_id}?apikey={config.RADARR_APIKEY}")
    radarr = radarr.json()

    try:
        cast = f"<{funcs.get_movie_cast(radarr_envs.tmdb_id)[0][0]}|{funcs.get_movie_cast(radarr_envs.tmdb_id)[1][0]}>, <{funcs.get_movie_cast(radarr_envs.tmdb_id)[0][1]}|{funcs.get_movie_cast(radarr_envs.tmdb_id)[1][1]}>, <{funcs.get_movie_cast(radarr_envs.tmdb_id)[0][2]}|{funcs.get_movie_cast(radarr_envs.tmdb_id)[1][2]}>"
    except (KeyError, TypeError, IndexError, Exception):
        try:
            cast = f"<{funcs.get_movie_cast(radarr_envs.tmdb_id)[0][0]}|{funcs.get_movie_cast(radarr_envs.tmdb_id)[1][0]}>"
        except (KeyError, TypeError, IndexError, Exception):
            cast = "Unknown"

    message = {
        "channel": config.SLACK_CHANNEL,
        "text": f"Grabbed *{radarr_envs.media_title} ({radarr_envs.year})* from *{radarr_envs.release_indexer}*",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"Grabbed *{radarr_envs.media_title}* ({radarr_envs.year}) from *{radarr_envs.release_indexer}*{ratings.mdblist_movie()[2]}"
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
                    "text": f"```{funcs.get_radarr_overview(radarr)[1]}```"
                }
            },
            {
                "type": "image",
                "image_url": funcs.get_radarrposter(radarr_envs.tmdb_id),
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
                        "text": f"*Quality*\n{radarr_envs.quality}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Size*\n{funcs.convert_size(int(radarr_envs.release_size))}",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Download Client*\n{radarr_envs.download_client}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Release Group*\n{radarr_envs.release_group}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Release Date*\n{funcs.get_radarr_releasedate(radarr_envs.tmdb_id)}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Content Rating*\n{ratings.mdblist_movie()[1]}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Genre(s)*\n{funcs.get_radarr_genres(radarr)}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Available On ({funcs.get_movie_watch_providers(radarr_envs.tmdb_id, radarr_envs.imdb_id)[1]})*\n{funcs.get_movie_watch_providers(radarr_envs.tmdb_id, radarr_envs.imdb_id)[0]}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Trailer*\n<{funcs.get_radarr_trailer(radarr)}|Youtube>"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*View Details*\n<{funcs.get_radarr_links(radarr_envs.imdb_id, radarr_envs.tmdb_id)[0]}|IMDb> | <{funcs.get_radarr_links(radarr_envs.imdb_id, radarr_envs.tmdb_id)[1]}|TheMovieDb> | <{funcs.get_radarr_links(radarr_envs.imdb_id, radarr_envs.tmdb_id)[2]}|Trakt> | <{funcs.get_radarr_links(radarr_envs.imdb_id, radarr_envs.tmdb_id)[3]}|MovieChat>"
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
                        "text": f"*Director*\n<{funcs.get_movie_crew(radarr_envs.tmdb_id)[0][0]}|{funcs.get_movie_crew(radarr_envs.tmdb_id)[1][0]}>"
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
                        "url": f"{config.RADARR_URL}movie/{radarr_envs.tmdb_id}"
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Go to Radarr",
                        },
                        "url": config.RADARR_URL
                    }
                ]
            }
        ]
    }

    if funcs.get_movie_watch_providers(radarr_envs.tmdb_id, radarr_envs.imdb_id)[0] == "None":
        del message["blocks"][5]["fields"][7]

    if cast == "Unknown":
        del message["blocks"][6]["fields"][0]

    if radarr_envs.release_group == "":
        del message["blocks"][5]["fields"][3]

    if ratings.mdblist_movie()[1] == "Unknown":
        del message["blocks"][5]["fields"][5]

    try:
        sender = requests.post(config.RADARR_SLACK_WEBHOOK, headers=HEADERS, json=message, timeout=60)
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


def radarr_import():
    radarr = requests.get(f"{config.RADARR_URL}api/v3/movie/{radarr_envs.movie_id}?apikey={config.RADARR_APIKEY}")
    radarr = radarr.json()

    if radarr_envs.is_upgrade == "True":
        content = f"Upgraded *{radarr_envs.media_title}* ({radarr_envs.year})"
    else:
        content = f"Downloaded *{radarr_envs.media_title}* ({radarr_envs.year})"

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
                    "text": f"```{funcs.get_radarr_overview(radarr)[1]}```"
                },
                "accessory": {
                    "type": "image",
                    "image_url": funcs.get_radarrposter(radarr_envs.tmdb_id),
                    "alt_text": "Poster"
                }
            },
            {
                "type": "image",
                "image_url": funcs.get_radarr_backdrop(radarr_envs.tmdb_id),
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
                        "text": f"*Quality*\n{radarr_envs.import_quality}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Release Date*\n{funcs.get_radarr_releasedate(radarr_envs.tmdb_id)}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Physical Release Date*\n{funcs.get_radarr_physicalrelease(radarr)}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Genre(s)*\n{funcs.get_radarr_genres(radarr)}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Release Name*\n`{radarr_envs.scene_name}`"
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
                        "url": f"{config.RADARR_URL}movie/{radarr_envs.tmdb_id}"
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Go to Radarr"
                        },
                        "url": config.RADARR_URL
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Trailer"
                        },
                        "url": funcs.get_radarr_trailer(radarr)
                    }
                ]
            }
        ]
    }

    if radarr_envs.scene_name == "":
        del message["blocks"][5]["fields"][4]

    try:
        sender = requests.post(config.RADARR_SLACK_WEBHOOK, headers=HEADERS, json=message, timeout=60)
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


def radarr_health():
    message = {
        "channel": config.SLACK_CHANNEL,
        "text": "*An issue has occured on Radarr*.",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*An issue has occured on Radarr*."
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
                        "text": f"*Error Level*\n{radarr_envs.issue_level}",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Error Type*\n{radarr_envs.issue_type}",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Error Message*\n{radarr_envs.issue_message}",
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
                        "url": config.RADARR_URL
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Wiki Link"
                        },
                        "url": radarr_envs.wiki_link
                    }
                ]
            }
        ]
    }

    try:
        sender = requests.post(config.RADARR_HEALTH_SLACK_WEBHOOK, headers=HEADERS, json=message, timeout=60)
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


def radarr_update():
    message = {
        "channel": config.SLACK_CHANNEL,
        "text": f"A new update `({radarr_envs.new_version})` is available for Radarr.",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"A new update `({radarr_envs.new_version})` is available for Radarr.",
                }
            },
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "Update Notes"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"```{radarr_envs.update_message}```"
                },
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*New version*\n{radarr_envs.new_version}",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Old version*\n{radarr_envs.old_version}",
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
                        "url": config.RADARR_URL
                    }
                ]
            }
        ]
    }

    try:
        sender = requests.post(config.RADARR_MISC_SLACK_WEBHOOK, headers=HEADERS, json=message, timeout=60)
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


def radarr_movie_delete():
    message = {
        "channel": config.SLACK_CHANNEL,
        "text": f"Deleted *{radarr_envs.media_title} ({radarr_envs.year})* from Radarr.",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"Deleted *{radarr_envs.media_title} ({radarr_envs.year})* from Radarr.",
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
                        "text": f"*Size*\n{funcs.convert_size(int(radarr_envs.deleted_size))}",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Path*\n{radarr_envs.delete_path}",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*View Details*\n<{funcs.get_radarr_links(radarr_envs.imdb_id, radarr_envs.tmdb_id)[0]}|IMDb> | <{funcs.get_radarr_links(radarr_envs.imdb_id, radarr_envs.tmdb_id)[1]}|TheMovieDb> | <{funcs.get_radarr_links(radarr_envs.imdb_id, radarr_envs.tmdb_id)[2]}|Trakt> | <{funcs.get_radarr_links(radarr_envs.imdb_id, radarr_envs.tmdb_id)[3]}|MovieChat>"
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
                        "url": config.RADARR_URL
                    }
                ]
            }
        ]
    }

    if radarr_envs.deleted_files == "False":
        del message['blocks'][2]['fields'][0]

    try:
        sender = requests.post(config.RADARR_MISC_SLACK_WEBHOOK, headers=HEADERS, json=message, timeout=60)
        if sender.status_code == 200:
            log.success("Successfully sent movie delete notification to Slack.")
        else:
            log.error(
                "Error occured when trying to send movie delete notification to Slack. Please open an issue with the below contents.")
            log.error("-------------------------------------------------------")
            log.error(f"Status code: {sender.status_code}")
            log.error(f"Status body: {sender.content}")
            log.error(json.dumps(message, sort_keys=True, indent=4, separators=(",", ": ")))
            log.error("-------------------------------------------------------")
    except RequestException as e:
        log.error(e)
        log.error("Error occured when trying to send movie delete notification to Slack.")


def radarr_moviefile_delete():
    message = {
        "channel": config.SLACK_CHANNEL,
        "text": f"Deleted *{radarr_envs.media_title} ({radarr_envs.year})* from Radarr.",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"Deleted *{radarr_envs.media_title} ({radarr_envs.year})* from Radarr.",
                }
            },
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "Deleted Reason"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"```{radarr_envs.deleted_moviefilereason}```"
                },
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Quality*\n{radarr_envs.import_quality}",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Size*\n{funcs.convert_size(int(radarr_envs.deleted_moviefilesize))}",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Path*\n`{radarr_envs.deleted_moviefilepath}`",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Release Group*\n{radarr_envs.deleted_moviereleasegroup}",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*File Name*\n`{radarr_envs.scene_name}`",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*View Details*\n<{funcs.get_radarr_links(radarr_envs.imdb_id, radarr_envs.tmdb_id)[0]}|IMDb> | <{funcs.get_radarr_links(radarr_envs.imdb_id, radarr_envs.tmdb_id)[1]}|TheMovieDb> | <{funcs.get_radarr_links(radarr_envs.imdb_id, radarr_envs.tmdb_id)[2]}|Trakt> | <{funcs.get_radarr_links(radarr_envs.imdb_id, radarr_envs.tmdb_id)[3]}|MovieChat>"
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
                        "url": config.RADARR_URL
                    }
                ]
            }
        ]
    }

    if radarr_envs.deleted_moviefilereason == "":
        del message['blocks'][1]
        del message['blocks'][2]

    if radarr_envs.deleted_moviefilesize == 0:
        del message['blocks'][4]['fields'][1]

    if radarr_envs.deleted_moviereleasegroup == "":
        del message['blocks'][4]['fields'][3]

    try:
        sender = requests.post(config.RADARR_MISC_SLACK_WEBHOOK, headers=HEADERS, json=message, timeout=60)
        if sender.status_code == 200:
            log.success("Successfully sent movie file delete notification to Slack.")
        else:
            log.error(
                "Error occured when trying to send movie file delete notification to Slack. Please open an issue with the below contents.")
            log.error("-------------------------------------------------------")
            log.error(f"Status code: {sender.status_code}")
            log.error(f"Status body: {sender.content}")
            log.error(json.dumps(message, sort_keys=True, indent=4, separators=(",", ": ")))
            log.error("-------------------------------------------------------")
    except RequestException as e:
        log.error(e)
        log.error("Error occured when trying to send movie file delete notification to Slack.")
