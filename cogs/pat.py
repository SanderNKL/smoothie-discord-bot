import discord
from discord import app_commands
from discord.ext import commands
from handlers import get
import random


class pat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.gifs = [
            "https://gifdb.com/images/high/cute-anime-umaru-head-pat-rabcmvfkpeuteckt.gif",
            "https://i.gifer.com/origin/a6/a68b167d7e9c8a47df7720a2cda1adfe.gif",
            "https://media.tenor.com/aZFqg65KvssAAAAC/pat-anime.gif"
        ]

        self.self_pat_gif = [
            "https://media3.giphy.com/media/XGnH2RGHoCqumsAXpo/giphy.gif",
            "https://media.tenor.com/9MYFMp6CyTYAAAAC/isnt-it-romantic-thumbs-up.gif"
        ]

        self.compliments = [
            "Pat Pat!",
            "Yes, Pat Pat.",
        ]

        self.pity = [
            "This is awkward..",
            "Ehh, self pity much?",
            "Okay."
        ]

    @app_commands.command(
        name="pat",
        description="Pat someone!",
    )
    async def pat(self, interaction: discord.Interaction, recipient: discord.Member):

        if interaction.user != recipient:
            embed = discord.Embed(
                title=f"{interaction.user.name} pats {recipient.name}! 🫳",
                description=random.choice(self.compliments),
                color=await get.embed_color(interaction.user.id)
            )
            embed.set_image(url=random.choice(self.gifs))

        else:
            embed = discord.Embed(
                title=f"{interaction.user.name} pat themselves. 🫳",
                description=random.choice(self.pity),
                color=await get.embed_color(interaction.user.id)
            )
            embed.set_image(url=random.choice(self.self_pat_gif))
        
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(pat(bot))
