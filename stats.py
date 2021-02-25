from asyncio import sleep
from asyncpg import DuplicateColumnError, UndefinedColumnError
from datetime import datetime
from discord.ext import commands
from discord.ext.tasks import loop

# sql syntax to create the following tables beforehand
"""
CREATE TABLE chats
(
    userid numeric NOT NULL,
    PRIMARY KEY (userid)
)

WITH (
    autovacuum_enabled = TRUE
);
"""

"""
CREATE TABLE chats_setting
(
    userid numeric NOT NULL,
    channel_id numeric NOT NULL
);
"""


class chats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        bot.loop.create_task(self.setup())

    async def setup(self):
        # a function to run on init
        # passing the con instead of letting each fn get their own so that they are run in an sequential manner
        async with self.bot.pool.acquire() as con:
            await self.add_channels(con)
            await self.get_last_message(con)

    async def add_channels(self, con):
        await sleep(5)
        # loops through all the channels in all the guild and adds them to the table if they are not already in it
        for guild in self.bot.guilds:
            for channel in guild.channels:
                await self.add_channel(con, channel)

    async def get_last_message(self, con):
        # go through the last entry in all the columns of the db and compare them to find latest timestamp
        place_holder = datetime.utcnow()
        await self.update_missed_messages(con, place_holder)

    async def update_missed_messages(self, con, timestamp: datetime):  # timestamp should be of type datetime.datetime
        # loop through all the channels in all the guilds and get all the messages sent after time stamp
        # https://discordpy.readthedocs.io/en/latest/api.html?highlight=channel%20history#discord.TextChannel.history
        pass

    @staticmethod
    async def add_channel(con, channel):
        try:
            # channel id is used so even if the channel name changes it does not affect our db
            # column name cannot start with a number so _ is added
            await con.execute(f"ALTER TABLE chats ADD COLUMN _{str(channel.id)} timestamp with time zone[]")
        except DuplicateColumnError:
            pass
        except Exception as e:
            print(e)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user or message.author.bot:  # ignores messages by self or other bots
            return

        channel = f"_{str(message.channel.id)}"
        async with self.bot.pool.acquire() as con:

            try:
                result = await con.execute(f"UPDATE chats set {channel} = {channel} || $1::timestamp with time zone[] "
                                           f"where userid = $2",
                                           [message.created_at], message.author.id)

                if result == "UPDATE 0":  # if result is UPDATE 0 the user had no earlier message in that channel
                    await con.execute(f"INSERT INTO chats(userid, {channel}) VALUES($1, $2)",
                                      message.author.id, [message.created_at])
            except UndefinedColumnError:
                await self.add_channel(con, message.channel)
                await con.execute(f"INSERT INTO chats(userid, {channel}) VALUES($1, $2)",
                                  message.author.id, [message.created_at])

    @loop(minutes=30)
    async def update_settings(self):
        pass


def setup(bot):
    bot.add_cog(chats(bot))
