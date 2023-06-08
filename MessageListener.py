from logging import Logger
from pymongo import MongoClient
from TomTomApi import TomTomAPI
from telegraph import Telegraph
from origamibot import OrigamiBot, types
from origamibot.listener import Listener
from GetProfileImage import get_profile_image

from pytz import timezone
from datetime import datetime
from timezonefinder import TimezoneFinder
from math import floor, ceil

class MessageListener(Listener):
    def __init__(self, bot: OrigamiBot, database: MongoClient, logger: Logger, mapApi: TomTomAPI, timefinder: TimezoneFinder, bot_token: str, telegraph: Telegraph) -> None:
        self.bot = bot
        self.database = database
        self.logger = logger
        self.mapApi = mapApi
        self.timefinder = timefinder
        self.bot_token = bot_token
        self.telegraph = telegraph


    def on_message(self, message: types.Message) -> None:
        self.logger.debug(f"{message.from_user.username} send a {message.message_id} message with text: {message.text}")
        
        try:
            # Добавление нового пользователя в базу данных
            if self.database['users'].find_one({'username': message.from_user.username}) is None:
                
                _photo = get_profile_image(telegraph=self.telegraph,
                                        bot=self.bot,
                                        chat_id=message.chat.id,
                                        bot_token=self.bot_token,
                                        logger=self.logger,
                                        photo=None)

                self.database['users'].insert_one({'username': message.from_user.username,
                                                   'first_name': message.from_user.first_name,
                                                   'language_code': message.from_user.language_code,
                                                   'position': {'latitude': 0.0, 'longitude': 0.0},
                                                   'photo_link': None if _photo['photo_link'] is None else _photo['photo_link'],
                                                   'photo_size': None if _photo['photo_size'] is None else _photo['photo_size']})
                
                self.logger.info(f"new user: {message.from_user.username}")
                self.logger.debug(f"{message.from_user.username} was added to database")

            # Изменение профиля пользователя при отправке имени/изображения
            if self.database['logger'].find_one({'type': 'callback_query', 'data': 'back_to_profile', 'message_id': message.message_id-1}) is None:
                if self.database['logger'].find_one({'type': 'callback_query', 'data': 'update_profile_username', 'message_id': message.message_id-2}) is not None:

                    self.bot.delete_message(chat_id=message.chat.id,
                                            message_id=message.message_id)

                    self.bot.delete_message(chat_id=message.chat.id,
                                            message_id=message.message_id-1)

                    self.bot.delete_message(chat_id=message.chat.id,
                                            message_id=message.message_id-2)

                    self.database['users'].find_one_and_update({'username': message.from_user.username}, {'$set': {'first_name': message.text}})

                    self.bot.command_container.find_command('profile')[0](message=message)

                if self.database['logger'].find_one({'type': 'callback_query', 'data': 'update_profile_photo', 'message_id': message.message_id-2}) is not None:
                    _photo = get_profile_image(telegraph=self.telegraph,
                                            bot=self.bot,
                                            bot_token=self.bot_token,
                                            logger=self.logger,
                                            photo=message.photo[ceil(len(message.photo)/2)-1],
                                            chat_id = None)
                    
                    self.bot.delete_message(chat_id=message.chat.id,
                                            message_id=message.message_id)

                    self.bot.delete_message(chat_id=message.chat.id,
                                            message_id=message.message_id-1)

                    self.bot.delete_message(chat_id=message.chat.id,
                                            message_id=message.message_id-2)
                    
                    self.database['users'].find_one_and_update({'username': message.from_user.username}, {'$set': {'photo_link': None if _photo['photo_link'] is None else _photo['photo_link'],
                                                                                                                'photo_size': None if _photo['photo_size'] is None else _photo['photo_size']}})
                    
                    self.bot.command_container.find_command('profile')[0](message=message)

            if message.via_bot is not None and message.location is not None:
                try:
                    # Отображение информации о месте
                    place = self.mapApi.place_by_id(entityId=self.bot.updates[0].chosen_inline_result.result_id,
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
                        
                        time_at_place_now = datetime.now(timezone(self.timefinder.timezone_at(lng=result['position']['lon'], lat=result['position']['lat']))).time()
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
                    # Записывание в базу данных сообщение с картой
                    self.database['positions'].insert_one({'user_id': self.bot.updates[0].chosen_inline_result.result_id,
                                                           'username': message.from_user.username,
                                                           'chat_id': message.chat.id,
                                                           'message_id': message.message_id,
                                                           'inline_message_id': self.bot.updates[0].chosen_inline_result.inline_message_id})
                except Exception as e:
                    self.logger.error('[MessageListener.py] '+str(e))
        
        except Exception as e:
            self.logger.error('[MessageListener.py] '+str(e))


    def on_edited_message(self, message: types.Message) -> None:
        try:
            if message.location is not None:
                # Когда пользователь отправляет впервые свою геолокацию, ему показывается это сообщение
                if self.database['users'].find_one({'username': message.from_user.username})['position'] == {'latitude': 0.0, 'longitude': 0.0}:
                    self.bot.send_message(chat_id=message.chat.id, 
                                        text="Отлично! Теперь введите @ggeogeobot люди и вам покажутся другие пользователи")
                self.logger.debug(f"{message.from_user.username} in message {message.message_id} update location {message.location.latitude}, {message.location.longitude}")
                if message.via_bot is None:
                    # Изменение геопозиции в базе данных и отображение в сообщении с картой
                    self.database['users'].find_one_and_update({'username': message.from_user.username}, {'$set': 
                                                                                                            {'position': 
                                                                                                                {'latitude': message.location.latitude, 
                                                                                                                 'longitude': message.location.longitude}}})
                                                                                                                 
                    for position in self.database['positions'].find({'username': message.from_user.username}):
                        try:
                            self.bot.edit_message_live_location(latitude=message.location.latitude,
                                                                longitude=message.location.longitude,
                                                                chat_id=position['chat_id'],
                                                                message_id=position['message_id'],
                                                                inline_message_id=position['inline_message_id'])
                        except:
                            self.database['positions'].find_one_and_delete({'message_id': position['message_id']})
                
        except Exception as e:
            self.logger.error('[MessageListener.py] '+str(e))