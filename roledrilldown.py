import csv
from datetime import datetime
from discord import File, Role, TextChannel
from discord.ext import commands
from functools import partial


class roledrilldown(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    async def _convert_to_datetime(data: str):
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
    def write_csv(fieldnames: list, data: list):  # data is a list of dictionaries
        with open("data.csv", "w") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)

            writer.writeheader()
            writer.writerows(data)

    @commands.command()
    async def role(self, ctx, roles: commands.Greedy[Role], *, time="None"):
        fieldnames = ["Name", "User ID", "Total"]
        data = []
        before, after = await self._convert_to_datetime(time)
        if before is None:
            before = datetime.utcnow()

        members = []
        for member in ctx.guild.members:
            check = any(role in member.roles for role in roles)
            if check is True:
                members.append(member)

        channels = []
        for channel in ctx.guild.channels:
            if not isinstance(channel, TextChannel):
                continue
            fieldnames.append(channel.name)
            channels.append(channel)

        async with self.bot.pool.acquire() as con:
            if after is None:
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

            elif isinstance(after, datetime):
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

        partial_obj = partial(self.write_csv, fieldnames, data)
        await self.bot.loop.run_in_executor(None, partial_obj)

        csv_file = File("data.csv")
        await ctx.send(file=csv_file)


def setup(bot):
    bot.add_cog(roledrilldown(bot))
