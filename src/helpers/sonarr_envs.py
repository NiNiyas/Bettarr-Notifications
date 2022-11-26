import os

imdb_id = os.environ.get('sonarr_series_imdbid')

season = os.environ.get('sonarr_release_seasonnumber')

episode = os.environ.get('sonarr_release_episodenumbers')

tvdb_id = os.environ.get('sonarr_series_tvdbid')

size = os.environ.get('sonarr_release_size')

release_group = os.environ.get('sonarr_release_releasegroup')

media_title = os.environ.get('sonarr_series_title')

episode_title = os.environ.get('sonarr_release_episodetitles')

quality = os.environ.get('sonarr_release_quality')

import_episode_title = os.environ.get('sonarr_episodefile_episodetitles')

import_quality = os.environ.get('sonarr_episodefile_quality')

import_episode = os.environ.get('sonarr_episodefile_episodenumbers')

import_season = os.environ.get('sonarr_episodefile_seasonnumber')

release_indexer = os.environ.get('sonarr_release_indexer')

download_client = os.environ.get('sonarr_download_client')

is_upgrade = os.environ.get('sonarr_isupgrade')

air_date = os.environ.get('sonarr_release_episodeairdatesutc')

scene_name = os.environ.get('sonarr_episodefile_scenename')

issue_level = os.environ.get('sonarr_health_issue_level')

issue_type = os.environ.get('sonarr_health_issue_type')

issue_message = os.environ.get('sonarr_health_issue_message')

wiki_link = os.environ.get('sonarr_health_issue_wiki')

episode_path = os.environ.get('sonarr_episodefile_path')

delete_episode_name = os.environ.get('sonarr_episodefile_episodetitles')

delete_episode = os.environ.get('sonarr_episodefile_episodenumbers')

delete_season = os.environ.get('sonarr_episodefile_seasonnumber')

delete_release_group = os.environ.get('sonarr_episodefile_releasegroup')

delete_quality = os.environ.get('sonarr_episodefile_quality')

delete_air_date = os.environ.get('sonarr_episodefile_episodeairdatesutc')

delete_reason = os.environ.get('sonarr_episodefile_deletereason')

series_path = os.environ.get('sonarr_series_path')

new_version = os.environ.get('sonarr_update_newversion')

old_version = os.environ.get('sonarr_update_previousversion')
