from os import getenv
from time import sleep
from dotenv import load_dotenv

from origamibot import OrigamiBot
from origamibot.listener import Listener
from origamibot.types import Message, InlineQuery, InputMessageContent, InlineQueryResultArticle, InlineQueryResultLocation

class BotsCommands:
    def __init__(self, bot: OrigamiBot) -> None:
        self.bot = bot
    
    def hello(self, message: Message) -> None:
        self.bot.send_message(message.chat.id, f'Привет {message.chat.first_name}')

class BotsInlines:
    def __init__(self, bot: OrigamiBot) -> None:
        self.bot = bot

    def on_inline(self, inline: InlineQuery) -> None:
        print(inline.location.latitude, inline.location.longitude)
        #self.bot.answer_inline_query(inline.id, [InlineQueryResultLocation('0', inline.location.latitude, inline.location.longitude, 'hi')])
        #if (inline.location != None):

if __name__ == '__main__':
    load_dotenv()
    token = getenv('TOKEN')

    bot = OrigamiBot(token)

    bot.add_inline(BotsInlines(bot))
    bot.add_commands(BotsCommands(bot))

    bot.start()
    while True:
        sleep(1)