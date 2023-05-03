from os import getenv
from time import sleep
from dotenv import load_dotenv

from tomtom_map import TomtomAPI

from origamibot import OrigamiBot
from origamibot.listener import Listener
from origamibot.types import Message, InlineQuery, InputMessageContent, InlineQueryResultArticle, InlineQueryResultLocation

class BotsCommands:
    def __init__(self, bot: OrigamiBot) -> None:
        self.bot = bot
    
    def hello(self, message: Message) -> None:
        print(message)
        self.bot.send_message(message.chat.id, f'Привет {message.chat.first_name}')

class BotsInlines:
    def __init__(self, bot: OrigamiBot) -> None:
        self.bot = bot

    def on_inline(self, inline: InlineQuery) -> None:
        inlines = []

        places = mapAPI.nearby_search(inline.location.latitude, inline.location.longitude, "ru-RU", inline.query)

        if places == None:
            return None

        for place in places["results"]:
            inlines.append(InlineQueryResultLocation(place["id"], place["position"]["lat"], place["position"]["lon"], place["poi"]["name"]))

        self.bot.answer_inline_query(inline.id, inlines)

if __name__ == '__main__':
    load_dotenv()
    token = getenv('TOKEN')
    token_map = getenv('TOKENMAP')

    bot = OrigamiBot(token)
    mapAPI = TomtomAPI(token_map)

    bot.add_inline(BotsInlines(bot))
    bot.add_commands(BotsCommands(bot))

    bot.start()
    while True:
        sleep(1)