import requests
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
        self.bot.send_message(message.chat.id, "Привет, я Геобот! Чтобы начать работу введите @ggeogeobot и любое желаемое место, например:\n@ggeogeobot кафе\n\nВ нашем боте есть функция отслеживания пользователей! Чтобы ей воспользоваться, пожалуйста, отправьте трансляцию своей геопозиции! \n\nВсе функции бота работают только на телефоне! Гайд находится здесь: \nhttps://telegra.ph/Gajd-na-to-kak-otpravit-translyaciyu-svoej-geopozicii-05-25")
    
    def stop(self, message: types.Message) -> None:
        if (message.from_user.username == 'ybbbno'):
            self.bot.send_message(message.chat.id, 'Бот остановлен')
            self.bot.stop()

class BotsInlines:
    def __init__(self, bot: OrigamiBot) -> None:
        self.bot = bot

    def inline_handler(self, inline_query: types.InlineQuery) -> None:
        inlines = []
        if(inline_query.query.lower() == 'люди'):
            for user in database['users'].find():
                if user['username'] != inline_query.from_user.username:
                    inlines.append(types.InlineQueryResultLocation(id=str(user['_id']),
                                                                latitude=user['position']['latitude'],
                                                                longitude=user['position']['longitude'],
                                                                title=user['username'],
                                                                live_period=86400,
                                                                thumb_url=user['photo_link']))
            
        else:
            if inline_query.location is None:
                return None
            
            # Getting nearby places
            places = mapAPI.nearby_search(lat=inline_query.location.latitude,
                                          lon=inline_query.location.longitude,
                                          lang='ru-RU',
                                          query=inline_query.query.capitalize())

            if places is None:
                return None
            
            for place in places['results']:
                inlines.append(types.InlineQueryResultLocation(id=place['id'],
                                                               latitude=place['position']['lat'],
                                                               longitude=place['position']['lon'],
                                                               title=f"{place['poi']['name']} в {round(place['dist'])} метрах от вас"))
        
        # Sending the user an inline query with nearby places or users
        self.bot.answer_inline_query(inline_query_id=inline_query.id,
                                     results=inlines)

class MessageListener(Listener):
    def __init__(self, bot) -> None:
        self.bot = bot
    
    def on_message(self, message: types.Message) -> None:
        
        # Inserting a new user into the database
        if database['users'].find_one({'username': message.from_user.username}) is None:
            _photo = self.bot.get_user_profile_photos(user_id = message.chat.id, limit = 1).photos[0][0]

            _headers = {"accept": "application/json",
                       "User-Agent": "Telegram Bot SDK - (https://github.com/irazasyed/telegram-bot-sdk)",
                       "content-type": "application/json"}

            _token = token.replace(':',f'%{token[9]}{token[11]}')
            
            getFile = requests.post(f"https://api.telegram.org/bot{_token}/getFile",
                         json={"file_id": _photo.file_id}, headers=_headers).json()

            database['users'].insert_one({'username': message.from_user.username,
                                          'first_name': message.from_user.first_name,
                                          'language_code': message.from_user.language_code,
                                          'position': {'latitude': 0.0, 'longitude': 0.0},
                                          'photo_link': f"https://api.telegram.org/bot{_token}/{getFile['result']['file_path']}",
                                          'photo_size': {'width': _photo.width, 'height': _photo.height}})

        if message.via_bot is not None and message.location is not None:
            try:
                place = mapAPI.place_by_id(entityId=self.bot.updates[0].chosen_inline_result.result_id,
                                        language='ru-RU',
                                        mapcodes='Local',
                                        view='RU')['results'][0]

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

                if result['today_work_time'] is not None:
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
                
                self.bot.send_message(chat_id=message.chat.id,
                                      text=text)
            except IndexError:
                database['positions'].insert_one({'user_id': self.bot.updates[0].chosen_inline_result.result_id,
                                                  'chat_id': message.chat.id,
                                                  'message_id': message.message_id,
                                                  'inline_message_id': self.bot.updates[0].chosen_inline_result.inline_message_id})
    
    def on_edited_message(self, message: types.Message):
        
        if message.location is not None and message.via_bot is None and database['users'].find_one({'username': message.from_user.username}) is not None:
            if database['users'].find_one({'username': message.from_user.username})['position'] == {'latitude': 0.0, 'longitude': 0.0}:
                self.bot.send_message(chat_id=message.chat.id, 
                                      text="Отлично! Теперь введите @ggeogeobot люди и вам покажутся другие пользователи")
            database['users'].find_one_and_update({'username': message.from_user.username}, {'$set': 
                                                                                             {'position': 
                                                                                              {'latitude': message.location.latitude, 
                                                                                               'longitude': message.location.longitude}}})
            for position in database['positions'].find({'user_id': database['users'].find_one({'username': message.from_user.username})['_id']}):
                if self.bot.edit_message_live_location(latitude=message.location.latitude,
                                                       longitude=message.location.longitude,
                                                       chat_id=position['chat_id'],
                                                       message_id=position['message_id'],
                                                       inline_message_id=position['inline_message_id']) == True:
                    database['positions'].find_one_and_delete({'message_id': position['message_id']})

if __name__ == '__main__':
    load_dotenv()
    token = getenv('TOKEN')
    token_map = getenv('TOMTOM')
    db_link = getenv('DB')

    bot = OrigamiBot(token)
    mapAPI = TomtomAPI(token_map)
    database = pymongo.MongoClient(db_link)['database-geobot']

    user_data = ''

    bot.add_listener(MessageListener(bot))
    bot.add_inline(BotsInlines(bot))
    bot.add_commands(BotsCommands(bot))

    timefinder = TimezoneFinder()

    bot.start()
    while True:
        sleep(1)