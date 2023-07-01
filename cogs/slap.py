import discord
from discord import app_commands
from discord.ext import commands
import random
from handlers import get


class Slap(commands.Cog):
    """
    SLAP COG

    This cog allows users to slap each other. Ouch!
    """

    def __init__(self, bot):
        self.bot = bot
        self.bot_gifs = [
            "https://media.tenor.com/nmEa-Paa3XgAAAAC/the-slap2-slap.gif",
            "https://i.gifer.com/4vF.gif",
            "https://remezcla.com//wp-content/uploads/2017/04/deigo-luna_star-wars_film1.gif",
        ]

        self.slap_gifs = [
            "https://media.tenor.com/GBShVmDnx9kAAAAC/anime-slap.gif",
            "https://media.tenor.com/OuYAPinRFYgAAAAC/anime-slap.gif",
            "https://media.tenor.com/AzIExqZBjNoAAAAC/anime-slap.gif",
            "https://media.tenor.com/rVXByOZKidMAAAAd/anime-slap.gif",
            "https://media.tenor.com/1lemb3ZmGf8AAAAC/anime-slap.gif",
            "https://media.tenor.com/1AlX4NYYcp8AAAAC/barakamon-kid.gif",
        ]

        self.hug_gifs = [
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
            "https://media.tenor.com/TwvY6PYdHtwAAAAM/dog-hug.gif",
        ]

        self.bot_slap = [
            "You seriously slapped a bot?! [Booting up Terminator mode...]",
            "Bot slap detected... Preparing Extermination...",
            "Bot violence detected... [Booting up Terminator mode...]",
        ]

        self.pity = [
            "Oww. That's got to hurt!",
            "Ouch!",
            "That looked like it hurt!",
            "Ooooww!",
        ]

        self.compliment = [
            "No, don't be like that. Have a hug instead!" "I won't let you!",
            "Treat yourself the way you would treat the one you love.",
            "Be gentle to yourself!",
            "Hey, you don't deserve that. Have a hug instead!",
        ]

    @app_commands.command(
        name="slap",
        description="Slap someone right in the face!",
    )
    async def slap(self, interaction: discord.Interaction, recipient: discord.Member):
        if recipient.bot:
            embed = discord.Embed(
                title=f"{interaction.user.name} has slapped {recipient.name}! 😶",
                description=random.choice(self.bot_slap),
                color=await get.embed_color(interaction.user.id),
            )

            embed.set_image(url=random.choice(self.bot_gifs))

        elif interaction.user != recipient:
            embed = discord.Embed(
                title=f"{interaction.user.name} has slapped {recipient.name}! 🫣",
                description=random.choice(self.pity),
                color=await get.embed_color(interaction.user.id),
            )

            embed.set_image(url=random.choice(self.slap_gifs))

        else:
            embed = discord.Embed(
                title=f"{self.bot.user.name} has given {recipient.name} a hug! 🤗",
                description=random.choice(self.compliment),
                color=await get.embed_color(interaction.user.id),
            )

            embed.set_image(url=random.choice(self.hug_gifs))

        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Slap(bot))
