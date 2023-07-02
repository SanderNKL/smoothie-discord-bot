import discord
from discord.ui import Button, View
from discord.ext import commands
from discord import app_commands
from database import Database
import emojis as emojis
import datetime
import config as config
from handlers import get


class SendSuggestion(discord.ui.Modal, title="Make a suggestion for your server!"):
    def __init__(self, bot, db, server_id):
        super().__init__()
        self.bot = bot
        self.db = db
        self.server_id = server_id

    suggestion = discord.ui.TextInput(
        label="Title",
        placeholder="Let us know what's on your mind",
        required=True,
        max_length=30,
    )

    description = discord.ui.TextInput(
        label="Description",
        placeholder="Why should this be done?",
        style=discord.TextStyle.long,
        required=True,
        max_length=1000,
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()  # Let's discord know we are processing it
        failed_suggestion = False  # If true, we alert the player

        embed = discord.Embed(
            title=self.suggestion.value.capitalize(),
            description=self.description.value,
            timestamp=datetime.datetime.utcnow(),
            color=await get.embed_color(interaction.user.id),
        )

        embed.set_author(
            name=f"Suggested by {interaction.user}",
            icon_url=get.user_avatar(interaction.user),
        )

        server = await Database().get_server(self.server_id)
        try:
            channel = await self.bot.fetch_channel(server["suggestions"]["channel"])
            message = await channel.send(embed=embed)
            thread = await message.create_thread(
                name=self.suggestion.value, auto_archive_duration=10080
            )

            buttons = [
                Button(
                    label="Accept Suggestion",
                    style=discord.ButtonStyle.green,
                    custom_id=f"suggestions_accept_{thread.id}",
                ),
                Button(
                    label="Reject Suggestion",
                    style=discord.ButtonStyle.red,
                    custom_id=f"suggestions_reject_{thread.id}",
                ),
            ]

            view = View()
            for button in buttons:
                view.add_item(button)

            await thread.send(
                f"{emojis.REFRESH} **Administrate Suggestion**", view=view
            )

        except Exception as e:
            print("Issue gathering or sending suggestion message:", e)
            failed_suggestion = True

        upvote_emoji = emojis.UPVOTE
        downvote_emoji = emojis.DOWNVOTE

        if "upvote_emoji" in server["suggestions"]:
            upvote_emoji = server["suggestions"]["upvote_emoji"]

        if "downvote_emoji" in server["suggestions"]:
            downvote_emoji = server["suggestions"]["downvote_emoji"]

        try:
            await message.add_reaction(upvote_emoji)
            await message.add_reaction(downvote_emoji)

        except Exception as e:
            print("issue adding message reaction:", e)
            failed_suggestion = True

        if failed_suggestion:
            await interaction.followup.send(
                f"{emojis.MAJOR_WARNING} **NOTICE**: Your suggestion has issues. Notify your server administrator to fix it.\n"
                "It may be a simple permission issue, emoji issue, or that they have improperly set this up!",
                ephemeral=True,
            )

            return

        await interaction.followup.send(
            f"Suggestion submitted! Your suggestion can be found [**here**]({message.jump_url})",
            ephemeral=True,
        )

    async def on_error(
        self, error: Exception, interaction: discord.Interaction
    ) -> None:
        await interaction.followup.send("Oops! Something went wrong.", ephemeral=True)

        # Make sure we know what the error actually is
        print(error.__traceback__)


class Suggestions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        """Detects when a user clicks a button or uses a slash command"""
        # Ensures that the interaction is a button, and not a slash commabd
        if interaction.type.name != "component":
            return

        button = interaction.data["custom_id"]
        # We make sure the button is a minigame button

        if button[0:11] != "suggestions":
            return

        server = await self.db.get_server(str(interaction.guild.id))

        if button[0:18] == "suggestions_accept":
            permissions = interaction.channel.permissions_for(interaction.user)
            if permissions.manage_guild is False:

                await interaction.response.send_message(
                    "You can't do that!", ephemeral=True
                )
                return

            id = button[19:]
            channel = await self.bot.fetch_channel(server["suggestions"]["channel"])
            message = await channel.fetch_message(int(id))

            original_embed = message.embeds[0]
            embed = discord.Embed(
                title=original_embed.title,
                description=original_embed.description,
                color=config.COLOR_ACCEPTED,
            )

            embed.set_author(
                name=original_embed.author.name, icon_url=original_embed.author.icon_url
            )

            embed.set_footer(
                text=f"This suggestion was accepted by {interaction.user}",
                icon_url=get.user_avatar(interaction.user),
            )

            await message.edit(embed=embed)
            await interaction.response.send_message(
                "You accepted this suggestion! (You may change your mind)",
                ephemeral=True,
            )

        if button[0:18] == "suggestions_reject":
            permissions = interaction.channel.permissions_for(interaction.user)
            if permissions.manage_guild is False:

                await interaction.response.send_message(
                    "You can't do that!", ephemeral=True
                )
                return

            id = button[19:]
            channel = await self.bot.fetch_channel(server["suggestions"]["channel"])
            message = await channel.fetch_message(int(id))

            original_embed = message.embeds[0]
            embed = discord.Embed(
                title=original_embed.title,
                description=original_embed.description,
                color=config.COLOR_ERROR,
            )

            embed.set_author(
                name=original_embed.author.name, icon_url=original_embed.author.icon_url
            )
            embed.set_footer(
                text=f"This suggestion was rejected by {interaction.user}",
                icon_url=get.user_avatar(interaction.user),
            )

            await message.edit(embed=embed)
            await interaction.response.send_message(
                "You rejected this suggestion! (You may change your mind)",
                ephemeral=True,
            )

    @app_commands.command(
        name="suggest", description="Send a suggestion to your server!"
    )
    async def suggest_command(self, interaction: discord.Interaction):
        server = await self.db.get_server(str(interaction.guild.id))
        if (
            server is None
            or "suggestions" not in server
            or server["suggestions"]["channel"] is None
        ):
            await interaction.response.send_message(
                "Your server doesn't support this feature!\n"
                "Tell your administrator to use [**/setup suggestions**](https://discord.com/invite/WTfaSnPMBw)",
                ephemeral=True,
            )

        else:
            await interaction.response.send_modal(
                SendSuggestion(
                    self.bot, Database, str(interaction.guild.id), config.COLOR_SMOOTHIE
                )
            )


async def setup(bot):
    await bot.add_cog(Suggestions(bot))
