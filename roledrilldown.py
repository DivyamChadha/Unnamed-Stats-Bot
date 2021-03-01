import csv
from datetime import datetime
from discord import File, InvalidArgument, Role, TextChannel
from discord.ext import commands
from functools import partial
from zipfile import ZipFile, ZIP_BZIP2


class roledrilldown(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    async def _convert_to_datetime(data: str):
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

        return before, after

    @staticmethod
    def _write_csv(fieldnames: list, data: list, file_name):  # data is a list of dictionaries
        """Writes the data to a csv."""
        with open(file_name, "w") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)

            writer.writeheader()
            writer.writerows(data)

    @staticmethod
    def _compress_and_zip(zip_name, file_name):
        """Converts the provided file into a zip file with highest compressions possible."""
        with ZipFile(zip_name, 'w', compression=ZIP_BZIP2, compresslevel=9) as zip_file:
            zip_file.write(file_name)

    @commands.command(aliases=["role"])
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
            if after is None:  # condition 1: when after is not provided by the user.
                for i, member in enumerate(members):
                    data.append({"Name": member.name, "User ID": member.id})
                    total = 0
                    for channel in channels:
                        if not isinstance(channel, TextChannel):
                            continue
                        result = await con.fetchval("""
                        SELECT COUNT(*) from chats WHERE userid = $1 and channel_id = $2 and created_at < $3
                        """, member.id, channel.id, before)
                        data[i].update({channel.name: result})
                        total += result
                    data[i].update({"Total": total})

            elif isinstance(after, datetime):  # condition 2: when after is provided by the user.
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
            await ctx.send(file=csv_file)
        except InvalidArgument:  # raised when the csv file size is too big to send

            # csv is converted to zip
            partial_obj = partial(self._compress_and_zip, f"{ctx.guild.name}.zip", f"{ctx.guild.name}.csv")
            await self.bot.loop.run_in_executor(None, partial_obj)  # runs the blocking code in executor

            zip_file = File(f"{ctx.guild.name}.zip")
            await ctx.send(csv_file=zip_file)


def setup(bot):
    bot.add_cog(roledrilldown(bot))
