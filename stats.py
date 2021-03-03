from discord.ext import commands
from discord.ext.tasks import loop


class stats(commands.Cog):
    message_cache = []

    def __init__(self, bot):
        self.bot = bot
        self.insert_messages.start()

    def cog_unload(self):
        self.bot.loop.create_task(self.insert_messages.__call__())
        self.insert_messages.cancel()

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

        print(f"Inserting {len(temp)} messages.")
        async with self.bot.pool.acquire() as con:
            await con.copy_records_to_table('chats', records=temp)

    @insert_messages.before_loop
    async def before_inserting_messages(self):
        """Waits for bots to be ready"""
        await self.bot.wait_until_ready()


def setup(bot):
    bot.add_cog(stats(bot))
