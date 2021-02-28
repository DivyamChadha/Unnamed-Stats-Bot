# Unnamed-Stats-Bot v1.0.0
A simple stats bot made by [KLK](https://github.com/klk645445) and [Rocky](https://github.com/rockboy987).


### Features:
- user drilldown
- role drilldown
- channel drilldown

### Setup:
- Install the database and create the table *(scroll down)*
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
    
    

### Commands:
| Name              | Description                 | Returns       |
| -------------     | --------------------------- | ------------- |
| `anaylyze user`   | Analyzes a user             | Embedded menu |
| `anaylyze channel`| Analyzes a channel          | Embedded menu |
| `anaylyze roles`  | Analyzes one or more roles  | CSV file      |

### Usage:
The prefix for the examples below is assumed to be `?`

#### ?anaylyze user {user}
- {user} can be the @user-mention or can be the user's id. 
- An optional argument `date_after` can be added to get messages after the date.
  eg `?analyze user {user} -a YYYY-MM-DD`
- An optional argument `date_before` can be added to get messages before the date.
  eg `?analyze user {user} -b YYYY-MM-DD`
- Both `date_after` and `date_before` can be used together as well. The order of input does not matter.
  eg `?analyze user {user} -a YYYY-MM-DD -b YYYY-MM-DD`

#### ?anaylyze channel {channel}
- {channel} can be the #channel-mention or can be the channel's id. 
- An optional argument `date_after` can be added to get messages after the date.
  eg `?analyze channel {channel} -a YYYY-MM-DD`
- An optional argument `date_before` can be added to get messages before the date.
  eg `?analyze channel {channel} -b YYYY-MM-DD`
- Both `date_after` and `date_before` can be used together as well. The order of input does not matter.
  eg `?analyze channel {channel} -a YYYY-MM-DD -b YYYY-MM-DD`
  
 #### ?anaylyze roles {role1}{role2}..{roles}
- {roles} can be the @role-mention or can be the role's id. There has to be at least one role. If multiple roles are 
  provided the should be separated by a single space.
- An optional argument `date_after` can be added to get messages after the date.
  eg `?analyze roles {role} -a YYYY-MM-DD`
- An optional argument `date_before` can be added to get messages before the date.
  eg `?analyze roles {role} -b YYYY-MM-DD`
- Both `date_after` and `date_before` can be used together as well. The order of input does not matter.
  eg `?analyze roles {role} -a YYYY-MM-DD -b YYYY-MM-DD`
- The optional arguments must be provided after all the roles.


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
- [asyncpg](https://pypi.org/project/asyncpg/)

