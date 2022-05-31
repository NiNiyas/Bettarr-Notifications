# Required
SONARR = False # set to True to enable
SONARR_URL = "http://localhost:8989/" # with url trailing
SONARR_APIKEY = ""

RADARR = False # set to True to enable
RADARR_URL = "http://localhost:7878/" # with url trailing
RADARR_APIKEY = ""

TMDB_APIKEY = ""
TMDB_URL = "api.themoviedb.org" # no need to change this if your isp doesn't block it
TMDB_COUNTRY_CODE = "US"

# Optional
MDBLIST_APIKEY = ""

# Notifiers
DISCORD = False # set to True to enable
SLACK = False # set to True to enable
PUSHOVER = False # set to True to enable
TELEGRAM = False # set to True to enable
ntfy = False # NOT IMPLEMENTED

# Discord Configuration
## Radarr
RADARR_HEALTH_DISCORD_WEBHOOK = ""
RADARR_MISC_DISCORD_WEBHOOK = ""
RADARR_DISCORD_WEBHOOK = ""
RADARR_DISCORD_USERICON = "https://github.com/Radarr/Radarr/raw/aphrodite/Logo/128.png"
RADARR_DISCORD_USERNAME = "Radarr"

## Sonarr
SONARR_HEALTH_DISCORD_WEBHOOK = ""
SONARR_MISC_DISCORD_WEBHOOK = ""
SONARR_DISCORD_WEBHOOK = ""
SONARR_DISCORD_USERICON = "https://user-images.githubusercontent.com/31781818/33885790-bc32aec0-df1a-11e7-83df-3bf737de68c5.png"
SONARR_DISCORD_USERNAME = "Sonarr"

# Slack Configuration
SLACK_CHANNEL = ""
## Radarr
RADARR_SLACK_WEBHOOK = ""
RADARR_HEALTH_SLACK_WEBHOOK = ""
RADARR_MISC_SLACK_WEBHOOK = ""

## Sonarr
SONARR_SLACK_WEBHOOK = ""
SONARR_HEALTH_SLACK_WEBHOOK = ""
SONARR_MISC_SLACK_WEBHOOK = ""

# Pushover Configuration
PUSHOVER_API_URL = "https://api.pushover.net/1/messages.json" # no need to change this
PUSHOVER_USER = ""
PUSHOVER_PRIORITY = ""
PUSHOVER_SOUND = ""
PUSHOVER_DEVICE = ""

## Radarr
RADARR_PUSHOVER_TOKEN = ""
RADARR_HEALTH_PUSHOVER_TOKEN = ""
RADARR_MISC_PUSHOVER_TOKEN = ""

## Sonarr
SONARR_PUSHOVER_TOKEN = ""
SONARR_HEALTH_PUSHOVER_TOKEN = ""
SONARR_MISC_PUSHOVER_TOKEN = ""

# Telegram Configuration
TELEGRAM_CHAT_ID = ""
TELEGRAM_MISC_CHAT_ID = ""
TELEGRAM_HEALTH_CHAT_ID = ""
TELEGRAM_SILENT = False
TELEGRAM_DISABLE_IMAGES = False

## Radarr
RADARR_TELEGRAM_BOT_ID = ""
RADARR_HEALTH_TELEGRAM_BOT_ID = ""
RADARR_MISC_TELEGRAM_BOT_ID = ""

## Sonarr
SONARR_TELEGRAM_BOT_ID = ""
SONARR_HEALTH_TELEGRAM_BOT_ID = ""
SONARR_MISC_TELEGRAM_BOT_ID = ""

TELEGRAM_RADARR_URL = f"https://api.telegram.org/bot{RADARR_TELEGRAM_BOT_ID}/sendMessage" # no need to change this
TELEGRAM_SONARR_URL = f"https://api.telegram.org/bot{SONARR_TELEGRAM_BOT_ID}/sendMessage" # no need to change this
TELEGRAM_RADARR_HEALTH_URL = f"https://api.telegram.org/bot{RADARR_HEALTH_TELEGRAM_BOT_ID}/sendMessage" # no need to change this
TELEGRAM_SONARR_HEALTH_URL = f"https://api.telegram.org/bot{SONARR_HEALTH_TELEGRAM_BOT_ID}/sendMessage" # no need to change this
TELEGRAM_RADARR_MISC_URL = f"https://api.telegram.org/bot{RADARR_MISC_TELEGRAM_BOT_ID}/sendMessage" # no need to change this
TELEGRAM_SONARR_MISC_URL = f"https://api.telegram.org/bot{SONARR_MISC_TELEGRAM_BOT_ID}/sendMessage" # no need to change this

# ntfy Configuration
NTFY_URL = ""
## Radarr
NTFY_RADARR_TOPIC = ""
NTFY_RADARR_PRIORITY = ""
