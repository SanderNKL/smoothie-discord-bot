import discord
from database import Database
from discord.ext import commands
import emojis as emojis
from datetime import datetime
database = Database()


async def fetch_server(guild_id: str):
    data = await database.server_data.find_one({"_guild_id": str(guild_id)})
    return data


async def disable_logging(guild_id: str, log_type: str):
    return database.server_data.update_one(
        {"_guild_id": str(guild_id)},
        {"$unset": {f"logs.{log_type}": ""}}
    )


async def log_violation(
        guild: discord.Guild,
        violator: discord.User,
        moderator: discord.User,
        action: str,
        reason: str
):
    try:
        await database.violations.insert_one(
            {
                "guild_id": guild.id,
                "violator_id": violator.id,
                "violator_name": violator.name,
                "action": action,
                "moderator_id": moderator.id,
                "moderator_name": moderator.name,
                "reason": reason,
                "timestamp": datetime.now()
            }
        )

    except Exception as e:
        print("Issue with logging violation:", e)


async def get_violations(
        guild: discord.Guild,
        violator: discord.User = None,
        moderator: discord.User = None,
        page: int = 0
):
    skip = page * 10

    query_data = {"guild_id": guild.id}
    if not violator and not moderator:
        return {}

    if violator:
        query_data['violator_id'] = violator.id

    if moderator:
        query_data['moderator_id'] = moderator.id

    search = database.violations.find(query_data).sort("_id", -1).skip(skip).limit(10)
    received = await search.to_list(length=10)
    if len(received) > 0:
        return received

    else:
        return {}


async def moderation_logging(
        bot: commands.AutoShardedBot,
        guild: discord.Guild,
        violator,
        moderator,
        action: str,
        reason: str
):
    """
    Automatically handles Moderation logging as long as it is called.

    ## Inputs:
    - guild_id: `guild.id`
    - violator: `user object` of violating user
    - moderator: `user object` of moderating user
    - action: Must be `banned / kicked / muted / warned` NOTHING ELSE.
    """

    try:
        server = await fetch_server(guild.id)
        if server and 'logs' in server and 'moderation' in server['logs']:
            channel = await bot.fetch_channel(server['logs']['moderation'])

            await channel.send(
                f"{emojis.MAJOR_WARNING} (`{violator.id}`) **{violator}** "
                f"was {action} by {moderator} (`{moderator.id}`) for "
                f"`{reason}`!\n"
            )

    except discord.Forbidden:
        await disable_logging(guild.id, "moderation")

    except discord.NotFound:
        await disable_logging(guild.id, "moderation")

    except Exception as e:
        print("Issue with moderation logging:", e)

    # Finally, Log the action that was taken
    await log_violation(guild, violator, moderator, action, reason)
