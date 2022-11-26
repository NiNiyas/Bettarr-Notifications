import json

import config
import requests
from helpers import funcs, ratings, radarr_envs, omdb
from loguru import logger as log
from requests import RequestException

HEADERS = {"content-type": "application/json"}

log = log.patch(lambda record: record.update(name="Telegram Radarr"))


def radarr_test():
    test = {
        "chat_id": config.TELEGRAM_CHAT_ID,
        "parse_mode": "HTML",
        "disable_notification": config.TELEGRAM_SILENT,
        "text": "<b>Bettarr Notifications for Radarr test message.\nThank you for using the script!</b>"}

    try:
        sender = requests.post(config.TELEGRAM_RADARR_URL, headers=HEADERS, json=test, timeout=60)
        if sender.status_code == 200:
            log.success("Successfully sent test notification to Telegram.")
        else:
            log.error(
                "Error occured when trying to send test notification to Telegram. Please open an issue with the below contents.")
            log.error("-------------------------------------------------------")
            log.error(f"Status code: {sender.status_code}")
            log.error(f"Status body: {sender.content}")
            log.error(json.dumps(test, sort_keys=True, indent=4, separators=(',', ': ')))
            log.error("-------------------------------------------------------")
    except RequestException as e:
        log.error(e)
        log.error("Error occured when trying to send test notification to Telegram.")


def radarr_grab():
    radarr = requests.get(f"{config.RADARR_URL}api/v3/movie/{radarr_envs.movie_id}?apikey={config.RADARR_APIKEY}")
    radarr = radarr.json()

    try:
        cast = f"<a href='{funcs.get_movie_cast(radarr_envs.tmdb_id)[0][0]}'>{funcs.get_movie_cast(radarr_envs.tmdb_id)[1][0]}</a>, <a href='{funcs.get_movie_cast(radarr_envs.tmdb_id)[0][1]}'>{funcs.get_movie_cast(radarr_envs.tmdb_id)[1][1]}</a>, <a href='{funcs.get_movie_cast(radarr_envs.tmdb_id)[0][2]}'>{funcs.get_movie_cast(radarr_envs.tmdb_id)[1][2]}</a>"
    except (KeyError, TypeError, IndexError):
        try:
            cast = f"<a href='{funcs.get_movie_cast(radarr_envs.tmdb_id)[0][0]}'>{funcs.get_movie_cast(radarr_envs.tmdb_id)[1][0]}</a>"
        except (KeyError, TypeError, IndexError):
            cast = "Unknown"

    if radarr_envs.release_group == "":
        release_group = ""
    else:
        release_group = f"\n<b>Release Group</b>: {radarr_envs.release_group}"

    if omdb.omdb_radarr(radarr_envs.imdb_id) == "N/A":
        awards = ""
    else:
        awards = f"\n<b>Awards</b>: {omdb.omdb_radarr(radarr_envs.imdb_id)}"

    message = {
        "chat_id": config.TELEGRAM_CHAT_ID,
        "parse_mode": "HTML",
        "disable_notification": config.TELEGRAM_SILENT,
        "disable_web_page_preview": config.TELEGRAM_DISABLE_IMAGES,
        "text": f"Grabbed <b>{radarr_envs.media_title}</b> ({radarr_envs.year}) from <b>{radarr_envs.release_indexer}</b>."
                f"\n\n<strong>Overview</strong>\n{funcs.get_radarr_overview(radarr)[1]}\n{ratings.mdblist_movie()[3]}"
                f"\n\n<b>Quality</b>: {radarr_envs.quality}"
                f"\n<b>Size</b>: {funcs.convert_size(int(radarr_envs.release_size))}"
                f"\n<b>Download Client</b>: {radarr_envs.download_client}"
                f"{release_group}"
                f"\n<b>Release Date</b>: {funcs.get_radarr_releasedate(radarr_envs.tmdb_id)}"
                f"\n<b>Content Rating</b>: {ratings.mdblist_movie()[1]}"
                f"\n<b>Genre(s)</b>: {funcs.get_radarr_genres(radarr)}"
                f"<a href='{funcs.get_radarrposter(radarr_envs.tmdb_id)}'>&#8204;</a>"
                f"\n<b>Cast</b>: {cast}"
                f"\n<b>Director</b>: <a href='{funcs.get_movie_crew(radarr_envs.tmdb_id)[0][0]}'>{funcs.get_movie_crew(radarr_envs.tmdb_id)[1][0]}</a>"
                f"\n<b>Available On</b> ({funcs.get_movie_watch_providers(radarr_envs.tmdb_id, radarr_envs.imdb_id)[1]}): {funcs.get_movie_watch_providers(radarr_envs.tmdb_id, radarr_envs.imdb_id)[0]}"
                f"{awards}"
                f"\n<b>View Details</b>: <a href='{funcs.get_radarr_links(radarr_envs.imdb_id, radarr_envs.tmdb_id)[0]}'>IMDb</a>, <a href='{funcs.get_radarr_links(radarr_envs.imdb_id, radarr_envs.tmdb_id)[1]}'>TheMovieDb</a>, <a href='{funcs.get_radarr_links(radarr_envs.imdb_id, radarr_envs.tmdb_id)[2]}'>Trakt</a>, <a href='{funcs.get_radarr_links(radarr_envs.imdb_id, radarr_envs.tmdb_id)[3]}'>MovieChat</a>"
    }

    if funcs.get_movie_watch_providers(radarr_envs.tmdb_id, radarr_envs.imdb_id)[0] == "None":
        import re
        pattern = r'<b>Available On<\/b> \([^()]*\): None'
        log.debug("Available On field is unknown, removing it..")
        mod_string = re.sub(pattern, '', message["text"])
        message["text"] = mod_string

    if cast == "Unknown":
        import re
        pattern = r'<b>Cast<\/b>: Unknown'
        log.debug("Cast field is unknown, removing it..")
        mod_string = re.sub(pattern, '', message["text"])
        message["text"] = mod_string

    if funcs.get_movie_crew(radarr_envs.tmdb_id)[1][0] == "Unknown":
        import re
        string = message["text"]
        pattern = r"<b>Director<\/b>: <a href='\[\]'>Unknown<\/a>"
        log.debug("Director field is unknown, removing it..")
        mod_string = re.sub(pattern, '', string)
        message["text"] = mod_string

    message['text'].rstrip()

    try:
        sender = requests.post(config.TELEGRAM_RADARR_URL, headers=HEADERS, json=message, timeout=60)
        if sender.status_code == 200:
            log.success("Successfully sent grab notification to Telegram.")
        else:
            log.error(
                "Error occured when trying to send grab notification to Telegram. Please open an issue with the below contents.")
            log.error("-------------------------------------------------------")
            log.error(f"Status code: {sender.status_code}")
            log.error(f"Status body: {sender.content}")
            log.error(json.dumps(message, sort_keys=True, indent=4, separators=(',', ': ')))
            log.error("-------------------------------------------------------")
    except RequestException as e:
        log.error(e)
        log.error("Error occured when trying to send grab notification to Telegram.")


def radarr_import():
    radarr = requests.get(f"{config.RADARR_URL}api/v3/movie/{radarr_envs.movie_id}?apikey={config.RADARR_APIKEY}")
    radarr = radarr.json()

    if radarr_envs.is_upgrade == "True":
        content = f"Upgraded <b>{radarr_envs.media_title}</b> ({radarr_envs.year}).\n\n"
    else:
        content = f"Downloaded <b>{radarr_envs.media_title}</b> ({radarr_envs.year}).\n\n"

    if funcs.get_radarr_physicalrelease(radarr) != "Unknown":
        physical_releasedate = f"\n<b>Physical Release</b>: {funcs.get_radarr_physicalrelease(radarr)}"
    else:
        physical_releasedate = ""

    if radarr_envs.scene_name != "":
        release_name = f"\n\n<b>Release Name</b>\n{radarr_envs.scene_name}"
    else:
        release_name = ""

    message = {
        "chat_id": config.TELEGRAM_CHAT_ID,
        "parse_mode": "HTML",
        "disable_notification": config.TELEGRAM_SILENT,
        "disable_web_page_preview": config.TELEGRAM_DISABLE_IMAGES,
        "text": f"{content}"
                f"<strong>Overview</strong>\n{funcs.get_radarr_overview(radarr)[2]}"
                f"\n<b>Quality</b>: {radarr_envs.import_quality}"
                f"\n<b>Release Date</b>: {funcs.get_radarr_releasedate(radarr_envs.tmdb_id)}"
                f"{physical_releasedate}"
                f"\n<b>Genre(s)</b>: {funcs.get_radarr_genres(radarr)}"
                f"<a href='{funcs.get_radarr_backdrop(radarr_envs.tmdb_id)}'>&#8204;</a>"
                f"\n<b>Trailer</b>: <a href='{funcs.get_radarr_trailer(radarr)}'>Youtube</a>"
                f"{release_name}"
    }

    if radarr_envs.scene_name == "":
        import re
        string = message["text"]
        pattern = r'<b>Release Name<\/b>: '
        mod_string = re.sub(pattern, '', string)
        message["text"] = mod_string

    try:
        sender = requests.post(config.TELEGRAM_RADARR_URL, headers=HEADERS, json=message, timeout=60)
        if sender.status_code == 200:
            log.success("Successfully sent import notification to Telegram.")
        else:
            log.error(
                "Error occured when trying to send import notification to Telegram. Please open an issue with the below contents.")
            log.error("-------------------------------------------------------")
            log.error(f"Status code: {sender.status_code}")
            log.error(f"Status body: {sender.content}")
            log.error(json.dumps(message, sort_keys=True, indent=4, separators=(',', ': ')))
            log.error("-------------------------------------------------------")
    except RequestException as e:
        log.error(e)
        log.error("Error occured when trying to send import notification to Telegram.")


def radarr_health():
    message = {
        "chat_id": config.TELEGRAM_HEALTH_CHAT_ID,
        "parse_mode": "HTML",
        "disable_notification": config.TELEGRAM_SILENT,
        "text": "<b>An issue has occured on Radarr.</b>"
                f"\n\n<b>Error Level</b>: {radarr_envs.issue_level}"
                f"\n<b>Error Type</b>: {radarr_envs.issue_type}"
                f"\n<b>Error Message</b>: {radarr_envs.issue_message}"
                f"\n<b>Visit Wiki</b>: <a href='{radarr_envs.wiki_link}'>Wiki</a>"
    }

    try:
        sender = requests.post(config.TELEGRAM_RADARR_HEALTH_URL, headers=HEADERS, json=message, timeout=60)
        if sender.status_code == 200:
            log.success("Successfully sent health notification to Telegram.")
        else:
            log.error(
                "Error occured when trying to send health notification to Telegram. Please open an issue with the below contents.")
            log.error("-------------------------------------------------------")
            log.error(f"Status code: {sender.status_code}")
            log.error(f"Status body: {sender.content}")
            log.error(json.dumps(message, sort_keys=True, indent=4, separators=(',', ': ')))
            log.error("-------------------------------------------------------")
    except RequestException as e:
        log.error(e)
        log.error("Error occured when trying to send health notification to Telegram.")


def radarr_update():
    message = {
        "chat_id": config.TELEGRAM_MISC_CHAT_ID,
        "parse_mode": "HTML",
        "disable_notification": config.TELEGRAM_SILENT,
        "text": f"Radarr has been updated to <b>({radarr_envs.new_version})</b>."
                f"\n\nOld version: {radarr_envs.old_version}"
    }

    try:
        sender = requests.post(config.TELEGRAM_RADARR_MISC_URL, headers=HEADERS, json=message, timeout=60)
        if sender.status_code == 200:
            log.success("Successfully sent app update notification to Telegram.")
        else:
            log.error(
                "Error occured when trying to send app update notification to Telegram. Please open an issue with the below contents.")
            log.error("-------------------------------------------------------")
            log.error(f"Status code: {sender.status_code}")
            log.error(f"Status body: {sender.content}")
            log.error(json.dumps(message, sort_keys=True, indent=4, separators=(',', ': ')))
            log.error("-------------------------------------------------------")
    except RequestException as e:
        log.error(e)
        log.error("Error occured when trying to send app update notification to Telegram.")


def radarr_movie_delete():
    message = {
        "chat_id": config.TELEGRAM_MISC_CHAT_ID,
        "parse_mode": "HTML",
        "disable_notification": config.TELEGRAM_SILENT,
        "text": f"Deleted <b>{radarr_envs.media_title} ({radarr_envs.year})</b> from Radarr."
                f"\n<b>Size</b>: {funcs.convert_size(int(radarr_envs.deleted_size))}"
                f"\n<b>Path</b>: {radarr_envs.delete_path}"
                f"<a href='{funcs.get_radarrposter(radarr_envs.tmdb_id)}'>&#8204;</a>"
                f"\n\n<b>View Details</b>: <a href='{funcs.get_radarr_links(radarr_envs.imdb_id, radarr_envs.tmdb_id)[0]}'>IMDb</a> | <a href='{funcs.get_radarr_links(radarr_envs.imdb_id, radarr_envs.tmdb_id)[1]}'>TheMovieDb</a> | <a href='{funcs.get_radarr_links(radarr_envs.imdb_id, radarr_envs.tmdb_id)[2]}'>Trakt</a> | <a href='{funcs.get_radarr_links(radarr_envs.imdb_id, radarr_envs.tmdb_id)[3]}'>MovieChat</a>"
    }

    if radarr_envs.deleted_size == "0":
        import re
        string = message["text"]
        pattern = r'<b>Size<\/b>: 0B'
        log.debug("Size field is 0B, removing it..")
        mod_string = re.sub(pattern, '', string)
        message["text"] = mod_string

    try:
        sender = requests.post(config.TELEGRAM_RADARR_MISC_URL, headers=HEADERS, json=message, timeout=60)
        if sender.status_code == 200:
            log.success("Successfully sent movie delete notification to Telegram.")
        else:
            log.error(
                "Error occured when trying to send movie delete notification to Telegram. Please open an issue with the below contents.")
            log.error("-------------------------------------------------------")
            log.error(f"Status code: {sender.status_code}")
            log.error(f"Status body: {sender.content}")
            log.error(json.dumps(message, sort_keys=True, indent=4, separators=(',', ': ')))
            log.error("-------------------------------------------------------")
    except RequestException as e:
        log.error(e)
        log.error("Error occured when trying to send movie delete notification to Telegram.")


def radarr_moviefile_delete():
    message = {
        "chat_id": config.TELEGRAM_MISC_CHAT_ID,
        "parse_mode": "HTML",
        "disable_notification": config.TELEGRAM_SILENT,
        "text": f"Deleted <b>{radarr_envs.media_title} ({radarr_envs.year})</b> from Radarr."
                f"\n<b>Quality</b>: {radarr_envs.import_quality}"
                f"\n<b>Size</b>: {funcs.convert_size(int(radarr_envs.deleted_moviefilesize))}"
                f"\n<b>Release Group</b>: {radarr_envs.deleted_moviereleasegroup}"
                f"\n<b>Delete Reason</b>: {radarr_envs.deleted_moviefilereason}"
                f"\n\n<b>File name</b>:\n{radarr_envs.scene_name}"
                f"\n\n<b>File location</b>:\n{radarr_envs.deleted_moviefilepath}"
                f"<a href='{funcs.get_radarrposter(radarr_envs.tmdb_id)}'>&#8204;</a>"
                f"\n\n<b>View Details</b>: <a href='{funcs.get_radarr_links(radarr_envs.imdb_id, radarr_envs.tmdb_id)[0]}'>IMDb</a> | <a href='{funcs.get_radarr_links(radarr_envs.imdb_id, radarr_envs.tmdb_id)[1]}'>TheMovieDb</a> | <a href='{funcs.get_radarr_links(radarr_envs.imdb_id, radarr_envs.tmdb_id)[2]}'>Trakt</a> | <a href='{funcs.get_radarr_links(radarr_envs.imdb_id, radarr_envs.tmdb_id)[3]}'>MovieChat</a>"
    }

    if radarr_envs.deleted_moviefilesize == 0:
        import re
        string = message["text"]
        pattern = r'<b>Size<\/b>: 0B'
        log.debug("Size field is 0B, removing it..")
        mod_string = re.sub(pattern, '', string)
        message["text"] = mod_string

    if radarr_envs.scene_name == "":
        import re
        string = message["text"]
        pattern = r'<b>Release Name<\/b>: '
        log.debug("Release Name field is Unknown, removing it..")
        mod_string = re.sub(pattern, '', string)
        message["text"] = mod_string

    if radarr_envs.deleted_moviereleasegroup == "":
        import re
        string = message["text"]
        pattern = r'<b>Release Group<\/b>: '
        log.debug("Release Group field is Unknown, removing it..")
        mod_string = re.sub(pattern, '', string)
        message["text"] = mod_string

    try:
        sender = requests.post(config.TELEGRAM_RADARR_MISC_URL, headers=HEADERS, json=message, timeout=60)
        if sender.status_code == 200:
            log.success("Successfully sent movie file delete notification to Telegram.")
        else:
            log.error(
                "Error occured when trying to send movie file delete notification to Telegram. Please open an issue with the below contents.")
            log.error("-------------------------------------------------------")
            log.error(f"Status code: {sender.status_code}")
            log.error(f"Status body: {sender.content}")
            log.error(json.dumps(message, sort_keys=True, indent=4, separators=(',', ': ')))
            log.error("-------------------------------------------------------")
    except RequestException as e:
        log.error(e)
        log.error("Error occured when trying to send movie file delete notification to Telegram.")


def radarr_movie_added():
    message = {
        "chat_id": config.TELEGRAM_MISC_CHAT_ID,
        "parse_mode": "HTML",
        "disable_notification": config.TELEGRAM_SILENT,
        "text": f"Added <b>{radarr_envs.media_title} ({radarr_envs.year})</b> to Radarr."
                f"<a href='{funcs.get_radarrposter(radarr_envs.tmdb_id)}'>&#8204;</a>"
                f"\n\n<b>View Details</b>: <a href='{funcs.get_radarr_links(radarr_envs.imdb_id, radarr_envs.tmdb_id)[0]}'>IMDb</a> | <a href='{funcs.get_radarr_links(radarr_envs.imdb_id, radarr_envs.tmdb_id)[1]}'>TheMovieDb</a> | <a href='{funcs.get_radarr_links(radarr_envs.imdb_id, radarr_envs.tmdb_id)[2]}'>Trakt</a> | <a href='{funcs.get_radarr_links(radarr_envs.imdb_id, radarr_envs.tmdb_id)[3]}'>MovieChat</a>"
    }

    try:
        sender = requests.post(config.TELEGRAM_RADARR_MISC_URL, headers=HEADERS, json=message, timeout=60)
        if sender.status_code == 200:
            log.success("Successfully sent movie added notification to Telegram.")
        else:
            log.error(
                "Error occured when trying to send movie added notification to Telegram. Please open an issue with the below contents.")
            log.error("-------------------------------------------------------")
            log.error(f"Status code: {sender.status_code}")
            log.error(f"Status body: {sender.content}")
            log.error(json.dumps(message, sort_keys=True, indent=4, separators=(',', ': ')))
            log.error("-------------------------------------------------------")
    except RequestException as e:
        log.error(e)
        log.error("Error occured when trying to send movie added notification to Telegram.")
