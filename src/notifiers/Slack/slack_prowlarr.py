import json
import os

import config
import requests
from loguru import logger as log
from requests import RequestException

HEADERS = {"content-type": "application/json"}

issue_level = os.environ.get("prowlarr_health_issue_level")
wiki_link = os.environ.get("prowlarr_health_issue_wiki")
issue_type = os.environ.get("prowlarr_health_issue_type")
issue_message = os.environ.get("prowlarr_health_issue_message")
_update_message = os.environ.get("prowlarr_update_message")
new_version = os.environ.get("prowlarr_update_newversion")
old_version = os.environ.get("prowlarr_update_previousversion")


def prowlarr_test():
    test = {
        "channel": config.SLACK_CHANNEL,
        "text": "*Bettarr Notifications for Prowlarr test message. Thank you for using the script!*"}

    try:
        sender = requests.post(config.PROWLARR_SLACK_WEBHOOK, headers=HEADERS, json=test)
        if sender.status_code == 200:
            log.success("Successfully sent test notification to Slack.")
        else:
            log.error(
                "Error occured when trying to send test notification to Slack. Please open an issue with the below contents.")
            log.error("-------------------------------------------------------")
            log.error(f"Status code: {sender.status_code}")
            log.error(f"Status body: {sender.content}")
            log.error(json.dumps(test, sort_keys=True, indent=4, separators=(",", ": ")))
            log.error("-------------------------------------------------------")
    except RequestException as e:
        log.error(e)
        log.error("Error occured when trying to send test notification to Slack.")


def prowlarr_health():
    message = {
        "channel": config.SLACK_CHANNEL,
        "text": "*An issue has occured on Prowlarr.*",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*An issue has occured on Prowlarr.*"
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Error Level*\n{issue_level}",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Error Type*\n{issue_type}",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Error Message*\n{issue_message}",
                    }
                ]
            },
            {
                "type": "divider"
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Visit Prowlarr"

                        },
                        "style": "primary",
                        "url": config.PROWLARR_URL
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Wiki Link"
                        },
                        "url": wiki_link
                    }
                ]
            }
        ]
    }

    try:
        sender = requests.post(config.PROWLARR_SLACK_WEBHOOK, headers=HEADERS, json=message, timeout=60)
        if sender.status_code == 200:
            log.success("Successfully sent health notification to Slack.")
        else:
            log.error(
                "Error occured when trying to send health notification to Slack. Please open an issue with the below contents.")
            log.error("-------------------------------------------------------")
            log.error(f"Status code: {sender.status_code}")
            log.error(f"Status body: {sender.content}")
            log.error(json.dumps(message, sort_keys=True, indent=4, separators=(",", ": ")))
            log.error("-------------------------------------------------------")
    except RequestException as e:
        log.error(e)
        log.error("Error occured when trying to send health notification to Slack.")


def prowlarr_update():
    message = {
        "channel": config.SLACK_CHANNEL,
        "text": f"Prowlarr has ben updated to `{new_version}`.",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"Prowlarr has ben updated to `{new_version}`.",
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Old version*\n{old_version}",
                    }
                ]
            },
            {
                "type": "divider"
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Visit Prowlarr"

                        },
                        "style": "primary",
                        "url": config.PROWLARR_URL
                    }
                ]
            }
        ]
    }

    try:
        sender = requests.post(config.PROWLARR_MISC_SLACK_WEBHOOK, headers=HEADERS, json=message, timeout=60)
        if sender.status_code == 200:
            log.success("Successfully sent app update notification to Slack.")
        else:
            log.error(
                "Error occured when trying to send app update notification to Slack. Please open an issue with the below contents.")
            log.error("-------------------------------------------------------")
            log.error(f"Status code: {sender.status_code}")
            log.error(f"Status body: {sender.content}")
            log.error(json.dumps(message, sort_keys=True, indent=4, separators=(",", ": ")))
            log.error("-------------------------------------------------------")
    except RequestException as e:
        log.error(e)
        log.error("Error occured when trying to send app update notification to Slack.")
