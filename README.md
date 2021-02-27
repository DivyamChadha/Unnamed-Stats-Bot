# Unnamed-Stats-Bot
Made by [KLK](https://github.com/klk645445) and [Rocky](https://github.com/rockboy987)

### Features:
- user drilldown
- role drilldown
- channel drilldown

### Commands:
| Name          | Description                    |
| ------------- | ------------------------------ |
| `anaylyze()`  | Analyzes the user.             |
| `bloop()`     | **bloop!**                     |

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

