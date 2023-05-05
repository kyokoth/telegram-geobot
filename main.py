from os import getenv
from time import sleep
from dotenv import load_dotenv
from hashlib import md5
from json import dumps

import pymongo
from tomtom_map import TomtomAPI

from origamibot import OrigamiBot, types
from origamibot.listener import Listener

class BotsCommands:
    def __init__(self, bot: OrigamiBot) -> None:
        self.bot = bot
    
    def start(self, message: types.Message) -> None:
        self.bot.send_message(message.chat.id, "Введите число!")

class BotsInlines:
    def __init__(self, bot: OrigamiBot) -> None:
        self.bot = bot

    def inline_handler(self, inline_query: types.InlineQuery) -> None:
        '''
        global results
        places = mapAPI.nearby_search(lat=inline_query.location.latitude,
                                      lon=inline_query.location.longitude, 
                                      lang='ru-RU',
                                      query=inline_query.query)
        
        if places == None: return None

        results = []

        for place in places['results']:
            for info_place in mapAPI.place_by_id(place['id'], language='ru-RU', mapcodes='Local', view='RU')['results']:
                results.append({
                    'id': place['id'],
                    'name': info_place['poi']['name'],
                    'phone': info_place['poi']['phone'] if 'phone' in info_place['poi'].keys() else None,
                    'address': info_place['address']['freeformAddress'],
                    'position': info_place['position'],
                    'entryMainPoint': info_place['entryPoints'][0]['position'],
                    'today_work_time': info_place['poi']['openingHours']['timeRanges'][0] if 'openingHours' in info_place['poi'].keys() else None
                })

        inlines = []

        for place in results:
            inlines.append(types.InlineQueryResultLocation(place['id'], place['entryMainPoint']['lat'], place['entryMainPoint']['lon'], place['name']))

        self.bot.answer_inline_query(inline_query.id, inlines, cache_time=1)
        '''
        #print(result)
        
        #with open('places.json', 'w', encoding='utf-8') as f:
        #    f.write(dumps(places, ensure_ascii=False, indent = 4))

        '''
        text = inline_query.query or 'echo'
        input_content = types.InputTextMessageContent(f'<b>{text}</b> - {user_data}', parse_mode='html')
        result_id: str = md5(text.encode()).hexdigest()

        item = types.InlineQueryResultArticle(
            id=result_id,
            title='hi',
            input_message_content=input_content,
            description='hi'
        )
        
        self.bot.answer_inline_query(inline_query_id=inline_query.id,
                                     results=[item],
                                     cache_time=1)
        '''

        inlines = []

        places = mapAPI.nearby_search(inline_query.location.latitude, inline_query.location.longitude, 'ru-RU', inline_query.query.capitalize())

        if places == None:
            return None

        for place in places['results']:
            inlines.append(types.InlineQueryResultLocation(place['id'], place['position']['lat'], place['position']['lon'], place['poi']['name']))

        self.bot.answer_inline_query(inline_query.id, inlines)

class MessageListener(Listener):
    def __init__(self, bot) -> None:
        self.bot = bot
    
    def on_message(self, message: types.Message) -> None:
        if message.via_bot != None and message.location != None:
            #print(self.bot.updates[0].chosen_inline_result)
            #print(self.bot.updates[0].chosen_inline_result.result_id)
            #print(mapAPI.reverse_geocode(message.location.latitude, message.location.longitude))
            print(mapAPI.place_by_id(self.bot.updates[0].chosen_inline_result.result_id, language='ru-RU', mapcodes='Local', view='RU'))
            

if __name__ == '__main__':
    load_dotenv()
    token = getenv('TOKEN')
    token_map = getenv('TOMTOM')
    token_map_details = getenv('GEOAPIFY_PDA')

    bot = OrigamiBot(token)
    mapAPI = TomtomAPI(token_map, token_map_details)
    database = pymongo.MongoClient("mongodb://localhost:27017/")['geobot']

    user_data = ''

    bot.add_listener(MessageListener(bot))
    bot.add_inline(BotsInlines(bot))
    bot.add_commands(BotsCommands(bot))

    bot.start()
    while True:
        sleep(1)