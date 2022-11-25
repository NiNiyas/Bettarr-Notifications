import config
import requests
from loguru import logger as log


def omdb_radarr(radarr_imdb):
    if config.OMDB_APIKEY != "":
        omdb = requests.get(f'https://www.omdbapi.com/?i={radarr_imdb}&apikey={config.OMDB_APIKEY}').json()
        if omdb["Response"] == "True":
            log.debug("Fetching awards from OMDB API.")
            try:
                awards = omdb["Awards"]
                log.debug("Successfully fetched awards.")
            except KeyError:
                awards = ""
        else:
            log.error("Failed to fetch awards from OMDB API.")
            log.error("-" * 50)
            log.error(omdb)
            log.error("-" * 50)
            awards = ""
    else:
        awards = ""

    return awards


def omdb_sonarr(sonarr_imdb):
    if config.OMDB_APIKEY != "":
        omdb = requests.get(f'https://www.omdbapi.com/?i={sonarr_imdb}&apikey={config.OMDB_APIKEY}').json()
        if omdb["Response"] == "True":
            log.debug("Fetching awards from OMDB API.")
            try:
                awards = omdb["Awards"]
                log.debug("Successfully fetched awards.")
            except KeyError:
                awards = ""
        else:
            log.error("Failed to fetch awards from OMDB API.")
            log.error("-" * 50)
            log.error(omdb)
            log.error("-" * 50)
            awards = ""
    else:
        awards = ""

    return awards
