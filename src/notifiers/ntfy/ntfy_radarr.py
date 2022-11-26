import json

import config
import requests
from helpers import funcs, ratings, radarr_envs, omdb
from loguru import logger as log
from requests import RequestException

log = log.patch(lambda record: record.update(name="ntfy Radarr"))


def radarr_test():
    test = {
        "title": "Radarr",
        "topic": config.NTFY_RADARR_TOPIC,
        "tags": ["radarr", "movie_camera", "test"],
        "priority": config.NTFY_RADARR_PRIORITY,
        "actions": [{"action": "view", "label": "Visit Radarr", "url": config.RADARR_URL}],
        "message": "Bettarr Notifications for Radarr test message.\nThank you for using the script!"}

    if test["priority"] == "":
        del test["priority"]

    try:
        sender = requests.post(config.NTFY_URL, headers=config.NTFY_HEADER, json=test, timeout=60)
        if sender.status_code == 200:
            log.success("Successfully sent test notification to ntfy.")
        else:
            log.error(
                "Error occured when trying to send test notification to ntfy. Please open an issue with the below contents.")
            log.error("-------------------------------------------------------")
            log.error(f"Status code: {sender.status_code}")
            log.error(f"Status body: {sender.content}")
            log.error(json.dumps(test, sort_keys=True, indent=4, separators=(',', ': ')))
            log.error("-------------------------------------------------------")
    except RequestException as e:
        log.error(e)
        log.error("Error occured when trying to send test notification to ntfy.")


def radarr_grab():
    radarr = requests.get(f"{config.RADARR_URL}api/v3/movie/{radarr_envs.movie_id}?apikey={config.RADARR_APIKEY}")
    radarr = radarr.json()

    try:
        cast = f"\nCast: {funcs.get_movie_cast(radarr_envs.tmdb_id)[1][0]}, {funcs.get_movie_cast(radarr_envs.tmdb_id)[1][1]}, {funcs.get_movie_cast(radarr_envs.tmdb_id)[1][2]}"
    except (KeyError, TypeError, IndexError):
        try:
            cast = f"\nCast: {funcs.get_movie_cast(radarr_envs.tmdb_id)[1][0]}"
        except (KeyError, TypeError, IndexError):
            cast = ""

    if funcs.get_movie_crew(radarr_envs.tmdb_id)[1][0] == "Unknown":
        director = ""
    else:
        director = f"\nDirector: {funcs.get_movie_crew(radarr_envs.tmdb_id)[1][0]}"

    if radarr_envs.release_group == "":
        release_group = ""
    else:
        release_group = f"\nRelease Group: {radarr_envs.release_group}"

    if omdb.omdb_radarr(radarr_envs.imdb_id) == "N/A":
        awards = ""
    else:
        awards = f"\nAwards: {omdb.omdb_radarr(radarr_envs.imdb_id)}"

    message = {
        "title": "Radarr",
        "topic": config.NTFY_RADARR_TOPIC,
        "tags": ["radarr", "movie_camera", "grabbed"],
        "priority": config.NTFY_RADARR_PRIORITY,
        "attach": funcs.get_radarrposter(radarr_envs.tmdb_id),
        "filename": "poster.jpg",
        "actions": [{"action": "view", "label": "Visit Radarr", "url": config.RADARR_URL},
                    {"action": "view", "label": "View Trailer", "url": f"{funcs.get_radarr_trailer(radarr)}"}],
        "message": f"Grabbed {radarr_envs.media_title} ({radarr_envs.year}) from {radarr_envs.release_indexer}."
                   f"\n\nOverview\n{funcs.get_radarr_overview(radarr)[3]}\n{ratings.mdblist_movie()[4]}"
                   f"\n\nQuality: {radarr_envs.quality}"
                   f"\nSize: {funcs.convert_size(int(radarr_envs.release_size))}"
                   f"\nDownload Client: {radarr_envs.download_client}"
                   f"{release_group}"
                   f"\nRelease Date: {funcs.get_radarr_releasedate(radarr_envs.tmdb_id)}"
                   f"\nContent Rating: {ratings.mdblist_movie()[1]}"
                   f"\nGenre(s): {funcs.get_radarr_genres(radarr)}"
                   f"{cast}"
                   f"{director}"
                   f"{awards}"
                   f"\nAvailable On ({funcs.get_movie_watch_providers(radarr_envs.tmdb_id, radarr_envs.imdb_id)[1]}): {funcs.get_movie_watch_providers(radarr_envs.tmdb_id, radarr_envs.imdb_id)[0]}"
    }

    if message["priority"] == "":
        del message["priority"]

    if funcs.get_movie_watch_providers(radarr_envs.tmdb_id, radarr_envs.imdb_id)[0] == "None":
        import re
        pattern = r'Available On \([^()]*\): None'
        log.debug("Available On field is unknown, removing it..")
        mod_string = re.sub(pattern, '', message["message"])
        message["message"] = mod_string

    message['message'].rstrip()

    try:
        sender = requests.post(config.NTFY_URL, headers=config.NTFY_HEADER, json=message, timeout=60)
        if sender.status_code == 200:
            log.success("Successfully sent grab notification to ntfy.")
        else:
            log.error(
                "Error occured when trying to send grab notification to ntfy. Please open an issue with the below contents.")
            log.error("-------------------------------------------------------")
            log.error(f"Status code: {sender.status_code}")
            log.error(f"Status body: {sender.content}")
            log.error(json.dumps(message, sort_keys=True, indent=4, separators=(',', ': ')))
            log.error("-------------------------------------------------------")
    except RequestException as e:
        log.error(e)
        log.error("Error occured when trying to grab notification to ntfy.")


def radarr_import():
    radarr = requests.get(f"{config.RADARR_URL}api/v3/movie/{radarr_envs.movie_id}?apikey={config.RADARR_APIKEY}")
    radarr = radarr.json()

    if radarr_envs.is_upgrade == "True":
        content = f"Upgraded {radarr_envs.media_title} ({radarr_envs.year}).\n\n"
    else:
        content = f"Downloaded {radarr_envs.media_title} ({radarr_envs.year}).\n\n"

    if funcs.get_radarr_physicalrelease(radarr) != "Unknown":
        physical_releasedate = f"\nPhysical Release: {funcs.get_radarr_physicalrelease(radarr)}"
    else:
        physical_releasedate = ""

    if radarr_envs.scene_name != "":
        release_name = f"\n\nRelease Name\n{radarr_envs.scene_name}"
    else:
        release_name = ""

    message = {
        "title": "Radarr",
        "topic": config.NTFY_RADARR_TOPIC,
        "tags": ["radarr", "movie_camera", "downloaded"],
        "priority": config.NTFY_RADARR_PRIORITY,
        "attach": funcs.get_radarr_backdrop(radarr_envs.tmdb_id),
        "filename": "backdrop.jpg",
        "actions": [{"action": "view", "label": "Visit Radarr", "url": config.RADARR_URL},
                    {"action": "view", "label": "View Trailer", "url": f"{funcs.get_radarr_trailer(radarr)}"}],
        "message": f"{content}"
                   f"Overview\n{funcs.get_radarr_overview(radarr)[3]}"
                   f"\n\nQuality: {radarr_envs.import_quality}"
                   f"\nRelease Date: {funcs.get_radarr_releasedate(radarr_envs.tmdb_id)}"
                   f"{physical_releasedate}"
                   f"\nGenre(s): {funcs.get_radarr_genres(radarr)}"
                   f"{release_name}"

    }

    if message["priority"] == "":
        del message["priority"]

    if radarr_envs.scene_name == "":
        import re
        string = message["message"]
        pattern = r'Release Name: '
        log.debug("Scene name field is unknown, removing it..")
        mod_string = re.sub(pattern, '', string)
        message["message"] = mod_string

    try:
        sender = requests.post(config.NTFY_URL, headers=config.NTFY_HEADER, json=message, timeout=60)
        if sender.status_code == 200:
            log.success("Successfully sent import notification to ntfy.")
        else:
            log.error(
                "Error occured when trying to send import notification to ntfy. Please open an issue with the below contents.")
            log.error("-------------------------------------------------------")
            log.error(f"Status code: {sender.status_code}")
            log.error(f"Status body: {sender.content}")
            log.error(json.dumps(message, sort_keys=True, indent=4, separators=(',', ': ')))
            log.error("-------------------------------------------------------")
    except RequestException as e:
        log.error(e)
        log.error("Error occured when trying to import notification to ntfy.")


def radarr_health():
    message = {
        "title": "Radarr",
        "topic": config.NTFY_RADARR_HEALTH_TOPIC,
        "tags": ["radarr", "movie_camera", "heartpulse"],
        "priority": config.NTFY_RADARR_PRIORITY,
        "actions": [{"action": "view", "label": "Visit Radarr", "url": config.RADARR_URL},
                    {"action": "view", "label": "Visit Wiki", "url": f"{radarr_envs.wiki_link}"}],
        "message": "An issue has occured on Radarr."
                   f"\n\nError Level: {radarr_envs.issue_level}"
                   f"\nError Type: {radarr_envs.issue_type}"
                   f"\nError Message: {radarr_envs.issue_message}"
    }

    if message["priority"] == "":
        del message["priority"]

    try:
        sender = requests.post(config.NTFY_URL, headers=config.NTFY_HEADER, json=message, timeout=60)
        if sender.status_code == 200:
            log.success("Successfully sent health notification to ntfy.")
        else:
            log.error(
                "Error occured when trying to send health notification to ntfy. Please open an issue with the below contents.")
            log.error("-------------------------------------------------------")
            log.error(f"Status code: {sender.status_code}")
            log.error(f"Status body: {sender.content}")
            log.error(json.dumps(message, sort_keys=True, indent=4, separators=(',', ': ')))
            log.error("-------------------------------------------------------")
    except RequestException as e:
        log.error(e)
        log.error("Error occured when trying to health notification to ntfy.")


def radarr_update():
    message = {
        "title": "Radarr",
        "topic": config.NTFY_RADARR_MISC_TOPIC,
        "tags": ["radarr", "movie_camera", "update"],
        "priority": config.NTFY_RADARR_PRIORITY,
        "actions": [{"action": "view", "label": "Visit Radarr", "url": config.RADARR_URL}],
        "message": f"Radarr has been updated to {radarr_envs.new_version}."
                   f"\n\nOld version: {radarr_envs.old_version}"
    }

    if message["priority"] == "":
        del message["priority"]

    try:
        sender = requests.post(config.NTFY_URL, headers=config.NTFY_HEADER, json=message, timeout=60)
        if sender.status_code == 200:
            log.success("Successfully sent app update notification to ntfy.")
        else:
            log.error(
                "Error occured when trying to send app update notification to ntfy. Please open an issue with the below contents.")
            log.error("-------------------------------------------------------")
            log.error(f"Status code: {sender.status_code}")
            log.error(f"Status body: {sender.content}")
            log.error(json.dumps(message, sort_keys=True, indent=4, separators=(',', ': ')))
            log.error("-------------------------------------------------------")
    except RequestException as e:
        log.error(e)
        log.error("Error occured when trying to app update notification to ntfy.")


def radarr_movie_delete():
    message = {
        "title": "Radarr",
        "topic": config.NTFY_RADARR_MISC_TOPIC,
        "tags": ["radarr", "movie_camera", "delete"],
        "priority": config.NTFY_RADARR_PRIORITY,
        "attach": funcs.get_radarrposter(radarr_envs.tmdb_id),
        "filename": "poster.jpg",
        "actions": [{"action": "view", "label": "Visit Radarr", "url": config.RADARR_URL},
                    {"action": "view", "label": "IMDb",
                     "url": f"{funcs.get_radarr_links(radarr_envs.imdb_id, radarr_envs.tmdb_id)[0]}"},
                    {"action": "view", "label": "TheMovieDb",
                     "url": f"{funcs.get_radarr_links(radarr_envs.imdb_id, radarr_envs.tmdb_id)[1]}"}],
        "message": f"Deleted {radarr_envs.media_title} ({radarr_envs.year}) from Radarr."
                   f"\nSize: {funcs.convert_size(int(radarr_envs.deleted_size))}"
                   f"\nPath: {radarr_envs.delete_path}"
        # f"\n\nView Details: Trakt: {funcs.get_radarr_links(radarr_envs.imdb_id, radarr_envs.tmdb_id)[2]}\nMovieChat: {funcs.get_radarr_links(radarr_envs.imdb_id, radarr_envs.tmdb_id)[3]}"
    }

    if message["priority"] == "":
        del message["priority"]

    if radarr_envs.deleted_size == "0":
        import re
        string = message["message"]
        pattern = r'Size: 0B'
        log.debug("Size field is 0B, removing it..")
        mod_string = re.sub(pattern, '', string)
        message["message"] = mod_string

    try:
        sender = requests.post(config.NTFY_URL, headers=config.NTFY_HEADER, json=message, timeout=60)
        if sender.status_code == 200:
            log.success("Successfully sent movie delete notification to ntfy.")
        else:
            log.error(
                "Error occured when trying to send movie delete notification to ntfy. Please open an issue with the below contents.")
            log.error("-------------------------------------------------------")
            log.error(f"Status code: {sender.status_code}")
            log.error(f"Status body: {sender.content}")
            log.error(json.dumps(message, sort_keys=True, indent=4, separators=(',', ': ')))
            log.error("-------------------------------------------------------")
    except RequestException as e:
        log.error(e)
        log.error("Error occured when trying to movie delete notification to ntfy.")


def radarr_moviefile_delete():
    message = {
        "title": "Radarr",
        "topic": config.NTFY_RADARR_MISC_TOPIC,
        "tags": ["radarr", "movie_camera", "delete"],
        "priority": config.NTFY_RADARR_PRIORITY,
        "attach": funcs.get_radarrposter(radarr_envs.tmdb_id),
        "filename": "poster.jpg",
        "actions": [{"action": "view", "label": "Visit Radarr", "url": config.RADARR_URL},
                    {"action": "view", "label": "IMDb",
                     "url": f"{funcs.get_radarr_links(radarr_envs.imdb_id, radarr_envs.tmdb_id)[0]}"},
                    {"action": "view", "label": "TheMovieDb",
                     "url": f"{funcs.get_radarr_links(radarr_envs.imdb_id, radarr_envs.tmdb_id)[1]}"}],
        "message": f"Deleted {radarr_envs.media_title} ({radarr_envs.year}) from Radarr."
                   f"\nQuality: {radarr_envs.import_quality}"
                   f"\nSize: {funcs.convert_size(int(radarr_envs.deleted_moviefilesize))}"
                   f"\nRelease Group: {radarr_envs.deleted_moviereleasegroup}"
                   f"\nDelete Reason: {radarr_envs.deleted_moviefilereason}"
                   f"\n\nFile name\n{radarr_envs.scene_name}"
                   f"\n\nFile location\n{radarr_envs.deleted_moviefilepath}"
        # f"\n\nView Details: Trakt: {funcs.get_radarr_links(radarr_envs.imdb_id, radarr_envs.tmdb_id)[2]}\nMovieChat: {funcs.get_radarr_links(radarr_envs.imdb_id, radarr_envs.tmdb_id)[3]}"
    }

    if message["priority"] == "":
        del message["priority"]

    if radarr_envs.deleted_moviefilesize == 0:
        import re
        string = message["message"]
        pattern = r'Size: 0B'
        log.debug("Size field is 0B, removing it..")
        mod_string = re.sub(pattern, '', string)
        message["message"] = mod_string

    if radarr_envs.scene_name == "":
        import re
        string = message["message"]
        pattern = r'Release Name: '
        log.debug("Release Name field is Unknown, removing it..")
        mod_string = re.sub(pattern, '', string)
        message["message"] = mod_string

    if radarr_envs.deleted_moviereleasegroup == "":
        import re
        string = message["message"]
        pattern = r'Release Group: '
        log.debug("Release Group field is Unknown, removing it..")
        mod_string = re.sub(pattern, '', string)
        message["message"] = mod_string

    try:
        sender = requests.post(config.NTFY_URL, headers=config.NTFY_HEADER, json=message, timeout=60)
        if sender.status_code == 200:
            log.success("Successfully sent movie file delete notification to ntfy.")
        else:
            log.error(
                "Error occured when trying to send movie file delete notification to ntfy. Please open an issue with the below contents.")
            log.error("-------------------------------------------------------")
            log.error(f"Status code: {sender.status_code}")
            log.error(f"Status body: {sender.content}")
            log.error(json.dumps(message, sort_keys=True, indent=4, separators=(',', ': ')))
            log.error("-------------------------------------------------------")
    except RequestException as e:
        log.error(e)
        log.error("Error occured when trying to movie file delete notification to ntfy.")


def radarr_movie_added():
    message = {
        "title": "Radarr",
        "topic": config.NTFY_RADARR_MISC_TOPIC,
        "tags": ["radarr", "movie_camera", "added"],
        "priority": config.NTFY_RADARR_PRIORITY,
        "attach": funcs.get_radarrposter(radarr_envs.tmdb_id),
        "filename": "poster.jpg",
        "actions": [{"action": "view", "label": "Visit Radarr", "url": config.RADARR_URL},
                    {"action": "view", "label": "IMDb",
                     "url": f"{funcs.get_radarr_links(radarr_envs.imdb_id, radarr_envs.tmdb_id)[0]}"},
                    {"action": "view", "label": "TheMovieDb",
                     "url": f"{funcs.get_radarr_links(radarr_envs.imdb_id, radarr_envs.tmdb_id)[1]}"}],
        "message": f"Added {radarr_envs.media_title} ({radarr_envs.year}) to Radarr."
    }

    if message["priority"] == "":
        del message["priority"]

    try:
        sender = requests.post(config.NTFY_URL, headers=config.NTFY_HEADER, json=message, timeout=60)
        if sender.status_code == 200:
            log.success("Successfully sent movie added notification to ntfy.")
        else:
            log.error(
                "Error occured when trying to send movie added notification to ntfy. Please open an issue with the below contents.")
            log.error("-------------------------------------------------------")
            log.error(f"Status code: {sender.status_code}")
            log.error(f"Status body: {sender.content}")
            log.error(json.dumps(message, sort_keys=True, indent=4, separators=(',', ': ')))
            log.error("-------------------------------------------------------")
    except RequestException as e:
        log.error(e)
        log.error("Error occured when trying to movie added notification to ntfy.")
