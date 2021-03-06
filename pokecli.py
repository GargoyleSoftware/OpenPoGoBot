#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
pgoapi - Pokemon Go API
Copyright (c) 2016 tjado <https://github.com/tejado>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE
OR OTHER DEALINGS IN THE SOFTWARE.

Author: tjado <https://github.com/tejado>
"""

from __future__ import print_function
from getpass import getpass
# pylint: disable=redefined-builtin
from builtins import input
import json
import argparse
import ssl
import logging
import sys

from pokemongo_bot import logger
from pokemongo_bot import PokemonGoBot
import colorama

# Disable HTTPS certificate verification
if sys.version_info >= (2, 7, 9):
    # pylint: disable=protected-access
    ssl._create_default_https_context = ssl._create_unverified_context  # type: ignore


def init_config():
    default_config = {
        "mode": "all",
        "walk": 2.5,
        "cp": 100,
        "pokemon_potential": 0.40,
        "max_steps": 50,
        "distance_unit": "km",
        "ign_init_trans": "",
        "exclude_plugins": "",
        "recycle_items": False,
        "item_filter": {
            1: 100,
            101: 0,
            102: 0,
            103: 10,
            104: 10,
            201: 10,
            202: 10
        },
        "location_cache": False,
        "initial_transfer": False,
        "debug": False,
        "test": False
    }

    parser = argparse.ArgumentParser()

    # Read passed in Arguments
    parser.add_argument(
        "-j",
        "--config-json",
        help="Load a config JSON file. Any arguments specified on command line override those specified in the file.",
        type=str,
        dest="json")
    parser.add_argument(
        "-a",
        "--auth-service",
        help="Auth Service ('ptc' or 'google')",
        dest="auth_service")
    parser.add_argument("-u", "--username", help="Username", dest="username")
    parser.add_argument("-p", "--password", help="Password", dest="password")
    parser.add_argument("-l", "--location", help="Location (Address or 'xx.yyyy,zz.ttttt')", dest="location")
    parser.add_argument(
        "-lc",
        "--location-cache",
        help="Bot will start at last known location",
        action="store_true",
        dest="location_cache",
        default=None)
    parser.add_argument(
        "-m",
        "--mode",
        help="Set farming Mode for the bot ('all', 'poke', 'farm')",
        type=str,
        dest="mode")
    parser.add_argument(
        "-w",
        "--walk",
        help="Walk instead of teleport with given speed (meters per second max 4.16 because of walking end on 15km/h)",
        type=float,
        dest="walk")
    parser.add_argument(
        "-du",
        "--distance-unit",
        help="Set the unit to display distance in (e.g, km for kilometers, mi for miles, ft for feet)",
        type=str,
        dest="distance_unit")
    parser.add_argument(
        "-ms",
        "--max-steps",
        help="Set the steps around your initial location (DEFAULT 5 mean 25 cells around your location)",
        type=int,
        dest="max_steps")
    parser.add_argument(
        "-cp",
        "--combat-power",
        "--combat-points",
        help="Transfer Pokemon that have CP less than this value (default 100)",
        type=int,
        dest="cp")
    parser.add_argument(
        "-it",
        "--initial-transfer",
        help="Transfer all pokemon with same ID on bot start, except pokemon with highest CP. Respects --cp",
        action="store_true",
        dest="initial_transfer",
        default=None)
    parser.add_argument(
        "-ri",
        "--recycle-items",
        help="Recycle unneeded items automatically",
        action="store_true",
        dest="recycle_items",
        default=None)
    parser.add_argument(
        "-iv",
        "--pokemon-potential",
        help="Set the ratio for the IV values to transfer (DEFAULT 0.4 eg. 0.4 will transfer a pokemon with IV 0.3)",
        type=float,
        dest="pokemon_potential")
    parser.add_argument(
        "-ign",
        "--ign-init-trans",
        help="Pass a list of pokemon to ignore during initial transfer (e.g. 017,049,001)",
        type=str,
        dest="ign_init_trans")
    parser.add_argument(
        "-k",
        "--gmapkey",
        help="Set Google Maps API KEY",
        type=str,
        dest="gmapkey")
    parser.add_argument(
        "-gd",
        "--google-directions",
        help="Bot will use directions from google maps API to navigate",
        action="store_true",
        dest="google_directions",
        default=None)
    parser.add_argument(
        "-d",
        "--debug",
        help="Debug Mode",
        action="store_true",
        dest="debug",
        default=None)
    parser.add_argument(
        "-t",
        "--test",
        help="Only parse the specified location",
        action="store_true",
        dest="test",
        default=None)

    parser.add_argument(
        "-ep",
        "--exclude-plugins",
        help="Pass a list of plugins to exclude from the loading process (e.g, logger,web).",
        type=str,
        dest="exclude_plugins")

    config = parser.parse_args()

    if config.json:
        try:
            # attempt to load values from JSON, overwriting any existing values
            loaded_config = {}
            with open(config.json) as data:
                loaded_config.update(json.load(data))
        except ValueError:
            logging.error("Error loading %s", config.json)
            return None
        for key in loaded_config:
            if config.__dict__.get(key) is None:
                config.__dict__[key] = loaded_config.get(key)

    for key in default_config:
        if config.__dict__.get(key) is None and default_config.get(key) is not None:
            config.__dict__[key] = default_config.get(key)

    config.exclude_plugins = config.exclude_plugins.split(",")

    print(config.__dict__)

    if config.auth_service not in ['ptc', 'google']:
        logging.error("Invalid Auth service specified! ('ptc' or 'google')")
        return None

    if config.location is None and config.location_cache is None:
        parser.error("Needs either --use-location-cache or --location.")
        return None

    if config.username is None:
        config.username = input("Username: ")
    if config.password is None:
        config.password = getpass("Password: ")

    return config


def main():
    # log settings
    # log format
    # logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(module)10s] [%(levelname)5s] %(message)s')

    colorama.init()

    config = init_config()
    if not config:
        return

    logger.log('[x] PokemonGO Bot v1.0', 'green')
    logger.log('[x] Configuration initialized', 'yellow')

    try:
        bot = PokemonGoBot(config)
        bot.start()

        logger.log('[x] Starting PokemonGo Bot....', 'green')

        while True:
            bot.take_step()

    except KeyboardInterrupt:
        logger.log('[x] Exiting PokemonGo Bot', 'red')


if __name__ == '__main__':
    main()
