import asyncio
import asyncpg
from json import load

try:
    with open("confidential") as file:
        confidential = load(file)


    async def run():
        print("Getting started...")
        con = await asyncpg.connect(database=confidential["database_name"],
                                    user=confidential["database_user"],
                                    password=confidential["database_password"])

        values = await con.fetch("SELECT userid, created_at FROM chats ORDER BY created_at")
        print(f"{len(values)} messages received. Checking for duplicated now. Please wait...")
        present = []
        duplicate = []

        for value in values:
            if value not in present:
                present.append(value)
                continue
            duplicate.append(value)

        if duplicate:
            print(f"Deleting {len(duplicate)} messages that were duplicated...")
            await con.executemany("DELETE FROM chats WHERE ctid IN (SELECT ctid FROM chats WHERE userid = $1 and "
                                  "created_at = $2 LIMIT 1)", duplicate)

        else:
            print("No duplicates found.")

        await con.close()


    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())
except Exception as e:
    print(e)
print("Press enter to continue...")
input()
