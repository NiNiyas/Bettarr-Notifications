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

HEADERS = {"content-type": "application/json"}


def prowlarr_test():
    test = {
        "chat_id": config.TELEGRAM_CHAT_ID,
        "parse_mode": "HTML",
        "disable_notification": config.TELEGRAM_SILENT,
        "text": "<b>Bettarr Notifications for Prowlarr test message.\nThank you for using the script!</b>"}

    try:
        sender = requests.post(config.TELEGRAM_PROWLARR_URL, headers=HEADERS, json=test, timeout=60)
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


def prowlarr_health():
    message = {
        "chat_id": config.TELEGRAM_HEALTH_CHAT_ID,
        "parse_mode": "HTML",
        "disable_notification": config.TELEGRAM_SILENT,
        "text": "<b>An issue has occured on Prowlarr.</b>"
                f"\n\n<b>Error Level</b>: {issue_level}"
                f"\n<b>Error Type</b>: {issue_type}"
                f"\n<b>Error Message</b>: {issue_message}"
                f"\n<b>Visit Wiki</b>: <a href='{wiki_link}'>Wiki</a>"
    }

    try:
        sender = requests.post(config.TELEGRAM_PROWLARR_URL, headers=HEADERS, json=message, timeout=60)
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


def prowlarr_update():
    message = {
        "chat_id": config.TELEGRAM_MISC_CHAT_ID,
        "parse_mode": "HTML",
        "disable_notification": config.TELEGRAM_SILENT,
        "text": f"Prowlarr has been updated to <b>({new_version})</b>."
                f"\n\nOld version: {old_version}"
    }

    try:
        sender = requests.post(config.TELEGRAM_PROWLARR_MISC_URL, headers=HEADERS, json=message, timeout=60)
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
