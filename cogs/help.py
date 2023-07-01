import discord
from discord import app_commands
from discord.ext import commands
from database import Database
import config as config
from handlers import get


class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()

    @app_commands.command(
        name="help",
        description="Learn more about smoothie"
    )
    async def help(self, interaction: discord.Interaction):
        """Opens a help menu to assist users"""

        embed = discord.Embed(
            description=(
                f"""
                \n**Server Commands**\n
                • [/suggest]({config.SERVER_INVITE_LINK}) - Suggest a feature to your server!\n
                \n**Moderation commands**\n
                f• [/warn]({config.SERVER_INVITE_LINK}) - Warn a discord user\n
                f• [/mute]({config.SERVER_INVITE_LINK}) - Mute a discord user\n
                f• [/ban]({config.SERVER_INVITE_LINK}) - Ban a discord user\n
                f• [/violations]({config.SERVER_INVITE_LINK}) - See the violations given to a user or given by a mod.\n
                \n**Giveaways**\n
                f• [/giveaway create]({config.SERVER_INVITE_LINK}) - Create a giveaway for your server\n
                f• [/giveaway grant]({config.SERVER_INVITE_LINK}) - Give users & roles access to creating giveaways\n
                f• [/giveaway revoke]({config.SERVER_INVITE_LINK}) - Remove users & roles from to creating giveaways\n
                • [/giveaway access]({config.SERVER_INVITE_LINK}) - See users and roles that have access\n
                \n**Utility Commands**\n
                f• [/invites]({config.SERVER_INVITE_LINK}) - See a users invite count\n
                f• [/messages]({config.SERVER_INVITE_LINK}) - See a users message count\n
                f• [/send]({config.SERVER_INVITE_LINK}) - Make smoothie send an embed a message!\n
                f• [/setup]({config.SERVER_INVITE_LINK}) - Set up logs, autoroles, and more!\n
                f• [/purge]({config.SERVER_INVITE_LINK}) - Mass delete messages from a channel\n
                f• [/lock]({config.SERVER_INVITE_LINK}) - Lock a channel permanently or temporarily\n
                f• [/unlock]({config.SERVER_INVITE_LINK}) - Unlock a channel\n
                f• [/reminder]({config.SERVER_INVITE_LINK}) - Get a reminder!\n
                f• [/timer]({config.SERVER_INVITE_LINK}) - Set a timer!\n
                f• [/poll]({config.SERVER_INVITE_LINK}) - Create a poll!\n
                \n**Fun Commands**\n
                f• [/meme]({config.SERVER_INVITE_LINK}) - Get dank memes\n
                f• [/cute]({config.SERVER_INVITE_LINK}) - Get cute pictures\n
                f• [/slap]({config.SERVER_INVITE_LINK}) - Slap a user\n
                f• [/hug]({config.SERVER_INVITE_LINK}) - Hug a user\n
                f• [/pat]({config.SERVER_INVITE_LINK}) - Pat a user\n
                f• [/8ball]({config.SERVER_INVITE_LINK}) - Ask the 8ball a question\n
                f• [/choose]({config.SERVER_INVITE_LINK}) - Make Smoothie choose!\n
                f• [/truthordare]({config.SERVER_INVITE_LINK}) - Play a game of truth or dare!\n
                f\n**Game Commands**\n
                f• [/cad]({config.SERVER_INVITE_LINK}) - Play a game of Cards against Humanity!\n
                f• [/conenct4]({config.SERVER_INVITE_LINK}) - Play a game of connect4\n
                f• [/tictactoe]({config.SERVER_INVITE_LINK}) - Play a game of tictactoe!\n
                """
                
            ),
            color=await get.embed_color(interaction.user.id)
        )

        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Help(bot))
