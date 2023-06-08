from requests import post, get

from origamibot import OrigamiBot, types
from telegraph import Telegraph
from logging import Logger
from io import BytesIO

# Получение изображения из базы данных telegram и загрузка их в telegraph
def get_profile_image(telegraph: Telegraph, bot: OrigamiBot, chat_id: str | None, bot_token: str, logger: Logger, photo: types.PhotoSize | None):
    try:
        if chat_id is not None:
            _photo = bot.get_user_profile_photos(user_id = chat_id,
                                                limit = 1).photos[0][0]
        else:
            _photo = photo
    
        _headers = {"accept": "application/json",
                    "User-Agent": "Telegram Bot SDK - (https://github.com/irazasyed/telegram-bot-sdk)",
                    "content-type": "application/json"}

        _token = bot_token.replace(':','%3A')

        _file = post(f"https://api.telegram.org/bot{_token}/getFile",
                       json={"file_id": _photo.file_id},
                       headers=_headers).json()

        if _file['ok']:
            _file = get(f"https://api.telegram.org/file/bot{_token}/{_file['result']['file_path']}").content

            return {
                'photo_link': f"telegra.ph{telegraph.upload_file(BytesIO(_file))[0]['src']}",
                'photo_size': {'width': _photo.width,
                               'height': _photo.height}
            }
        else:
            logger.error('[GetProfileImage.py] '+_file.description)
            return None

    except Exception as e:
        logger.error('[GetProfileImage.py] '+str(e))
        return None