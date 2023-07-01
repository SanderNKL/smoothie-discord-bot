import discord
from discord import app_commands
from discord.ext import commands
import random
from handlers import get
from typing import Literal


class Roll(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="roll",
        description="Roll a dice of your choice!",
    )
    async def roll(
        self,
        interaction: discord.Interaction,
        dice: Literal["d3", "d8", "dice", "d20", "d40"] = "dice",
    ):
        if dice == "dice":
            rolled_number = random.randint(1, 6)

        else:
            rolled_number = random.randint(1, int(dice.replace("d", "")))

        embed = discord.Embed(
            description=f"You rolled a `{dice}` and got `{rolled_number}`",
            color=await get.embed_color(interaction.user.id),
        )

        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Roll(bot))
