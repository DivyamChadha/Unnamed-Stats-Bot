import asyncio
import asyncpg
from csv import DictWriter
from datetime import datetime, timedelta
from json import load

try:
    with open("confidential") as file:
        confidential = load(file)


    async def run():
        print("Getting started...")
        time_now = datetime.utcnow() - timedelta(seconds=5)
        file_name = time_now.strftime('%Y-%m-%d.csv')

        con = await asyncpg.connect(database=confidential["database_name"],
                                    user=confidential["database_user"],
                                    password=confidential["database_password"])

        values = await con.fetch("SELECT * FROM chats WHERE created_at < $1", time_now)

        if len(values) > 1:
            data = []
            print(f"{len(values)} messages collected. Deleting now...")
            await con.execute("DELETE FROM chats where created_at < $1", time_now)
            print("Messages deleted and now are being transferred to a CSV...")

            for value in values:
                data.append({"userid": value[0], "channel_id": value[1], "created_at": value[2]})

            with open(file_name, "w", encoding="utf-8") as f:
                writer = DictWriter(f, fieldnames=["userid", "channel_id", "created_at"])

                writer.writeheader()
                writer.writerows(data)

            print("Done.")
        else:
            print("No messages in the database.")
        await con.close()


    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())
except Exception as e:
    print(e)
print("Press enter to continue...")
input()
