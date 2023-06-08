from logging import Logger
from pymongo import MongoClient
from origamibot import OrigamiBot, types
from langdetect import detect

class BotCallbacks:
    def __init__(self, bot: OrigamiBot, database: MongoClient, logger: Logger) -> None:
        self.bot = bot
        self.database = database
        self.logger = logger


    def callback_handler(self, callback_query: types.CallbackQuery):
        try:
            # Логирование данных
            self.logger.debug(f"{callback_query.from_user.username} used {callback_query.data} callback query with {callback_query.from_user.language_code} language code")
            self.database['logger'].insert_one({'type': 'callback_query',
                                                'callback_query_id': callback_query.id,
                                                'message_id': callback_query.message.message_id,
                                                'chat_id': callback_query.message.chat.id,
                                                'message_date': callback_query.message.date,
                                                'username': callback_query.from_user.username,
                                                'language_code': callback_query.from_user.language_code,
                                                'data': callback_query.data})
            
            # Действия при нажатии определённой кнопки в сообщении
            match callback_query.data:
                case 'update_profile_username':

                    match callback_query.from_user.language_code:
                        case 'ru':
                            _update_profile_username_text = 'Отправьте сообщение с новым именем'
                            _back_to_profile_text = 'Назад'
                        case _:
                            _update_profile_username_text = 'Send a message with a new name'
                            _back_to_profile_text = 'Back'

                    _back_to_profile_button = types.InlineKeyboardButton(text=_back_to_profile_text,
                                                                         callback_data='back_to_profile')

                    self.bot.send_message(chat_id=callback_query.message.chat.id,
                                          text=_update_profile_username_text,
                                          reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[_back_to_profile_button]]))
                
                case 'update_profile_photo':

                    match callback_query.from_user.language_code:
                        case 'ru':
                            _update_profile_photo_text = 'Отправьте новое фото'
                            _back_to_profile_text = 'Назад'
                        case _:
                            _update_profile_photo_text = 'Send a new photo'
                            _back_to_profile_text = 'Back'

                    _back_to_profile_button = types.InlineKeyboardButton(text=_back_to_profile_text,
                                                                         callback_data='back_to_profile')

                    self.bot.send_message(chat_id=callback_query.message.chat.id,
                                          text=_update_profile_photo_text,
                                          reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[_back_to_profile_button]]))

                case 'back_to_profile':
                    _message = types.Message(message_id=callback_query.message.message_id,
                                             date=callback_query.message.date,
                                             chat=callback_query.message.chat,
                                             from_user=types.User(id=callback_query.message.chat.id,
                                                                  is_bot=False,
                                                                  first_name=callback_query.message.chat.first_name,
                                                                  username=callback_query.message.chat.username,
                                                                  is_premium=False,
                                                                  language_code=detect(callback_query.message.text)),
                                             text=callback_query.message.text,
                                             reply_markup=callback_query.message.reply_markup)
                    
                    self.bot.delete_message(chat_id=callback_query.message.chat.id,
                                            message_id=callback_query.message.message_id)

                    self.bot.delete_message(chat_id=callback_query.message.chat.id,
                                            message_id=callback_query.message.message_id-1)
                    
                    self.bot.command_container.find_command('profile')[0](message=_message)

        except Exception as e:
            self.logger.error('[BotCallbacks.py] '+str(e))