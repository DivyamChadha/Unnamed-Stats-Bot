# Unnamed-Stats-Bot v1.0.0
A simple stats bot made by [KLK](https://github.com/klk645445) and [Rocky](https://github.com/rockboy987).
Currently being used and tested in [Official LdoE server](https://discord.com/invite/ldoe)


### Features:
- User analysis
- Role analysis
- Channel analysis

### Setup:
- Install the database and [create the table](https://github.com/rockboy987/Unnamed-Stats-Bot/tree/rocky#database)
- Clone this repository to get the files
- Create a json file named `confidential` with indent 0. It should have the following keys:
    - token *(your [discord bot](https://discord.com/developers/applications) token)*
    - database_name
    - database_user
    - database_password
    - prefixes
    
  ``````
  {
  "token" : "",
  "database_name" : "",
  "database_user" : "",
  "database_password" : "",
  "prefixes" : ["?", "!"]
    }
- Run the main file and voila!

- **Note**: For the bot to collect all the data properly it needs to have view channel, 
  read messages and read messages history permission in the channels where you want the stats to be maintained. 
  Further for the commands to work the bot needs send messages, embed messages and attach files permission.
    
### Commands:
| Name              | Description                 | Returns                  |
| -------------     | --------------------------- | -------------            |
| `anaylyze user`   | Analyzes a user             | Embedded menu            |
| `anaylyze channel`| Analyzes a channel          | Embedded menu            |
| `anaylyze roles`  | Analyzes one or more roles  | CSV or a Zip file        |
| `reset-database`  | Clears the entire database  | CSV file to the directory|

### Usage:
The prefix for the examples below is assumed to be `?`

#### ?anaylyze user {user}
- {user} can be the @user-mention or can be the user's id. 
- An optional argument `date_after` can be added to get messages after the date. <br/>
  eg `?analyze user {user} -a YYYY-MM-DD`
- An optional argument `date_before` can be added to get messages before the date. <br/>
  eg `?analyze user {user} -b YYYY-MM-DD`
- Both `date_after` and `date_before` can be used together as well. The order of input does not matter. <br/>
  eg `?analyze user {user} -a YYYY-MM-DD -b YYYY-MM-DD`

#### ?anaylyze channel {channel}
- {channel} can be the #channel-mention or can be the channel's id. 
- An optional argument `date_after` can be added to get messages after the date. <br/>
  eg `?analyze channel {channel} -a YYYY-MM-DD`
- An optional argument `date_before` can be added to get messages before the date. <br/>
  eg `?analyze channel {channel} -b YYYY-MM-DD`
- Both `date_after` and `date_before` can be used together as well. The order of input does not matter. <br/>
  eg `?analyze channel {channel} -a YYYY-MM-DD -b YYYY-MM-DD`
  
#### ?anaylyze roles {role1}{role2}..{roles}
- {roles} can be the @role-mention or can be the role's id. There has to be at least one role. If multiple roles are 
  provided the should be separated by a single space.
- An optional argument `date_after` can be added to get messages after the date. <br/>
  eg `?analyze roles {role} -a YYYY-MM-DD`
- An optional argument `date_before` can be added to get messages before the date. <br/>
  eg `?analyze roles {role} -b YYYY-MM-DD`
- Both `date_after` and `date_before` can be used together as well. The order of input does not matter. <br/>
  eg `?analyze roles {role} -a YYYY-MM-DD -b YYYY-MM-DD`
- The optional arguments must be provided after all the roles.

#### ?reset-database
- Clears the database.
- Converts the data into a csv before clearing.
- This command should be used by you periodically to avoid the database becoming too large.
- Analyze commands wont work for the data which has been cleared.


### Database:

The bot uses [postgresql](https://www.postgresql.org/) database. Before running the bot create the following table:

```
CREATE TABLE chats
(
    userid numeric NOT NULL,
    channel_id numeric NOT NULL,
    created_at timestamp without time zone NOT NULL,
    PRIMARY KEY (created_at)
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

### Libraries used:

- [discord.py](https://pypi.org/project/discord.py/)
- [discord-ext-menus](https://github.com/Rapptz/discord-ext-menus)
- [asyncpg](https://pypi.org/project/asyncpg/)

### Scope for future improvement (v2 or later):
- Switch to a different database (such as Cassandra) since the bot is write-heavy.
- Automated resetting/clearing of the database.
- Ability to read older CSVs created on resetting and get analysis from them.
- A better way to store older data than CSV (?)
- Tell us.

