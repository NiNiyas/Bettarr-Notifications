import json

import config
import requests
from helpers import funcs, ratings, radarr_envs
from loguru import logger as log
from requests import RequestException

HEADERS = {"content-type": "application/json"}


def radarr_test():
    test = {
        "html": 1,
        "user": config.PUSHOVER_USER,
        "token": config.RADARR_PUSHOVER_TOKEN,
        "device": config.PUSHOVER_DEVICE,
        "priority": config.PUSHOVER_PRIORITY,
        "sound": config.PUSHOVER_SOUND,
        "retry": 60,
        "expire": 3600,
        "url": config.RADARR_URL,
        "url_title": "Visit Radarr",
        "message": "<b>Bettarr Notifications for Radarr test message.\nThank you for using the script!</b>"}

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
            log.error(json.dumps(test, sort_keys=True, indent=4, separators=(',', ': ')))
            log.error("-------------------------------------------------------")
    except RequestException as e:
        log.error(e)
        log.error("Error occured when trying to send test notification to Pushover.")


def radarr_grab():
    radarr = requests.get(f"{config.RADARR_URL}api/v3/movie/{radarr_envs.movie_id}?apikey={config.RADARR_APIKEY}")
    radarr = radarr.json()

    message = {
        "html": 1,
        "user": config.PUSHOVER_USER,
        "token": config.RADARR_PUSHOVER_TOKEN,
        "device": config.PUSHOVER_DEVICE,
        "priority": config.PUSHOVER_PRIORITY,
        "sound": config.PUSHOVER_SOUND,
        "retry": 60,
        "expire": 3600,
        "url": config.RADARR_URL,
        "url_title": "Visit Radarr",
        "message": f"Grabbed <b>{radarr_envs.media_title}</b> ({radarr_envs.year}) from <i>{radarr_envs.release_indexer}</i>."
                   f"\n\n<strong>Overview</strong>\n{funcs.get_radarr_overview(radarr)[2]}\n{ratings.mdblist_movie()[3]}"
                   f"\n\n<b>Quality</b>: {radarr_envs.quality}"
                   f"\n<b>Size</b>: {funcs.convert_size(int(radarr_envs.release_size))}"
                   f"\n<b>Download Client</b>: {radarr_envs.download_client}"
                   f"\n<b>Release Group</b>: {radarr_envs.release_group}"
                   f"\n<b>Release Date</b>: {funcs.get_radarr_releasedate(radarr_envs.tmdb_id)}"
                   f"\n<b>Content Rating</b>: {ratings.mdblist_movie()[1]}"
                   f"\n<b>Genre(s)</b>: {funcs.get_radarr_genres(radarr)}"
                   f"\n<b>Cast</b>: <a href={funcs.get_movie_cast(radarr_envs.tmdb_id)[0][0]}>{funcs.get_movie_cast(radarr_envs.tmdb_id)[1][0]}</a>, <a href={funcs.get_movie_cast(radarr_envs.tmdb_id)[0][1]}>{funcs.get_movie_cast(radarr_envs.tmdb_id)[1][1]}</a>, <a href={funcs.get_movie_cast(radarr_envs.tmdb_id)[0][2]}>{funcs.get_movie_cast(radarr_envs.tmdb_id)[1][2]}</a>"
                   f"\n<b>Director</b>: <a href={funcs.get_movie_crew(radarr_envs.tmdb_id)[0][0]}>{funcs.get_movie_crew(radarr_envs.tmdb_id)[1][0]}</a>"
                   f"\n<b>Available On</b>: ({funcs.get_movie_watch_providers(radarr_envs.tmdb_id, radarr_envs.imdb_id)[1]}): {funcs.get_movie_watch_providers(radarr_envs.tmdb_id, radarr_envs.imdb_id)[0]}"
                   f"\n<b>Trailer</b>: <a href={funcs.get_radarr_trailer(radarr)}>Youtube</a>"
    }

    if funcs.get_movie_crew(radarr_envs.tmdb_id)[1][0] == "Unknown":
        import re
        string = message["message"]
        pattern = r'<b>Director<\/b>: <a href=\[\]>Unknown<\/a>'
        log.warning("Director field is unknown, removing it..")
        mod_string = re.sub(pattern, '', string)
        message["message"] = mod_string

    if radarr_envs.release_group == "Unknown":
        import re
        string = message["message"]
        pattern = r'<b>Release Group<\/b>: Unknown'
        log.warning("Release group field is unknown, removing it..")
        mod_string = re.sub(pattern, '', string)
        message["message"] = mod_string

    if len(message["message"]) > 1024:
        log.warning(
            f"Pushover message length is greater than 1024, current length: {len(message['message'])}. Some of the message will be removed.")

    try:
        sender = requests.post(config.PUSHOVER_API_URL, data=message,
                               files={"attachment": (
                                   "poster.jpg", open(funcs.get_pushover_radarrposter(radarr_envs.tmdb_id),
                                                      "rb"), "image/jpeg")})

        if sender.status_code == 200:
            log.success("Successfully sent grab notification to Pushover.")
        else:
            log.error(
                "Error occured when trying to send grab notification to Pushover. Please open an issue with the below contents.")
            log.error("-------------------------------------------------------")
            log.error(f"Status code: {sender.status_code}")
            log.error(f"Status body: {sender.content}")
            log.error(json.dumps(message, sort_keys=True, indent=4, separators=(',', ': ')))
            log.error("-------------------------------------------------------")
    except RequestException as e:
        log.error(e)
        log.error("Error occured when trying to grab test notification to Pushover.")


def radarr_import():
    radarr = requests.get(f"{config.RADARR_URL}api/v3/movie/{radarr_envs.movie_id}?apikey={config.RADARR_APIKEY}")
    radarr = radarr.json()

    if radarr_envs.is_upgrade == "True":
        content = f"Upgraded <b>{radarr_envs.media_title}</b> ({radarr_envs.year})\n\n"
    else:
        content = f"Downloaded <b>{radarr_envs.media_title}</b> ({radarr_envs.year})\n\n"

    message = {
        "html": 1,
        "user": config.PUSHOVER_USER,
        "token": config.RADARR_PUSHOVER_TOKEN,
        "device": config.PUSHOVER_DEVICE,
        "priority": config.PUSHOVER_PRIORITY,
        "sound": config.PUSHOVER_SOUND,
        "retry": 60,
        "expire": 3600,
        "url": config.RADARR_URL,
        "url_title": "Visit Radarr",
        "message": f"{content}"
                   f"<strong>Overview</strong>\n{funcs.get_radarr_overview(radarr)[2]}"
                   f"\n\n<b>Quality</b>: {radarr_envs.import_quality}"
                   f"\n<b>Release Date</b>: {funcs.get_radarr_releasedate(radarr_envs.tmdb_id)}"
                   f"\n<b>Physical Release</b>: {funcs.get_radarr_physicalrelease(radarr)}"
                   f"\n<b>Genre(s)</b>: {funcs.get_radarr_genres(radarr)}"
                   f"\n<b>Trailer</b>: <a href={funcs.get_radarr_trailer(radarr)}>Youtube</a>"
                   f"\n<b>Release Name</b>: {radarr_envs.scene_name}"

    }

    if radarr_envs.scene_name == "Unknown":
        import re
        string = message["message"]
        pattern = r'<b>Release Name<\/b>: Unknown'
        log.warning("Scene name field is unknown, removing it..")
        mod_string = re.sub(pattern, '', string)
        message["message"] = mod_string

    try:
        sender = requests.post(config.PUSHOVER_API_URL, data=message,
                               files={
                                   "attachment": ("still.jpg", open(funcs.get_pushover_radarrstill(radarr_envs.tmdb_id),
                                                                    "rb"), "image/jpeg")})

        if sender.status_code == 200:
            log.success("Successfully sent import notification to Pushover.")
        else:
            log.error(
                "Error occured when trying to send import notification to Pushover. Please open an issue with the below contents.")
            log.error("-------------------------------------------------------")
            log.error(f"Status code: {sender.status_code}")
            log.error(f"Status body: {sender.content}")
            log.error(json.dumps(message, sort_keys=True, indent=4, separators=(',', ': ')))
            log.error("-------------------------------------------------------")
    except RequestException as e:
        log.error(e)
        log.error("Error occured when trying to import test notification to Pushover.")


def radarr_health():
    message = {
        "html": 1,
        "user": config.PUSHOVER_USER,
        "token": config.RADARR_HEALTH_PUSHOVER_TOKEN,
        "device": config.PUSHOVER_DEVICE,
        "priority": config.PUSHOVER_PRIORITY,
        "sound": config.PUSHOVER_SOUND,
        "retry": 60,
        "expire": 3600,
        "url": config.RADARR_URL,
        "url_title": "Visit Radarr",
        "message": "<b>An issue has occured on Radarr</b>"
                   f"\n\n<b>Error Level</b>: {radarr_envs.issue_level}"
                   f"\n<b>Error Type</b>: {radarr_envs.issue_type}"
                   f"\n<b>Error Message</b>: {radarr_envs.issue_message}"
                   f"\n<b>Visit Wiki</b>: <a href={radarr_envs.wiki_link}>Wiki</a>"
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
            log.error(json.dumps(message, sort_keys=True, indent=4, separators=(',', ': ')))
            log.error("-------------------------------------------------------")
    except RequestException as e:
        log.error(e)
        log.error("Error occured when trying to health test notification to Pushover.")


def radarr_update():
    message = {
        "html": 1,
        "user": config.PUSHOVER_USER,
        "token": config.RADARR_MISC_PUSHOVER_TOKEN,
        "device": config.PUSHOVER_DEVICE,
        "priority": config.PUSHOVER_PRIORITY,
        "sound": config.PUSHOVER_SOUND,
        "retry": 60,
        "expire": 3600,
        "url": config.RADARR_URL,
        "url_title": "Visit Radarr",
        "message": f"A new update <b>({radarr_envs.new_version})</b> is available for Radarr."
                   f"\n\nNew version: {radarr_envs.new_version}"
                   f"\nOld version: {radarr_envs.old_version}"
                   f"\nUpdate Notes:\n{radarr_envs.update_message}"
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
            log.error(json.dumps(message, sort_keys=True, indent=4, separators=(',', ': ')))
            log.error("-------------------------------------------------------")
    except RequestException as e:
        log.error(e)
        log.error("Error occured when trying to app update notification to Pushover.")


def radarr_movie_delete():
    message = {
        "html": 1,
        "user": config.PUSHOVER_USER,
        "token": config.RADARR_MISC_PUSHOVER_TOKEN,
        "device": config.PUSHOVER_DEVICE,
        "priority": config.PUSHOVER_PRIORITY,
        "sound": config.PUSHOVER_SOUND,
        "retry": 60,
        "expire": 3600,
        "url": config.RADARR_URL,
        "url_title": "Visit Radarr",
        "message": f"Deleted <b>{radarr_envs.media_title} ({radarr_envs.year})</b> from Radarr."
                   f"\n<b>Size</b>: {funcs.convert_size(int(radarr_envs.deleted_size))}"
                   f"\n<b>Path</b>: {radarr_envs.delete_path}"
                   f"\n\n<b>View Details</b>: <a href={funcs.get_radarr_links(radarr_envs.imdb_id, radarr_envs.tmdb_id)[0]}>IMDb</a> | <a href={funcs.get_radarr_links(radarr_envs.imdb_id, radarr_envs.tmdb_id)[1]}>TheMovieDb</a> | <a href={funcs.get_radarr_links(radarr_envs.imdb_id, radarr_envs.tmdb_id)[2]}>Trakt</a> | <a href={funcs.get_radarr_links(radarr_envs.imdb_id, radarr_envs.tmdb_id)[3]}>MovieChat</a>"
    }

    if funcs.convert_size(int(radarr_envs.deleted_size)) == "0B":
        import re
        string = message["message"]
        pattern = r'<b>Size<\/b>: 0B'
        log.warning("Size field is 0B, removing it..")
        mod_string = re.sub(pattern, '', string)
        message["message"] = mod_string

    try:
        sender = requests.post(config.PUSHOVER_API_URL, headers=HEADERS, json=message)
        if sender.status_code == 200:
            log.success("Successfully sent movie delete notification to Pushover.")
        else:
            log.error(
                "Error occured when trying to send movie delete notification to Pushover. Please open an issue with the below contents.")
            log.error("-------------------------------------------------------")
            log.error(f"Status code: {sender.status_code}")
            log.error(f"Status body: {sender.content}")
            log.error(json.dumps(message, sort_keys=True, indent=4, separators=(',', ': ')))
            log.error("-------------------------------------------------------")
    except RequestException as e:
        log.error(e)
        log.error("Error occured when trying to movie delete notification to Pushover.")


def radarr_moviefile_delete():
    message = {
        "html": 1,
        "user": config.PUSHOVER_USER,
        "token": config.RADARR_MISC_PUSHOVER_TOKEN,
        "device": config.PUSHOVER_DEVICE,
        "priority": config.PUSHOVER_PRIORITY,
        "sound": config.PUSHOVER_SOUND,
        "retry": 60,
        "expire": 3600,
        "url": config.RADARR_URL,
        "url_title": "Visit Radarr",
        "message": f"Deleted <b>{radarr_envs.media_title} ({radarr_envs.year})</b> from Radarr."
                   f"\n<b>Quality</b>: {radarr_envs.import_quality}"
                   f"\n<b>Size</b>: {funcs.convert_size(int(radarr_envs.deleted_moviefilesize))}"
                   f"\n<b>Release Group</b>: {radarr_envs.deleted_moviereleasegroup}"
                   f"\n\n<b>File name</b>: {radarr_envs.scene_name}"
                   f"\n\n<b>File location</b>: {radarr_envs.deleted_moviefilepath}"
                   f"\n\n<b>View Details</b>: <a href={funcs.get_radarr_links(radarr_envs.imdb_id, radarr_envs.tmdb_id)[0]}>IMDb</a> | <a href={funcs.get_radarr_links(radarr_envs.imdb_id, radarr_envs.tmdb_id)[1]}>TheMovieDb</a> | <a href={funcs.get_radarr_links(radarr_envs.imdb_id, radarr_envs.tmdb_id)[2]}>Trakt</a> | <a href={funcs.get_radarr_links(radarr_envs.imdb_id, radarr_envs.tmdb_id)[3]}>MovieChat</a>"
    }

    if radarr_envs.deleted_moviefilesize == 0:
        import re
        string = message["message"]
        pattern = r'<b>Size<\/b>: 0B'
        log.warning("Size field is 0B, removing it..")
        mod_string = re.sub(pattern, '', string)
        message["message"] = mod_string

    if radarr_envs.scene_name == "Unknown":
        import re
        string = message["message"]
        pattern = r'<b>Release Name<\/b>: Unknown'
        log.warning("Release Name field is Unknown, removing it..")
        mod_string = re.sub(pattern, '', string)
        message["message"] = mod_string

    if radarr_envs.deleted_moviereleasegroup == "Unknown":
        import re
        string = message["message"]
        pattern = r'<b>Release Group<\/b>: Unknown'
        log.warning("Release Group field is Unknown, removing it..")
        mod_string = re.sub(pattern, '', string)
        message["message"] = mod_string

    try:
        sender = requests.post(config.PUSHOVER_API_URL, headers=HEADERS, json=message)
        if sender.status_code == 200:
            log.success("Successfully sent movie file delete notification to Pushover.")
        else:
            log.error(
                "Error occured when trying to send movie file delete notification to Pushover. Please open an issue with the below contents.")
            log.error("-------------------------------------------------------")
            log.error(f"Status code: {sender.status_code}")
            log.error(f"Status body: {sender.content}")
            log.error(json.dumps(message, sort_keys=True, indent=4, separators=(',', ': ')))
            log.error("-------------------------------------------------------")
    except RequestException as e:
        log.error(e)
        log.error("Error occured when trying to movie file delete notification to Pushover.")
