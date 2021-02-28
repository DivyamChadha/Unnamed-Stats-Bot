from asyncio import get_event_loop as loop
from asyncpg import create_pool as pool
from discord import Intents
from discord.ext.commands import Bot
from json import load
from logging import basicConfig

"""
install these libraries:

1) discord.py : pip install -U discord.py
2) asyncpg : pip install asyncpg
3) discord.ext.menus : pip install -U git+https://github.com/Rapptz/discord-ext-menus  (is installed through git)

"""
intents = Intents.default()
intents.members = True

with open("confidential") as file:
    data = load(file)

bot = Bot(command_prefix=data["prefixes"], intents=intents)
bot.pool = loop().run_until_complete(pool(database=data["database_name"],
                                          user=data["database_user"],
                                          password=data["database_password"]))


@bot.event
async def on_ready():
    print(f"Unnamed StatBot v1.0\n\tMade by Rocky and KLK\n\nLogging in as {bot.user.name}")

basicConfig()
bot.load_extension("stats")
bot.load_extension("analyze")
bot.load_extension("roledrilldown")
bot.run(data["token"])
