import json
import random

import config
import requests
from helpers import funcs, ratings, radarr_envs, omdb
from loguru import logger as log
from requests import RequestException

HEADERS = {"content-type": "application/json"}

log = log.patch(lambda record: record.update(name="Discord Radarr"))


def radarr_test():
    test = {
        "username": config.RADARR_DISCORD_USERNAME,
        "content": "**Bettarr Notifications for Radarr test message.\nThank you for using the script!**"}

    try:
        sender = requests.post(config.RADARR_DISCORD_WEBHOOK, headers=HEADERS, json=test, timeout=60)
        if sender.status_code == 204:
            log.success("Successfully sent test notification to Discord.")
        else:
            log.error(
                "Error occured when trying to send test notification to Discord. Please open an issue with the below contents.")
            log.error("-------------------------------------------------------")
            log.error(f"Status code: {sender.status_code}")
            log.error(f"Status body: {sender.content}")
            log.error(json.dumps(test, sort_keys=True, indent=4, separators=(",", ": ")))
            log.error("-------------------------------------------------------")
    except RequestException as e:
        log.error(e)
        log.error("Error occured when trying to send test notification to Discord.")


def radarr_grab():
    radarr = requests.get(f"{config.RADARR_URL}api/v3/movie/{radarr_envs.movie_id}?apikey={config.RADARR_APIKEY}")
    radarr = radarr.json()

    try:
        cast = f"[{funcs.get_movie_cast(radarr_envs.tmdb_id)[1][0]}]({funcs.get_movie_cast(radarr_envs.tmdb_id)[0][0]}), [{funcs.get_movie_cast(radarr_envs.tmdb_id)[1][1]}]({funcs.get_movie_cast(radarr_envs.tmdb_id)[0][1]}), [{funcs.get_movie_cast(radarr_envs.tmdb_id)[1][2]}]({funcs.get_movie_cast(radarr_envs.tmdb_id)[0][2]})"
    except (KeyError, TypeError, IndexError):
        try:
            cast = f"[{funcs.get_movie_cast(radarr_envs.tmdb_id)[1][0]}]({funcs.get_movie_cast(radarr_envs.tmdb_id)[0][0]})"
        except (KeyError, TypeError, IndexError):
            cast = "Unknown"

    message = {
        "username": config.RADARR_DISCORD_USERNAME,
        "content": f"Grabbed **{radarr_envs.media_title} ({radarr_envs.year})** from **{radarr_envs.release_indexer}**.",
        "embeds": [
            {
                "description": f"{funcs.get_radarr_overview(radarr)[0]}{ratings.mdblist_movie()[0]}",
                "author": {
                    "name": "Radarr",
                    "url": config.RADARR_URL,
                    "icon_url": config.RADARR_DISCORD_USERICON
                },
                "title": f"{radarr_envs.media_title}",
                "footer": {
                    "icon_url": config.RADARR_DISCORD_USERICON,
                    "text": f"{radarr_envs.media_title} | {radarr_envs.year}"
                },
                "timestamp": funcs.utc_now_iso(),
                "color": random.choice(funcs.colors),
                "url": f"{config.RADARR_URL}movie/{radarr_envs.tmdb_id}",
                "image": {
                    "url": funcs.get_radarrposter(radarr_envs.tmdb_id)
                },
                "fields": [
                    {
                        "name": "Quality",
                        "value": radarr_envs.quality,
                        "inline": True
                    },
                    {
                        "name": "Size",
                        "value": f"{funcs.convert_size(int(radarr_envs.release_size))}",
                        "inline": True
                    },
                    {
                        "name": "Download Client",
                        "value": radarr_envs.download_client,
                        "inline": True
                    },
                    {
                        "name": "Release Group",
                        "value": f"{radarr_envs.release_group}",
                        "inline": True
                    },
                    {
                        "name": "Release Date",
                        "value": funcs.get_radarr_releasedate(radarr_envs.tmdb_id),
                        "inline": True
                    },
                    {
                        "name": "Content Rating",
                        "value": f"{ratings.mdblist_movie()[1]}",
                        "inline": True
                    },
                    {
                        "name": "Genre(s)",
                        "value": funcs.get_radarr_genres(radarr),
                        "inline": False
                    },
                    {
                        "name": "Cast",
                        "value": cast,
                        "inline": False
                    },
                    {
                        "name": "Director",
                        "value": f"[{funcs.get_movie_crew(radarr_envs.tmdb_id)[1][0]}]({funcs.get_movie_crew(radarr_envs.tmdb_id)[0][0]})",
                        "inline": False
                    },
                    {
                        "name": f"Available On ({funcs.get_movie_watch_providers(radarr_envs.tmdb_id, radarr_envs.imdb_id)[1]})",
                        "value": f"{funcs.get_movie_watch_providers(radarr_envs.tmdb_id, radarr_envs.imdb_id)[0]}",
                        "inline": False
                    },
                    {
                        "name": "Trailer",
                        "value": f"[Youtube]({funcs.get_radarr_trailer(radarr)})",
                        "inline": False
                    },
                    {
                        "name": "View Details",
                        "value": f"[IMDb]({funcs.get_radarr_links(radarr_envs.imdb_id, radarr_envs.tmdb_id)[0]}) | [TheMovieDb]({funcs.get_radarr_links(radarr_envs.imdb_id, radarr_envs.tmdb_id)[1]}) | [Trakt]({funcs.get_radarr_links(radarr_envs.imdb_id, radarr_envs.tmdb_id)[2]}) | [MovieChat]({funcs.get_radarr_links(radarr_envs.imdb_id, radarr_envs.tmdb_id)[3]})",
                        "inline": False
                    },
                    {
                        "name": "Awards",
                        "value": omdb.omdb_radarr(radarr_envs.imdb_id),
                        "inline": False
                    }
                ]
            }
        ]
    }

    if omdb.omdb_radarr(radarr_envs.imdb_id) == "N/A":
        del message['embeds'][0]['12']

    if funcs.get_movie_watch_providers(radarr_envs.tmdb_id, radarr_envs.imdb_id)[0] == "None":
        del message['embeds'][0]['fields'][9]

    if cast == "Unknown":
        del message['embeds'][0]['fields'][7]

    if radarr_envs.release_group == "":
        del message["embeds"][0]["fields"][3]
        message["embeds"][0]["fields"][3]["inline"] = False

    if ratings.mdblist_movie()[1] == "Unknown":
        del message["embeds"][0]["fields"][5]
        message["embeds"][0]["fields"][4]["inline"] = False

    try:
        sender = requests.post(config.RADARR_DISCORD_WEBHOOK, headers=HEADERS, json=message, timeout=60)
        if sender.status_code == 204:
            log.success("Successfully sent grab notification to Discord.")
        else:
            log.error(
                "Error occured when trying to send grab notification to Discord. Please open an issue with the below contents.")
            log.error("-------------------------------------------------------")
            log.error(f"Status code: {sender.status_code}")
            log.error(f"Status body: {sender.content}")
            log.error(json.dumps(message, sort_keys=True, indent=4, separators=(",", ": ")))
            log.error("-------------------------------------------------------")
    except RequestException as e:
        log.error(e)
        log.error("Error occured when trying to send grab notification to Discord.")


def radarr_import():
    radarr = requests.get(f"{config.RADARR_URL}api/v3/movie/{radarr_envs.movie_id}?apikey={config.RADARR_APIKEY}")
    radarr = radarr.json()

    if radarr_envs.is_upgrade == "True":
        content = f"Upgraded **{radarr_envs.media_title}** ({radarr_envs.year})."
    else:
        content = f"Downloaded **{radarr_envs.media_title}** ({radarr_envs.year})."

    message = {
        "username": config.RADARR_DISCORD_USERNAME,
        "content": f"{content}",
        "embeds": [
            {
                "description": f"{funcs.get_radarr_overview(radarr)[0]}",
                "author": {
                    "name": "Radarr",
                    "url": config.RADARR_URL,
                    "icon_url": config.RADARR_DISCORD_USERICON
                },
                "title": f"{radarr_envs.media_title}",
                "footer": {
                    "text": f"{radarr_envs.media_title} ({radarr_envs.year})",
                    "icon_url": config.RADARR_DISCORD_USERICON
                },
                "timestamp": funcs.utc_now_iso(),
                "color": random.choice(funcs.colors),
                "url": f"{config.RADARR_URL}movie/{radarr_envs.tmdb_id}",
                "image": {
                    "url": funcs.get_radarr_backdrop(radarr_envs.tmdb_id)
                },
                "thumbnail": {
                    "url": funcs.get_radarrposter(radarr_envs.tmdb_id)
                },
                "fields": [
                    {
                        "name": "Quality",
                        "value": radarr_envs.import_quality,
                        "inline": True
                    },
                    {
                        "name": "Release Date",
                        "value": funcs.get_radarr_releasedate(radarr_envs.tmdb_id),
                        "inline": True
                    },
                    {
                        "name": "Physical Release Date",
                        "value": funcs.get_radarr_physicalrelease(radarr),
                        "inline": False
                    },
                    {
                        "name": "Genre(s)",
                        "value": funcs.get_radarr_genres(radarr),
                        "inline": False

                    },
                    {
                        "name": "Trailer",
                        "value": f"[Youtube]({funcs.get_radarr_trailer(radarr)})",
                        "inline": False
                    },
                    {
                        "name": "Release Name",
                        "value": f"`{radarr_envs.scene_name}`",
                        "inline": False
                    }
                ]
            }
        ]
    }

    if funcs.get_radarr_physicalrelease(radarr) == "Unknown":
        del message["embeds"][0]["fields"][2]
        if radarr_envs.scene_name == "":
            del message["embeds"][0]["fields"][4]

    if radarr_envs.scene_name == "":
        del message["embeds"][0]["fields"][5]

    try:
        sender = requests.post(config.RADARR_DISCORD_WEBHOOK, headers=HEADERS, json=message, timeout=60)
        if sender.status_code == 204:
            log.success("Successfully sent import notification to Discord.")
        else:
            log.error(
                "Error occured when trying to send import notification to Discord. Please open an issue with the below contents.")
            log.error("-------------------------------------------------------")
            log.error(f"Status code: {sender.status_code}")
            log.error(f"Status body: {sender.content}")
            log.error(json.dumps(message, sort_keys=True, indent=4, separators=(",", ": ")))
            log.error("-------------------------------------------------------")
    except RequestException as e:
        log.error(e)
        log.error("Error occured when trying to send import notification to Discord.")


def radarr_health():
    message = {
        "username": config.RADARR_DISCORD_USERNAME,
        "content": "**An issue has occured on Radarr.**",
        "embeds": [
            {
                "author": {
                    "name": config.RADARR_DISCORD_USERNAME,
                    "url": config.RADARR_URL,
                    "icon_url": config.RADARR_DISCORD_USERICON
                },
                "footer": {
                    "icon_url": config.RADARR_DISCORD_USERICON,
                    "text": "Radarr"
                },
                "timestamp": funcs.utc_now_iso(),
                "color": random.choice(funcs.colors),
                "fields": [
                    {
                        "name": "Error Level",
                        "value": radarr_envs.issue_level,
                        "inline": False
                    },
                    {
                        "name": "Error Type",
                        "value": radarr_envs.issue_type,
                        "inline": False
                    },
                    {
                        "name": "Error Message",
                        "value": radarr_envs.issue_message,
                        "inline": False
                    },
                    {
                        "name": "Wiki Link",
                        "value": f"[View Wiki]({radarr_envs.wiki_link})",
                        "inline": False
                    },
                    {
                        "name": "Visit Radarr",
                        "value": f"[Radarr]({config.RADARR_URL})",
                        "inline": False
                    }
                ]
            }
        ]
    }

    try:
        sender = requests.post(config.RADARR_HEALTH_DISCORD_WEBHOOK, headers=HEADERS, json=message, timeout=60)
        if sender.status_code == 204:
            log.success("Successfully sent health notification to Discord.")
        else:
            log.error(
                "Error occured when trying to send health notification to Discord. Please open an issue with the below contents.")
            log.error("-------------------------------------------------------")
            log.error(f"Status code: {sender.status_code}")
            log.error(f"Status body: {sender.content}")
            log.error(json.dumps(message, sort_keys=True, indent=4, separators=(",", ": ")))
            log.error("-------------------------------------------------------")
    except RequestException as e:
        log.error(e)
        log.error("Error occured when trying to send health notification to Discord.")


def radarr_update():
    message = {
        'username': config.RADARR_DISCORD_USERNAME,
        'content': f"Radarr has been updated to `{radarr_envs.new_version}`.",
        'embeds': [
            {
                'author': {
                    'name': config.RADARR_DISCORD_USERNAME,
                    'url': config.RADARR_URL,
                    'icon_url': config.RADARR_DISCORD_USERICON
                },
                "footer": {
                    "icon_url": config.RADARR_DISCORD_USERICON,
                    "text": "Radarr"
                },
                'timestamp': funcs.utc_now_iso(),
                'title': f"Radarr has been updated to `{radarr_envs.new_version}`.",
                'color': random.choice(funcs.colors),
                'fields': [
                    {
                        "name": "Old version",
                        "value": radarr_envs.old_version,
                        "inline": False
                    }
                ]
            }
        ]
    }

    try:
        sender = requests.post(config.RADARR_MISC_DISCORD_WEBHOOK, headers=HEADERS, json=message, timeout=60)
        if sender.status_code == 204:
            log.success("Successfully sent app update notification to Discord.")
        else:
            log.error(
                "Error occured when trying to send app update notification to Discord. Please open an issue with the below contents.")
            log.error("-------------------------------------------------------")
            log.error(f"Status code: {sender.status_code}")
            log.error(f"Status body: {sender.content}")
            log.error(json.dumps(message, sort_keys=True, indent=4, separators=(",", ": ")))
            log.error("-------------------------------------------------------")
    except RequestException as e:
        log.error(e)
        log.error("Error occured when trying to send app update notification to Discord.")


def radarr_movie_delete():
    message = {
        'username': config.RADARR_DISCORD_USERNAME,
        'content': f"Deleted **{radarr_envs.media_title} ({radarr_envs.year})** from Radarr.",
        'embeds': [
            {
                'author': {
                    'name': config.RADARR_DISCORD_USERNAME,
                    'url': config.RADARR_URL,
                    'icon_url': config.RADARR_DISCORD_USERICON
                },
                "footer": {
                    "icon_url": config.RADARR_DISCORD_USERICON,
                    "text": "Radarr"
                },
                'timestamp': funcs.utc_now_iso(),
                'title': f"{radarr_envs.media_title}",
                'color': random.choice(funcs.colors),
                "image": {
                    "url": funcs.get_radarrposter(radarr_envs.tmdb_id)
                },
                'fields': [
                    {
                        "name": "Size",
                        "value": funcs.convert_size(int(radarr_envs.deleted_size)),
                        "inline": False
                    },
                    {
                        "name": "Path",
                        "value": radarr_envs.delete_path,
                        "inline": False
                    },
                    {
                        "name": "View Details",
                        "value": f"[IMDb]({funcs.get_radarr_links(radarr_envs.imdb_id, radarr_envs.tmdb_id)[0]}) | [TheMovieDb]({funcs.get_radarr_links(radarr_envs.imdb_id, radarr_envs.tmdb_id)[1]}) | [Trakt]({funcs.get_radarr_links(radarr_envs.imdb_id, radarr_envs.tmdb_id)[2]}) | [MovieChat]({funcs.get_radarr_links(radarr_envs.imdb_id, radarr_envs.tmdb_id)[3]})",
                        "inline": False
                    },
                    {
                        "name": "Visit Radarr",
                        "value": f'[Radarr]({config.RADARR_URL})',
                        "inline": False
                    },
                ]
            }
        ]
    }

    if radarr_envs.deleted_size == 0:
        del message['embeds'][0]['fields'][0]

    try:
        sender = requests.post(config.RADARR_MISC_DISCORD_WEBHOOK, headers=HEADERS, json=message, timeout=60)
        if sender.status_code == 204:
            log.success("Successfully sent movie delete notification to Discord.")
        else:
            log.error(
                "Error occured when trying to send movie delete notification to Discord. Please open an issue with the below contents.")
            log.error("-------------------------------------------------------")
            log.error(f"Status code: {sender.status_code}")
            log.error(f"Status body: {sender.content}")
            log.error(json.dumps(message, sort_keys=True, indent=4, separators=(",", ": ")))
            log.error("-------------------------------------------------------")
    except RequestException as e:
        log.error(e)
        log.error("Error occured when trying to send movie delete notification to Discord.")


def radarr_moviefile_delete():
    message = {
        'username': config.RADARR_DISCORD_USERNAME,
        'content': f"Deleted **{radarr_envs.media_title} ({radarr_envs.year})** from Radarr.",
        'embeds': [
            {
                'author': {
                    'name': config.RADARR_DISCORD_USERNAME,
                    'url': config.RADARR_URL,
                    'icon_url': config.RADARR_DISCORD_USERICON
                },
                "footer": {
                    "icon_url": config.RADARR_DISCORD_USERICON,
                    "text": "Radarr"
                },
                'timestamp': funcs.utc_now_iso(),
                'title': f"{radarr_envs.media_title}",
                'description': f"**File location**\n```{radarr_envs.deleted_moviefilepath}```\n**Deleted Reason**\n```{radarr_envs.deleted_moviefilereason}```",
                'color': random.choice(funcs.colors),
                "image": {
                    "url": funcs.get_radarrposter(radarr_envs.tmdb_id)
                },
                'fields': [
                    {
                        "name": "Quality",
                        "value": radarr_envs.import_quality,
                        "inline": False
                    },
                    {
                        "name": "Size",
                        "value": funcs.convert_size(int(radarr_envs.deleted_moviefilesize)),
                        "inline": False
                    },
                    {
                        "name": "Release Group",
                        "value": radarr_envs.deleted_moviereleasegroup,
                        "inline": False
                    },
                    {
                        "name": "File Name",
                        "value": f"`{radarr_envs.scene_name}`",
                        "inline": False
                    },
                    {
                        "name": "View Details",
                        "value": f"[IMDb]({funcs.get_radarr_links(radarr_envs.imdb_id, radarr_envs.tmdb_id)[0]}) | [TheMovieDb]({funcs.get_radarr_links(radarr_envs.imdb_id, radarr_envs.tmdb_id)[1]}) | [Trakt]({funcs.get_radarr_links(radarr_envs.imdb_id, radarr_envs.tmdb_id)[2]}) | [MovieChat]({funcs.get_radarr_links(radarr_envs.imdb_id, radarr_envs.tmdb_id)[3]})",
                        "inline": False
                    },
                    {
                        "name": "Visit Radarr",
                        "value": f'[Radarr]({config.RADARR_URL})',
                        "inline": False
                    }
                ]
            }
        ]
    }

    if radarr_envs.scene_name == "":
        del message['embeds'][0]['fields'][4]

    if radarr_envs.deleted_moviereleasegroup == "":
        del message['embeds'][0]['fields'][3]

    if radarr_envs.deleted_moviefilesize == 0:
        del message['embeds'][0]['fields'][1]

    if radarr_envs.deleted_moviefilereason == "":
        del message['embeds'][0]['description']

    try:
        sender = requests.post(config.RADARR_MISC_DISCORD_WEBHOOK, headers=HEADERS, json=message, timeout=60)
        if sender.status_code == 204:
            log.success("Successfully sent movie file delete notification to Discord.")
        else:
            log.error(
                "Error occured when trying to send movie file delete notification to Discord. Please open an issue with the below contents.")
            log.error("-------------------------------------------------------")
            log.error(f"Status code: {sender.status_code}")
            log.error(f"Status body: {sender.content}")
            log.error(json.dumps(message, sort_keys=True, indent=4, separators=(",", ": ")))
            log.error("-------------------------------------------------------")
    except RequestException as e:
        log.error(e)
        log.error("Error occured when trying to send movie file delete notification to Discord.")


def radarr_movie_added():
    message = {
        'username': config.RADARR_DISCORD_USERNAME,
        'content': f"Added **{radarr_envs.media_title} ({radarr_envs.year})** to Radarr.",
        'embeds': [
            {
                'author': {
                    'name': config.RADARR_DISCORD_USERNAME,
                    'url': config.RADARR_URL,
                    'icon_url': config.RADARR_DISCORD_USERICON
                },
                "footer": {
                    "icon_url": config.RADARR_DISCORD_USERICON,
                    "text": "Radarr"
                },
                'timestamp': funcs.utc_now_iso(),
                'title': f"{radarr_envs.media_title}",
                'color': random.choice(funcs.colors),
                "image": {
                    "url": funcs.get_radarrposter(radarr_envs.tmdb_id)
                },
                'fields': [
                    {
                        "name": "View Details",
                        "value": f"[IMDb]({funcs.get_radarr_links(radarr_envs.imdb_id, radarr_envs.tmdb_id)[0]}) | [TheMovieDb]({funcs.get_radarr_links(radarr_envs.imdb_id, radarr_envs.tmdb_id)[1]}) | [Trakt]({funcs.get_radarr_links(radarr_envs.imdb_id, radarr_envs.tmdb_id)[2]}) | [MovieChat]({funcs.get_radarr_links(radarr_envs.imdb_id, radarr_envs.tmdb_id)[3]})",
                        "inline": False
                    },
                    {
                        "name": "Visit Radarr",
                        "value": f'[Radarr]({config.RADARR_URL})',
                        "inline": False
                    }
                ]
            }
        ]
    }

    try:
        sender = requests.post(config.RADARR_MISC_DISCORD_WEBHOOK, headers=HEADERS, json=message, timeout=60)
        if sender.status_code == 204:
            log.success("Successfully sent movie added notification to Discord.")
        else:
            log.error(
                "Error occured when trying to send movie added notification to Discord. Please open an issue with the below contents.")
            log.error("-------------------------------------------------------")
            log.error(f"Status code: {sender.status_code}")
            log.error(f"Status body: {sender.content}")
            log.error(json.dumps(message, sort_keys=True, indent=4, separators=(",", ": ")))
            log.error("-------------------------------------------------------")
    except RequestException as e:
        log.error(e)
        log.error("Error occured when trying to send movie added notification to Discord.")
