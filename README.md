# Unnamed-Stats-Bot v1.0.0
A simple stats bot made by [KLK](https://github.com/klk645445) and [Rocky](https://github.com/rockboy987).
Currently being used and tested in [Official LdoE server](https://discord.com/invite/ldoe) </br>
Messages are loaded in the database every 30 minutes.

### Features:
- User analysis
- Role/s analysis
- Channel analysis

### Setup:
- Install the database and [create the table](https://github.com/rockboy987/Unnamed-Stats-Bot/tree/rocky#database)
- Make sure you have the [required libraries](https://github.com/rockboy987/Unnamed-Stats-Bot#libraries-used).
- Clone this repository to get the files
- Create a json file named `confidential` with indent 0. It should have the following keys:
    - [token](https://discord.com/developers/applications)
    - database_name
    - database_user
    - database_password
    - prefixes
    
  ```
  {
  "token" : "",
  "database_name" : "",
  "database_user" : "",
  "database_password" : "",
  "prefixes" : ["?", "!"]
  }
  ```
  
- Run the main file and voila!

- **Note**: For the bot to collect all the data properly it needs to have view channel, 
  read messages and read messages history permission in the channels where you want the stats to be maintained. 
  Further for the commands to work the bot needs send messages, embed messages and attach files permission.
    
## Commands:
| Name              | Description                     | Returns                  |
| -------------     | ---------------------------     | -------------            |
| `analyse`         | Analyzes a user, channel or role| Embedded menu or a CSV   |
| `reload`          | Reloads/Refreshes a Cog         |            -             |

### Usage:
The prefix for the examples below is assumed to be `?`

#### ?analyse <argument_type>
 **<argument_type>** can be a discord _User_, _TextChannel_ or a _Role_. You can mention them, or use the ID instead.<br>
 For User or TextChannel, analysis is done only for the first argument. To analyse more than one role separate each
    role with a single space.<br>
 - An optional argument `date_after` can be added to get messages after a certain date. <br>
   eg `?analyse <argument_type> -a YYYY-MM-DD`
- An optional argument `date_before` can be added to get messages before a certain date. <br>
   eg `?analyse <argument_type> -b YYYY-MM-DD`
- Both `date_after` and `date_before` can be used together as well. The order of input does not matter. <br>
   eg `?analyse <argument_type> -a YYYY-MM-DD -b YYYY-MM-DD`

Examples:
- ?analyse @Rockboy987#2519
- ?analyse @LegendaryKLK#1559 -a 2021-02-28
- ?analyse #general -b 2021-03-3
- ?analyse @Moderators -a 2021-02-28 -b 2021-03-3

#### ?reload <cog-name>
- Reloads a cog.
- This bot has 2 cogs: `stats` and `analyze`.
- Reloading `stats` cog will force update the database with all the messages that are currently in cache.
- Reloading `analyze` does nothing.

### Extras: 
In the bots directory you will find 2 python scripts named `remove_duplicates.py` and `reset_database.py`.

- The bot does an excellent work in ensuring no duplicates are stored in the database. However if any condition arises 
resulting in the duplication of the messages, `remove_duplicates.py` can be run. It runs on the assumption that no user can 
have 2 messages at the exact same time.
- If you wish to remove all the current messages in the database and store them in a CSV then you can run 
`reset_database.py`. It is recommended to do so occasionally to avoid database table from getting too big. However messages 
once removed from the db cannot be analysed through the bot.

### Database:

The bot uses [postgresql](https://www.postgresql.org/) database. Before running the bot create the following table:

```
CREATE TABLE chats
(
    userid numeric NOT NULL,
    channel_id numeric NOT NULL,
    created_at timestamp without time zone NOT NULL
)

WITH (
    autovacuum_enabled = TRUE
);
```

It should look something like this:

| userid  | channel_id | created_at|
| --------| -----------|-----------|
|         |            |           |
|         |            |           |

### External libraries used:

- [discord.py](https://pypi.org/project/discord.py/)
- [discord-ext-menus](https://github.com/Rapptz/discord-ext-menus)
- [asyncpg](https://pypi.org/project/asyncpg/)

### Scope for future improvement (v2 or later):
- Switch to a different database (such as Cassandra) since the bot is write-heavy.
- Automated resetting/clearing of the database.
- Ability to read older CSVs created on resetting and get analysis from them.
- A better way to store older data than CSV (?) 
- Using regex to store all the data in a single text column (?)
- Tell us.

