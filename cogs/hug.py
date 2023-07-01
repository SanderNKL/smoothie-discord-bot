import discord
from discord import app_commands
from discord.ext import commands
from handlers import get
import random


class Hug(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.gifs = [
            # Cats
            "https://c.tenor.com/zYJO9AovWgYAAAAC/cat-hug.gif",
            "https://media.tenor.com/kBlRhi7nqYwAAAAC/cat-hugs-alydn.gif",
            "https://media.tenor.com/wSJZSQqIHhUAAAAM/love-cats-cat.gif",
            "https://i.pinimg.com/originals/f8/f2/8e/f8f28eb6e935987fb1dd92b81cc2ead7.gif",
            "https://media.tenor.com/eAKshP8ZYWAAAAAM/cat-love.gif",
            "https://media.tenor.com/RW6pudwHS9YAAAAM/mochi-mochi-peach-cat-white-cat.gif",
            "https://cdn.shopify.com/s/files/1/0344/6469/files/cat-hug-13.gif?v=1527882244",
            # Dogs
            "https://media.tenor.com/t6_eM5VECsUAAAAC/hugs-and.gif",
            "https://media1.giphy.com/media/jGRHaDpv4Y4mRU5hkF/giphy.gif?cid=6c09b95273976c923b099f2812898c6dfd748949d7e186cf&ep=v1_internal_gifs_gifId&rid=giphy.gif&ct=g",
            "https://media4.giphy.com/media/cFI3VyVHYhQusx3QiS/giphy.gif?cid=6c09b952f2905a82a5c42fe99150cffa95078803eb4fcbb8&ep=v1_internal_gifs_gifId&rid=giphy.gif&ct=g",
            "https://media.tenor.com/TwvY6PYdHtwAAAAM/dog-hug.gif"
        ]

        self.compliments = [
            "Awww!",
            "How adorable!",
            "Look at you both... So adorable! ❤️",
            "Bet that felt good!"
        ]

        self.pity = [
            "Don't hug yourself... Have a hug from me instead! ❤️",
            "I'm sorry... Here's a hug from me instead!",
            "I'll give you a hug instead",
        ]

    @app_commands.command(
        name="hug",
        description="Send someone a hug <3",
    )
    async def hug(self, interaction: discord.Interaction, recipient: discord.Member):

        if interaction.user != recipient:
            embed = discord.Embed(
                title=f"{interaction.user.name} has given {recipient.name} a hug! 🤗",
                description=random.choice(self.compliments),
                color=await get.embed_color(interaction.user.id)
            )

        else:
            embed = discord.Embed(
                title=f"{self.bot.user.name} has given {recipient.name} a hug! 🤗",
                description=random.choice(self.pity),
                color=await get.embed_color(interaction.user.id)
            )

        embed.set_image(url=random.choice(self.gifs))
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Hug(bot))
