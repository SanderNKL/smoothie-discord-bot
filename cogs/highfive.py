import discord
from discord import app_commands
from discord.ext import commands
from handlers import get
import random


class Highfive(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="highfive",
        description="Give someone a highfive!",

    )
    async def highfive(self, interaction: discord.Interaction, user: discord.User):
        """Get cute posts from reddit"""
        await interaction.response.defer()

        compliments = [
            'Highfive!',
            'Heck Yeah!',
            'Awesome!',
            'Wooohoo!',
            'Yaay!',
            'Super!'
        ]

        gifs = [
            'https://media.tenor.com/JBBZ9mQntx8AAAAC/anime-high-five.gif',
            'https://64.media.tumblr.com/670b47fe8f7da2a49e8089ccfa233c9d/tumblr_pc1t0wl1xR1wn2b96o1_1280.gif',
            'https://media.tenor.com/mpzev9mwQkQAAAAM/yay-high-five.gif',
            'https://media.tenor.com/0WN6DfnOfF8AAAAM/wataten-watashi-ni-tenshi-ga-maiorita.gif'
        ]

        embed = discord.Embed(
            description=random.choice(compliments),
            color=await get.embed_color(interaction.user.id)
        )

        embed.set_image(url=random.choice(gifs))
        embed.set_author(
            name=f"{interaction.user.name} highfived {user.name}!",
            icon_url=get.user_avatar(interaction.user)
        )

        await interaction.followup.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Highfive(bot))
