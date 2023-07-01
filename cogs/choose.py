import discord
from discord import app_commands
from discord.ext import commands
import random
from handlers import get


class Choose(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="choose",
        description="Make me choose something for you!",
    )
    async def choose(self, interaction: discord.Interaction, one: str, two: str):
        """Makes smoothie pick an option"""

        choices = [one, two]

        descriptions = [
            f"You should definetly go with **{random.choice(choices)}**!",
            f"My gut feeling tells me that **{random.choice(choices)}** is the right choice...",
            f"I'm sure you would agree that **{random.choice(choices)}** is the supirior choice"
        ]

        choice = random.choice(descriptions)

        #  If they try to choose against smoothie, the bot will be biased
        def rigged_response(choice):
            rigged_descriptions = [
                f"Without a doubt, I'd pick **{choice}**!",
                f"Not that I'm biased, but I choose **{choice}** ❤️",
                f"My totally unbiased opinion says that **{choice}** is the best",
                f"I will ignore my programming and say **{choice}**!",
                f"You know **{choice}** is right. Why even ask?"
            ]

            return random.choice(rigged_descriptions)

        if "smoothie" in choices[0].lower() and "smoothie" not in choices[1].lower():
            choice = rigged_response(choices[0])

        elif "smoothie" in choices[1].lower() and "smoothie" not in choices[0].lower():
            choice = rigged_response(choices[1])

        embed = discord.Embed(
            color=await get.embed_color(interaction.user.id)
        )

        embed.add_field(
            name=f"**{one.capitalize()}** or **{two.capitalize()}**?\n",
            value=f"{choice.capitalize()}"
        )

        embed.set_thumbnail(url="https://i.imgur.com/Y5kIUuP.png")
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Choose(bot))
