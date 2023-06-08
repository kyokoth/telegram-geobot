from logging import Logger
from pymongo import MongoClient
from origamibot import OrigamiBot, types

class BotCommands:
    def __init__(self, bot: OrigamiBot, database: MongoClient, logger: Logger) -> None:
        self.bot = bot
        self.database = database
        self.logger = logger


    # Отправка начального сообщения с инструкцией при использовании команды /start
    def start(self, message: types.Message) -> None:
        try:
            self.logger.debug(f"{message.from_user.username} used /start command with {message.from_user.language_code} language code")

            match message.from_user.language_code:
                case 'ru':
                    _instruction_message_text = "Привет, я Геобот! Чтобы начать работу введите @ggeogeobot и любое желаемое место, например:\n@ggeogeobot кафе\n\nВ нашем боте есть функция отслеживания пользователей! Чтобы ей воспользоваться, пожалуйста, отправьте трансляцию своей геопозиции! \n\nВсе функции бота работают только на телефоне! Гайд находится здесь: \nhttps://telegra.ph/Gajd-na-to-kak-otpravit-translyaciyu-svoej-geopozicii-05-25"
                case _:
                    _instruction_message_text = "Hello, I'm Geobot! To get started, enter @ggeogeobot and any location you want, for example:\n@ggeogeobot cafe\n\nOur bot has a user tracking feature! To use it, please send a broadcast of your location! \n\nAll bot functions work only on the phone! The guide is here: \nhttps://telegra.ph/Guide-on-how-to-send-a-broadcast-of-your-location-06-07"

            self.bot.send_message(message.chat.id, _instruction_message_text)

        except Exception as e:
            self.logger.error('[BotCommands.py] '+str(e))


    # Получение профиля пользователя через команду /profile
    def profile(self, message: types.Message) -> None:
        try:
            self.logger.debug(f"{message.from_user.username} used /profile command with {message.from_user.language_code} language code")

            _user = self.database['users'].find_one({'username': message.from_user.username})

            match message.from_user.language_code:
                case 'ru':
                    _caption = f"<b>Имя: </b>{_user['first_name']}"
                    _update_profile_photo_text = 'Обновить фотографию'
                    _update_profile_username_text = 'Обновить имя'
                case _:
                    _caption = f"<b>Name: </b>{_user['first_name']}"
                    _update_profile_photo_text = 'Update photo'
                    _update_profile_username_text = 'Update name'

            _update_profile_photo_button = types.InlineKeyboardButton(text=_update_profile_photo_text,
                                                                      callback_data='update_profile_photo')

            _update_profile_username_button = types.InlineKeyboardButton(text=_update_profile_username_text,
                                                                         callback_data='update_profile_username')

            self.bot.send_photo(chat_id=message.chat.id,
                                photo=_user['photo_link'],
                                caption=_caption,
                                parse_mode='HTML',
                                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[_update_profile_photo_button], [_update_profile_username_button]]))

        except Exception as e:
            self.logger.error('[BotCommands.py] '+str(e))


    # Помощь через команду /help
    def help(self, message: types.Message) -> None:
        try:
            self.logger.debug(f"{message.from_user.username} used /help command with {message.from_user.language_code} language code")

            match message.from_user.language_code:
                case 'ru':
                    _help_message_text = '/profile - показывает профиль пользователя, там же можно изменить его\n\n@ggeogeobot *какое-то место* - показывает рядом находящиеся места\nПример: @ggeogeobot кафе\n\n@ggeogeobot люди - показывает пользователей, которые делятся своей геолокацией\nЧтобы поделиться своей геопозицией, воспользуйтесь этим гайдом: <a href="https://telegra.ph/Gajd-na-to-kak-otpravit-translyaciyu-svoej-geopozicii-05-25">Гайд на отправку трансляции геопозиции</a>\n\n<a href="tg://user?id=123456789">Связь с автором: @ybbbno</a>'
                case _:
                    _help_message_text = '/profile - shows the users profile, you can also change it there\n\n@ggeogeobot *some place* - shows nearby places\nExample: @ggeogeobot cafe\n\n@ggeogeobot people - shows users who share their geolocation\nTo share your location, use this guide: <a href="https://telegra.ph/Guide-on-how-to-send-a-broadcast-of-your-location-06-07">Guide to send location broadcast</a>\n\nCommunication with the author: @ybbbno'

            self.bot.send_message(chat_id=message.chat.id,
                                text=_help_message_text,
                                parse_mode='HTML')
        except Exception as e:
            self.logger.error('[BotCommands.py] '+str(e))


    # Остановка работы бота с помощью команды /stop
    def stop(self, message: types.Message) -> None:
        try:
            self.logger.debug(f"{message.from_user.username} used /stop command with {message.from_user.language_code} language code")

            if (message.from_user.username == 'ybbbno'):
                self.logger.info('bot is stopped')
                match message.from_user.language_code:
                    case 'ru':
                        _stop_message_text = 'Бот остановлен'
                    case _:
                        _stop_message_text = 'Bot is stopped'

                self.bot.send_message(chat_id=message.chat.id,
                                      text=_stop_message_text)

                self.bot.stop()

        except Exception as e:
            self.logger.error('[BotCommands.py] '+str(e))