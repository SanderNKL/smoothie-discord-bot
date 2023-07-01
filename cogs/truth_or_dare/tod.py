import discord
from discord.ext import commands
from discord import app_commands
import random
from handlers import get
from discord.ui import Button, View


view = View()
view.add_item(
    Button(
        label="Truth",
        emoji="😇",
        custom_id="tod_truth"
    )
)

view.add_item(
    Button(
        label="Dare",
        emoji="😈",
        custom_id="tod_dare"
    )
)


class WouldYouRather(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        # Ensures that the interaction is a button, and not a slash commabd
        if interaction.type.name != "component":
            return

        button = interaction.data["custom_id"].split("_")
        if button[0] != "tod":
            return

        if button[1] == "truth":
            await self.truth(interaction)

        if button[1] == "dare":
            await self.dare(interaction)

    async def dare(
        self,
        interaction: discord.Interaction
    ):
        await interaction.response.defer()
        with open("text/dare.txt", "r", encoding="utf-8") as f:
            dare = f.read().splitlines()

        question = random.randint(0, len(dare)-1)

        await interaction.followup.send(
            embed=discord.Embed(
                title=f"{interaction.user.name}'s dare! 😈",
                description=dare[question],
                color=await get.embed_color(interaction.user.id)
            ).set_footer(
                text=f"Truth Or Dare | Question: #{question}",
                icon_url=self.bot.application.icon.url
            ),
            view=view
        )

    async def truth(
        self,
        interaction: discord.Interaction
    ):
        await interaction.response.defer()

        with open("text/truth.txt", "r", encoding="utf-8") as f:
            truth = f.read().splitlines()

        question = random.randint(0, len(truth)-1)

        await interaction.followup.send(
            embed=discord.Embed(
                title=f"{interaction.user.name}'s Truth! 😇",
                description=truth[question],
                color=await get.embed_color(interaction.user.id)
            ).set_footer(
                text=f"Truth Or Dare | Question: #{question}",
                icon_url=self.bot.application.icon.url
            ),
            view=view
        )

    @app_commands.command(
        name="truthordare",
        description="Let's play a game of truth or dare!"
    )
    @app_commands.default_permissions(manage_messages=True)
    async def truthordare(
        self,
        interaction: discord.Interaction
    ):
        await interaction.response.send_message(
            embed= discord.Embed(
                title=f"Truth or Dare?",
                description="You choose!",
                color=await get.embed_color(interaction.user.id)
            ),
            view=view
        )

async def setup(bot):
    await bot.add_cog(WouldYouRather(bot))
