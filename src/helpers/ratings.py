import os

import config
import requests
from loguru import logger as log


def mdblist_movie():
    imdb_id = os.environ.get("radarr_movie_imdbid")
    if config.MDBLIST_APIKEY != "":
        mdblist = requests.get(f'https://mdblist.com/api/?apikey={config.MDBLIST_APIKEY}&i={imdb_id}').json()

        if mdblist['response']:
            log.debug(f"Fetching ratings from mdblist for imdb id {imdb_id}.")

            try:
                imdb_rating = mdblist['ratings'][0]['value']
            except KeyError:
                imdb_rating = 'None'

            try:
                metacritic = mdblist['ratings'][1]['value']
            except KeyError:
                metacritic = 'None'

            try:
                trakt_rating = mdblist['ratings'][3]['value']
            except KeyError:
                trakt_rating = 'None'

            try:
                tmdb_rating = mdblist['ratings'][6]['value']
            except KeyError:
                tmdb_rating = 'None'

            try:
                rottentomatoes = mdblist['ratings'][4]['value']
            except KeyError:
                rottentomatoes = 'None'

            try:
                letterboxd = mdblist['ratings'][7]['value']
            except KeyError:
                letterboxd = 'None'

            try:
                certification = mdblist['certification']
            except KeyError:
                certification = 'None'

            try:
                log.debug(f"mdblist API used: {mdblist['apiused']}")
            except KeyError:
                pass

            discord_ratings = f"\n\n**Ratings**\n**IMDb**: {imdb_rating} | **Metacritic**: {metacritic} | **Rotten Tomatoes**: {rottentomatoes} | **TMDb**: {tmdb_rating} | **Trakt**: {trakt_rating} | **LetterBoxd**: {letterboxd}"
            slack_ratings = f"\n\n*Ratings*\n*IMDb*: {imdb_rating} | *Metacritic*: {metacritic} | *Rotten Tomatoes*: {rottentomatoes} | *TMDb*: {tmdb_rating} | *Trakt*: {trakt_rating} | *LetterBoxd*: {letterboxd}"
            html_ratings = f"\n<strong>Ratings</strong>\n<b>IMDb</b>: {imdb_rating}\n<b>Metacritic</b>: {metacritic}\n<b>Rotten Tomatoes</b>: {rottentomatoes}\n<b>TMDb</b>: {tmdb_rating}\n<b>Trakt</b>: {trakt_rating}\n<b>LetterBoxd</b>: {letterboxd}"
            ntfy_ratings = f"\nRatings\nIMDb: {imdb_rating}\nMetacritic: {metacritic}\nRotten Tomatoes: {rottentomatoes}\nTMDb: {tmdb_rating}\nTrakt: {trakt_rating}\nLetterBoxd: {letterboxd}"

        else:
            discord_ratings = ""
            slack_ratings = ""
            html_ratings = ""
            certification = "Unknown"
            ntfy_ratings = ""
            log.warning("Failed to fetch ratings and trailer. API limit reached.")
    else:
        discord_ratings = ""
        slack_ratings = ""
        html_ratings = ""
        certification = "Unknown"
        ntfy_ratings = ""
        log.warning("Didn't fetch ratings, trailer and certification because MDBLIST_APIKEY is not set in config.")

    return discord_ratings, certification, slack_ratings, html_ratings, ntfy_ratings


def mdblist_tv():
    imdb_id = os.environ.get('sonarr_series_imdbid')

    if config.MDBLIST_APIKEY != "":
        mdblist = requests.get(f'https://mdblist.com/api/?apikey={config.MDBLIST_APIKEY}&i={imdb_id}&m=show')
        mdblist_data = mdblist.json()

        if mdblist_data['response']:
            log.debug(f"Fetching ratings from mdblist for imdb id {imdb_id}.")

            try:
                imdb_rating = mdblist_data['ratings'][0]['value']
            except KeyError:
                imdb_rating = 'None'

            try:
                metacritic = mdblist_data['ratings'][1]['value']
            except KeyError:
                metacritic = 'None'

            try:
                trakt_rating = mdblist_data['ratings'][3]['value']
            except KeyError:
                trakt_rating = 'None'

            try:
                tmdb_rating = mdblist_data['ratings'][6]['value']
            except KeyError:
                tmdb_rating = 'None'

            try:
                rottentomatoes = mdblist_data['ratings'][4]['value']
            except KeyError:
                rottentomatoes = 'None'

            try:
                letterboxd = mdblist_data['ratings'][7]['value']
            except KeyError:
                letterboxd = 'None'

            try:
                poster = mdblist_data["poster"]
            except KeyError:
                poster = "https://i.imgur.com/GoqfZJe.jpg"

            try:
                backdrop = mdblist_data["backdrop"]
            except KeyError:
                backdrop = "https://i.imgur.com/IMQb6ia.png"

            try:
                log.debug(f"mdblist API used: {mdblist_data['apiused']}", )
            except KeyError:
                pass

            try:
                certification = mdblist_data['certification']
            except KeyError:
                certification = 'None'

            discord_ratings = f"\n\n**Ratings**\n**IMDb**: {imdb_rating} | **Metacritic**: {metacritic} | **Rotten Tomatoes**: {rottentomatoes} | **TMDb**: {tmdb_rating} | **Trakt**: {trakt_rating} | **LetterBoxd**: {letterboxd}"
            slack_ratings = f"\n\n*Ratings*\n*IMDb*: {imdb_rating} | *Metacritic*: {metacritic} | *Rotten Tomatoes*: {rottentomatoes} | *TMDb*: {tmdb_rating} | *Trakt*: {trakt_rating} | *LetterBoxd*: {letterboxd}"
            html_ratings = f"\n<b>Ratings</b>\n<b>IMDb</b>: {imdb_rating}\n<b>Metacritic</b>: {metacritic}\n<b>Rotten Tomatoes</b>: {rottentomatoes}\n<b>TMDb</b>: {tmdb_rating}\n<b>Trakt</b>: {trakt_rating}\n<b>LetterBoxd</b>: {letterboxd}"
            ntfy_ratings = f"\nRatings\nIMDb: {imdb_rating}\nMetacritic: {metacritic}\nRotten Tomatoes: {rottentomatoes}\nTMDb: {tmdb_rating}\nTrakt: {trakt_rating}\nLetterBoxd: {letterboxd}"

            try:
                trailer = mdblist_data['trailer']
                if trailer is None:
                    trailer = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
            except KeyError:
                log.warning("Trailer not found. Using default.")
                trailer = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'

        else:
            trailer = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
            discord_ratings = ""
            slack_ratings = ""
            html_ratings = ""
            certification = ""
            ntfy_ratings = ""
            backdrop = "https://i.imgur.com/IMQb6ia.png"
            poster = "https://i.imgur.com/GoqfZJe.jpg"
            log.warning("Failed to fetch ratings and trailer. API limit reached.")
    else:
        trailer = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        discord_ratings = ""
        certification = ""
        slack_ratings = ""
        html_ratings = ""
        ntfy_ratings = ""
        backdrop = "https://i.imgur.com/IMQb6ia.png"
        poster = "https://i.imgur.com/GoqfZJe.jpg"
        log.warning("Didn't fetch ratings, trailer and certification because MDBLIST_APIKEY is not set in config.")

    return discord_ratings, certification, trailer, poster, backdrop, slack_ratings, html_ratings, ntfy_ratings
