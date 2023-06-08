from logging import Logger
from pymongo import MongoClient
from TomTomApi import TomTomAPI
from origamibot import OrigamiBot, types


class BotInlines:
    def __init__(self, bot: OrigamiBot, database: MongoClient, logger: Logger, mapApi: TomTomAPI) -> None:
        self.bot = bot
        self.database = database
        self.logger = logger
        self.mapApi = mapApi


    def inline_handler(self, inline_query: types.InlineQuery) -> None:
        self.logger.debug(f"{inline_query.from_user.username} used {inline_query.query} inline query with {inline_query.from_user.language_code} language code")
        inlines = []
        # Отображение пользователей с помощью inline query
        if(inline_query.query.lower() == 'люди'):
            for user in self.database['users'].find():
                if user['username'] != inline_query.from_user.username and user['position'] != {'latitude': 0, 'longitude': 0}:
                    inlines.append(types.InlineQueryResultLocation(id=str(user['_id']),
                                                                   latitude=user['position']['latitude'],
                                                                   longitude=user['position']['longitude'],
                                                                   title=user['first_name'],
                                                                   live_period=86400,
                                                                   thumb_url=user['photo_link']))
        # Отображение мест с помощью inline query
        else:
            if inline_query.location is None:
                return None
            
            # Getting nearby places
            places = self.mapApi.nearby_search(lat=inline_query.location.latitude,
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
        
        self.bot.answer_inline_query(inline_query_id=inline_query.id,
                                     results=inlines)