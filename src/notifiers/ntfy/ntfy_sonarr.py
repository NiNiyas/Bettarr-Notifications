import json

import config
import requests
from helpers import funcs, ratings, sonarr_envs, omdb
from loguru import logger as log
from requests import RequestException


def sonarr_test():
    test = {
        "title": "Sonarr",
        "topic": config.NTFY_SONARR_TOPIC,
        "tags": ["sonarr", "tv", "test"],
        "priority": config.NTFY_SONARR_PRIORITY,
        "actions": [{"action": "view", "label": "Visit Sonarr", "url": f"{config.SONARR_URL}"}],
        "message": "Bettarr Notifications for Sonarr test message.\nThank you for using the script!"}

    if config.NTFY_SONARR_PRIORITY == "":
        del test["priority"]

    try:
        sender = requests.post(config.NTFY_URL, headers=config.NTFY_HEADER, json=test)
        if sender.status_code == 200:
            log.success("Successfully sent test notification to ntfy.")
        else:
            log.error(
                "Error occured when trying to send test notification to ntfy. Please open an issue with the below contents.")
            log.error("-------------------------------------------------------")
            log.error(f"Status code: {sender.status_code}")
            log.error(f"Status body: {sender.content}")
            log.error(json.dumps(test, sort_keys=True, indent=4, separators=(",", ": ")))
            log.error("-------------------------------------------------------")
    except RequestException as e:
        log.error(e)
        log.error("Error occured when trying to send test notification to ntfy.")


def sonarr_grab():
    skyhook = requests.get(f"http://skyhook.sonarr.tv/v1/tvdb/shows/en/{sonarr_envs.tvdb_id}").json()
    season = funcs.format_season_episode(sonarr_envs.season, sonarr_envs.episode)[0]
    episode = funcs.format_season_episode(sonarr_envs.season, sonarr_envs.episode)[1]

    title = f"Grabbed {sonarr_envs.media_title} - S{season}E{episode} - {sonarr_envs.episode_title} from {sonarr_envs.release_indexer}."
    if len(title) >= 150:
        title = title[:100]
        title += f'... from {sonarr_envs.release_indexer}.'

    try:
        cast = f"\nCast: {funcs.get_seriescast(sonarr_envs.tvdb_id, sonarr_envs.imdb_id)[1][0]}, {funcs.get_seriescast(sonarr_envs.tvdb_id, sonarr_envs.imdb_id)[1][1]}, {funcs.get_seriescast(sonarr_envs.tvdb_id, sonarr_envs.imdb_id)[1][2]}"
    except (KeyError, TypeError, IndexError, Exception):
        try:
            cast = f"\nCast: {funcs.get_seriescast(sonarr_envs.tvdb_id, sonarr_envs.imdb_id)[1][0]}"
        except (KeyError, TypeError, IndexError, Exception):
            cast = ""

    if funcs.get_seriescrew(sonarr_envs.tvdb_id, sonarr_envs.imdb_id)[1] == "Unknown":
        director = ""
    else:
        director = f"\nDirector: {funcs.get_seriescrew(sonarr_envs.tvdb_id, sonarr_envs.imdb_id)[1]}\n"

    if sonarr_envs.release_group == "":
        release_group = ""
    else:
        release_group = f"\nRelease Group: {sonarr_envs.release_group}"

    if omdb.omdb_sonarr(sonarr_envs.imdb_id) == "":
        awards = ""
    else:
        awards = f"\nAwards: {omdb.omdb_sonarr(sonarr_envs.imdb_id)}"

    message = {
        "title": "Sonarr",
        "topic": config.NTFY_SONARR_TOPIC,
        "tags": ["sonarr", "tv", "grabbed"],
        "priority": config.NTFY_SONARR_PRIORITY,
        "actions": [{"action": "view", "label": "Visit Sonarr", "url": f"{config.SONARR_URL}"},
                    {"action": "view", "label": "View Trailer", "url": f"{funcs.get_sonarr_trailer()}"}],
        "attach": funcs.get_posterseries(sonarr_envs.tvdb_id, sonarr_envs.imdb_id),
        "filename": "poster.jpg",
        "message": f"{title}{funcs.get_sonarr_overview(sonarr_envs.tvdb_id, sonarr_envs.imdb_id)[3]}{ratings.mdblist_tv()[7]}\n"
                   f"\nEpisode: S{season}E{episode}"
                   f"\nQuality: {sonarr_envs.quality}"
                   f"\nSize: {funcs.convert_size(int(sonarr_envs.size))}"
                   f"\nDownload Client: {sonarr_envs.download_client}"
                   f"{release_group}"
                   f"\nNetwork: {funcs.get_sonarr_network(skyhook)}"
                   f"\nContent Rating: {funcs.get_sonarr_contentrating(skyhook)}"
                   f"\nGenre(s): {funcs.get_sonarrgenres(skyhook)}"
                   f"{cast}"
                   f"{director}"
                   f"\nAvailable On ({funcs.get_tv_watch_providers(sonarr_envs.tvdb_id, sonarr_envs.imdb_id)[1]}): {funcs.get_tv_watch_providers(sonarr_envs.tvdb_id, sonarr_envs.imdb_id)[0]}"
                   f"{awards}"
    }

    if config.NTFY_SONARR_PRIORITY == "":
        del message["priority"]

    if funcs.get_tv_watch_providers(sonarr_envs.tvdb_id, sonarr_envs.imdb_id)[0] == "None":
        import re
        pattern = r'Available On \([^()]*\): None'
        log.warning("Available On field is unknown, removing it..")
        mod_string = re.sub(pattern, '', message["message"])
        message["message"] = mod_string

    if funcs.get_sonarr_contentrating(skyhook) == "Unknown":
        import re
        pattern = r'Content Rating: '
        log.warning("Content Rating field is unknown, removing it..")
        mod_string = re.sub(pattern, '', message["message"])
        message["message"] = mod_string

    if funcs.get_seriescrew(sonarr_envs.tvdb_id, sonarr_envs.imdb_id)[1] == "Unknown":
        import re
        pattern = r'Director: Unknown'
        log.warning("Director field is unknown, removing it..")
        mod_string = re.sub(pattern, '', message["message"])
        message["message"] = mod_string

    message['message'].rstrip()

    """
    if sonarr_envs.release_group == "":
        import re
        pattern = r'Release Group: '
        log.warning("Release Group field is unknown, removing it..")
        mod_string = re.sub(pattern, '', message["message"])
        message["message"] = mod_string
    """

    try:
        sender = requests.post(config.NTFY_URL, headers=config.NTFY_HEADER, json=message)
        if sender.status_code == 200:
            log.success("Successfully sent grab notification to ntfy.")
        else:
            log.error(
                "Error occured when trying to send grab notification to ntfy. Please open an issue with the below contents.")
            log.error("-------------------------------------------------------")
            log.error(f"Status code: {sender.status_code}")
            log.error(f"Status body: {sender.content}")
            log.error(json.dumps(message, sort_keys=True, indent=4, separators=(",", ": ")))
            log.error("-------------------------------------------------------")
    except RequestException as e:
        log.error(e)
        log.error("Error occured when trying to send grab notification to ntfy.")


def sonarr_import():
    skyhook = requests.get(f'http://skyhook.sonarr.tv/v1/tvdb/shows/en/{sonarr_envs.tvdb_id}').json()
    season = funcs.format_season_episode(sonarr_envs.import_season, sonarr_envs.import_episode)[0]
    episode = funcs.format_season_episode(sonarr_envs.import_season, sonarr_envs.import_episode)[1]

    if sonarr_envs.is_upgrade == "True":
        content = f'Upgraded {sonarr_envs.media_title} - S{season}E{episode} - {sonarr_envs.import_episode_title}.'
    else:
        content = f'Downloaded {sonarr_envs.media_title} - S{season}E{episode} - {sonarr_envs.import_episode_title}.'

    if sonarr_envs.scene_name != "":
        release_name = f"\n\nRelease Name\n{sonarr_envs.scene_name}"
    else:
        release_name = ""

    message = {
        "title": "Sonarr",
        "topic": config.NTFY_SONARR_TOPIC,
        "tags": ["sonarr", "tv", "downloaded"],
        "priority": config.NTFY_SONARR_PRIORITY,
        "actions": [{"action": "view", "label": "Visit Sonarr", "url": f"{config.SONARR_URL}"}],
        "attach": funcs.get_sonarr_episodesample(sonarr_envs.tvdb_id, sonarr_envs.imdb_id, season, episode, skyhook),
        "filename": "episode_sample.jpg",
        "message": f"{content}{funcs.get_sonarr_episodeoverview(season, episode, sonarr_envs.tvdb_id, sonarr_envs.imdb_id)[3]}"
                   f"\nEpisode: S{season}E{episode}"
                   f"\nQuality: {sonarr_envs.import_quality}"
                   f"\nContent Rating: {funcs.get_sonarr_contentrating(skyhook)}"
                   f"\nNetwork: {funcs.get_sonarr_network(skyhook)}"
                   f"\nGenre(s): {funcs.get_sonarrgenres(skyhook)}"
                   f"\nAir Date: {sonarr_envs.delete_air_date} UTC"
                   f"{release_name}"
    }

    if config.NTFY_SONARR_PRIORITY == "":
        del message["priority"]

    """
    if funcs.get_sonarr_episodeoverview(season, episode, sonarr_envs.tvdb_id, sonarr_envs.imdb_id)[1] == "":
        import re
        pattern = r'Overview ...'
        log.warning("Overview field is unknown, removing it..")
        mod_string = re.sub(pattern, '', message["message"])
        message["message"] = mod_string
    """

    if sonarr_envs.delete_air_date == "":
        import re
        pattern = r'Air Date: UTC'
        log.warning("Air Date field is unknown, removing it..")
        mod_string = re.sub(pattern, '', message["message"])
        message["message"] = mod_string

    if funcs.get_sonarr_contentrating(skyhook) == "Unknown":
        import re
        pattern = r'Content Rating: '
        log.warning("Content Rating field is unknown, removing it..")
        mod_string = re.sub(pattern, '', message["message"])
        message["message"] = mod_string

    try:
        sender = requests.post(config.NTFY_URL, headers=config.NTFY_HEADER, json=message)
        if sender.status_code == 200:
            log.success("Successfully sent import notification to ntfy.")
        else:
            log.error(
                "Error occured when trying to send import notification to ntfy. Please open an issue with the below contents.")
            log.error("-------------------------------------------------------")
            log.error(f"Status code: {sender.status_code}")
            log.error(f"Status body: {sender.content}")
            log.error(json.dumps(message, sort_keys=True, indent=4, separators=(",", ": ")))
            log.error("-------------------------------------------------------")
    except RequestException as e:
        log.error(e)
        log.error("Error occured when trying to send import notification to ntfy.")


def sonarr_health():
    message = {
        "title": "Sonarr",
        "topic": config.NTFY_SONARR_HEALTH_TOPIC,
        "tags": ["sonarr", "tv", "heartpulse"],
        "priority": config.NTFY_SONARR_PRIORITY,
        "actions": [{"action": "view", "label": "Visit Sonarr", "url": f"{config.SONARR_URL}"},
                    {"action": "view", "label": "Visit Wiki", "url": f"{sonarr_envs.wiki_link}"}],
        "message": "An issue has occured on Sonarr."
                   f"\n\nError Level: {sonarr_envs.issue_level}"
                   f"\nError Type: {sonarr_envs.issue_type}"
                   f"\nError Message: {sonarr_envs.issue_message}"
    }

    if config.NTFY_SONARR_PRIORITY == "":
        del message["priority"]

    try:
        sender = requests.post(config.NTFY_URL, headers=config.NTFY_HEADER, json=message)
        if sender.status_code == 200:
            log.success("Successfully sent health notification to ntfy.")
        else:
            log.error(
                "Error occured when trying to send health notification to ntfy. Please open an issue with the below contents.")
            log.error("-------------------------------------------------------")
            log.error(f"Status code: {sender.status_code}")
            log.error(f"Status body: {sender.content}")
            log.error(json.dumps(message, sort_keys=True, indent=4, separators=(",", ": ")))
            log.error("-------------------------------------------------------")
    except RequestException as e:
        log.error(e)
        log.error("Error occured when trying to send health notification to ntfy.")


def sonarr_delete_episode():
    skyhook = requests.get(f'http://skyhook.sonarr.tv/v1/tvdb/shows/en/{sonarr_envs.tvdb_id}').json()
    slug = skyhook['slug']
    season = funcs.format_season_episode(sonarr_envs.delete_season, sonarr_envs.delete_episode)[0]
    episode = funcs.format_season_episode(sonarr_envs.delete_season, sonarr_envs.delete_episode)[1]

    message = {
        "title": "Sonarr",
        "topic": config.NTFY_SONARR_MISC_TOPIC,
        "tags": ["sonarr", "tv", "delete"],
        "priority": config.NTFY_SONARR_PRIORITY,
        "actions": [{"action": "view", "label": "Visit Sonarr", "url": f"{config.SONARR_URL}"},
                    {"action": "view", "label": "IMDb",
                     "url": f"{funcs.get_sonarr_links(sonarr_envs.tvdb_id, sonarr_envs.imdb_id, skyhook, slug)[3]}"},
                    {"action": "view", "label": "TheTVDB",
                     "url": f"{funcs.get_sonarr_links(sonarr_envs.tvdb_id, sonarr_envs.imdb_id, skyhook, slug)[0]}"}],
        "message": f"Deleted {sonarr_envs.media_title} - S{season}E{episode} - {sonarr_envs.delete_episode_name} from Sonarr."
                   f"\n\nSeries name: {sonarr_envs.media_title}"
                   f"\nEpisode name: {sonarr_envs.delete_episode_name}"
                   f"\nSeason: {season}"
                   f"\nEpisode: {episode}"
                   f"\nQuality: {sonarr_envs.delete_quality}"
                   f"\nRelease Group: {sonarr_envs.delete_release_group}"
                   f"\nAired on: {sonarr_envs.delete_air_date} UTC"
                   f"\n\nFile name\n{sonarr_envs.scene_name}"
                   f"\n\nFile location\n{sonarr_envs.episode_path}"
        # f"\n\nView Details: TheMovieDb: {funcs.get_sonarr_links(sonarr_envs.tvdb_id, sonarr_envs.imdb_id, skyhook, slug)[4]}, Trakt: {funcs.get_sonarr_links(sonarr_envs.tvdb_id, sonarr_envs.imdb_id, skyhook, slug)[2]}, TVMaze: {funcs.get_sonarr_links(sonarr_envs.tvdb_id, sonarr_envs.imdb_id, skyhook, slug)[1]}"
    }

    if config.NTFY_SONARR_PRIORITY == "":
        del message["priority"]

    if sonarr_envs.delete_release_group == "":
        import re
        pattern = r'Release Group: '
        log.warning("Release Group field is unknown, removing it..")
        mod_string = re.sub(pattern, '', message["message"])
        message["message"] = mod_string

    if sonarr_envs.scene_name == "":
        import re
        pattern = r'Release Name: Unknown'
        log.warning("Release Name field is unknown, removing it..")
        mod_string = re.sub(pattern, '', message["message"])
        message["message"] = mod_string

    try:
        sender = requests.post(config.NTFY_URL, headers=config.NTFY_HEADER, json=message)
        if sender.status_code == 200:
            log.success("Successfully sent delete episode notification to ntfy.")
        else:
            log.error(
                "Error occured when trying to send delete episode notification to ntfy. Please open an issue with the below contents.")
            log.error("-------------------------------------------------------")
            log.error(f"Status code: {sender.status_code}")
            log.error(f"Status body: {sender.content}")
            log.error(json.dumps(message, sort_keys=True, indent=4, separators=(",", ": ")))
            log.error("-------------------------------------------------------")
    except RequestException as e:
        log.error(e)
        log.error("Error occured when trying to send delete episode notification to ntfy.")


def sonarr_delete_series():
    skyhook = requests.get(f'http://skyhook.sonarr.tv/v1/tvdb/shows/en/{sonarr_envs.tvdb_id}').json()
    slug = skyhook['slug']

    message = {
        "title": "Sonarr",
        "topic": config.NTFY_SONARR_MISC_TOPIC,
        "tags": ["sonarr", "tv", "delete"],
        "priority": config.NTFY_SONARR_PRIORITY,
        "actions": [{"action": "view", "label": "Visit Sonarr", "url": f"{config.SONARR_URL}"},
                    {"action": "view", "label": "IMDb",
                     "url": f"{funcs.get_sonarr_links(sonarr_envs.tvdb_id, sonarr_envs.imdb_id, skyhook, slug)[3]}"},
                    {"action": "view", "label": "TheTVDB",
                     "url": f"{funcs.get_sonarr_links(sonarr_envs.tvdb_id, sonarr_envs.imdb_id, skyhook, slug)[0]}"}],
        "message": f"Deleted {sonarr_envs.media_title} from Sonarr."
                   f"\n\nSeries name: {sonarr_envs.media_title}"
                   f"\nPath: {sonarr_envs.series_path}"
        # f"\n\nView Details: TheMovieDb: {funcs.get_sonarr_links(sonarr_envs.tvdb_id, sonarr_envs.imdb_id, skyhook, slug)[4]}, Trakt: {funcs.get_sonarr_links(sonarr_envs.tvdb_id, sonarr_envs.imdb_id, skyhook, slug)[2]}, TVMaze: {funcs.get_sonarr_links(sonarr_envs.tvdb_id, sonarr_envs.imdb_id, skyhook, slug)[1]}"
    }

    if config.NTFY_SONARR_PRIORITY == "":
        del message["priority"]

    try:
        sender = requests.post(config.NTFY_URL, headers=config.NTFY_HEADER, json=message)
        if sender.status_code == 200:
            log.success("Successfully sent series delete notification to ntfy.")
        else:
            log.error(
                "Error occured when trying to send series delete notification to ntfy. Please open an issue with the below contents.")
            log.error("-------------------------------------------------------")
            log.error(f"Status code: {sender.status_code}")
            log.error(f"Status body: {sender.content}")
            log.error(json.dumps(message, sort_keys=True, indent=4, separators=(",", ": ")))
            log.error("-------------------------------------------------------")
    except RequestException as e:
        log.error(e)
        log.error("Error occured when trying to send series delete notification to ntfy.")


def sonarr_update():
    update_message = sonarr_envs.update_message

    if len(update_message) >= 250:
        update_message = update_message[:200]
        update_message += '...'

    message = {
        "title": "Sonarr",
        "topic": config.NTFY_SONARR_MISC_TOPIC,
        "tags": ["sonarr", "tv", "update"],
        "priority": config.NTFY_SONARR_PRIORITY,
        "actions": [{"action": "view", "label": "Visit Sonarr", "url": f"{config.SONARR_URL}"}],
        "message": f"Sonarr has been updated to {sonarr_envs.new_version}."
                   #f"\n\nNew version: {sonarr_envs.new_version}"
                   f"\n\nOld version: {sonarr_envs.old_version}"
                   f"\n\nUpdate Notes\n{update_message}"
    }

    if config.NTFY_SONARR_PRIORITY == "":
        del message["priority"]

    try:
        sender = requests.post(config.NTFY_URL, headers=config.NTFY_HEADER, json=message)
        if sender.status_code == 200:
            log.success("Successfully sent app update notification to ntfy.")
        else:
            log.error(
                "Error occured when trying to send app update notification to ntfy. Please open an issue with the below contents.")
            log.error("-------------------------------------------------------")
            log.error(f"Status code: {sender.status_code}")
            log.error(f"Status body: {sender.content}")
            log.error(json.dumps(message, sort_keys=True, indent=4, separators=(",", ": ")))
            log.error("-------------------------------------------------------")
    except RequestException as e:
        log.error(e)
        log.error("Error occured when trying to send app update notification to ntfy.")
