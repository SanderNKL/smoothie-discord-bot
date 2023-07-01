import validators
import discord
from discord import app_commands
from discord.ext import commands
from database import Database
from handlers.get import embed_color


class SendMessage(discord.ui.Modal, title='Send a Message!'):
    """
    SEND MESSAGE MODAL

    Modals allow users to fill out a form.
    The user can here add in embed fields for the bot to send.
    """

    def __init__(self, bot, color):
        super().__init__()
        self.bot = bot
        self.color = color

    name = discord.ui.TextInput(
        label='Title (Optional)',
        placeholder='Title goes here...',
        required=False,
        max_length=80
    )

    description = discord.ui.TextInput(
        label='Description (Optional)',
        placeholder='Description goes here...',
        required=False,
        style=discord.TextStyle.long,
        max_length=2000
    )

    footer = discord.ui.TextInput(
        label='Footer (Optional)',
        placeholder='Footer goes here...',
        required=False,
        style=discord.TextStyle.long,
        max_length=2000
    )

    image = discord.ui.TextInput(
        label='Image (Optional)',
        placeholder='Image link goes here...',
        required=False,
        style=discord.TextStyle.long
    )

    thumbnail = discord.ui.TextInput(
        label='Thumbnail (Optional)',
        placeholder='Image link goes here...',
        required=False,
        style=discord.TextStyle.long
    )

    async def on_submit(self, interaction: discord.Interaction):
        if (
            self.name.value == ""
            and self.description.value == ""
            and self.image.value == ""
            and self.thumbnail.value == ""
        ):
            await interaction.response.send_message(
                "I can't send an empty message...",
                ephemeral=True
            )
            return

        name = self.name.value
        if name == "":
            name = None

        description = self.description.value
        if description == "":
            description = None

        footer = self.footer.value
        if footer == "":
            footer = None

        embed = discord.Embed(
            title=name,
            description=description,
            color=self.color
        )

        if footer:
            embed.set_footer(text=footer)

        if validators.url(self.image.value):
            embed.set_image(url=self.image.value)

        if validators.url(self.thumbnail.value):
            embed.set_thumbnail(url=self.thumbnail.value)

        await interaction.response.defer()  # Let's discord know we are processing it
        await interaction.channel.send(embed=embed)

        return

    async def on_error(self, error: Exception, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(
            'Oops! Something went wrong. '
            'Try sending the bug report in our server: https://discord.com/invite/WTfaSnPMBw',
            ephemeral=True
        )

        # Make sure we know what the error actually is
        print(error.__traceback__)


class Send(commands.Cog):
    """
    SEND COG

    This cog allows users to go send
    custom messages with Smoothie.
    """

    def __init__(self, bot):
        self.bot = bot
        self.db = Database()

    @app_commands.command(name="send", description="Send a message!")
    @app_commands.default_permissions(manage_guild=True)
    async def send(self, interaction: discord.Interaction):
        await interaction.response.send_modal(
            SendMessage(
                self.bot,
                await embed_color(interaction.user.id)
            )
        )


async def setup(bot):
    await bot.add_cog(Send(bot))
