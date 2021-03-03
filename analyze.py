from csv import DictWriter
from discord import Embed, File, InvalidArgument, Role, TextChannel, User
from discord.ext import commands
from discord.ext.menus import ListPageSource, MenuPages
from datetime import datetime
from functools import partial
from zipfile import ZipFile, ZIP_BZIP2

_help = {
    "user": ["""Command to analyse a user in the server.\n
    - <user> can be the @user-mention or can be the user's id. 
    - An optional argument `date_after` can be added to get messages after the date. <br/>
     eg `?analyze user <user> -a YYYY-MM-DD`
    - An optional argument `date_before` can be added to get messages before the date. <br/>
     eg `?analyze user <user> -b YYYY-MM-DD`
    - Both `date_after` and `date_before` can be used together as well. The order of input does not matter. <br/>
     eg `?analyze user <user> -a YYYY-MM-DD -b YYYY-MM-DD`
    """, "<user> -a YYYY-MM-DD -b YYYY-MM-DD"],

    "channel": ["""Command to analyse top members in a channel.\n
    - <channel> can be the #channel-mention or can be the channel's id. 
    - An optional argument `date_after` can be added to get messages after the date. <br/>
        eg `?analyze channel <channel> -a YYYY-MM-DD`
    - An optional argument `date_before` can be added to get messages before the date. <br/>
        eg `?analyze channel <channel> -b YYYY-MM-DD`
    - Both `date_after` and `date_before` can be used together as well. The order of input does not matter. <br/>
        eg `?analyze channel <channel> -a YYYY-MM-DD -b YYYY-MM-DD`
    """, "<channel> -a YYYY-MM-DD -b YYYY-MM-DD"],

    "role": ["""Command to analyse all members in a role.\n
    - <roles> can be the @role-mention or can be the role's id. There has to be at least one role. If multiple roles are 
      provided the should be separated by a single space.
    - An optional argument `date_after` can be added to get messages after the date. <br/>
        eg `?analyze roles <role> -a YYYY-MM-DD`
    - An optional argument `date_before` can be added to get messages before the date. <br/>
        eg `?analyze roles <role> -b YYYY-MM-DD`
    - Both `date_after` and `date_before` can be used together as well. The order of input does not matter. <br/>
        eg `?analyze roles <role> -a YYYY-MM-DD -b YYYY-MM-DD`
    - The optional arguments must be provided after all the roles.
    """, "<role> -a YYYY-MM-DD -b YYYY-MM-DD"],

    "reset-database": ["""
    - Clears the database.
    - Converts the data into a csv before clearing.
    - This command should be used by you periodically to avoid the database becoming too large.
    - Analyze commands wont work for the data which has been cleared.
    """]
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
            print(type(v))
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
                                  f'\nTotal Messages Sent in Channel: `{sum(total_messages)}`')
        embed.set_footer(text=f'Page: {menu.current_page + 1}/{self.get_max_pages()}')

        position = 1

        for k, v in entries:  # k->  user, v -> number of messages sent in channel
            user = menu.bot.get_user(k)
            embed.add_field(name="Position", value=f"{position}", inline=True)
            embed.add_field(name="User", value=f'{user.name}#{user.discriminator}', inline=True)
            embed.add_field(name="Messages Sent", value=f"{v}", inline=True)
            position += 1

        return embed


class analyze(commands.Cog):
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
        with open(file_name, "w") as file:
            writer = DictWriter(file, fieldnames=fieldnames)

            writer.writeheader()
            writer.writerows(data)

    @staticmethod
    def _compress_and_zip(zip_name, file_name):
        """Converts the provided file into a zip file with highest compressions possible."""
        with ZipFile(zip_name, 'w', compression=ZIP_BZIP2, compresslevel=9) as zip_file:
            zip_file.write(file_name)

    @commands.group(name="analyse", aliases=["analyze"])
    @commands.has_permissions(administrator=True)
    async def _analyse(self, ctx):
        """Parent command for the 3 analysis sub commands."""
        pass

    @_analyse.command(help=_help['user'][0], usage=_help['user'][1])
    async def user(self, ctx, user: User, *, time="None"):
        async with self.bot.pool.acquire() as con:

            # if a time period isn't specified, get the default results
            before, after = await self._convert_to_datetime(time)

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

    @_analyse.command(help=_help['channel'][0], usage=_help['channel'][1])
    async def channel(self, ctx, channel: TextChannel, *, time="None"):
        async with self.bot.pool.acquire() as con:
            # select the channel id's along with the user id
            before, after = await self._convert_to_datetime(time)

            results = await con.fetch(f"""SELECT userid, COUNT(*)
                                          FROM chats
                                          WHERE channel_id = {channel.id}
                                          AND (created_at BETWEEN $2 AND $1)
                                          GROUP BY userid
                                          ORDER BY COUNT(*) DESC""", before, after)

            data = []
            # for each result in the array, append to the data list the user id and how many messages they send
            # (userid, int)
            for result in results:
                data.append((int(result['userid']), result['count']))

            pages = MenuPages(source=ChannelMenu(data, before, after), clear_reactions_after=True)

            await pages.start(ctx)

    @_analyse.command(aliases=["role"], help=_help['role'][0], usage=_help['role'][1])
    async def roles(self, ctx, roles: commands.Greedy[Role], *, time="None"):
        fieldnames = ["Name", "User ID", "Total"]
        data = []
        before, after = await self._convert_to_datetime(time)
        if before is None:
            before = datetime.utcnow()

        members = []
        for member in ctx.guild.members:  # gets all the members in the guild having the provided roles
            check = any(role in member.roles for role in roles)
            if check is True:
                members.append(member)

        channels = []
        for channel in ctx.guild.channels:  # gets all the text channels in the guild
            if not isinstance(channel, TextChannel):
                continue
            fieldnames.append(channel.name)
            channels.append(channel)

        async with self.bot.pool.acquire() as con:

            for i, member in enumerate(members):
                data.append({"Name": member.name, "User ID": member.id})
                total = 0
                for channel in channels:
                    if not isinstance(channel, TextChannel):
                        continue
                    result = await con.fetchval("""
                        SELECT COUNT(*) from chats WHERE userid = $1 and channel_id = $2 and 
                        (created_at BETWEEN $4 and $3)
                        """, member.id, channel.id, before, after)
                    data[i].update({channel.name: result})
                    total += result
                data[i].update({"Total": total})

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
                           f"{before.strftime('%Y/%m/%d')}", csv_file=zip_file)

    @commands.command(name="reset-database", help=_help["reset-database"][0])
    @commands.has_permissions(administrator=True)
    async def reset_database(self, ctx):
        time_now = datetime.utcnow()
        data = []
        file_name = time_now.strftime('%Y/%m/%d')

        async with self.bot.pool.acquire() as con:
            values = await con.fetch("SELECT * FROM chats WHERE created_at < $1", time_now)
            await con.execute("DELETE FROM chats where created_at < $1", time_now)

        for value in values:
            data.append({"userid": value[0], "channel_id": value[1], "created_at": value[2]})

        partial_obj = partial(self._write_csv, ["userid", "channel_id", "created_at"], data,
                              f"{ctx.guild.name}-{file_name}.csv")
        await self.bot.loop.run_in_executor(None, partial_obj)  # runs the blocking code in executor

        await ctx.send(f"The database has been reset and a file has been created with the name "
                       f"`{ctx.guild.name}-{file_name}`")

        message = await self.bot.wait_for("message")
        self.first_message = message.created_at


def setup(bot):
    bot.add_cog(analyze(bot))
