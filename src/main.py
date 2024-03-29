#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import sys

import requests
from loguru import logger as log
from requests import RequestException

import config
from notifiers.Discord import *
from notifiers.Pushover import *
from notifiers.Slack import *
from notifiers.Telegram import *
from notifiers.ntfy import *

fmt = "{time:YYYY-MM-DD HH:mm:ss Z} | {name} | {level} | {message}"
LOG_LEVEL = config.LOG_LEVEL
log.add(sys.stderr, level="INFO")
log.remove()
dir_path = os.path.dirname(os.path.realpath(__file__))
log.add(f"{dir_path}/logs/better-notifications.log", level=LOG_LEVEL, format=fmt, backtrace=True, rotation="1 week")

if not any((config.SONARR, config.RADARR, config.PROWLARR)):
    log.error("None of the *arrs are enabled. Exiting...")
    exit(1)

RADARR_EVENT_TYPE = os.environ.get("radarr_eventtype")
SONARR_EVENT_TYPE = os.environ.get("sonarr_eventtype")
PROWLARR_EVENT_TYPE = os.environ.get("prowlarr_eventtype")

log = log.patch(lambda record: record.update(name="BettarrNotifications"))


def initialize_sonarr():
    """
    Checking if required variables are set for sonarr
    """
    required_variables = [config.SONARR_URL, config.SONARR_APIKEY]
    for x in required_variables:
        if x == "":
            log.error(
                "Required variables for Sonarr are not set. Please check your config and make sure you set everything correct.")
            log.error("Exiting...")
            exit(1)


def initialize_radarr():
    """
    Checking if required variables are set for radarr
    """
    required_variables = [config.RADARR_URL, config.RADARR_APIKEY]
    for x in required_variables:
        if x == "":
            log.error(
                "Required variables for Radarr are not set. Please check your config and make sure you set everything correct.")
            log.error("Exiting...")
            exit(1)


def initialize_prowlarr():
    """
    Checking if required variables are set for prowlarr
    """

    if config.PROWLARR_URL == "":
        log.error(
            "Required variables for Radarr are not set. Please check your config and make sure you set everything correct.")
        log.error("Exiting...")
        exit(1)


def check_sonarr_connection():
    """
    Checking sonarr connection.
    """
    initialize_sonarr()
    try:
        cmd = requests.get(f"{config.SONARR_URL}/api/v3/health?apikey={config.SONARR_APIKEY}")
        if cmd.status_code == 200:
            log.debug("Successfully connected to Sonarr.")
        else:
            log.error(
                "Error occurred when trying to connect to Sonarr. Please check your config and make sure you set everything correct.")
            log.error("Exiting...")
            exit(1)
    except RequestException as e:
        log.error("Error occured when trying to connect to Sonarr.")
        log.exception(e)


def check_radarr_connection():
    """
    Checking radarr connection.
    """
    initialize_radarr()
    try:
        cmd = requests.get(f"{config.RADARR_URL}/api/v3/health?apikey={config.RADARR_APIKEY}")
        if cmd.status_code == 200:
            log.debug("Successfully connected to Radarr.")
        else:
            log.error(
                "Error occurred when trying to connect to Radarr. Please check your config and make sure you set everything correct.")
            log.error("Exiting...")
            exit(1)
    except RequestException as e:
        log.error("Error occured when trying to connect to Radarr.")
        log.exception(e)


def check_prowlarr_connection():
    """
    Checking prowlarr connection.
    """
    initialize_prowlarr()
    try:
        cmd = requests.get(config.PROWLARR_URL)
        if cmd.status_code == 200:
            log.debug("Successfully connected to Prowlarr.")
        else:
            log.error(
                "Error occurred when trying to connect to Prowlarr. Please check your config and make sure you set everything correct.")
            log.error("Exiting...")
            exit(1)
    except RequestException as e:
        log.error("Error occured when trying to connect to Prowlarr.")
        log.exception(e)


def radarr_send():
    """
    Sends radarr notifications to respective platforms
    """

    check_radarr_connection()
    if config.DISCORD:
        if RADARR_EVENT_TYPE == "Test":
            discord_radarr.radarr_test()
        elif RADARR_EVENT_TYPE == "Grab":
            discord_radarr.radarr_grab()
        elif RADARR_EVENT_TYPE == "Download":
            discord_radarr.radarr_import()
        elif RADARR_EVENT_TYPE == "HealthIssue":
            discord_radarr.radarr_health()
        elif RADARR_EVENT_TYPE == "MovieDelete":
            discord_radarr.radarr_movie_delete()
        elif RADARR_EVENT_TYPE == "MovieFileDelete":
            discord_radarr.radarr_moviefile_delete()
        elif RADARR_EVENT_TYPE == "ApplicationUpdate":
            discord_radarr.radarr_update()
        elif RADARR_EVENT_TYPE == "MovieAdded":
            discord_radarr.radarr_movie_added()

    if config.SLACK:
        if RADARR_EVENT_TYPE == "Test":
            slack_radarr.radarr_test()
        elif RADARR_EVENT_TYPE == "Grab":
            slack_radarr.radarr_grab()
        elif RADARR_EVENT_TYPE == "Download":
            slack_radarr.radarr_import()
        elif RADARR_EVENT_TYPE == "MovieDelete":
            slack_radarr.radarr_movie_delete()
        elif RADARR_EVENT_TYPE == "MovieFileDelete":
            slack_radarr.radarr_moviefile_delete()
        elif RADARR_EVENT_TYPE == "HealthIssue":
            slack_radarr.radarr_health()
        elif RADARR_EVENT_TYPE == "ApplicationUpdate":
            slack_radarr.radarr_update()
        elif RADARR_EVENT_TYPE == "MovieAdded":
            slack_radarr.radarr_movie_added()

    if config.PUSHOVER:
        if RADARR_EVENT_TYPE == "Test":
            pushover_radarr.radarr_test()
        elif RADARR_EVENT_TYPE == "Grab":
            pushover_radarr.radarr_grab()
        elif RADARR_EVENT_TYPE == "Download":
            pushover_radarr.radarr_import()
        elif RADARR_EVENT_TYPE == "MovieDelete":
            pushover_radarr.radarr_movie_delete()
        elif RADARR_EVENT_TYPE == "MovieFileDelete":
            pushover_radarr.radarr_moviefile_delete()
        elif RADARR_EVENT_TYPE == "HealthIssue":
            pushover_radarr.radarr_health()
        elif RADARR_EVENT_TYPE == "ApplicationUpdate":
            pushover_radarr.radarr_update()
        elif RADARR_EVENT_TYPE == "MovieAdded":
            pushover_radarr.radarr_movie_added()

    if config.TELEGRAM:
        if RADARR_EVENT_TYPE == "Test":
            telegram_radarr.radarr_test()
        elif RADARR_EVENT_TYPE == "Grab":
            telegram_radarr.radarr_grab()
        elif RADARR_EVENT_TYPE == "Download":
            telegram_radarr.radarr_import()
        elif RADARR_EVENT_TYPE == "MovieDelete":
            telegram_radarr.radarr_movie_delete()
        elif RADARR_EVENT_TYPE == "MovieFileDelete":
            telegram_radarr.radarr_moviefile_delete()
        elif RADARR_EVENT_TYPE == "HealthIssue":
            telegram_radarr.radarr_health()
        elif RADARR_EVENT_TYPE == "ApplicationUpdate":
            telegram_radarr.radarr_update()
        elif RADARR_EVENT_TYPE == "MovieAdded":
            telegram_radarr.radarr_movie_added()

    if config.ntfy:
        if RADARR_EVENT_TYPE == "Test":
            ntfy_radarr.radarr_test()
        elif RADARR_EVENT_TYPE == "Grab":
            ntfy_radarr.radarr_grab()
        elif RADARR_EVENT_TYPE == "Download":
            ntfy_radarr.radarr_import()
        elif RADARR_EVENT_TYPE == "MovieDelete":
            ntfy_radarr.radarr_movie_delete()
        elif RADARR_EVENT_TYPE == "MovieFileDelete":
            ntfy_radarr.radarr_moviefile_delete()
        elif RADARR_EVENT_TYPE == "HealthIssue":
            ntfy_radarr.radarr_health()
        elif RADARR_EVENT_TYPE == "ApplicationUpdate":
            ntfy_radarr.radarr_update()
        elif RADARR_EVENT_TYPE == "MovieAdded":
            ntfy_radarr.radarr_movie_added()


def sonarr_send():
    """
    Sends sonarr notifications to respective platforms
    """

    check_sonarr_connection()
    if config.DISCORD:
        if SONARR_EVENT_TYPE == "Test":
            discord_sonarr.sonarr_test()
        elif SONARR_EVENT_TYPE == "Grab":
            discord_sonarr.sonarr_grab()
        elif SONARR_EVENT_TYPE == "Download":
            discord_sonarr.sonarr_import()
        elif SONARR_EVENT_TYPE == "HealthIssue":
            discord_sonarr.sonarr_health()
        elif SONARR_EVENT_TYPE == "EpisodeFileDelete":
            discord_sonarr.sonarr_delete_episode()
        elif SONARR_EVENT_TYPE == "SeriesDelete":
            discord_sonarr.sonarr_delete_series()
        elif SONARR_EVENT_TYPE == "ApplicationUpdate":
            discord_sonarr.sonarr_update()

    if config.SLACK:
        if SONARR_EVENT_TYPE == "Test":
            slack_sonarr.sonarr_test()
        elif SONARR_EVENT_TYPE == "Grab":
            slack_sonarr.sonarr_grab()
        elif SONARR_EVENT_TYPE == "Download":
            slack_sonarr.sonarr_import()
        elif SONARR_EVENT_TYPE == "HealthIssue":
            slack_sonarr.sonarr_health()
        elif SONARR_EVENT_TYPE == "EpisodeFileDelete":
            slack_sonarr.sonarr_delete_episode()
        elif SONARR_EVENT_TYPE == "SeriesDelete":
            slack_sonarr.sonarr_delete_series()
        elif SONARR_EVENT_TYPE == "ApplicationUpdate":
            slack_sonarr.sonarr_update()

    if config.PUSHOVER:
        if SONARR_EVENT_TYPE == "Test":
            pushover_sonarr.sonarr_test()
        elif SONARR_EVENT_TYPE == "Grab":
            pushover_sonarr.sonarr_grab()
        elif SONARR_EVENT_TYPE == "Download":
            pushover_sonarr.sonarr_import()
        elif SONARR_EVENT_TYPE == "HealthIssue":
            pushover_sonarr.sonarr_health()
        elif SONARR_EVENT_TYPE == "EpisodeFileDelete":
            pushover_sonarr.sonarr_delete_episode()
        elif SONARR_EVENT_TYPE == "SeriesDelete":
            pushover_sonarr.sonarr_delete_series()
        elif SONARR_EVENT_TYPE == "ApplicationUpdate":
            pushover_sonarr.sonarr_update()

    if config.TELEGRAM:
        if SONARR_EVENT_TYPE == "Test":
            telegram_sonarr.sonarr_test()
        elif SONARR_EVENT_TYPE == "Grab":
            telegram_sonarr.sonarr_grab()
        elif SONARR_EVENT_TYPE == "Download":
            telegram_sonarr.sonarr_import()
        elif SONARR_EVENT_TYPE == "HealthIssue":
            telegram_sonarr.sonarr_health()
        elif SONARR_EVENT_TYPE == "EpisodeFileDelete":
            telegram_sonarr.sonarr_delete_episode()
        elif SONARR_EVENT_TYPE == "SeriesDelete":
            telegram_sonarr.sonarr_delete_series()
        elif SONARR_EVENT_TYPE == "ApplicationUpdate":
            telegram_sonarr.sonarr_update()

    if config.ntfy:
        if SONARR_EVENT_TYPE == "Test":
            ntfy_sonarr.sonarr_test()
        elif SONARR_EVENT_TYPE == "Grab":
            ntfy_sonarr.sonarr_grab()
        elif SONARR_EVENT_TYPE == "Download":
            ntfy_sonarr.sonarr_import()
        elif SONARR_EVENT_TYPE == "HealthIssue":
            ntfy_sonarr.sonarr_health()
        elif SONARR_EVENT_TYPE == "EpisodeFileDelete":
            ntfy_sonarr.sonarr_delete_episode()
        elif SONARR_EVENT_TYPE == "SeriesDelete":
            ntfy_sonarr.sonarr_delete_series()
        elif SONARR_EVENT_TYPE == "ApplicationUpdate":
            ntfy_sonarr.sonarr_update()


def prowlarr_send():
    """
    Sends prowlarr notifications to respective platforms
    """

    check_prowlarr_connection()
    if config.DISCORD:
        if PROWLARR_EVENT_TYPE == "Test":
            discord_prowlarr.prowlarr_test()
        elif PROWLARR_EVENT_TYPE == "HealthIssue":
            discord_prowlarr.prowlarr_health()
        elif PROWLARR_EVENT_TYPE == "ApplicationUpdate":
            discord_prowlarr.prowlarr_update()

    if config.SLACK:
        if PROWLARR_EVENT_TYPE == "Test":
            slack_prowlarr.prowlarr_test()
        elif PROWLARR_EVENT_TYPE == "HealthIssue":
            slack_prowlarr.prowlarr_health()
        elif PROWLARR_EVENT_TYPE == "ApplicationUpdate":
            slack_prowlarr.prowlarr_update()

    if config.PUSHOVER:
        if PROWLARR_EVENT_TYPE == "Test":
            pushover_prowlarr.prowlarr_test()
        elif PROWLARR_EVENT_TYPE == "HealthIssue":
            pushover_prowlarr.prowlarr_health()
        elif PROWLARR_EVENT_TYPE == "ApplicationUpdate":
            pushover_prowlarr.prowlarr_update()

    if config.TELEGRAM:
        if PROWLARR_EVENT_TYPE == "Test":
            telegram_prowlarr.prowlarr_test()
        elif PROWLARR_EVENT_TYPE == "HealthIssue":
            telegram_prowlarr.prowlarr_health()
        elif PROWLARR_EVENT_TYPE == "ApplicationUpdate":
            telegram_prowlarr.prowlarr_update()

    if config.ntfy:
        if PROWLARR_EVENT_TYPE == "Test":
            ntfy_prowlarr.prowlarr_test()
        elif PROWLARR_EVENT_TYPE == "HealthIssue":
            ntfy_prowlarr.prowlarr_health()
        elif PROWLARR_EVENT_TYPE == "ApplicationUpdate":
            ntfy_prowlarr.prowlarr_update()


if config.SONARR:
    if SONARR_EVENT_TYPE:
        sonarr_send()

if config.RADARR:
    if RADARR_EVENT_TYPE:
        radarr_send()

if config.PROWLARR:
    if PROWLARR_EVENT_TYPE:
        prowlarr_send()
