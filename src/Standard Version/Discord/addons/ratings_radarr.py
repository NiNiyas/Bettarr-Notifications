import os

import requests
from . import config

imdb_id = os.environ.get('radarr_movie_imdbid')

if config.mdbapi != "":
    mdblist = requests.get('https://mdblist.com/api/?apikey={}&i={}'.format(config.mdbapi, imdb_id))
    mdblist_data = mdblist.json()

    if mdblist_data['response']:
        print("Fetching ratings from mdblist.")

        try:
            imdb_rating = mdblist_data['ratings'][0]['value']
        except (KeyError, IndexError, TypeError):
            imdb_rating = 'None'

        try:
            metacritic = mdblist_data['ratings'][1]['value']
        except (KeyError, IndexError, TypeError):
            metacritic = 'None'

        try:
            trakt_rating = mdblist_data['ratings'][3]['value']
        except (KeyError, IndexError, TypeError):
            trakt_rating = 'None'

        try:
            tmdb_rating = mdblist_data['ratings'][6]['value']
        except (KeyError, IndexError, TypeError):
            tmdb_rating = 'None'

        try:
            rottentomatoes = mdblist_data['ratings'][4]['value']
        except (KeyError, IndexError, TypeError):
            rottentomatoes = 'None'

        try:
            letterboxd = mdblist_data['ratings'][7]['value']
        except (KeyError, IndexError, TypeError):
            letterboxd = 'None'

        try:
            poster = mdblist_data["poster"]
        except (KeyError, IndexError, TypeError):
            poster = "https://i.imgur.com/GoqfZJe.jpg"

        try:
            backdrop = mdblist_data["backdrop"]
        except (KeyError, IndexError, TypeError):
            backdrop = "https://i.imgur.com/IMQb6ia.png"

        try:
            print("mdblist API used:", mdblist_data['apiused'])
        except (KeyError, IndexError, TypeError):
            print("API limit reached.")

        try:
            certification = mdblist_data['certification']
        except (KeyError, TypeError, IndexError):
            certification = 'None'

        ratings = "**IMDb**: {} | **Metacritic**: {} | **Rotten Tomatoes**: {} | **TMDb**: {} | **Trakt**: {} | **LetterBoxd**: {}".format(
            imdb_rating,
            metacritic, rottentomatoes, tmdb_rating, trakt_rating,
            letterboxd)

        try:
            trailer = mdblist_data['trailer']
        except (KeyError, IndexError, TypeError):
            print("Trailer not found. Using default.")
            trailer = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'

    else:
        ratings = "None"
        certification = 'None'
        print("Failed to fetch ratings and trailer. API limit reached.")
