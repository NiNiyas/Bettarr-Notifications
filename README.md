# Bettarr Notifications
Better Notifications for Sonarr and Radarr. \
Discord is based on script by @samwiseg0 - [Link to his repo](https://github.com/samwiseg0/better-discord-notifications).

Neither of his script worked for me, so I kinda tweaked it a bit and now it seems to be working. \
I have tested it with v3.0.4.1091 of Sonarr and v3.0.2.4369 of Radarr. Might work with v2 too.

## To Install
- Clone the repo.
- Extract and cd to the folder. Install Python requirements using `pip install -r requirements.txt`
- On Sonarr and Radarr, add a custom script in settings.
- Files with `-grab` is for grab event notifications and `-import` for import and upgrade events.

## Discord
- Create a webhook in your server, copy paste it in the `sonarr_discord_url` or `sonarr_discord_url` field in `script_config.py` found in Discord folder.
- Add all the other required fields in the file.

## Slack
- Create a webhook. Check [here](https://api.slack.com/messaging/webhooks#create_a_webhook) for more information.
- Copy paste it in the `radarr_slack_url` or `radarr_slack_url` field in `script_config.py` found in Slack folder.
- Add all the other required fields.

## Telegram
- Create a bot by messaging [BotFather](https://t.me/botfather). Follow the instructions and copy paste it in the `bot_id` field on `script_config.py` file in Telegram folder.
- To get your chat id, message [getidbot](https://telegram.me/get_id_bot) and copy paste it in the `chat_id` field of the file. 
- If you are sending message to  a group chat, you should add `-` sign to the group id. **Example** - if your group id is 1234567891234, your actual group id will be -1234567891234

### Rating API
In order to get ratings, you should set your api key in `script_config.py` file.
- Create your mdb API key from [here](https://mdblist.com/). This has a 100 calls per day limit. This is for `mdbapi` field in `script_config.py` files.
- To create TMDb API, check [here](https://www.themoviedb.org/settings/api). This has no known limit.

#### Samples

##### Discord
[Radarr Grab - Discord](https://user-images.githubusercontent.com/54862871/105728794-8ea3f980-5f52-11eb-86d1-fbd2b02da663.jpg "Radarr Grab - Discord")\
[Radarr Import - Discord](https://user-images.githubusercontent.com/54862871/105728796-8f3c9000-5f52-11eb-90b0-ffe0e23d24ee.jpg "Radarr Import - Discord")\
[Sonarr Grab - Discord](https://user-images.githubusercontent.com/54862871/105728802-8fd52680-5f52-11eb-8301-4c85d14e9c32.jpg "Sonarr Grab - Discord")\
[Sonarr Import - Discord](https://user-images.githubusercontent.com/54862871/105728806-906dbd00-5f52-11eb-9898-c1d08a3ccdcc.jpg "Sonarr Import - Discord")

##### Slack
[Radarr Grab - Slack](https://user-images.githubusercontent.com/54862871/105728811-91065380-5f52-11eb-9576-44d0b3cf2d09.jpg "Radarr Grab - Slack")\
[Radarr Import - Slack](https://user-images.githubusercontent.com/54862871/105728815-919eea00-5f52-11eb-9fb3-e96edc46a940.jpg "Radarr Import - Slack")\
[Sonarr Grab - Slack](https://user-images.githubusercontent.com/54862871/105728816-92378080-5f52-11eb-90d2-56515dfacff0.jpg "Sonarr Grab - Slack")\
[Sonarr Import - Slack](https://user-images.githubusercontent.com/54862871/105728820-92d01700-5f52-11eb-81fe-8c66f463c74a.jpg "Sonarr Import - Slack")

##### Telegram
[Radarr Grab - Telegram](https://user-images.githubusercontent.com/54862871/105728778-8ba90900-5f52-11eb-8cf6-200ac605e56d.jpg "Radarr Grab - Telegram")\
[Radarr Import - Telegram](https://user-images.githubusercontent.com/54862871/105728785-8cda3600-5f52-11eb-958a-0a21a625517e.jpg "Radarr Import - Telegram")\
[Sonarr Grab - Telegram](https://user-images.githubusercontent.com/54862871/105728789-8d72cc80-5f52-11eb-8a5e-c94f7d08c921.jpg "Sonarr Grab - Telegram") \
[Sonarr Import - Telegram](https://user-images.githubusercontent.com/54862871/105728792-8e0b6300-5f52-11eb-87ce-f9ecf033d2e3.jpg "Sonarr Import - Telegram")
