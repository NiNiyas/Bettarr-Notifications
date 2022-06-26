import json

import config
import requests
from helpers import funcs, ratings, sonarr_envs
from loguru import logger as log
from requests import RequestException

HEADERS = {"content-type": "application/json"}


def sonarr_test():
    test = {
        "chat_id": config.TELEGRAM_CHAT_ID,
        "parse_mode": "HTML",
        "disable_notification": config.TELEGRAM_SILENT,
        "text": "<b>Bettarr Notifications for Sonarr test message.\nThank you for using the script!</b>"}

    try:
        sender = requests.post(config.TELEGRAM_SONARR_URL, headers=HEADERS, json=test)
        if sender.status_code == 200:
            log.success("Successfully sent test notification to Telegram.")
        else:
            log.error(
                "Error occured when trying to send test notification to Telegram. Please open an issue with the below contents.")
            log.error("-------------------------------------------------------")
            log.error(f"Status code: {sender.status_code}")
            log.error(f"Status body: {sender.content}")
            log.error(json.dumps(test, sort_keys=True, indent=4, separators=(",", ": ")))
            log.error("-------------------------------------------------------")
    except RequestException as e:
        log.error(e)
        log.error("Error occured when trying to send test notification to Telegram.")


def sonarr_grab():
    skyhook = requests.get(f"http://skyhook.sonarr.tv/v1/tvdb/shows/en/{sonarr_envs.tvdb_id}").json()
    slug = skyhook["slug"]
    season = funcs.format_season_episode(sonarr_envs.season, sonarr_envs.episode)[0]
    episode = funcs.format_season_episode(sonarr_envs.season, sonarr_envs.episode)[1]

    title = f"Grabbed <b>{sonarr_envs.media_title}</b> - <b>S{season}E{episode}</b> - <b>{sonarr_envs.episode_title}</b> from <b>{sonarr_envs.release_indexer}</b>."

    try:
        cast = f"\nCast: <a href='{funcs.get_seriescast(sonarr_envs.tvdb_id, sonarr_envs.imdb_id)[0][0]}'>{funcs.get_seriescast(sonarr_envs.tvdb_id, sonarr_envs.imdb_id)[1][0]}</a>, <a href='{funcs.get_seriescast(sonarr_envs.tvdb_id, sonarr_envs.imdb_id)[0][2]}'>{funcs.get_seriescast(sonarr_envs.tvdb_id, sonarr_envs.imdb_id)[1][1]}</a>, <a href='{funcs.get_seriescast(sonarr_envs.tvdb_id, sonarr_envs.imdb_id)[0][1]}'>{funcs.get_seriescast(sonarr_envs.tvdb_id, sonarr_envs.imdb_id)[1][2]}</a>"
    except (KeyError, TypeError, IndexError, Exception):
        try:
            cast = f"\nCast: <a href='{funcs.get_seriescast(sonarr_envs.tvdb_id, sonarr_envs.imdb_id)[0][0]}'>{funcs.get_seriescast(sonarr_envs.tvdb_id, sonarr_envs.imdb_id)[1][0]}</a>"
        except (KeyError, TypeError, IndexError, Exception):
            cast = ""

    if funcs.get_seriescrew(sonarr_envs.tvdb_id, sonarr_envs.imdb_id)[1] == "Unknown":
        director = ""
    else:
        director = f"\n<b>Director</b>: <a href='{funcs.get_seriescrew(sonarr_envs.tvdb_id, sonarr_envs.imdb_id)[0]}'>{funcs.get_seriescrew(sonarr_envs.tvdb_id, sonarr_envs.imdb_id)[1]}</a>"

    message = {
        "chat_id": config.TELEGRAM_CHAT_ID,
        "parse_mode": "HTML",
        "disable_notification": config.TELEGRAM_SILENT,
        "disable_web_page_preview": config.TELEGRAM_DISABLE_IMAGES,
        "text": f"{title}\n\n<strong>Overview</strong>\n{funcs.get_sonarr_overview(sonarr_envs.tvdb_id, sonarr_envs.imdb_id)[1]}\n{ratings.mdblist_tv()[6]}\n"
                f"\n<b>Episode</b>: S{season}E{episode}"
                f"\n<b>Quality</b>: {sonarr_envs.quality}"
                f"\n<b>Size</b>: {funcs.convert_size(int(sonarr_envs.size))}"
                f"\n<b>Download Client</b>: {sonarr_envs.download_client}"
                f"\n<b>Release Group</b>: {sonarr_envs.release_group}"
                f"\n<b>Network</b>: {funcs.get_sonarr_network(skyhook)}"
                f"\n<b>Content Rating</b>: {funcs.get_sonarr_contentrating(skyhook)}"
                f"\n<b>Genre(s)</b>: {funcs.get_sonarrgenres(skyhook)}"
                f"<a href='{funcs.get_posterseries(sonarr_envs.tvdb_id, sonarr_envs.imdb_id)}'>&#8204;</a>"
                f"{cast}"
                f"{director}"
                f"\n<b>Available On</b> ({funcs.get_tv_watch_providers(sonarr_envs.tvdb_id, sonarr_envs.imdb_id)[1]}):  {funcs.get_tv_watch_providers(sonarr_envs.tvdb_id, sonarr_envs.imdb_id)[0]}"
                f"\n<b>Trailer</b>: <a href='{funcs.get_sonarr_trailer()}'>YouTube</a>"
                f"\n<b>View Details</b>: <a href='{funcs.get_sonarr_links(sonarr_envs.tvdb_id, sonarr_envs.imdb_id, skyhook, slug)[3]}'>IMDb</a>, <a href='{funcs.get_sonarr_links(sonarr_envs.tvdb_id, sonarr_envs.imdb_id, skyhook, slug)[0]}'>TheTVDB</a>, <a href='{funcs.get_sonarr_links(sonarr_envs.tvdb_id, sonarr_envs.imdb_id, skyhook, slug)[4]}'>TheMovieDb</a>, <a href='{funcs.get_sonarr_links(sonarr_envs.tvdb_id, sonarr_envs.imdb_id, skyhook, slug)[2]}'>Trakt</a>, <a href='{funcs.get_sonarr_links(sonarr_envs.tvdb_id, sonarr_envs.imdb_id, skyhook, slug)[1]}'>TVmaze</a>"

    }

    if funcs.get_tv_watch_providers(sonarr_envs.tvdb_id, sonarr_envs.imdb_id)[0] == "None":
        import re
        pattern = r'<b>Available On \([^()]*\)<\/b>: None'
        log.warning("Available On field is unknown, removing it..")
        mod_string = re.sub(pattern, '', message["text"])
        message["text"] = mod_string

    if funcs.get_sonarr_contentrating(skyhook) == "Unknown":
        import re
        pattern = r'<b>Content Rating<\/b>: '
        log.warning("Content Rating field is unknown, removing it..")
        mod_string = re.sub(pattern, '', message["text"])
        message["text"] = mod_string

    if sonarr_envs.release_group == "":
        import re
        pattern = r'<b>Release Group<\/b>: Unknown'
        mod_string = re.sub(pattern, '', message["text"])
        message["text"] = mod_string
        log.warning("Release group field is unknown, removing it..")

    try:
        sender = requests.post(config.TELEGRAM_SONARR_URL, headers=HEADERS, json=message)
        if sender.status_code == 200:
            log.success("Successfully sent grab notification to Telegram.")
        else:
            log.error(
                "Error occured when trying to send grab notification to Telegram. Please open an issue with the below contents.")
            log.error("-------------------------------------------------------")
            log.error(f"Status code: {sender.status_code}")
            log.error(f"Status body: {sender.content}")
            log.error(json.dumps(message, sort_keys=True, indent=4, separators=(",", ": ")))
            log.error("-------------------------------------------------------")
    except RequestException as e:
        log.error(e)
        log.error("Error occured when trying to send grab notification to Telegram.")


def sonarr_import():
    skyhook = requests.get(f'http://skyhook.sonarr.tv/v1/tvdb/shows/en/{sonarr_envs.tvdb_id}').json()
    season = funcs.format_season_episode(sonarr_envs.import_season, sonarr_envs.import_episode)[0]
    episode = funcs.format_season_episode(sonarr_envs.import_season, sonarr_envs.import_episode)[1]

    if sonarr_envs.is_upgrade == "True":
        content = f'Upgraded <b>{sonarr_envs.media_title}</b> - <b>S{season}E{episode}</b> - <b>{sonarr_envs.import_episode_title}</b>.'
    else:
        content = f'Downloaded <b>{sonarr_envs.media_title}</b> - <b>S{season}E{episode}</b> - <b>{sonarr_envs.import_episode_title}</b>.'

    if sonarr_envs.scene_name != "":
        release_name = f"\n<b>Release Name</b>: {sonarr_envs.scene_name}"
    else:
        release_name = ""

    message = {
        "chat_id": config.TELEGRAM_CHAT_ID,
        "parse_mode": "HTML",
        "disable_notification": config.TELEGRAM_SILENT,
        "disable_web_page_preview": config.TELEGRAM_DISABLE_IMAGES,
        "text": f"{content}\n\n<strong>Overview</strong>\n{funcs.get_sonarr_episodeoverview(season, episode, sonarr_envs.tvdb_id, sonarr_envs.imdb_id)[1]}\n"
                f"\n<b>Episode</b>: S{season}E{episode}"
                f"\n<b>Quality</b>: {sonarr_envs.import_quality}"
                f"\n<b>Content Rating</b>: {funcs.get_sonarr_contentrating(skyhook)}"
                f"\n<b>Network</b>: {funcs.get_sonarr_network(skyhook)}"
                f"\n<b>Genre(s)</b>: {funcs.get_sonarrgenres(skyhook)}"
                f"\n<b>Air Date</b>: {sonarr_envs.delete_air_date} UTC"
                f"{release_name}"
                f"<a href='{funcs.get_sonarr_episodesample(sonarr_envs.tvdb_id, sonarr_envs.imdb_id, season, episode, skyhook)}'>&#8204;</a>"
    }

    if funcs.get_sonarr_episodeoverview(season, episode, sonarr_envs.tvdb_id, sonarr_envs.imdb_id)[2] == "...":
        import re
        pattern = r'<strong>Overview<\/strong> ...'
        log.warning("Overview field is unknown, removing it..")
        mod_string = re.sub(pattern, '', message["text"])
        message["text"] = mod_string

    if sonarr_envs.delete_air_date == "":
        import re
        pattern = r'<b>Air Date<\/b>: UTC'
        log.warning("Air Date field is unknown, removing it..")
        mod_string = re.sub(pattern, '', message["text"])
        message["text"] = mod_string

    if funcs.get_sonarr_contentrating(skyhook) == "Unknown":
        import re
        pattern = r'<b>Content Rating<\/b>: '
        log.warning("Content Rating field is unknown, removing it..")
        mod_string = re.sub(pattern, '', message["text"])
        message["text"] = mod_string

    try:
        sender = requests.post(config.TELEGRAM_SONARR_URL, headers=HEADERS, json=message)
        if sender.status_code == 200:
            log.success("Successfully sent import notification to Telegram.")
        else:
            log.error(
                "Error occured when trying to send import notification to Telegram. Please open an issue with the below contents.")
            log.error("-------------------------------------------------------")
            log.error(f"Status code: {sender.status_code}")
            log.error(f"Status body: {sender.content}")
            log.error(json.dumps(message, sort_keys=True, indent=4, separators=(",", ": ")))
            log.error("-------------------------------------------------------")
    except RequestException as e:
        log.error(e)
        log.error("Error occured when trying to send import notification to Telegram.")


def sonarr_health():
    message = {
        "chat_id": config.TELEGRAM_HEALTH_CHAT_ID,
        "parse_mode": "HTML",
        "disable_notification": config.TELEGRAM_SILENT,
        "text": "<b>An issue has occured on Sonarr.</b>"
                f"\n\n<b>Error Level</b>: {sonarr_envs.issue_level}"
                f"\n<b>Error Type</b>: {sonarr_envs.issue_type}"
                f"\n<b>Error Message</b>: {sonarr_envs.issue_message}"
                f"\n<b>Visit Wiki</b>: <a href='{sonarr_envs.wiki_link}'>Visit</a>"
    }

    try:
        sender = requests.post(config.TELEGRAM_SONARR_HEALTH_URL, headers=HEADERS, json=message)
        if sender.status_code == 200:
            log.success("Successfully sent health notification to Telegram.")
        else:
            log.error(
                "Error occured when trying to send health notification to Telegram. Please open an issue with the below contents.")
            log.error("-------------------------------------------------------")
            log.error(f"Status code: {sender.status_code}")
            log.error(f"Status body: {sender.content}")
            log.error(json.dumps(message, sort_keys=True, indent=4, separators=(",", ": ")))
            log.error("-------------------------------------------------------")
    except RequestException as e:
        log.error(e)
        log.error("Error occured when trying to send health notification to Telegram.")


def sonarr_delete_episode():
    skyhook = requests.get(f'http://skyhook.sonarr.tv/v1/tvdb/shows/en/{sonarr_envs.tvdb_id}').json()
    slug = skyhook['slug']
    season = funcs.format_season_episode(sonarr_envs.delete_season, sonarr_envs.delete_episode)[0]
    episode = funcs.format_season_episode(sonarr_envs.delete_season, sonarr_envs.delete_episode)[1]

    message = {
        "chat_id": config.TELEGRAM_MISC_CHAT_ID,
        "parse_mode": "HTML",
        "disable_notification": config.TELEGRAM_SILENT,
        "text": f"Deleted <b>{sonarr_envs.media_title}</b> - <b>S{season}E{episode}</b> - <b>{sonarr_envs.delete_episode_name}</b>."
                f"\n\n<b>Series name</b>: {sonarr_envs.media_title}"
                f"\n<b>Episode name</b>: {sonarr_envs.delete_episode_name}"
                f"\n<b>Season</b>: {season}"
                f"\n<b>Episode</b>: {episode}"
                f"\n<b>Quality</b>: {sonarr_envs.delete_quality}"
                f"\n<b>Release Group</b>: {sonarr_envs.delete_release_group}"
                f"\n<b>Aired on</b>: {sonarr_envs.delete_air_date} UTC"
                f"\n\n<b>File name</b>:\n{sonarr_envs.scene_name}"
                f"\n\n<b>File location</b>:\n{sonarr_envs.episode_path}"
                f"\n\n<b>View Details</b>: <a href='{funcs.get_sonarr_links(sonarr_envs.tvdb_id, sonarr_envs.imdb_id, skyhook, slug)[3]}'>IMDb</a> | <a href='{funcs.get_sonarr_links(sonarr_envs.tvdb_id, sonarr_envs.imdb_id, skyhook, slug)[0]}'>TheTVDB</a> | <a href='{funcs.get_sonarr_links(sonarr_envs.tvdb_id, sonarr_envs.imdb_id, skyhook, slug)[4]}'>TheMovieDb</a> | <a href='{funcs.get_sonarr_links(sonarr_envs.tvdb_id, sonarr_envs.imdb_id, skyhook, slug)[2]}'>Trakt</a> | <a href='{funcs.get_sonarr_links(sonarr_envs.tvdb_id, sonarr_envs.imdb_id, skyhook, slug)[1]}'>TVmaze</a>"
    }

    if sonarr_envs.delete_release_group == "":
        import re
        pattern = r'<b>Release Group<\/b>: Unknown'
        mod_string = re.sub(pattern, '', message["text"])
        message["text"] = mod_string
        log.warning("Release Group field is unknown, removing it..")

    if sonarr_envs.scene_name == "":
        import re
        pattern = r'<b>Release Name<\/b>: '
        mod_string = re.sub(pattern, '', message["text"])
        message["text"] = mod_string
        log.warning("Scene name field is unknown, removing it..")

    try:
        sender = requests.post(config.TELEGRAM_SONARR_MISC_URL, headers=HEADERS, json=message)
        if sender.status_code == 200:
            log.success("Successfully sent episode delete notification to Telegram.")
        else:
            log.error(
                "Error occured when trying to send delete episode notification to Telegram. Please open an issue with the below contents.")
            log.error("-------------------------------------------------------")
            log.error(f"Status code: {sender.status_code}")
            log.error(f"Status body: {sender.content}")
            log.error(json.dumps(message, sort_keys=True, indent=4, separators=(",", ": ")))
            log.error("-------------------------------------------------------")
    except RequestException as e:
        log.error(e)
        log.error("Error occured when trying to send delete episode notification to Telegram.")


def sonarr_delete_series():
    skyhook = requests.get(f'http://skyhook.sonarr.tv/v1/tvdb/shows/en/{sonarr_envs.tvdb_id}').json()
    slug = skyhook['slug']

    message = {
        "chat_id": config.TELEGRAM_MISC_CHAT_ID,
        "parse_mode": "HTML",
        "disable_notification": config.TELEGRAM_SILENT,
        "text": f"Deleted <b>{sonarr_envs.media_title}</b> from Sonarr."
                f"\n\n<b>Series name</b>: {sonarr_envs.media_title}"
                f"\n<b>Path</b>: {sonarr_envs.series_path}"
                f"\n<b>View Details</b>: <a href='{funcs.get_sonarr_links(sonarr_envs.tvdb_id, sonarr_envs.imdb_id, skyhook, slug)[3]}'>IMDb</a> | <a href='{funcs.get_sonarr_links(sonarr_envs.tvdb_id, sonarr_envs.imdb_id, skyhook, slug)[0]}'>TheTVDB</a> | <a href='{funcs.get_sonarr_links(sonarr_envs.tvdb_id, sonarr_envs.imdb_id, skyhook, slug)[4]}'>TheMovieDb</a> | <a href='{funcs.get_sonarr_links(sonarr_envs.tvdb_id, sonarr_envs.imdb_id, skyhook, slug)[2]}'>Trakt</a> | <a href='{funcs.get_sonarr_links(sonarr_envs.tvdb_id, sonarr_envs.imdb_id, skyhook, slug)[1]}'>TVmaze</a>"

    }

    try:
        sender = requests.post(config.TELEGRAM_SONARR_MISC_URL, headers=HEADERS, json=message)
        if sender.status_code == 200:
            log.success("Successfully sent series delete notification to Telegram.")
        else:
            log.error(
                "Error occured when trying to send series delete notification to Telegram. Please open an issue with the below contents.")
            log.error("-------------------------------------------------------")
            log.error(f"Status code: {sender.status_code}")
            log.error(f"Status body: {sender.content}")
            log.error(json.dumps(message, sort_keys=True, indent=4, separators=(",", ": ")))
            log.error("-------------------------------------------------------")
    except RequestException as e:
        log.error(e)
        log.error("Error occured when trying to send series delete notification to Telegram.")


def sonarr_update():
    message = {
        "chat_id": config.TELEGRAM_MISC_CHAT_ID,
        "parse_mode": "HTML",
        "disable_notification": config.TELEGRAM_SILENT,
        "text": f"A new update <b>({sonarr_envs.new_version})</b> is available for Sonarr."
                f"\n\n<b>New version</b>: {sonarr_envs.new_version}"
                f"\n<b>Old version</b>: {sonarr_envs.old_version}"
                f"\n<b>Update Notes</b>: {sonarr_envs.update_message}"
    }

    try:
        sender = requests.post(config.TELEGRAM_SONARR_MISC_URL, headers=HEADERS, json=message)
        if sender.status_code == 200:
            log.success("Successfully sent app update notification to Telegram.")
        else:
            log.error(
                "Error occured when trying to send app update notification to Telegram. Please open an issue with the below contents.")
            log.error("-------------------------------------------------------")
            log.error(f"Status code: {sender.status_code}")
            log.error(f"Status body: {sender.content}")
            log.error(json.dumps(message, sort_keys=True, indent=4, separators=(",", ": ")))
            log.error("-------------------------------------------------------")
    except RequestException as e:
        log.error(e)
        log.error("Error occured when trying to send app update notification to Telegram.")
