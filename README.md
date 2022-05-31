# Bettarr Notifications

Better Notifications for Sonarr and Radarr. \
Discord is based on script by @samwiseg0 - [Link to his repo](https://github.com/samwiseg0/better-discord-notifications)

Tested with v3.0.8.1507 of Sonarr and v4.1.0.6175 of Radarr.

## Installation

- Clone the repo, `git clone https://github.com/NiNiyas/Bettarr-Notifications.git` and `cd Bettarr-Notifications`.
- Install requirements `pip install --no-cache --upgrade -r requirements.txt`.
- On Sonarr and/or Radarr, add a custom script in `Settings -> Connect`.
- Select everything except `On Rename`.

## Docker Installation

- Clone the repo.
- Mount it to the docker container.
- Install requirements:
    - For [linuxserver's](https://linuxserver.io/) image,
      read [this](https://www.linuxserver.io/blog/2019-09-14-customizing-our-containers).
    - For [hotio's](https://hotio.dev/) image, read [this](https://hotio.dev/faq/#guides)
    - Custom script is available in [install](https://github.com/NiNiyas/Bettarr-Notifications/tree/master/src/install)
      folder.

# API Keys

### TMDB (Required)

- To create TMDB API, check [here](https://www.themoviedb.org/settings/api). This has no known limit.
- Fill in the `TMDB_APIKEY` in `config.py` file.
- If you need the JustWatch providers for you country, fill in the `TMDB_COUNTRY_CODE`.
- For country codes, see [here](https://www.justwatch.com/), scroll down to the very bottom of the page.

If your ISP block access to TMDB API like mine does, host a [tmdb-proxy](https://github.com/chervontsev/tmdb-proxy) on
Heroku ot Railway and fill in `TMDB_URL`. I personally host mine in Railway.

### mdblist (Optional)

In order to get ratings, you should set `MDBLIST_APIKEY` in `config.py` file.

- Create your mdblist API key from [here](https://mdblist.com/).
- You will need a [Trakt](https://trakt.tv) account for this. This has a 1000 calls per day limit which is more than
  enough.

# Notifiers

`*_*_WEBHOOK` is for downloading and importing notifications. \
`*_HEALTH_*_WEBHOOK` is for health notifications. \
`*_MISC_*_WEBHOOK` is for file deletion and app update notifications.

## [Discord](https://discord.com/)

Create a [webhook](https://support.discord.com/hc/en-us/articles/228383668-Intro-to-Webhooks) in your server.

##### Radarr

- Fill in `RADARR_DISCORD_WEBHOOK`, `RADARR_HEALTH_DISCORD_WEBHOOK` and `RADARR_MISC_DISCORD_WEBHOOK`.

##### Sonarr

- Fill in `SONARR_DISCORD_WEBHOOK`, `SONARR_HEALTH_DISCORD_WEBHOOK` and `SONARR_MISC_DISCORD_WEBHOOK`.

## [Slack](https://slack.com)

Create a webhook. More info [here](https://api.slack.com/messaging/webhooks#create_a_webhook).

##### Radarr

- Fill in `RADARR_SLACK_WEBHOOK`, `RADARR_HEALTH_SLACK_WEBHOOK` and `RADARR_MISC_SLACK_WEBHOOK`.

##### Sonarr

- Fill in `SOANRR_SLACK_WEBHOOK`, `SONARR_HEALTH_SLACK_WEBHOOK` and `SONARR_MISC_SLACK_WEBHOOK`.

## [Telegram](https://telegram.org/)

Create a bot using [BotFather](https://t.me/botfather). \
Set `TELEGRAM_SILENT` to `True` if you want silent notifications. \
Set `TELEGRAM_DISABLE_IMAGES` to `True` if you want to disable images in notifications.

If you are sending message to a group chat,
see [here](https://stackoverflow.com/questions/32423837/telegram-bot-how-to-get-a-group-chat-id)

Fill in `TELEGRAM_CHAT_ID`,`TELEGRAM_MISC_CHAT_ID` and `TELEGRAM_HEALTH_CHAT_ID`.

##### Radarr

- Fill in `RADARR_TELEGRAM_BOT_ID`, `RADARR_HEALTH_TELEGRAM_BOT_ID`, `RADARR_MISC_TELEGRAM_BOT_ID`.

##### Sonarr

- Fill in `SONARR_TELEGRAM_BOT_ID`, `SONARR_HEALTH_TELEGRAM_BOT_ID`, `SONARR_MISC_TELEGRAM_BOT_ID`.

## [Pushover](https://pushover.net)

Create an application on [Pushover](https://pushover.net).

Fill in `PUSHOVER_USER` with your user token.

If you want to change priority, fill in `PUSHOVER_PRIORITY`. [List](https://pushover.net/api#priority) of available
priorities.\
If you want to change notification sound, fill in `PUSHOVER_SOUND`. [List](https://pushover.net/api#sounds) of available
notification sounds.\
If you want to route message to different device, fill in`PUSHOVER_DEVICE`.

Emergency priority (2) has default 30 second timeout between retries and will expire after 1 hour.

##### Radarr

- Fill in `RADARR_PUSHOVER_TOKEN`, `RADARR_HEALTH_PUSHOVER_TOKEN` and `RADARR_MISC_PUSHOVER_TOKEN`.

##### Sonarr

- Fill in `SONARR_PUSHOVER_TOKEN`, `SONARR_HEALTH_PUSHOVER_TOKEN` and `SONARR_MISC_PUSHOVER_TOKEN`.

## [ntfy](https://ntfy.sh)

I probably will be supporting ntfy in the near future.