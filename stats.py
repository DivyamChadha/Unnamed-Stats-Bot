from asyncio import sleep
from csv import DictWriter
from datetime import datetime
from discord import TextChannel
from discord.ext import commands
from discord.ext.tasks import loop


class chats(commands.Cog):
    message_cache = []

    def __init__(self, bot):
        self.bot = bot
        bot.loop.create_task(self._get_last_message())
        self.insert_messages.start()

    async def _get_last_message(self):
        """Gets the last message stored in the database"""
        async with self.bot.pool.acquire() as con:
            data = await con.fetchval("SELECT created_at from chats ORDER BY created_at DESC LIMIT 1")

            if data is None:  # for first time ever launch
                return

            await self._update_missed_messages(con, data)

    async def _update_missed_messages(self, con, timestamp: datetime):
        """Updates the database with all the messages sent while the bot was offline"""
        await sleep(5)  # sleep gives time for the bot cache to be populated by the guilds

        missed_messages = []
        for guild in self.bot.guilds:
            for channel in guild.channels:
                if not isinstance(channel, TextChannel):  # ignore Voice and Category channels
                    continue

                async for message in channel.history(limit=None, before=datetime.utcnow(), after=timestamp):
                    missed_messages.append((message.author.id, message.channel.id, message.created_at))

        if missed_messages:
            await con.copy_records_to_table('chats', records=missed_messages)

    @staticmethod
    def _write_csv(fieldnames: list, data: list, file_name):  # data is a list of dictionaries
        """Writes the data to a csv."""
        with open(file_name, "w") as file:
            writer = DictWriter(file, fieldnames=fieldnames)

            writer.writeheader()
            writer.writerows(data)

    @commands.Cog.listener()
    async def on_message(self, message):
        """Event triggered on every message, adds the message-data to the cache"""
        if message.author == self.bot.user or message.author.bot:  # ignores messages by self or other bots
            return
        self.message_cache.append((message.author.id, message.channel.id, message.created_at))

    @loop(minutes=30)
    async def insert_messages(self):
        """Scheduled task to add messages to the database in small chunks"""
        temp = self.message_cache.copy()  # just an extra security measure so that no message is missed without adding
        self.message_cache.clear()

        async with self.bot.pool.acquire() as con:
            await con.copy_records_to_table('chats', records=temp)

    @commands.command(name="reset-database")
    @commands.is_owner()
    async def reset_database(self, ctx):
        time_now = datetime.utcnow()
        data = []
        file_name = time_now.strftime('%m/%d/%Y')

        async with self.bot.pool.acquire() as con:
            values = await con.fetch("SELECT * FROM chats WHERE created_at < $1", time_now)
            await con.execute("DELETE FROM chats where created_at < $1", time_now)

        for value in values:
            data.append({"userid": value[0], "channel_id": value[1], "created_at": value[2]})
        self._write_csv(["userid", "channel_id", "created_at"], data, f"{file_name}.csv")

        await ctx.send(f"The database has been reset and a file has been created with the name {file_name}")


def setup(bot):
    bot.add_cog(chats(bot))
