from asyncio import get_event_loop as loop
from asyncpg import create_pool as pool
from datetime import datetime
from discord import Forbidden, HTTPException, Intents, TextChannel
from discord.ext.commands import Bot, has_permissions
from json import load
from logging import basicConfig

intents = Intents.default()
intents.members = True

with open("confidential") as file:
    confidential = load(file)

bot = Bot(command_prefix=confidential["prefixes"], intents=intents)
bot.pool = loop().run_until_complete(pool(database=confidential["database_name"],
                                          user=confidential["database_user"],
                                          password=confidential["database_password"]))


@bot.event
async def on_ready():
    print(f"Unnamed StatBot v1.0\n\tMade by Rocky and KLK\n\nLogging in as {bot.user.name}")


@bot.command(help="""
- Reloads a cog.
- This bot has 2 cogs: `stats` and `analyze`.
- Reloading `stats` cog will force update the database with all the messages that are currently in cache.
- Reloading `analyze` does nothing.
""")
@has_permissions(administrator=True)
async def reload(ctx, cog_name: str = None):
    bot.reload_extension(f"{cog_name}")
    await ctx.send("Cog Reloaded")


async def _get_last_message():
    """Gets the last message stored in the database"""
    async with bot.pool.acquire() as con:
        data = await con.fetchval("SELECT created_at from chats ORDER BY created_at DESC LIMIT 1")

        if data is None:  # for first time ever launch
            return

        await _update_missed_messages(con, data)


async def _update_missed_messages(con, timestamp: datetime):
    """Updates the database with all the messages sent while the bot was offline"""
    await bot.wait_until_ready()  # gives time for the bot cache to be populated by the guilds

    missed_messages = []
    for guild in bot.guilds:
        for channel in guild.channels:
            if not isinstance(channel, TextChannel):  # ignore Voice and Category channels
                continue

            try:
                async for message in channel.history(limit=None, before=datetime.utcnow(), after=timestamp):

                    if message.author == bot.user or message.author.bot:
                        continue  # ignores messages by self or other bots
                    missed_messages.append((message.author.id, message.channel.id, message.created_at))

            except Forbidden or HTTPException:  # ignores if the bot does not have read/read history permissions
                pass
    if missed_messages:
        print(f"Inserting {len(missed_messages)} messages that were missed.")
        await con.copy_records_to_table('chats', records=missed_messages)

basicConfig()
bot.loop.create_task(_get_last_message())
bot.load_extension("stats")
bot.load_extension("analyze")
bot.run(confidential["token"])
