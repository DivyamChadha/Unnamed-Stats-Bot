from csv import DictWriter
from discord import Embed, File, InvalidArgument, Role, TextChannel, User
from discord.ext import commands
from discord.ext.menus import ListPageSource, MenuPages
from datetime import datetime
from functools import partial
from typing import Union
from zipfile import ZipFile, ZIP_BZIP2

_help = {
    "analyse": ["""Command to analyse a user, channel or role/s in the server.\n
    <argument_type> can be a discord User, TextChannel or a Role/s. You can mention them, or use the ID instead. 
    For User or TextChannel, analysis is done only for the first argument. To analyse more than one role separate each
    role with a single space.\n\n
    - An optional argument `date_after` can be added to get messages after a certain date. 
     eg `?analyze <argument_type> -a YYYY-MM-DD`
    - An optional argument `date_before` can be added to get messages before a certain date. 
     eg `?analyze <argument_type> -b YYYY-MM-DD`
    - Both `date_after` and `date_before` can be used together as well. The order of input does not matter.
     eg `?analyze <argument_type> -a YYYY-MM-DD -b YYYY-MM-DD`
    """, "<argument_type> -a YYYY-MM-DD -b YYYY-MM-DD"]
}


class ChatsMenu(ListPageSource):
    def __init__(self, data, before, after):
        super().__init__(data, per_page=5)
        self.before = before
        self.after = after

    # the stuff it does in this function can probably be split into its own function
    async def format_page(self, menu: MenuPages, entries):
        # I get the full list of entries, not just the entries for this specific page.
        total_messages = [v for k, v in self.__dict__['entries']]
        embed = Embed(title=f'Analysis of User',
                      description=f'Between: `{self.after.strftime("%Y/%m/%d")}` and '
                                  f'`{self.before.strftime("%Y/%m/%d")}`'
                                  f'\nTotal Messages Sent: `{sum(total_messages)}`')
        embed.set_footer(text=f'Page: {menu.current_page + 1}/{self.get_max_pages()}')
        # simple menu to display all channels and the numbers of messages by the user in those channels

        for k, v in entries:  # k-> channel id, v -> number of messages
            channel = menu.bot.get_channel(k)
            embed.add_field(name="Channel", value=channel.name, inline=True)
            embed.add_field(name="Messages Sent", value=f"{v}", inline=True)
            # formula is (messages_in_channel / total messages sent by user) * 100
            # round it to the nearest whole number to prevent decimals
            embed.add_field(name="Percentage", value=f'{round(int(v) / sum(total_messages) * 100)}%', inline=True)

        return embed


class ChannelMenu(ListPageSource):
    def __init__(self, data, before, after):
        super().__init__(data, per_page=5)
        self.before = before
        self.after = after

    async def format_page(self, menu: MenuPages, entries):
        total_messages = [v for k, v in self.__dict__['entries']]
        embed = Embed(title=f'Analysis of Channel',
                      description=f'Between: `{self.after.strftime("%Y/%m/%d")}` and '
                                  f'`{self.before.strftime("%Y/%m/%d")}`'
                                  f'\nTotal Messages Sent in Channel by the top {len(self.__dict__["entries"])} users: '
                                  f'`{sum(total_messages)}`')
        embed.set_footer(text=f'Page: {menu.current_page + 1}/{self.get_max_pages()}')

        position = 1

        for k, v in entries:  # k->  user, v -> number of messages sent in channel
            user = menu.bot.get_user(k)
            embed.add_field(name="Position", value=f"{self.__dict__['entries'].index((k, v)) + 1}", inline=True)
            embed.add_field(name="User", value=f'{user.name}#{user.discriminator}', inline=True)
            embed.add_field(name="Messages Sent", value=f"{v}", inline=True)
            position += 1

        return embed


class analyze(commands.Cog):
    """Module containing the commands for analysis"""
    first_message: datetime

    def __init__(self, bot):
        self.bot = bot
        bot.loop.create_task(self._get_first_message())

    async def _get_first_message(self):
        """Gets the first message stored in the database"""
        async with self.bot.pool.acquire() as con:
            data = await con.fetchval("SELECT created_at from chats ORDER BY created_at ASC LIMIT 1")

            if data is None:  # for first time ever launch
                message = await self.bot.wait_for("message")
                self.first_message = message.created_at
                return

            self.first_message = data

    async def _convert_to_datetime(self, data: str):
        """Converts the provided data from str to datetime if found.
            Format:
             -b YYYY-MM-DD
             -a YYYY-MM-DD
        """

        words = data.split()
        before = None
        after = None

        for i, word in enumerate(words):
            if word.lower() == "-b":
                try:
                    before = datetime.strptime(words[i + 1], "%Y-%m-%d")
                except Exception as e:
                    print(e)

            if word.lower() == "-a":
                try:
                    after = datetime.strptime(words[i + 1], "%Y-%m-%d")
                except Exception as e:
                    print(e)

        if not isinstance(before, datetime):
            before = datetime.utcnow()
        if not isinstance(after, datetime):
            after = self.first_message

        return before, after

    @staticmethod
    def _write_csv(fieldnames: list, data: list, file_name):  # data is a list of dictionaries
        """Writes the data to a csv."""
        with open(file_name, "w", encoding="utf-8") as file:
            writer = DictWriter(file, fieldnames=fieldnames)

            writer.writeheader()
            writer.writerows(data)

    @staticmethod
    def _compress_and_zip(zip_name, file_name):
        """Converts the provided file into a zip file with highest compressions possible."""
        with ZipFile(zip_name, 'w', compression=ZIP_BZIP2, compresslevel=9) as zip_file:
            zip_file.write(file_name)

    @commands.group(name="analyse", aliases=["analyze"], help=_help["analyse"][0], usage=_help["analyse"][1])
    @commands.has_permissions(administrator=True)
    async def _analyse(self, ctx, arguments: commands.Greedy[Union[User, TextChannel, Role]], *, time="None"):
        before, after = await self._convert_to_datetime(time)

        if isinstance(arguments[0], User):
            await self.analyse_user(ctx, arguments[0], before, after)
        elif isinstance(arguments[0], TextChannel):
            await self.analyse_channel(ctx, arguments[0], before, after)
        elif isinstance(arguments[0], Role):
            await self.analyse_role(ctx, arguments, before, after)
        else:
            await ctx.send("Invalid Argument. Must be of type **User, TextChannel or Role**.")

    async def analyse_user(self, ctx, user: User, before, after):
        async with self.bot.pool.acquire() as con:
            results = await con.fetch(f"""SELECT channel_id, COUNT(*)
                                          FROM chats
                                          WHERE userid = {user.id}
                                          AND (created_at BETWEEN $2 AND $1)
                                          GROUP BY channel_id
                                          ORDER BY COUNT(*) DESC""", before, after)

            if not results:
                return await ctx.reply("No records found.")

            data = []
            for result in results:
                data.append((int(result['channel_id']), result['count']))

            pages = MenuPages(source=ChatsMenu(data, before, after), clear_reactions_after=True)
            await pages.start(ctx)

    async def analyse_channel(self, ctx, channel: TextChannel, before, after):
        async with self.bot.pool.acquire() as con:
            results = await con.fetch(f"""SELECT userid, COUNT(*)
                                          FROM chats
                                          WHERE channel_id = {channel.id}
                                          AND (created_at BETWEEN $2 AND $1)
                                          GROUP BY userid
                                          ORDER BY COUNT(*) DESC
                                          LIMIT 100""", before, after)

            data = []
            # for each result in the array, append to the data list the user id and how many messages they send
            # (userid, int)
            for result in results:
                data.append((int(result['userid']), result['count']))

            pages = MenuPages(source=ChannelMenu(data, before, after), clear_reactions_after=True)

            await pages.start(ctx)

    async def analyse_role(self, ctx, roles, before, after):
        fieldnames = ["Name", "User ID", "Total"]
        data = []

        members = []
        for member in ctx.guild.members:  # gets all the members in the guild having the provided role
            check = any(role in member.roles for role in roles)
            if check is True:
                members.append(member)

        channels = {}
        for channel in ctx.guild.channels:  # gets all the text channels in the guild
            if not isinstance(channel, TextChannel):
                continue
            fieldnames.append(channel.name)
            channels.update({channel.id: channel.name})

        async with self.bot.pool.acquire() as con:
            for member in members:
                member_info = {"Name": member.name, "User ID": member.id}
                results = await con.fetch("""
                                    SELECT channel_id, count(*) 
                                    FROM chats 
                                    WHERE userid = $1 and created_at BETWEEN $2 AND $3 and 
                                                                                        channel_id = any($4::numeric[])
                                    GROUP BY channel_id 
                                    ORDER BY count(*) DESC
                                    """, member.id, after, before, list(channels.keys()))

                if len(results) < 1:  # ignores the member if they have had no message
                    continue
                total = 0

                for result in results:
                    if result[1] > 0:  # ignores the channel if they have had no message from the user
                        total += result[1]
                        member_info.update({channels[result[0]]: result[1]})

                if total > 0:
                    member_info.update({"Total": total})
                    data.append(member_info)

        if len(data) < 1:
            await ctx.send(f"No stats found for the provided role/s between `{after.strftime('%Y/%m/%d')}` and "
                           f"`{before.strftime('%Y/%m/%d')}`")
            return

        partial_obj = partial(self._write_csv, fieldnames, data, f"{ctx.guild.name}.csv")
        await self.bot.loop.run_in_executor(None, partial_obj)  # runs the blocking code in executor
        csv_file = File(f"{ctx.guild.name}.csv")

        try:
            await ctx.send(f"Stats for the provided role/s between `{after.strftime('%Y/%m/%d')}` and "
                           f"`{before.strftime('%Y/%m/%d')}`", file=csv_file)
        except InvalidArgument:  # raised when the csv file size is too big to send

            # csv is converted to zip
            partial_obj = partial(self._compress_and_zip, f"{ctx.guild.name}.zip", f"{ctx.guild.name}.csv")
            await self.bot.loop.run_in_executor(None, partial_obj)  # runs the blocking code in executor

            zip_file = File(f"{ctx.guild.name}.zip")
            await ctx.send(f"Stats for the provided role between {after.strftime('%Y/%m/%d')} and "
                           f"{before.strftime('%Y/%m/%d')}", file=zip_file)


def setup(bot):
    bot.add_cog(analyze(bot))
