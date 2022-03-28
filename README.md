# Bettarr Notifications
Better Notifications for Sonarr and Radarr. \
Discord is based on script by @samwiseg0 - [Link to his repo](https://github.com/samwiseg0/better-discord-notifications).

Neither of his script worked for me, so I kinda tweaked it a bit and now it seems to be working. \
I have tested it with v3.0.7.1477 of Sonarr and v4.0.5.5981 of Radarr. Might work with v2 too.

## Installation
- Clone the repo.
- Extract and cd to the folder. Install requirements using `pip install -r requirements.txt`.
- On Sonarr and/or Radarr, add a custom script in `Settings -> Connect`.
- Sonarr notification triggers: `On Grab`, `On Import`, `On Upgrade`, `On Health Issue`, `Include Health Warnings`, `On Series Delete`, `On Episode File Delete`, `On Episode File Delete For Upgrade`, `On Application Update`.
- Radarr notification triggers: `On Grab`, `On Import`, `On Upgrade`, `On Health Issue`, `Include Health Warnings`.
- `On Health Issue`, `Include Health Warnings` is optional.

## Docker Installation
- Clone the repo.
- Mount it to the docker container.
- Install requirements:
  - For [linuxserver's](https://hub.docker.com/r/linuxserver/sonarr) image, read [this](https://www.linuxserver.io/blog/2019-09-14-customizing-our-containers).
  - For [hotio's](https://hotio.dev/containers/sonarr/) image, read [this](https://hotio.dev/faq/#guides)
  - Custom script is available in [install](https://github.com/NiNiyas/Bettarr-Notifications/tree/master/src/Standard%20Version/install) folder.

# APIs

### TMDB (Required)
- To create TMDB API, check [here](https://www.themoviedb.org/settings/api). This has no known limit.
- Fill in the `moviedb_key` in `config.py` in all notifier folders you use.
- If you need the JustWatch providers for you country, fill in the `tmdb_country`. For country codes, see [here](https://www.justwatch.com/), scroll down to the very bottom of the page.

### mdblist (Optional)
In order to get ratings, you should set your api key in `config.py` file in `addons` directory. This is optional.
- Create your mdblist API key from [here](https://mdblist.com/). 
- You will need a [Trakt](https://trakt.tv) account for this. This has a 100 calls per day limit unless you are a Patreon subscriber. Fill in `mdbapi`.

# Notifiers

### Discord
- Create a webhook in your server, fill in `sonarr_discord_url` and/or `radarr_discord_url` field in `config.py` found in Discord folder.
- If you want the health messages in another channel, fill in `radarr_health_url` and/or `sonarr_health_url`.
- Add all the other required fields in the file.

### Slack
- Create a webhook. Check [here](https://api.slack.com/messaging/webhooks#create_a_webhook) for more information.
- Fill in `sonarr_slack_url` and/or `radarr_slack_url` field in `config.py` found in Slack folder.
- If you want the health messages in another channel, fill in `radarr_health_url` and/or `sonarr_health_url`.
- Add all the other required fields.

### Telegram
- Create a bot using [BotFather](https://t.me/botfather). Follow the instructions and fill in the `sonarr_botid` and/or `radarr_botid` field on `config.py` file in Telegram folder.
- To get your chat id, message [getidbot](https://telegram.me/get_id_bot) and copy paste it in the `chat_id` field of the file. 
- If you are sending message to  a group chat, see [this](https://stackoverflow.com/questions/32423837/telegram-bot-how-to-get-a-group-chat-id)
- If you want the health messages in another channel, fill in `sonarr_error_botid` and/or `radarr_error_botid` and `error_channel`.
- If you want the notifications to be silent, set `silent` to `True`. Default is `False`.

### Pushover
- Create an application on [Pushover](https://pushover.net).
- Fill in `push_user`, `push_radarr`, `push_sonarr` in `config.py` file in Pushover folder.
- If you want the health messages in another application, fill in `push_error`.
- If you want to customize notifications, fill in `push_sound`, `push_priority`, `push_device`.
- Emergency priority (2) has default 30 second timeout between retries and will expire after 1 hour.

## Samples
Discord, Slack and Telegram samples are outdated.

##### Discord
[Radarr Grab](https://user-images.githubusercontent.com/54862871/105728794-8ea3f980-5f52-11eb-86d1-fbd2b02da663.jpg "Radarr Grab - Discord")\
[Radarr Import](https://user-images.githubusercontent.com/54862871/105728796-8f3c9000-5f52-11eb-90b0-ffe0e23d24ee.jpg "Radarr Import - Discord")\
[Sonarr Grab](https://user-images.githubusercontent.com/54862871/105728802-8fd52680-5f52-11eb-8301-4c85d14e9c32.jpg "Sonarr Grab - Discord")\
[Sonarr Import](https://user-images.githubusercontent.com/54862871/105728806-906dbd00-5f52-11eb-9898-c1d08a3ccdcc.jpg "Sonarr Import - Discord")

##### Slack
[Radarr Grab](https://user-images.githubusercontent.com/54862871/105728811-91065380-5f52-11eb-9576-44d0b3cf2d09.jpg "Radarr Grab - Slack")\
[Radarr Import](https://user-images.githubusercontent.com/54862871/105728815-919eea00-5f52-11eb-9fb3-e96edc46a940.jpg "Radarr Import - Slack")\
[Sonarr Grab](https://user-images.githubusercontent.com/54862871/105728816-92378080-5f52-11eb-90d2-56515dfacff0.jpg "Sonarr Grab - Slack")\
[Sonarr Import](https://user-images.githubusercontent.com/54862871/105728820-92d01700-5f52-11eb-81fe-8c66f463c74a.jpg "Sonarr Import - Slack")

##### Telegram
[Radarr Grab](https://user-images.githubusercontent.com/54862871/105728778-8ba90900-5f52-11eb-8cf6-200ac605e56d.jpg "Radarr Grab - Telegram")\
[Radarr Import](https://user-images.githubusercontent.com/54862871/105728785-8cda3600-5f52-11eb-958a-0a21a625517e.jpg "Radarr Import - Telegram")\
[Sonarr Grab](https://user-images.githubusercontent.com/54862871/105728789-8d72cc80-5f52-11eb-8a5e-c94f7d08c921.jpg "Sonarr Grab - Telegram") \
[Sonarr Import](https://user-images.githubusercontent.com/54862871/105728792-8e0b6300-5f52-11eb-87ce-f9ecf033d2e3.jpg "Sonarr Import - Telegram")

##### Pushover
[Radarr Grab](https://user-images.githubusercontent.com/54862871/157842632-605b7177-76c9-4e22-b079-9df694f35e05.jpg "Radarr Grab - Pushover")\
[Radarr Import](https://user-images.githubusercontent.com/54862871/157842640-ca4a9f69-7273-4fdf-b633-cfec69034f02.jpg "Radarr Import - Pushover")\
[Sonarr Grab](https://user-images.githubusercontent.com/54862871/157842643-5780ce15-68f7-4b23-bc9f-45c35b73b0ea.jpg "Sonarr Grab - Pushover")\
[Sonarr Import](https://user-images.githubusercontent.com/54862871/157842624-5b80aeaf-a7a0-44d8-b296-ea0a01dbd359.jpg "Sonarr Import - Pushover")
