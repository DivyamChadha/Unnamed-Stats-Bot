from discord import Embed, User, TextChannel
from discord.ext import commands
from discord.ext.menus import ListPageSource, MenuPages


class ChatsMenu(ListPageSource):  # just shows number of messages, no functionality to check before or after some time
    def __init__(self, data):
        super().__init__(data, per_page=5)

    # the stuff it does in this function can probably be split into its own function
    async def format_page(self, menu, entries):
        # I get the full list of entries, not just the entries for this specific page.
        total_messages = [v for k, v in self.__dict__['entries']]
        embed = Embed(title=f'Analysis of User',
                      description=f'Total Messages Sent: {sum(total_messages)}')
        embed.set_footer(text=f'Page: {menu.current_page + 1}/{menu._source.get_max_pages()}')
        # simple menu to display all channels and the numbers of messages by the user in those channels

        for k, v in entries:  # k-> channel id, v -> number of messages
            channel = menu.bot.get_channel(k)
            embed.add_field(name="Channel", value=channel.name, inline=True)
            embed.add_field(name="Messages Sent", value=int(v), inline=True)
            # formula is (messages_in_channel / total messages sent by user) * 100
            # round it to the nearest whole number to prevent decimals
            embed.add_field(name="Percentage", value=f'{round(int(v) / sum(total_messages) * 100)}%', inline=True)

        return embed


class ChannelMenu(ListPageSource):  # just shows number of messages, no functionality to check before or after some time
    def __init__(self, data):
        super().__init__(data, per_page=5)

    async def format_page(self, menu, entries):
        total_messages = [v for k, v in self.__dict__['entries']]
        embed = Embed(title=f'Analysis of Channel',
                      description=f'Total Messages Sent in Channel: {sum(total_messages)}')
        embed.set_footer(text=f'Page: {menu.current_page + 1}/{menu._source.get_max_pages()}')

        position = 1

        for k, v in entries:  # k-> channel id, v -> number of messages
            user = menu.bot.get_user(k)
            embed.add_field(name="Position", value=position, inline=True)
            embed.add_field(name="User", value=f'{user.name}#{user.discriminator}', inline=True)
            embed.add_field(name="Messages Sent", value=int(v), inline=True)
            position += 1

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

    @commands.command(name="analyzechannel")
    async def _analyzechannel(self, ctx, channel: TextChannel):
        async with self.bot.pool.acquire() as con:
            # select the channel id's along with the user ids
            result = await con.fetch(f"SELECT _{channel.id}, userid FROM chats ORDER BY array_length(_{channel.id}, 1) desc")
            data = []
            # for each result in the array, append to the data list the user id and how many messages they send
            # (userid, int)
            for user in result:
                data.append((int(user['userid']), len(user[f'_{channel.id}'])))

            pages = MenuPages(source=ChannelMenu(data), clear_reactions_after=True)

            await pages.start(ctx)


def setup(bot):
    bot.add_cog(analyze(bot))
