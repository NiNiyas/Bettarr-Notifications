import datetime
import os

import requests

import script_config

discord_headers = {'content-type': 'application/json'}


# Footer Timestamp
def utc_now_iso():
    utcnow = datetime.datetime.utcnow()
    return utcnow.isoformat()


telegramurl = 'https://api.telegram.org/bot{}/sendMessage'.format(script_config.bot_id)

# Get variables from Radarr
eventtype = os.environ.get('radarr_eventtype')
issue_level = os.environ.get('radarr_health_issue_level')
issue_type = os.environ.get('radarr_health_issue_type')
issue_message = os.environ.get('radarr_health_issue_message')
wiki_link = os.environ.get('radarr_health_issue_wiki')

discordmessage = {
    'username': script_config.radarr_discord_user,
    'embeds': [
        {
            'author': {
                'name': script_config.radarr_discord_user,
                'url': script_config.radarr_url,
                'icon_url': script_config.radarr_icon
            },
            "footer": {
                "icon_url": script_config.radarr_icon,
                "text": "Radarr"
            },
            'description': "**An error has occured on Radarr.**",
            'timestamp': utc_now_iso(),
            'color': 15158332,
            'fields': [
                {
                    "name": 'Error Level',
                    "value": issue_level,
                    "inline": False
                },
                {
                    "name": 'Error Type',
                    "value": issue_type,
                    "inline": False
                },
                {
                    "name": 'Error Message',
                    "value": issue_message,
                    "inline": False
                },
                {
                    "name": 'Wiki Link',
                    "value": '[{}]({})'.format("View Wiki", wiki_link),
                    "inline": False
                },
                {
                    "name": 'Visit Radarr',
                    "value": '[{}]({})'.format("Radarr", script_config.radarr_url),
                    "inline": False
                },
            ],
        },
    ]
}

discordsender = requests.post(script_config.radarr_discord_url, headers=discord_headers, json=discordmessage)

slackmessage = {
    "blocks": [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "Radarr"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "An error has occured on Radarr."
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
                    "text": "*Error Level*\n{}".format(issue_level),
                },
                {
                    "type": "mrkdwn",
                    "text": "*Error Type*\n{}".format(issue_type),
                },
                {
                    "type": "mrkdwn",
                    "text": "*Error Message*\n{}".format(issue_message),
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
                        "text": "Visit Radarr"

                    },
                    "style": "primary",
                    "url": script_config.radarr_url
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

slacksender = requests.post(script_config.radarr_slack_url, headers=discord_headers, json=slackmessage)

telegrammessage = {
    "chat_id": script_config.chat_id,
    "parse_mode": "HTML",
    "text": "An error has occured on Radarr"
            "\n\n<b>Error Level - </b>{}"
            "\n\n<b>Error Type</b> - {}"
            "\n<b>Error Message</b> - {}".format(issue_level, issue_type, issue_message),
    "reply_markup": {
        "inline_keyboard": [[
            {
                "text": "Visit Radarr",
                "url": script_config.radarr_url
            },
            {
                "text": "Visit Wiki",
                "url": wiki_link
            }]
        ]
    }

}

telegramsender = requests.post(telegramurl, json=telegrammessage)

if eventtype == 'Test':
    print("Successfully sent test notification")
else:
    print("Successfully sent notification to Discord, Slack and Telegram.")
