import logging
from sys import stdout
from os import getenv
from time import sleep
from dotenv import load_dotenv
from timezonefinder import TimezoneFinder

import pymongo
from TomTomApi import TomTomAPI

from origamibot import OrigamiBot
from MessageListener import MessageListener
from BotCommands import BotCommands
from BotInlines import BotInlines
from BotCallbacks import BotCallbacks

from telegraph import Telegraph

if __name__ == '__main__':
    load_dotenv()
    token = getenv('BOT_TOKEN')
    token_map = getenv('TOMTOM')
    db_link = getenv('DB')

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(stream=stdout)
    handler.setFormatter(logging.Formatter(fmt='[%(asctime)s: %(levelname)s] %(message)s'))
    logger.addHandler(handler)

    bot = OrigamiBot(token)
    mapAPI = TomTomAPI(token_map)
    database = pymongo.MongoClient(db_link)['database-geobot']

    telegraph = Telegraph()
    telegraph.create_account(short_name='for_bot')

    timefinder = TimezoneFinder()

    bot.add_listener(MessageListener(bot=bot,
                                     database=database,
                                     logger=logger,
                                     mapApi=mapAPI,
                                     timefinder=timefinder,
                                     bot_token=token,
                                     telegraph=telegraph))
    
    bot.add_inline(BotInlines(bot=bot,
                              database=database,
                              logger=logger,
                              mapApi=mapAPI))
    
    bot.add_commands(BotCommands(bot=bot,
                                 database=database,
                                 logger=logger))
    
    bot.add_callback(BotCallbacks(bot=bot,
                                  database=database,
                                  logger=logger))

    bot.start()
    while True:
        sleep(1)