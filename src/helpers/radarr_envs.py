import os

imdb_id = os.environ.get("radarr_movie_imdbid")

movie_id = os.environ.get("radarr_movie_id")

media_title = os.environ.get("radarr_movie_title")

quality = os.environ.get("radarr_release_quality")

import_quality = os.environ.get('radarr_moviefile_quality')

download_client = os.environ.get("radarr_download_client")

release_indexer = os.environ.get("radarr_release_indexer")

release_size = os.environ.get("radarr_release_size")

release_group = os.environ.get("radarr_release_releasegroup", "Unknown")

tmdb_id = os.environ.get("radarr_movie_tmdbid")

year = os.environ.get("radarr_movie_year")

scene_name = os.environ.get("radarr_moviefile_scenename", "Unknown")

is_upgrade = os.environ.get("radarr_isupgrade")

issue_level = os.environ.get("radarr_health_issue_level")

issue_type = os.environ.get("radarr_health_issue_type")

issue_message = os.environ.get("radarr_health_issue_message")

wiki_link = os.environ.get("radarr_health_issue_wiki")

update_message = os.environ.get('radarr_update_message')

new_version = os.environ.get('radarr_update_newversion')

old_version = os.environ.get('radarr_update_previousversion')

delete_path = os.environ.get('radarr_movie_path')

deleted_files = os.environ.get('radarr_movie_deletedfiles')

deleted_size = os.environ.get('radarr_movie_folder_size', 0)

deleted_moviefilereason = os.environ.get('radarr_moviefile_deletereason', "Unknown")

deleted_moviefilepath = os.environ.get('radarr_moviefile_path')

deleted_moviefilesize = os.environ.get('radarr_moviefile_size', 0)

deleted_moviereleasegroup = os.environ.get('radarr_moviefile_releasegroup', "Unknown")