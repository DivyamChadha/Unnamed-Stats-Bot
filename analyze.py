from discord import Embed, User
from discord.ext import commands
from discord.ext.menus import ListPageSource, MenuPages


class ChatsMenu(ListPageSource):  # just shows number of messages, no functionality to check before or after some time
    def __init__(self, data):
        super().__init__(data, per_page=10)

    async def format_page(self, menu, entries):
        total_messages = [v for k, v in entries]
        embed = Embed(title="Analysis",
                      description=f'Total Messages Sent: {sum(total_messages)}')
        embed.set_footer(text=f'Page: {menu.current_page + 1}/{menu._source.get_max_pages()}')
        # simple menu to display all channels and the numbers of messages by the user in those channels

        for k, v in entries:  # k-> channel id, v -> number of messages
            channel = menu.bot.get_channel(k)
            embed.add_field(name="Channel", value=channel.name, inline=True)
            embed.add_field(name="Messages Sent", value=int(v), inline=True)
            embed.add_field(name="Percentage", value=f'{round(int(v)/sum(total_messages) * 100)}%', inline=True)

        return embed


class analyze(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="analyze")
    async def _analyze(self, ctx, user: User):
        async with self.bot.pool.acquire() as con:
            result = await con.fetch("select * from chats where userid = $1", user.id)

            x = dict(result[0])
            data = []
            for k, v in x.items():
                if v:  # if the array is empty, its not appended to the list
                    if k == "userid":  # ignores the userid column
                        continue
                    data.append((int(k[1:]), len(v)))

            pages = MenuPages(source=ChatsMenu(data), clear_reactions_after=True)
            await pages.start(ctx)


def setup(bot):
    bot.add_cog(analyze(bot))
