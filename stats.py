from asyncio import sleep
from datetime import datetime
from discord import TextChannel
from discord.ext import commands


class chats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        bot.loop.create_task(self.get_last_message())

    async def get_last_message(self):
        await sleep(5)
        async with self.bot.pool.acquire() as con:
            data = await con.fetchval("SELECT created_at from chats ORDER BY created_at DESC LIMIT 1")

            if data is None:
                return
            print(data)
            await self.update_missed_messages(con, data)

    async def update_missed_messages(self, con, timestamp: datetime):  # timestamp should be of type datetime.datetime
        for guild in self.bot.guilds:
            for channel in guild.channels:
                if not isinstance(channel, TextChannel):
                    continue

                async for message in channel.history(limit=None, before=datetime.utcnow(), after=timestamp):
                    await con.execute("INSERT INTO chats(userid, channel_id, created_at) values($1, $2, $3)",
                                      message.author.id, message.channel.id, message.created_at)
                    print(message.id)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user or message.author.bot:  # ignores messages by self or other bots
            return

        async with self.bot.pool.acquire() as con:
            await con.execute("INSERT INTO chats(userid, channel_id, created_at) values($1, $2, $3)",
                              message.author.id, message.channel.id, message.created_at)


def setup(bot):
    bot.add_cog(chats(bot))
