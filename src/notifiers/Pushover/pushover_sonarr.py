import json

import config
import requests
from helpers import funcs, ratings, sonarr_envs, omdb
from loguru import logger as log
from requests import RequestException

HEADERS = {"content-type": "application/json"}


def sonarr_test():
    test = {
        "html": 1,
        "user": config.PUSHOVER_USER,
        "token": config.SONARR_PUSHOVER_TOKEN,
        "device": config.PUSHOVER_DEVICE,
        "priority": config.PUSHOVER_PRIORITY,
        "sound": config.PUSHOVER_SOUND,
        "retry": 60,
        "expire": 3600,
        "url": config.SONARR_URL,
        "url_title": "Visit Sonarr",
        "message": "<b>Bettarr Notifications for Sonarr test message.\nThank you for using the script!</b>"}

    try:
        sender = requests.post(config.PUSHOVER_API_URL, headers=HEADERS, json=test)
        if sender.status_code == 200:
            log.success("Successfully sent test notification to Pushover.")
        else:
            log.error(
                "Error occured when trying to send test notification to Pushover. Please open an issue with the below contents.")
            log.error("-------------------------------------------------------")
            log.error(f"Status code: {sender.status_code}")
            log.error(f"Status body: {sender.content}")
            log.error(json.dumps(test, sort_keys=True, indent=4, separators=(",", ": ")))
            log.error("-------------------------------------------------------")
    except RequestException as e:
        log.error(e)
        log.error("Error occured when trying to send test notification to Pushover.")


def sonarr_grab():
    skyhook = requests.get(f"http://skyhook.sonarr.tv/v1/tvdb/shows/en/{sonarr_envs.tvdb_id}").json()
    season = funcs.format_season_episode(sonarr_envs.season, sonarr_envs.episode)[0]
    episode = funcs.format_season_episode(sonarr_envs.season, sonarr_envs.episode)[1]

    title = f"Grabbed <b>{sonarr_envs.media_title}</b> - <b>S{season}E{episode}</b> - <b>{sonarr_envs.episode_title}</b> from <b>{sonarr_envs.release_indexer}</b>."
    if len(title) >= 150:
        title = title[:100]
        title += f'...</b> from <b>{sonarr_envs.release_indexer}</b>.'

    try:
        cast = f"\nCast: <a href={funcs.get_seriescast(sonarr_envs.tvdb_id, sonarr_envs.imdb_id)[0][0]}>{funcs.get_seriescast(sonarr_envs.tvdb_id, sonarr_envs.imdb_id)[1][0]}</a>, <a href={funcs.get_seriescast(sonarr_envs.tvdb_id, sonarr_envs.imdb_id)[0][2]}>{funcs.get_seriescast(sonarr_envs.tvdb_id, sonarr_envs.imdb_id)[1][1]}</a>, <a href={funcs.get_seriescast(sonarr_envs.tvdb_id, sonarr_envs.imdb_id)[0][1]}>{funcs.get_seriescast(sonarr_envs.tvdb_id, sonarr_envs.imdb_id)[1][2]}</a>"
    except (KeyError, TypeError, IndexError, Exception):
        try:
            cast = f"\nCast: <a href={funcs.get_seriescast(sonarr_envs.tvdb_id, sonarr_envs.imdb_id)[0][0]}>{funcs.get_seriescast(sonarr_envs.tvdb_id, sonarr_envs.imdb_id)[1][0]}</a>"
        except (KeyError, TypeError, IndexError, Exception):
            cast = ""

    if funcs.get_seriescrew(sonarr_envs.tvdb_id, sonarr_envs.imdb_id)[1] == "Unknown":
        director = ""
    else:
        director = f"\n<b>Director</b>: <a href={funcs.get_seriescrew(sonarr_envs.tvdb_id, sonarr_envs.imdb_id)[0]}>{funcs.get_seriescrew(sonarr_envs.tvdb_id, sonarr_envs.imdb_id)[1]}</a>"

    if sonarr_envs.release_group == "":
        release_group = ""
    else:
        release_group = f"\n<b>Release Group</b>: {sonarr_envs.release_group}"

    if omdb.omdb_sonarr(sonarr_envs.imdb_id) == "":
        awards = ""
    else:
        awards = f"\n<b>Awards</b>: {omdb.omdb_sonarr(sonarr_envs.imdb_id)}"

    message = {
        "html": 1,
        "user": config.PUSHOVER_USER,
        "token": config.SONARR_PUSHOVER_TOKEN,
        "device": config.PUSHOVER_DEVICE,
        "priority": config.PUSHOVER_PRIORITY,
        "sound": config.PUSHOVER_SOUND,
        "retry": 60,
        "expire": 3600,
        "url": config.SONARR_URL,
        "url_title": "Visit Sonarr",
        "message": f"{title}{funcs.get_sonarr_overview(sonarr_envs.tvdb_id, sonarr_envs.imdb_id)[2]}{ratings.mdblist_tv()[6]}\n"
                   f"\n<b>Episode</b>: S{season}E{episode}"
                   f"\n<b>Quality</b>: {sonarr_envs.quality}"
                   f"\n<b>Size</b>: {funcs.convert_size(int(sonarr_envs.size))}"
                   f"\n<b>Download Client</b>: {sonarr_envs.download_client}"
                   f"{release_group}"
                   f"\n<b>Network</b>: {funcs.get_sonarr_network(skyhook)}"
                   f"\n<b>Content Rating</b>: {funcs.get_sonarr_contentrating(skyhook)}"
                   f"\n<b>Genre(s)</b>: {funcs.get_sonarrgenres(skyhook)}"
                   f"{cast}"
                   f"{director}"
                   f"\n<b>Available On</b> ({funcs.get_tv_watch_providers(sonarr_envs.tvdb_id, sonarr_envs.imdb_id)[1]}): {funcs.get_tv_watch_providers(sonarr_envs.tvdb_id, sonarr_envs.imdb_id)[0]}"
                   f"\n<a href={funcs.get_sonarr_trailer()}>Trailer</a>"
                   f"{awards}"
    }

    if funcs.get_tv_watch_providers(sonarr_envs.tvdb_id, sonarr_envs.imdb_id)[0] == "None":
        import re
        pattern = r'<b>Available On \([^()]*\)<\/b>: None'
        log.warning("Available On field is unknown, removing it..")
        mod_string = re.sub(pattern, '', message["message"])
        message["message"] = mod_string

    if funcs.get_sonarr_contentrating(skyhook) == "Unknown":
        import re
        pattern = r'<b>Content Rating<\/b>: '
        log.warning("Content Rating field is unknown, removing it..")
        mod_string = re.sub(pattern, '', message["message"])
        message["message"] = mod_string

    """
    if sonarr_envs.release_group == "":
        import re
        pattern = r'<b>Release Group<\/b>: '
        log.warning("Release Group field is unknown, removing it..")
        mod_string = re.sub(pattern, '', message["message"])
        message["message"] = mod_string
    """

    if len(message["message"]) > 1024:
        log.warning(
            f"Pushover message length is greater than 1024, current length: {len(message['message'])}. Some of the message will be removed.")

    message['message'].rstrip()

    try:
        sender = requests.post(config.PUSHOVER_API_URL, data=message,
                               files={"attachment": ("poster.jpg", open(
                                   funcs.get_pushover_sonarrposter(sonarr_envs.tvdb_id, sonarr_envs.imdb_id), "rb"),
                                                     "image/jpeg")})
        if sender.status_code == 200:
            log.success("Successfully sent grab notification to Pushover.")
        else:
            log.error(
                "Error occured when trying to send grab notification to Pushover. Please open an issue with the below contents.")
            log.error("-------------------------------------------------------")
            log.error(f"Status code: {sender.status_code}")
            log.error(f"Status body: {sender.content}")
            log.error(json.dumps(message, sort_keys=True, indent=4, separators=(",", ": ")))
            log.error("-------------------------------------------------------")
    except RequestException as e:
        log.error(e)
        log.error("Error occured when trying to send grab notification to Pushover.")


def sonarr_import():
    skyhook = requests.get(f'http://skyhook.sonarr.tv/v1/tvdb/shows/en/{sonarr_envs.tvdb_id}').json()
    season = funcs.format_season_episode(sonarr_envs.import_season, sonarr_envs.import_episode)[0]
    episode = funcs.format_season_episode(sonarr_envs.import_season, sonarr_envs.import_episode)[1]

    if sonarr_envs.is_upgrade == "True":
        content = f'Upgraded <b>{sonarr_envs.media_title}</b> - <b>S{season}E{episode}</b> - <b>{sonarr_envs.import_episode_title}</b>.'
    else:
        content = f'Downloaded <b>{sonarr_envs.media_title}</b> - <b>S{season}E{episode}</b> - <b>{sonarr_envs.import_episode_title}</b>.'

    if sonarr_envs.scene_name != "":
        release_name = f"\n\n<b>Release Name</b>\n{sonarr_envs.scene_name}"
    else:
        release_name = ""

    message = {
        "html": 1,
        "user": config.PUSHOVER_USER,
        "token": config.SONARR_PUSHOVER_TOKEN,
        "device": config.PUSHOVER_DEVICE,
        "priority": config.PUSHOVER_PRIORITY,
        "sound": config.PUSHOVER_SOUND,
        "retry": 60,
        "expire": 3600,
        "url": config.SONARR_URL,
        "url_title": "Visit Sonarr",
        "message": f"{content}{funcs.get_sonarr_episodeoverview(season, episode, sonarr_envs.tvdb_id, sonarr_envs.imdb_id)[2]}"
                   f"\n<b>Episode</b>: S{season}E{episode}"
                   f"\n<b>Quality</b>: {sonarr_envs.import_quality}"
                   f"\n<b>Content Rating</b>: {funcs.get_sonarr_contentrating(skyhook)}"
                   f"\n<b>Network</b>: {funcs.get_sonarr_network(skyhook)}"
                   f"\n<b>Genre(s)</b>: {funcs.get_sonarrgenres(skyhook)}"
                   f"\n<b>Air Date</b>: {sonarr_envs.delete_air_date} UTC"
                   f"{release_name}"
    }

    if funcs.get_sonarr_episodeoverview(season, episode, sonarr_envs.tvdb_id, sonarr_envs.imdb_id)[2] == "...":
        import re
        pattern = r'<strong>Overview<\/strong> ...'
        log.warning("Overview field is unknown, removing it..")
        mod_string = re.sub(pattern, '', message["message"])
        message["message"] = mod_string

    if sonarr_envs.delete_air_date == "":
        import re
        pattern = r'<b>Air Date<\/b>: UTC'
        log.warning("Air Date field is unknown, removing it..")
        mod_string = re.sub(pattern, '', message["message"])
        message["message"] = mod_string

    if funcs.get_sonarr_contentrating(skyhook) == "Unknown":
        import re
        pattern = r'<b>Content Rating<\/b>: '
        log.warning("Content Rating field is unknown, removing it..")
        mod_string = re.sub(pattern, '', message["message"])
        message["message"] = mod_string

    try:
        sender = requests.post(config.PUSHOVER_API_URL, data=message,
                               files={"attachment": ("still.jpg", open(
                                   funcs.get_pushover_sonarrstill(sonarr_envs.tvdb_id, sonarr_envs.imdb_id, season,
                                                                  episode, skyhook), "rb"), "image/jpeg")})
        if sender.status_code == 200:
            log.success("Successfully sent import notification to Pushover.")
        else:
            log.error(
                "Error occured when trying to send import notification to Pushover. Please open an issue with the below contents.")
            log.error("-------------------------------------------------------")
            log.error(f"Status code: {sender.status_code}")
            log.error(f"Status body: {sender.content}")
            log.error(json.dumps(message, sort_keys=True, indent=4, separators=(",", ": ")))
            log.error("-------------------------------------------------------")
    except RequestException as e:
        log.error(e)
        log.error("Error occured when trying to send import notification to Pushover.")


def sonarr_health():
    message = {
        "html": 1,
        "user": config.PUSHOVER_USER,
        "token": config.SONARR_HEALTH_PUSHOVER_TOKEN,
        "device": config.PUSHOVER_DEVICE,
        "priority": config.PUSHOVER_PRIORITY,
        "sound": config.PUSHOVER_SOUND,
        "retry": 60,
        "expire": 3600,
        "url": config.SONARR_URL,
        "url_title": "Visit Sonarr",
        "message": "<b>An issue has occured on Sonarr.</b>"
                   f"\n\n<b>Error Level</b>: {sonarr_envs.issue_level}"
                   f"\n<b>Error Type</b>: {sonarr_envs.issue_type}"
                   f"\n<b>Error Message</b>: {sonarr_envs.issue_message}"
                   f"\n<b>Visit Wiki</b>: <a href={sonarr_envs.wiki_link}>Visit</a>"
    }

    try:
        sender = requests.post(config.PUSHOVER_API_URL, headers=HEADERS, json=message)
        if sender.status_code == 200:
            log.success("Successfully sent health notification to Pushover.")
        else:
            log.error(
                "Error occured when trying to send health notification to Pushover. Please open an issue with the below contents.")
            log.error("-------------------------------------------------------")
            log.error(f"Status code: {sender.status_code}")
            log.error(f"Status body: {sender.content}")
            log.error(json.dumps(message, sort_keys=True, indent=4, separators=(",", ": ")))
            log.error("-------------------------------------------------------")
    except RequestException as e:
        log.error(e)
        log.error("Error occured when trying to send health notification to Pushover.")


def sonarr_delete_episode():
    skyhook = requests.get(f'http://skyhook.sonarr.tv/v1/tvdb/shows/en/{sonarr_envs.tvdb_id}').json()
    slug = skyhook['slug']
    season = funcs.format_season_episode(sonarr_envs.delete_season, sonarr_envs.delete_episode)[0]
    episode = funcs.format_season_episode(sonarr_envs.delete_season, sonarr_envs.delete_episode)[1]

    message = {
        "html": 1,
        "user": config.PUSHOVER_USER,
        "token": config.SONARR_MISC_PUSHOVER_TOKEN,
        "device": config.PUSHOVER_DEVICE,
        "priority": config.PUSHOVER_PRIORITY,
        "sound": config.PUSHOVER_SOUND,
        "retry": 60,
        "expire": 3600,
        "url": config.SONARR_URL,
        "url_title": "Visit Sonarr",
        "message": f"Deleted <b>{sonarr_envs.media_title}</b> - <b>S{season}E{episode}</b> - <b>{sonarr_envs.delete_episode_name}</b> from Sonarr."
                   f"\n\n<b>Series name</b>: {sonarr_envs.media_title}"
                   f"\n<b>Episode name</b>: {sonarr_envs.delete_episode_name}"
                   f"\n<b>Season</b>: {season}"
                   f"\n<b>Episode</b>: {episode}"
                   f"\n<b>Quality</b>: {sonarr_envs.delete_quality}"
                   f"\n<b>Release Group</b>: {sonarr_envs.delete_release_group}"
                   f"\n<b>Aired on</b>: {sonarr_envs.delete_air_date} UTC"
                   f"\n\n<b>File name</b>:\n{sonarr_envs.scene_name}"
                   f"\n\n<b>File location</b>:\n{sonarr_envs.episode_path}"
                   f"\n\n<b>View Details</b>: <a href={funcs.get_sonarr_links(sonarr_envs.tvdb_id, sonarr_envs.imdb_id, skyhook, slug)[3]}>IMDb</a> | <a href={funcs.get_sonarr_links(sonarr_envs.tvdb_id, sonarr_envs.imdb_id, skyhook, slug)[0]}>TheTVDB</a> | <a href={funcs.get_sonarr_links(sonarr_envs.tvdb_id, sonarr_envs.imdb_id, skyhook, slug)[4]}>TheMovieDb</a> | <a href={funcs.get_sonarr_links(sonarr_envs.tvdb_id, sonarr_envs.imdb_id, skyhook, slug)[2]}>Trakt</a> | <a href={funcs.get_sonarr_links(sonarr_envs.tvdb_id, sonarr_envs.imdb_id, skyhook, slug)[1]}>TVmaze</a>"
    }

    if sonarr_envs.delete_release_group == "":
        import re
        pattern = r'<b>Release Group<\/b>: '
        log.warning("Release Group field is unknown, removing it..")
        mod_string = re.sub(pattern, '', message["message"])
        message["message"] = mod_string

    if sonarr_envs.scene_name == "":
        import re
        pattern = r'<b>Release Name<\/b>: Unknown'
        log.warning("Release Name field is unknown, removing it..")
        mod_string = re.sub(pattern, '', message["message"])
        message["message"] = mod_string

    try:
        sender = requests.post(config.PUSHOVER_API_URL, headers=HEADERS, json=message)
        if sender.status_code == 200:
            log.success("Successfully sent delete episode notification to Pushover.")
        else:
            log.error(
                "Error occured when trying to send delete episode notification to Pushover. Please open an issue with the below contents.")
            log.error("-------------------------------------------------------")
            log.error(f"Status code: {sender.status_code}")
            log.error(f"Status body: {sender.content}")
            log.error(json.dumps(message, sort_keys=True, indent=4, separators=(",", ": ")))
            log.error("-------------------------------------------------------")
    except RequestException as e:
        log.error(e)
        log.error("Error occured when trying to send delete episode notification to Pushover.")


def sonarr_delete_series():
    skyhook = requests.get(f'http://skyhook.sonarr.tv/v1/tvdb/shows/en/{sonarr_envs.tvdb_id}').json()
    slug = skyhook['slug']

    message = {
        "html": 1,
        "user": config.PUSHOVER_USER,
        "token": config.SONARR_MISC_PUSHOVER_TOKEN,
        "device": config.PUSHOVER_DEVICE,
        "priority": config.PUSHOVER_PRIORITY,
        "sound": config.PUSHOVER_SOUND,
        "retry": 60,
        "expire": 3600,
        "url": config.SONARR_URL,
        "url_title": "Visit Sonarr",
        "message": f"Deleted <b>{sonarr_envs.media_title}</b> from Sonarr."
                   f"\n\n<b>Series name</b>: {sonarr_envs.media_title}"
                   f"\n<b>Path</b>: {sonarr_envs.series_path}"
                   f"\n\n<b>View Details</b>: <a href={funcs.get_sonarr_links(sonarr_envs.tvdb_id, sonarr_envs.imdb_id, skyhook, slug)[3]}>IMDb</a> | <a href={funcs.get_sonarr_links(sonarr_envs.tvdb_id, sonarr_envs.imdb_id, skyhook, slug)[0]}>TheTVDB</a> | <a href={funcs.get_sonarr_links(sonarr_envs.tvdb_id, sonarr_envs.imdb_id, skyhook, slug)[4]}>TheMovieDb</a> | <a href={funcs.get_sonarr_links(sonarr_envs.tvdb_id, sonarr_envs.imdb_id, skyhook, slug)[2]}>Trakt</a> | <a href={funcs.get_sonarr_links(sonarr_envs.tvdb_id, sonarr_envs.imdb_id, skyhook, slug)[1]}>TVmaze</a>"
    }

    try:
        sender = requests.post(config.PUSHOVER_API_URL, headers=HEADERS, json=message)
        if sender.status_code == 200:
            log.success("Successfully sent series delete notification to Pushover.")
        else:
            log.error(
                "Error occured when trying to send series delete notification to Pushover. Please open an issue with the below contents.")
            log.error("-------------------------------------------------------")
            log.error(f"Status code: {sender.status_code}")
            log.error(f"Status body: {sender.content}")
            log.error(json.dumps(message, sort_keys=True, indent=4, separators=(",", ": ")))
            log.error("-------------------------------------------------------")
    except RequestException as e:
        log.error(e)
        log.error("Error occured when trying to send series delete notification to Pushover.")


def sonarr_update():
    update_message = sonarr_envs.update_message

    if len(update_message) >= 250:
        update_message = update_message[:200]
        update_message += '...</b>'

    message = {
        "html": 1,
        "user": config.PUSHOVER_USER,
        "token": config.SONARR_MISC_PUSHOVER_TOKEN,
        "device": config.PUSHOVER_DEVICE,
        "priority": config.PUSHOVER_PRIORITY,
        "sound": config.PUSHOVER_SOUND,
        "retry": 60,
        "expire": 3600,
        "url": config.SONARR_URL,
        "url_title": "Visit Sonarr",
        "message": f"Sonarr has been updated to <b>({sonarr_envs.new_version})</b>."
                   f"\n\n<b>Old version</b>: {sonarr_envs.old_version}"
                   f"\n\n<b>Update Notes</b>\n{update_message}"
    }

    try:
        sender = requests.post(config.PUSHOVER_API_URL, headers=HEADERS, json=message)
        if sender.status_code == 200:
            log.success("Successfully sent app update notification to Pushover.")
        else:
            log.error(
                "Error occured when trying to send app update notification to Pushover. Please open an issue with the below contents.")
            log.error("-------------------------------------------------------")
            log.error(f"Status code: {sender.status_code}")
            log.error(f"Status body: {sender.content}")
            log.error(json.dumps(message, sort_keys=True, indent=4, separators=(",", ": ")))
            log.error("-------------------------------------------------------")
    except RequestException as e:
        log.error(e)
        log.error("Error occured when trying to send app update notification to Pushover.")
