import discord
from discord import app_commands
from discord.ext import commands
import random
from handlers import get


class EightBall(commands.Cog):
    """
    EIGHT BALL COG

    This cog allows users to ask an 8ball yes/no questions.
    The bot will respond with a "wise" and totally not random response
    """

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="8ball",
        description="Ask the magic 8ball a question",

    )
    async def eightball(self, interaction: discord.Interaction, question: str):
        if len(question) > 100:
            await interaction.response.send_message(
                "Your question is a bit long... Try something shorter than 100 characters. :)",
                ephemeral=True)
            return

        answers = [
            "It is certain.",
            "It is decidedly so.",
            "Without a doubt.",
            "Yes definitely",
            "You may rely on it",
            "As I see it, yes.",
            "Most likely.",
            "Outlook good.",
            "Yes.",
            "Signs point to yes.",
            "Reply hazy, try again.",
            "I'm having trouble predicting that. Could you try again?",
            "Ask again later.",
            "Better not tell you now.",
            "Cannot predict now.",
            "Concentrate and ask again.",
            "Don't count on it.",
            "My reply is no.",
            "My sources say no.",
            "Outlook not so good.",
            "Very doubtful."
        ]

        embed = discord.Embed(
            title=question,
            description=random.choice(answers),
            color=await get.embed_color(interaction.user.id)
        )

        embed.set_thumbnail(url="https://i.imgur.com/XrDkFkh.png")
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(EightBall(bot))
