'''
------------------------------------------------------
    .d8888b.                                      888    888      d8b
    d88P  Y88b                                    888    888      Y8P
    Y88b.                                         888    888
    "Y888b.    88888b.d88b.    .d88b.   .d88b.  888888 88888b.   888  .d88b.
       "Y88b.  888 "888 "88b  d88""88b d88""88b  888    888 "88b 888 d8P  Y8b
         "888  888  888   888 888  888 888  888  888    888  888 888 88888888
    Y88b  d88P 888  888   888 Y88..88P Y88..88P  Y88b.  888  888 888 Y8b.
    "Y8888P"   888  888   888  "Y88P"   "Y88P"   "Y888  888  888 888  "Y8888

    Developer: Nattugle
    2022 / 2023
-------------------------------------------------------
'''

import discord
from discord.ext import commands
from database import Database
import config as config
from handlers import healthcheck

DATABASE = Database()
INTENTS = discord.Intents.default()
INTENTS.guilds = True
INTENTS.message_content = True

bot = commands.AutoShardedBot(
    intents=INTENTS,
    shard_count=config.BOT_SHARDS,
    case_insensitive=True,
    command_prefix=config.BOT_PREFIX,
    chunk_guilds_at_startup=False,
)

bot.remove_command("help")

# Only if the bot is the main bot shall we do this
# IF you don't use digital oceans app platform, you can remove the health check
if config.FAKE_HEALTH_CHECK:
    healthcheck.fake_health_check()

COGS = [
    'cogs.memes',
    'cogs.cute',
    'cogs.highfive',
    'cogs.giveaway',
    'cogs.poll',
    'cogs.reminder',
    'cogs.moderation',
    'cogs.channel_lock',
    'cogs.violations',
    'cogs.translations.translator',
    'cogs.suggestions',
    'cogs.reaction_roles',
    'cogs.truth_or_dare.tod',
    'cogs.setup',
    'cogs.help',
    'cogs.roles',
    'cogs.roll',
    'cogs.channel',
    'cogs.send',
    'cogs.messages',
    'cogs.8ball',
    'cogs.hug',
    'cogs.pat',
    'cogs.slap',
    'cogs.invites',
    'cogs.choose',
    'cogs.connect4',
    'cogs.ttt',
]

@bot.event
async def on_disconnect():
    print("[! CONNECTION LOSS]: Lost connection to Discord. Bot will automatically try to reconnect.")

@bot.event
async def on_ready():
    try:
        await bot.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.playing,
                name=f"in {str(len(bot.guilds))} guilds!"
            )
        )

        for cog in COGS:
            try:
                print("Loading cog:", cog)
                await bot.load_extension(cog)

            except Exception as e:
                print("Issues with cog: {}. ({})".format(cog, e))

        await bot.tree.sync()

        print(
            f"""
            Smoothie . gg

            Currently in I'm currently in: {str(len(bot.guilds))} servers!
            """
        )

    except Exception as e:
        print("Bot code encountered an error:", e)

bot.run(
    token=config.BOT_TOKEN
)
