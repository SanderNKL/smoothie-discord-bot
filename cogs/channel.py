import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Button, View, Select
from database import Database
import emojis as emojis
from typing import Literal
from handlers import get


class ChannelManagement(commands.GroupCog, name="channel"):
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
        if button[0:6] != "manage":
            return

        await interaction.response.defer()  # Let's discord know we are processing it
        user_id = str(interaction.user.id)

        if button[0:13] == "manage_thread":
            thread = interaction.guild.get_thread(interaction.channel_id)

            if user_id != button[14:] and interaction.user.guild_permissions.manage_threads is False:
                await interaction.followup.send("You don't moderate this thread. Shoo!", ephemeral=True)
                return

            if thread:
                duration = int(interaction.data['values'][0])
                await thread.edit(auto_archive_duration=duration)

                # Add a way for thread owner or server mod to administrate the thread
                buttons = self.thread_dropdown(user_id, duration)
                view = View()
                for button in buttons:
                    view.add_item(button)

                await interaction.message.edit(view=view)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.guild is None:
            return

        if message.author.bot:
            return

        server = await self.db.get_server(str(message.guild.id))

        if 'channels' not in server:
            return

        if str(message.channel.id) not in server['channels']:
            return

        if server['channels'][str(message.channel.id)]["channel_type"] == "threads":
            await self.add_thread(message)

        return

    def thread_dropdown(self, user_id, new_duration):
        options = []
        times = {60: "1 Hour", 1440: "1 Days", 4320: "3 Days", 10080: "1 Week"}

        for duration in times:
            is_default = False
            if duration == new_duration:
                is_default = True

            options.append(
                discord.SelectOption(
                    default=is_default,
                    value=duration,
                    label=times[duration],
                    description=f'Archives after {times[duration]} of inactivity'
                )
            )

        return [
            Select(
                custom_id=f"manage_thread_{user_id}",
                options=options
            )
        ]

    async def add_thread(self, message: discord.Message):
        """Adds a thread to a message"""
        thread = await message.create_thread(name=f"{message.author.name}'s thread", auto_archive_duration=4320)
        duration = 4320
        user_id = str(message.author.id)

        # Add a way for thread owner or server mod to administrate the thread
        buttons = self.thread_dropdown(user_id, duration)

        view = View()
        for button in buttons:
            view.add_item(button)

        await thread.send(f"{emojis.TIMER} **Thread Archives After**", view=view)

    async def setup_suggestions(self, interaction: discord.Interaction, user_id, channel):
        try:  # We try to send a message that auto deletes to ensure the bot has permissions
            await channel.send("This is a test message. Auto deletes in 2 seconds...", delete_after=2)

        except discord.Forbidden:
            await interaction.followup.send_message(
                f"Failed to send messages to <#{channel.id}>.\n"
                "Give me `Send messages` permission and try again!",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title=f"{emojis.HOT} Customise Suggestions",
            description=(
                f"Suggestions will be forwarded to: <#{channel.id}>\n"
                "If this is not the channel you want, or something went wrong, please use "
                "[**/setup suggestions**](https://discord.com/invite/WTfaSnPMBw) again!\n\n"
                "Use [**/disable suggestions**](https://discord.com/invite/WTfaSnPMBw) "
                "if you wish to disable this feature"
            ),
            color=await get.embed_color(interaction.user.id)
        )

        await self.db.update_server(interaction.guild.id, "suggestions.channel", channel.id)
        await self.db.update_server(interaction.guild.id, "suggestions.upvote_emoji", emojis.UPVOTE)
        await self.db.update_server(interaction.guild.id, "suggestions.downvote_emoji", emojis.DOWNVOTE)

        custom_emojis = await self.load_user_perk(user_id, "custom_suggestion_emojis")

        buttons = []

        if custom_emojis:
            buttons.append(
                Button(
                    label="Custom Upvote",
                    style=discord.ButtonStyle.green,
                    emoji=emojis.UPVOTE,
                    custom_id=f"setup_upvote_{user_id}"
                )
            )

            buttons.append(
                Button(
                    label="Custom Downvote",
                    style=discord.ButtonStyle.green,
                    emoji=emojis.DOWNVOTE,
                    custom_id=f"setup_downvote_{user_id}"
                )
            )

        else:
            buttons.append(
                Button(
                    label="Custom Upvote",
                    style=discord.ButtonStyle.red,
                    emoji=emojis.UPVOTE,
                    custom_id=f"setup_upvote_{user_id}"
                )
            )

            buttons.append(
                Button(
                    label="Custom Downvote",
                    style=discord.ButtonStyle.red,
                    emoji=emojis.DOWNVOTE,
                    custom_id=f"setup_downvote_{user_id}"
                )
            )

        view = View()
        for button in buttons:
            view.add_item(button)

        await interaction.followup.send(
            "This channel is now a **SUGGESTIONS** channel\n"
            "Your users can now use [**/suggest**](https://discord.com/invite/WTfaSnPMBw)\n"
            "We **recommend** that you make this channel **locked** for all users.",
            embed=embed,
            view=view,
            ephemeral=True
        )

    def uses_suggestions(self, server, channel):
        if 'suggestions' in server:
            if channel.id == server['suggestions']['channel']:
                return True

        return False

    @app_commands.command(
        name="type",
        description="Choose the channel type",
    )
    @app_commands.default_permissions(manage_guild=True)
    async def channel_type(self, interaction: discord.Interaction, type: Literal["suggestions", "threads", "nothing"]):
        user_id = str(interaction.user.id)
        channel = interaction.channel
        server = await self.db.get_server(str(interaction.guild.id))  # to ensure it exists

        await interaction.response.defer()

        if type == "nothing":
            await self.db.update_server(interaction.guild.id, f"channels.{channel.id}", 1, True)

            if self.uses_suggestions(server, channel):
                await self.db.update_server(interaction.guild.id, "suggestions", 1, True)
                await interaction.followup.send(
                    "this channel was previously a suggestions channel, but is now nothing"
                )
                return

            await interaction.followup.send("This channel is no longer managed by me")

        elif type == "suggestions":
            await self.db.update_server(interaction.guild.id, f"channels.{channel.id}", {"channel_type": type})
            await self.setup_suggestions(interaction, user_id, channel)

        else:
            await self.db.update_server(interaction.guild.id, f"channels.{channel.id}", {"channel_type": type})

            if self.uses_suggestions(server, channel):
                await self.db.update_server(interaction.guild.id, "suggestions", 1, True)
                await interaction.followup.send(
                    f"this channel was previously a suggestions channel, but is now a **{type}** channel"
                )
                return

            await interaction.followup.send(f"This channel is now a **{type}** channel.")


async def setup(bot):
    await bot.add_cog(ChannelManagement(bot))
