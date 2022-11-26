import json
import os
import random

import config
import requests
from helpers import funcs
from loguru import logger as log
from requests import RequestException

issue_level = os.environ.get("prowlarr_health_issue_level")
wiki_link = os.environ.get("prowlarr_health_issue_wiki")
issue_type = os.environ.get("prowlarr_health_issue_type")
issue_message = os.environ.get("prowlarr_health_issue_message")
new_version = os.environ.get("prowlarr_update_newversion")
old_version = os.environ.get("prowlarr_update_previousversion")

HEADERS = {"content-type": "application/json"}

log = log.patch(lambda record: record.update(name="Discord Prowlarr"))


def prowlarr_test():
    test = {
        "username": config.PROWLARR_DISCORD_USERNAME,
        "content": "**Bettarr Notifications for Prowlarr test message.\nThank you for using the script!**"}

    try:
        sender = requests.post(config.PROWLARR_DISCORD_WEBHOOK, headers=HEADERS, json=test, timeout=60)
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


def prowlarr_health():
    message = {
        "username": config.PROWLARR_DISCORD_USERNAME,
        "content": "**An issue has occured on Prowlarr.**",
        "embeds": [
            {
                "author": {
                    "name": config.PROWLARR_DISCORD_USERNAME,
                    "url": config.PROWLARR_URL,
                    "icon_url": config.PROWLARR_DISCORD_USERICON
                },
                "footer": {
                    "icon_url": config.PROWLARR_DISCORD_USERICON,
                    "text": "Prowlarr"
                },
                "timestamp": funcs.utc_now_iso(),
                "color": random.choice(funcs.colors),
                "fields": [
                    {
                        "name": "Error Level",
                        "value": issue_level,
                        "inline": False
                    },
                    {
                        "name": "Error Type",
                        "value": issue_type,
                        "inline": False
                    },
                    {
                        "name": "Error Message",
                        "value": issue_message,
                        "inline": False
                    },
                    {
                        "name": "Wiki Link",
                        "value": f"[View Wiki]({wiki_link})",
                        "inline": False
                    },
                    {
                        "name": "Visit Prowlarr",
                        "value": f"[Prowlarr]({config.PROWLARR_URL})",
                        "inline": False
                    }
                ]
            }
        ]
    }

    try:
        sender = requests.post(config.PROWLARR_DISCORD_WEBHOOK, headers=HEADERS, json=message, timeout=60)
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


def prowlarr_update():
    message = {
        'username': config.PROWLARR_DISCORD_USERNAME,
        'content': f"Prowlarr has been updated to `{new_version}`.",
        'embeds': [
            {
                'author': {
                    'name': config.PROWLARR_DISCORD_USERNAME,
                    'url': config.PROWLARR_URL,
                    'icon_url': config.PROWLARR_DISCORD_USERICON
                },
                "footer": {
                    "icon_url": config.PROWLARR_DISCORD_USERICON,
                    "text": "Prowlarr"
                },
                'timestamp': funcs.utc_now_iso(),
                'title': f"Prowlarr has been updated to `{new_version}`.",
                'color': random.choice(funcs.colors),
                'fields': [
                    {
                        "name": "Old version",
                        "value": old_version,
                        "inline": False
                    }
                ]
            }
        ]
    }

    try:
        sender = requests.post(config.PROWLARR_MISC_DISCORD_WEBHOOK, headers=HEADERS, json=message, timeout=60)
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
