import json
import random

import config
import requests
from helpers import funcs, ratings, sonarr_envs, omdb
from loguru import logger as log
from requests import RequestException

HEADERS = {"content-type": "application/json"}


def sonarr_test():
    test = {
        "username": config.SONARR_DISCORD_USERNAME,
        "content": "**Bettarr Notifications for Sonarr test message.\nThank you for using the script!**"}

    try:
        sender = requests.post(config.SONARR_DISCORD_WEBHOOK, headers=HEADERS, json=test, timeout=60)
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
        cast = f"[{funcs.get_seriescast(sonarr_envs.tvdb_id, sonarr_envs.imdb_id)[1][0]}]({funcs.get_seriescast(sonarr_envs.tvdb_id, sonarr_envs.imdb_id)[0][0]}), [{funcs.get_seriescast(sonarr_envs.tvdb_id, sonarr_envs.imdb_id)[1][1]}]({funcs.get_seriescast(sonarr_envs.tvdb_id, sonarr_envs.imdb_id)[0][1]}), [{funcs.get_seriescast(sonarr_envs.tvdb_id, sonarr_envs.imdb_id)[1][2]}]({funcs.get_seriescast(sonarr_envs.tvdb_id, sonarr_envs.imdb_id)[0][2]})"
    except (KeyError, TypeError, IndexError, Exception):
        try:
            cast = f"[{funcs.get_seriescast(sonarr_envs.tvdb_id, sonarr_envs.imdb_id)[1][0]}]({funcs.get_seriescast(sonarr_envs.tvdb_id, sonarr_envs.imdb_id)[0][0]})"
        except (KeyError, TypeError, IndexError, Exception):
            cast = "Unknown"

    message = {
        "username": config.SONARR_DISCORD_USERNAME,
        'content': f"Grabbed **{sonarr_envs.media_title}** - **S{season}E{episode}** - **{sonarr_envs.episode_title}** from **{sonarr_envs.release_indexer}**.",
        "embeds": [
            {
                "description": f'{funcs.get_sonarr_overview(sonarr_envs.tvdb_id, sonarr_envs.imdb_id)[0]}{ratings.mdblist_tv()[0]}',
                "author": {
                    "name": "Sonarr",
                    "url": config.SONARR_URL,
                    "icon_url": config.SONARR_DISCORD_USERICON
                },
                "title": title,
                "color": random.choice(funcs.colors),
                "timestamp": funcs.utc_now_iso(),
                "footer": {
                    "icon_url": config.SONARR_DISCORD_USERICON,
                    "text": f"{sonarr_envs.media_title}"
                },
                "url": f"{config.SONARR_URL}series/{slug}",
                "image": {
                    "url": funcs.get_posterseries(sonarr_envs.tvdb_id, sonarr_envs.imdb_id)
                },
                "fields": [
                    {
                        "name": "Episode",
                        "value": f"S{season}E{episode}",
                        "inline": True
                    },
                    {
                        "name": "Quality",
                        "value": sonarr_envs.quality,
                        "inline": True
                    },
                    {
                        "name": "Size",
                        "value": f"{funcs.convert_size(int(sonarr_envs.size))}",
                        "inline": True
                    },
                    {
                        "name": "Download Client",
                        "value": sonarr_envs.download_client,
                        "inline": True
                    },
                    {
                        "name": "Release Group",
                        "value": sonarr_envs.release_group,
                        "inline": True
                    },
                    {
                        "name": "Network",
                        "value": funcs.get_sonarr_network(skyhook),
                        "inline": True
                    },
                    {
                        "name": "Content Rating",
                        "value": funcs.get_sonarr_contentrating(skyhook),
                        "inline": False
                    },
                    {
                        "name": "Genre(s)",
                        "value": funcs.get_sonarrgenres(skyhook),
                        "inline": False
                    },
                    {
                        "name": "Cast",
                        "value": cast,
                        "inline": False
                    },
                    {
                        "name": "Director",
                        "value": f"[{funcs.get_seriescrew(sonarr_envs.tvdb_id, sonarr_envs.imdb_id)[1]}]({funcs.get_seriescrew(sonarr_envs.tvdb_id, sonarr_envs.imdb_id)[0]})",
                        "inline": False
                    },
                    {
                        "name": f"Available On ({funcs.get_tv_watch_providers(sonarr_envs.tvdb_id, sonarr_envs.imdb_id)[1]})",
                        "value": f"{funcs.get_tv_watch_providers(sonarr_envs.tvdb_id, sonarr_envs.imdb_id)[0]}",
                        "inline": False
                    },
                    {
                        "name": "Trailer",
                        "value": f"[Youtube]({funcs.get_sonarr_trailer()})",
                        "inline": False
                    },
                    {
                        "name": "View Details",
                        "value": f"[IMDb]({funcs.get_sonarr_links(sonarr_envs.tvdb_id, sonarr_envs.imdb_id, skyhook, slug)[3]}) | [TheTVDB]({funcs.get_sonarr_links(sonarr_envs.tvdb_id, sonarr_envs.imdb_id, skyhook, slug)[0]}) | [TheMovieDb]({funcs.get_sonarr_links(sonarr_envs.tvdb_id, sonarr_envs.imdb_id, skyhook, slug)[4]}) | [Trakt]({funcs.get_sonarr_links(sonarr_envs.tvdb_id, sonarr_envs.imdb_id, skyhook, slug)[2]}) | [TVmaze]({funcs.get_sonarr_links(sonarr_envs.tvdb_id, sonarr_envs.imdb_id, skyhook, slug)[1]})",
                        "inline": False
                    },
                    {
                        "name": "Awards",
                        "value": omdb.omdb_sonarr(sonarr_envs.imdb_id),
                        "inline": False
                    }
                ]
            }
        ]
    }

    if omdb.omdb_sonarr(sonarr_envs.imdb_id) == "N/A":
        del message['embeds'][0]['13']

    if funcs.get_tv_watch_providers(sonarr_envs.tvdb_id, sonarr_envs.imdb_id)[0] == "None":
        del message['embeds'][0]['fields'][10]

    if cast == "Unknown":
        del message['embeds'][0]['fields'][9]

    if sonarr_envs.release_group == "":
        del message['embeds'][0]['fields'][4]
        if funcs.get_seriescrew(sonarr_envs.tvdb_id, sonarr_envs.imdb_id)[1] == "Unknown":
            del message['embeds'][0]['fields'][8]

    if funcs.get_seriescrew(sonarr_envs.tvdb_id, sonarr_envs.imdb_id)[1] == "Unknown":
        del message['embeds'][0]['fields'][9]

    if funcs.get_sonarr_contentrating(skyhook) == "Unknown":
        del message['embeds'][0]['fields'][6]

    try:
        sender = requests.post(config.SONARR_DISCORD_WEBHOOK, headers=HEADERS, json=message, timeout=60)
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


def sonarr_import():
    skyhook = requests.get(f'http://skyhook.sonarr.tv/v1/tvdb/shows/en/{sonarr_envs.tvdb_id}').json()
    slug = skyhook["slug"]
    season = funcs.format_season_episode(sonarr_envs.import_season, sonarr_envs.import_episode)[0]
    episode = funcs.format_season_episode(sonarr_envs.import_season, sonarr_envs.import_episode)[1]

    if sonarr_envs.is_upgrade == "True":
        content = f'Upgraded **{sonarr_envs.media_title}** - **S{season}E{episode}** - **{sonarr_envs.import_episode_title}**.'
    else:
        content = f'Downloaded **{sonarr_envs.media_title}** - **S{season}E{episode}** - **{sonarr_envs.import_episode_title}**.'

    message = {
        "username": config.SONARR_DISCORD_USERNAME,
        "content": content,
        "embeds": [
            {
                "description": funcs.get_sonarr_episodeoverview(season, episode,
                                                                sonarr_envs.tvdb_id, sonarr_envs.imdb_id)[0],
                "author": {
                    "name": "Sonarr",
                    "url": config.SONARR_URL,
                    "icon_url": config.SONARR_DISCORD_USERICON
                },
                "title": f"{sonarr_envs.media_title}: S{season}E{episode} - {sonarr_envs.import_episode_title}",
                "color": random.choice(funcs.colors),
                "footer": {
                    "icon_url": config.SONARR_DISCORD_USERICON,
                    "text": f"{sonarr_envs.media_title}"
                },
                "timestamp": funcs.utc_now_iso(),
                "url": f"{config.SONARR_URL}series/{slug}",
                "thumbnail": {
                    "url": funcs.get_posterseries(sonarr_envs.tvdb_id, sonarr_envs.imdb_id)
                },
                "image": {
                    "url": funcs.get_sonarr_episodesample(sonarr_envs.tvdb_id, sonarr_envs.imdb_id, season, episode,
                                                          skyhook)
                },
                "fields": [
                    {
                        "name": "Episode",
                        "value": f"S{season}E{episode}",
                        "inline": True
                    },
                    {
                        "name": "Quality",
                        "value": sonarr_envs.import_quality,
                        "inline": True
                    },
                    {
                        "name": "Content Rating",
                        "value": funcs.get_sonarr_contentrating(skyhook),
                        "inline": True
                    },
                    {
                        "name": "Network",
                        "value": funcs.get_sonarr_network(skyhook),
                        "inline": False
                    },
                    {
                        "name": "Genre(s)",
                        "value": funcs.get_sonarrgenres(skyhook),
                        "inline": False
                    },
                    {
                        "name": "Air Date",
                        "value": f'{sonarr_envs.delete_air_date} UTC',
                        "inline": False
                    },
                    {
                        "name": "Release Name",
                        "value": f"`{sonarr_envs.scene_name}`",
                        "inline": False
                    }
                ]
            }
        ]
    }

    if funcs.get_sonarr_episodeoverview(season, episode, sonarr_envs.tvdb_id, sonarr_envs.imdb_id)[
        0] == "**Overview**\n":
        del message['embeds'][0]['description']

    if sonarr_envs.scene_name == "":
        del message['embeds'][0]['fields'][6]

    if funcs.get_sonarr_contentrating(skyhook) == "Unknown":
        del message['embeds'][0]['fields'][2]

    if sonarr_envs.delete_air_date == "":
        del message['embeds'][0]['fields'][5]

    try:
        sender = requests.post(config.SONARR_DISCORD_WEBHOOK, headers=HEADERS, json=message, timeout=60)
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


def sonarr_health():
    message = {
        'username': config.SONARR_DISCORD_USERNAME,
        'title': "**An issue has occured on Sonarr.**",
        'embeds': [
            {
                'author': {
                    'name': config.SONARR_DISCORD_USERNAME,
                    'url': config.SONARR_URL,
                    'icon_url': config.SONARR_DISCORD_USERICON
                },
                "footer": {
                    "icon_url": config.SONARR_DISCORD_USERICON,
                    "text": "Sonarr"
                },
                'timestamp': funcs.utc_now_iso(),
                'color': random.choice(funcs.colors),
                'fields': [
                    {
                        "name": "Error Level",
                        "value": sonarr_envs.issue_level,
                        "inline": False
                    },
                    {
                        "name": "Error Type",
                        "value": sonarr_envs.issue_type,
                        "inline": False
                    },
                    {
                        "name": "Error Message",
                        "value": sonarr_envs.issue_message,
                        "inline": False
                    },
                    {
                        "name": "Wiki Link",
                        "value": f'[View Wiki]({sonarr_envs.wiki_link})',
                        "inline": False
                    },
                    {
                        "name": "Visit Sonarr",
                        "value": f'[Sonarr]({config.SONARR_URL})',
                        "inline": False
                    }
                ]
            }
        ]
    }

    try:
        sender = requests.post(config.SONARR_HEALTH_DISCORD_WEBHOOK, headers=HEADERS, json=message, timeout=60)
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


def sonarr_delete_episode():
    skyhook = requests.get(f'http://skyhook.sonarr.tv/v1/tvdb/shows/en/{sonarr_envs.tvdb_id}').json()
    slug = skyhook['slug']
    season = funcs.format_season_episode(sonarr_envs.delete_season, sonarr_envs.delete_episode)[0]
    episode = funcs.format_season_episode(sonarr_envs.delete_season, sonarr_envs.delete_episode)[1]

    message = {
        'username': config.SONARR_DISCORD_USERNAME,
        'content': f"Deleted **{sonarr_envs.media_title}** - **S{season}E{episode}** - **{sonarr_envs.delete_episode_name}**.",
        'embeds': [
            {
                'author': {
                    'name': config.SONARR_DISCORD_USERNAME,
                    'url': config.SONARR_URL,
                    'icon_url': config.SONARR_DISCORD_USERICON
                },
                "footer": {
                    "icon_url": config.SONARR_DISCORD_USERICON,
                    "text": "Sonarr"
                },
                'timestamp': funcs.utc_now_iso(),
                'title': f"**{sonarr_envs.media_title}** - **S{season}E{episode}** - **{sonarr_envs.delete_episode_name}**",
                'description': f"**File location**\n```{sonarr_envs.episode_path}```",
                'color': random.choice(funcs.colors),
                'fields': [
                    {
                        "name": "Series Name",
                        "value": sonarr_envs.media_title,
                        "inline": False
                    },
                    {
                        "name": "Episode Name",
                        "value": sonarr_envs.delete_episode_name,
                        "inline": False
                    },
                    {
                        "name": "Season",
                        "value": season,
                        "inline": True
                    },
                    {
                        "name": "Episode",
                        "value": episode,
                        "inline": True
                    },
                    {
                        "name": "Quality",
                        "value": sonarr_envs.delete_quality,
                        "inline": True
                    },
                    {
                        "name": "Release Group",
                        "value": sonarr_envs.delete_release_group,
                        "inline": False
                    },
                    {
                        "name": "File Name",
                        "value": f"`{sonarr_envs.scene_name}`",
                        "inline": False
                    },
                    {
                        "name": "Air Date",
                        "value": f'{sonarr_envs.delete_air_date} UTC',
                        "inline": False
                    },
                    {
                        "name": "View Details",
                        "value": f"[IMDb]({funcs.get_sonarr_links(sonarr_envs.tvdb_id, sonarr_envs.imdb_id, skyhook, slug)[3]}) | [TheTVDB]({funcs.get_sonarr_links(sonarr_envs.tvdb_id, sonarr_envs.imdb_id, skyhook, slug)[0]}) | [TheMovieDb]({funcs.get_sonarr_links(sonarr_envs.tvdb_id, sonarr_envs.imdb_id, skyhook, slug)[4]}) | [Trakt]({funcs.get_sonarr_links(sonarr_envs.tvdb_id, sonarr_envs.imdb_id, skyhook, slug)[2]}) | [TVmaze]({funcs.get_sonarr_links(sonarr_envs.tvdb_id, sonarr_envs.imdb_id, skyhook, slug)[1]})",
                        "inline": False
                    },
                    {
                        "name": "Visit Sonarr",
                        "value": f'[Sonarr]({config.SONARR_URL})',
                        "inline": False
                    }
                ]
            }
        ]
    }

    if sonarr_envs.scene_name == "":
        del message['embeds'][0]['fields'][6]

    if sonarr_envs.delete_release_group == "":
        del message['embeds'][0]['fields'][5]

    try:
        sender = requests.post(config.SONARR_MISC_DISCORD_WEBHOOK, headers=HEADERS, json=message, timeout=60)
        if sender.status_code == 204:
            log.success("Successfully sent delete episode notification to Discord.")
        else:
            log.error(
                "Error occured when trying to send delete episode notification to Discord. Please open an issue with the below contents.")
            log.error("-------------------------------------------------------")
            log.error(f"Status code: {sender.status_code}")
            log.error(f"Status body: {sender.content}")
            log.error(json.dumps(message, sort_keys=True, indent=4, separators=(",", ": ")))
            log.error("-------------------------------------------------------")
    except RequestException as e:
        log.error(e)
        log.error("Error occured when trying to send delete episode notification to Discord.")


def sonarr_delete_series():
    skyhook = requests.get(f'http://skyhook.sonarr.tv/v1/tvdb/shows/en/{sonarr_envs.tvdb_id}').json()
    slug = skyhook['slug']

    message = {
        'username': config.SONARR_DISCORD_USERNAME,
        'content': f"Deleted **{sonarr_envs.media_title}** from Sonarr.",
        'embeds': [
            {
                'author': {
                    'name': config.SONARR_DISCORD_USERNAME,
                    'url': config.SONARR_URL,
                    'icon_url': config.SONARR_DISCORD_USERICON
                },
                "footer": {
                    "icon_url": config.SONARR_DISCORD_USERICON,
                    "text": "Sonarr"
                },
                'timestamp': funcs.utc_now_iso(),
                'title': f"Deleted `{sonarr_envs.media_title}` from Sonarr",
                'color': random.choice(funcs.colors),
                'fields': [
                    {
                        "name": "Series name",
                        "value": sonarr_envs.media_title,
                        "inline": False
                    },
                    {
                        "name": "Path",
                        "value": sonarr_envs.series_path,
                        "inline": False
                    },
                    {
                        "name": "View Details",
                        "value": f"[IMDb]({funcs.get_sonarr_links(sonarr_envs.tvdb_id, sonarr_envs.imdb_id, skyhook, slug)[3]}) | [TheTVDB]({funcs.get_sonarr_links(sonarr_envs.tvdb_id, sonarr_envs.imdb_id, skyhook, slug)[0]}) | [TheMovieDb]({funcs.get_sonarr_links(sonarr_envs.tvdb_id, sonarr_envs.imdb_id, skyhook, slug)[4]}) | [Trakt]({funcs.get_sonarr_links(sonarr_envs.tvdb_id, sonarr_envs.imdb_id, skyhook, slug)[2]}) | [TVmaze]({funcs.get_sonarr_links(sonarr_envs.tvdb_id, sonarr_envs.imdb_id, skyhook, slug)[1]})",
                        "inline": False
                    },
                    {
                        "name": "Visit Sonarr",
                        "value": f'[Sonarr]({config.SONARR_URL})',
                        "inline": False
                    }
                ]
            }
        ]
    }

    try:
        sender = requests.post(config.SONARR_MISC_DISCORD_WEBHOOK, headers=HEADERS, json=message, timeout=60)
        if sender.status_code == 204:
            log.success("Successfully sent delete series notification to Discord.")
        else:
            log.error(
                "Error occured when trying to send delete series notification to Discord. Please open an issue with the below contents.")
            log.error("-------------------------------------------------------")
            log.error(f"Status code: {sender.status_code}")
            log.error(f"Status body: {sender.content}")
            log.error(json.dumps(message, sort_keys=True, indent=4, separators=(",", ": ")))
            log.error("-------------------------------------------------------")
    except RequestException as e:
        log.error(e)
        log.error("Error occured when trying to send delete series notification to Discord.")


def sonarr_update():
    message = {
        'username': config.SONARR_DISCORD_USERNAME,
        'content': f"Sonarr has been updated to `{sonarr_envs.new_version}`.",
        'embeds': [
            {
                'author': {
                    'name': config.SONARR_DISCORD_USERNAME,
                    'url': config.SONARR_URL,
                    'icon_url': config.SONARR_DISCORD_USERICON
                },
                "footer": {
                    "icon_url": config.SONARR_DISCORD_USERICON,
                    "text": "Sonarr"
                },
                'timestamp': funcs.utc_now_iso(),
                'title': f"Sonarr has been updated to `{sonarr_envs.new_version}`.",
                'color': random.choice(funcs.colors),
                'fields': [
                    {
                        "name": "Old version",
                        "value": sonarr_envs.old_version,
                        "inline": False
                    }
                ]
            }
        ]
    }

    try:
        sender = requests.post(config.SONARR_MISC_DISCORD_WEBHOOK, headers=HEADERS, json=message, timeout=60)
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
