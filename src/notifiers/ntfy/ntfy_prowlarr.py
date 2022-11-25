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
new_version = os.environ.get("prowlarr_update_newversion")
old_version = os.environ.get("prowlarr_update_previousversion")


def prowlarr_test():
    test = {
        "title": "Prowlarr",
        "topic": config.NTFY_PROWLARR_TOPIC,
        "tags": ["prowlarr", "test"],
        "priority": config.NTFY_PROWLARR_PRIORITY,
        "actions": [{"action": "view", "label": "Visit Prowlarr", "url": config.PROWLARR_URL}],
        "message": "Bettarr Notifications for Prowlarr test message.\nThank you for using the script!"}

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


def prowlarr_health():
    message = {
        "title": "Prowlarr",
        "topic": config.NTFY_PROWLARR_TOPIC,
        "tags": ["prowlarr", "heartpulse"],
        "priority": config.NTFY_PROWLARR_PRIORITY,
        "actions": [{"action": "view", "label": "Visit Prowlarr", "url": f"{config.PROWLARR_URL}"},
                    {"action": "view", "label": "Visit Wiki", "url": f"{wiki_link}"}],
        "message": "An issue has occured on Prowlarr."
                   f"\n\nError Level: {issue_level}"
                   f"\nError Type: {issue_type}"
                   f"\nError Message: {issue_message}"
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


def prowlarr_update():
    message = {
        "title": "Prowlarr",
        "topic": config.NTFY_PROWLARR_MISC_TOPIC,
        "tags": ["prowlarr", "update"],
        "priority": config.NTFY_PROWLARR_PRIORITY,
        "actions": [{"action": "view", "label": "Visit Prowlarr", "url": f"{config.PROWLARR_URL}"}],
        "message": f"Prowlarr has been updated to {new_version}."
                   f"\n\nOld version: {old_version}"
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
