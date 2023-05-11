from os import getenv
from time import sleep
from dotenv import load_dotenv
from pytz import timezone
from datetime import datetime
from timezonefinder import TimezoneFinder
from math import floor

import pymongo
from tomtom_map import TomtomAPI

from origamibot import OrigamiBot, types
from origamibot.listener import Listener

class BotsCommands:
    def __init__(self, bot: OrigamiBot) -> None:
        self.bot = bot
    
    def start(self, message: types.Message) -> None:
        self.bot.send_message(message.chat.id, "Привет, я Геобот! Чтобы начать работу введите @ggeogeobot и любое желаемое место, например:\n@ggeogeobot кафе")

class BotsInlines:
    def __init__(self, bot: OrigamiBot) -> None:
        self.bot = bot

    def inline_handler(self, inline_query: types.InlineQuery) -> None:
        if inline_query.location == None:
            return None
        
        inlines = []

        places = mapAPI.nearby_search(inline_query.location.latitude, inline_query.location.longitude, 'ru-RU', inline_query.query.capitalize())

        if places == None:
            return None

        for place in places['results']:
            inlines.append(types.InlineQueryResultLocation(place['id'], place['position']['lat'], place['position']['lon'], f"{place['poi']['name']} в {round(place['dist'])} метрах от вас"))#, input_message_content=types.InputTextMessageContent(f"В {round(place['dist'])} метрах от вас")))

        self.bot.answer_inline_query(inline_query.id, inlines)

class MessageListener(Listener):
    def __init__(self, bot) -> None:
        self.bot = bot
    
    def on_message(self, message: types.Message) -> None:
        if message.via_bot != None and message.location != None:
            place = mapAPI.place_by_id(self.bot.updates[0].chosen_inline_result.result_id, language='ru-RU', mapcodes='Local', view='RU')['results'][0]

            result = {
                'id': place['id'],
                'name': place['poi']['name'],
                'phone': place['poi']['phone'] if 'phone' in place['poi'].keys() else None,
                'address': place['address']['freeformAddress'],
                'position': place['position'],
                'entryMainPoint': place['entryPoints'][0]['position'],
                'today_work_time': place['poi']['openingHours']['timeRanges'][0] if 'openingHours' in place['poi'].keys() else None
            }

            text = ""

            text += f"{result['name']}\n"
            text += f"{result['phone']}\n" if result['phone'] != None else ''

            if result['today_work_time'] != None:
                text += f"Время работы: {''.join(('{:>02}'.format(str(result['today_work_time']['startTime']['hour'])), ':', '{:>02}'.format(str(result['today_work_time']['startTime']['minute'])), ' - ', '{:>02}'.format(str(result['today_work_time']['endTime']['hour'])), ':', '{:>02}'.format(str(result['today_work_time']['endTime']['minute']))))}\n"
                
                time_at_place_now = datetime.now(timezone(timefinder.timezone_at(lng=result['position']['lon'], lat=result['position']['lat']))).time()
                time_start = datetime.strptime(''.join((str(result['today_work_time']['startTime']['hour']), ':', str(result['today_work_time']['startTime']['minute']))), '%H:%M').time()
                time_end = datetime.strptime(''.join((str(result['today_work_time']['endTime']['hour']), ':', str(result['today_work_time']['endTime']['minute']))), '%H:%M').time()

                if time_at_place_now.hour == time_start.hour:
                    if time_at_place_now.minute == time_start.minute:
                        text += f'Заведение недавно открылось'
                    elif time_at_place_now.minute < time_start.minute:
                        text += f'До открытия осталось {floor((time_start.minute*60 - (time_at_place_now.minute*60 + time_at_place_now.second)) / 60)} минут\n'
                    else:
                        text += f'До открытия осталось {floor(((time_at_place_now.minute*60 + time_at_place_now.second) - time_start.minute*60) / 60)} минут\n'
                
                elif time_at_place_now.hour == time_end.hour:
                    if time_at_place_now.minute == time_end.minute:
                        text += f'Заведение недавно закрылось'
                    elif time_at_place_now.minute < time_end.minute:
                        text += f'До закрытия осталось {floor((time_end.minute*60 - (time_at_place_now.minute*60 + time_at_place_now.second)) / 60)} минут\n'
                    else:
                        text += f'До закрытия осталось {floor(((time_at_place_now.minute*60 + time_at_place_now.second) - time_end.minute*60) / 60)} минут\n'
                
                elif time_at_place_now.hour < time_start.hour:
                    text += f'До открытия осталось '
                    hours = floor(((time_start.hour*3600 + time_start.minute*60) - (time_at_place_now.hour*3600 + time_at_place_now.minute*60 + time_at_place_now.second)) / 3600)
                    if time_at_place_now.minute == time_start.minute:
                        text += f'{hours} часа'
                    elif time_at_place_now.minute < time_start.minute:
                        text += f'{hours} часа и {floor((time_start.minute*60 - (time_at_place_now.minute*60 + time_at_place_now.second)) / 60)} минут'
                    else:
                        text += f'{hours} часа и {floor(((time_at_place_now.minute*60 + time_at_place_now.second) - time_start.minute*60) / 60)} минут'
                    text += '\n'

                elif time_at_place_now.hour < time_end.hour:
                    text += f'До закрытия осталось '
                    hours = floor(((time_end.hour*3600 + time_end.minute*60) - (time_at_place_now.hour*3600 + time_at_place_now.minute*60 + time_at_place_now.second)) / 3600)
                    if time_at_place_now.minute == time_end.minute:
                        text += f'{hours} часа'
                    elif time_at_place_now.minute < time_end.minute:
                        text += f'{hours} часа и {floor((time_end.minute*60 - (time_at_place_now.minute*60 + time_at_place_now.second)) / 60)} минут'
                    else:
                        text += f'{hours} часа и {floor(((time_at_place_now.minute*60 + time_at_place_now.second) - time_end.minute*60) / 60)} минут'
                    text += '\n'

            text += f"Адрес: {result['address']}"
            
            bot.send_message(chat_id=message.chat.id,
                             text=text)
            

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

    timefinder = TimezoneFinder()

    bot.start()
    while True:
        sleep(1)