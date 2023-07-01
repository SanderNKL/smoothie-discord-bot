import discord
from discord.ext import commands
from discord import app_commands
import json
import random

# NOT IMPLEMENTED YET!
# NOT IMPLEMENTED YET!
# NOT IMPLEMENTED YET!
# NOT IMPLEMENTED YET!
class WouldYouRather(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="wyr",
        description="Would You Rather?",
    )
    @app_commands.default_permissions(manage_messages=True)
    async def would_you_rather(
        self, interaction: discord.Interaction
    ):
        await interaction.response.defer()
        with open('configs/would_you_rather.json', 'r') as f:
            questions = json.load(f)

        embed = discord.Embed(
            title="Would You Rather?",
            description=random.choice(questions)
        )

        await interaction.followup.send(embed=embed)


async def setup(bot):
    await bot.add_cog(WouldYouRather(bot))
