import json
import os

import config
import requests
from loguru import logger as log
from requests import RequestException

issue_level = os.environ.get("prowlarr_health_issue_level")
wiki_link = os.environ.get("prowlarr_health_issue_wiki")
issue_type = os.environ.get("prowlarr_health_issue_type")
issue_message = os.environ.get("prowlarr_health_issue_message")
_update_message = os.environ.get("prowlarr_update_message")
new_version = os.environ.get("prowlarr_update_newversion")
old_version = os.environ.get("prowlarr_update_previousversion")

HEADERS = {"content-type": "application/json"}


def prowlarr_test():
    test = {
        "html": 1,
        "user": config.PUSHOVER_USER,
        "token": config.PROWLARR_PUSHOVER_TOKEN,
        "device": config.PUSHOVER_DEVICE,
        "priority": config.PUSHOVER_PRIORITY,
        "sound": config.PUSHOVER_SOUND,
        "retry": 60,
        "expire": 3600,
        "url": config.PROWLARR_URL,
        "url_title": "Visit Prowlarr",
        "message": "<b>Bettarr Notifications for Prowlarr test message.\nThank you for using the script!</b>"}

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


def prowlarr_health():
    message = {
        "html": 1,
        "user": config.PUSHOVER_USER,
        "token": config.PROWLARR_PUSHOVER_TOKEN,
        "device": config.PUSHOVER_DEVICE,
        "priority": config.PUSHOVER_PRIORITY,
        "sound": config.PUSHOVER_SOUND,
        "retry": 60,
        "expire": 3600,
        "url": config.PROWLARR_URL,
        "url_title": "Visit Prowlarr",
        "message": "<b>An issue has occured on Prowlarr.</b>"
                   f"\n\n<b>Error Level</b>: {issue_level}"
                   f"\n<b>Error Type</b>: {issue_type}"
                   f"\n<b>Error Message</b>: {issue_message}"
                   f"\n<b>Visit Wiki</b>: <a href={wiki_link}>Wiki</a>"
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
        log.error("Error occured when trying to health notification to Pushover.")

def prowlarr_update():
    message = {
        "html": 1,
        "user": config.PUSHOVER_USER,
        "token": config.PROWLARR_MISC_PUSHOVER_TOKEN,
        "device": config.PUSHOVER_DEVICE,
        "priority": config.PUSHOVER_PRIORITY,
        "sound": config.PUSHOVER_SOUND,
        "retry": 60,
        "expire": 3600,
        "url": config.PROWLARR_URL,
        "url_title": "Visit Prowlarr",
        "message": f"Prowlarr has been updated to <b>({new_version})</b>."
                   f"\n\nOld version: {old_version}"
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