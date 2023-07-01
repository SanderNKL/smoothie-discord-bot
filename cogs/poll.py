from typing import Literal, Optional
import discord
from discord.ext import commands
from database import Database
import emojis as emojis
from discord import app_commands
import config as config
from discord.ui import Button, View
from time import time
from handlers import get


class CreateUpvotePoll(discord.ui.Modal, title='CREATE YOUR POLL'):
    def __init__(self, bot, db, required_role):
        super().__init__()
        self.bot = bot
        self.db = db
        self.required_role = required_role

    question = discord.ui.TextInput(
        label='What is the poll about?',
        placeholder='Text goes here...',
        required=True,
        style=discord.TextStyle.long
    )

    async def on_submit(self, interaction: discord.Interaction):
        data = {
            "question": self.question.value,
            "created": int(time()),
            "upvotes": [str(interaction.user.id)],
            "downvotes": [],
            "ended": False,
            "host": str(interaction.user.id)
        }

        embed = discord.Embed(
            description=data['question'],
            color=config.COLOR_SMOOTHIE
        )

        if self.required_role:
            data["required_role"] = self.required_role.id
            embed.add_field(
                name="Required Role",
                value=f"You must have the role <@&{self.required_role.id}> to vote",
            )

        embed.set_author(name=f"Poll submitted by: {interaction.user.name}", icon_url=get.user_avatar(interaction.user))
        embed.set_thumbnail(url=interaction.guild.icon.url)
        embed.set_footer(text="This poll is anonymous")

        buttons = [
            Button(
                label="Upvote (1)",
                style=discord.ButtonStyle.green,
                emoji=emojis.UPVOTE,
                custom_id="poll_upvote"
            ),
            Button(
                label="Downvote (0)",
                style=discord.ButtonStyle.gray,
                emoji=emojis.DOWNVOTE,
                custom_id="poll_downvote"
            ),
        ]

        view = View()
        for button in buttons:
            view.add_item(button)

        await interaction.response.send_message(embed=embed, view=view)
        message = await interaction.original_response()

        data["channel_id"] = message.channel.id
        data["message_id"] = message.id

        await Database().polls.insert_one(data)
        return

    async def on_error(self, error: Exception, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(
            'Oops! Something went wrong. '
            'Try sending the bug report in our server: https://discord.com/invite/WTfaSnPMBw',
            ephemeral=True
        )

        # Make sure we know what the error actually is
        print(error.__traceback__)


class CreateNumberedPoll(discord.ui.Modal, title='CREATE YOUR POLL'):
    def __init__(self, bot, db, required_role):
        super().__init__()
        self.bot = bot
        self.db = db
        self.required_role = required_role

    question = discord.ui.TextInput(
        label='Ouestion',
        placeholder='Text goes here...',
        required=True,
        style=discord.TextStyle.long
    )

    option = discord.ui.TextInput(
        label='Option 1 (Required)',
        placeholder='Text goes here...',
        required=True,
        style=discord.TextStyle.long
    )

    option_two = discord.ui.TextInput(
        label='Option 2 (Required)',
        placeholder='Text goes here...',
        required=True,
        style=discord.TextStyle.long
    )

    option_three = discord.ui.TextInput(
        label='Option 3 (Optional)',
        placeholder='May be left blank',
        required=False,
        style=discord.TextStyle.long
    )

    option_four = discord.ui.TextInput(
        label='Option 4 (Optional)',
        placeholder='May be left blank',
        required=False,
        style=discord.TextStyle.long
    )

    async def on_submit(self, interaction: discord.Interaction):
        data = {
            "question": self.question.value,
            "created": int(time()),
            "votes": {},
            "options": [],
            "ended": False,
            "host": str(interaction.user.id)
        }

        options = [
            self.option.value,
            self.option_two.value,
            self.option_three.value,
            self.option_four.value,
        ]

        view = View()
        i = 0
        for option in options:
            if option:
                i += 1
                data['options'].append(option)
                view.add_item(
                    Button(
                        style=discord.ButtonStyle.gray,
                        emoji=emojis.NUMBERS[i],
                        custom_id=f"poll_number_{i}"
                    )
                )

        embed = discord.Embed(
            description=data['question'],
            color=config.COLOR_SMOOTHIE
        )

        if self.required_role:
            data["required_role"] = self.required_role.id
            embed.add_field(
                name="Required Role",
                value=f"You must have the role <@&{self.required_role.id}> to vote",
            )

        embed.set_author(name=f"Poll submitted by: {interaction.user.name}", icon_url=get.user_avatar(interaction.user))
        embed.set_thumbnail(url=interaction.guild.icon.url)
        embed.set_footer(text="This poll is anonymous", icon_url=self.bot.application.icon.url)

        await interaction.response.send_message(embed=embed, view=view)
        message = await interaction.original_response()

        data["channel_id"] = message.channel.id
        data["message_id"] = message.id

        await Database().polls.insert_one(data)
        return

    async def on_error(self, error: Exception, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(
            'Oops! Something went wrong. '
            'Try sending the bug report in our server: https://discord.com/invite/WTfaSnPMBw',
            ephemeral=True
        )

        # Make sure we know what the error actually is
        print(error.__traceback__)


class Poll(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()

    def user_has_role(self, interaction: discord.Interaction, poll_data):
        """
        Check if the user has the required role
        """

        found = False
        for role in interaction.user.roles:
            if role.id == poll_data['required_role']:
                found = True
                break

        return found

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        """Detects when a user clicks a button or uses a slash command"""

        # Ensures that the interaction is a button, and not a slash commabd
        if interaction.type.name != "component":
            return

        button = interaction.data["custom_id"]
        button_content = button.split("_")

        if button_content[0] != "poll":
            return

        await interaction.response.defer()

        if button_content[1] == "number":
            poll_data = await self.db.polls.find_one({"message_id": interaction.message.id})
            if 'required_role' in poll_data:
                found = self.user_has_role(interaction, poll_data)

                if found is False:
                    await interaction.followup.send(
                        f"You can't vote on this poll. You need the role <@&{poll_data['required_role']}>",
                        ephemeral=True
                    )
                    return

            if poll_data is None:
                await interaction.followup.send("It appears this poll no longer exists!", ephemeral=True)
                return

            if (
                str(interaction.user.id) in poll_data['votes']
                and poll_data['votes'][str(interaction.user.id)] == button_content[2]
            ):
                await interaction.followup.send("You have already voted that!", ephemeral=True)
                return

            elif str(interaction.user.id) in poll_data['votes']:
                data = await self.db.polls.update_one(
                    {"message_id": interaction.message.id, f"upvotes.{interaction.user.id}": {"$exists": False}},
                    {"$set": {str(interaction.user.id): button_content[2]}}
                )

            else:
                data = await self.db.polls.update_one(
                    {"message_id": interaction.message.id, f"upvotes.{interaction.user.id}": {"$exists": False}},
                    {"$push": {str(interaction.user.id): button_content[2]}}
                )

            if data.modified_count > 0:
                view = await self.update_poll(interaction.message.id)
                await interaction.message.edit(view=view)
                await interaction.followup.send("Successfully voted on the post!", ephemeral=True)

            else:
                await interaction.followup.send(
                    "Failed to vote. Report this issue to the Smoothie support team if it persists.",
                    ephemeral=True
                )

        elif button_content[1] == "upvote":
            poll_data = await self.db.polls.find_one({"message_id": interaction.message.id})
            if 'required_role' in poll_data:
                found = self.user_has_role(interaction, poll_data)

                if found is False:
                    await interaction.followup.send(
                        f"You can't vote on this poll. You need the role <@&{poll_data['required_role']}>",
                        ephemeral=True
                    )
                    return

            if poll_data is None:
                await interaction.followup.send("It appears this poll no longer exists!", ephemeral=True)
                return

            if str(interaction.user.id) in poll_data['upvotes']:
                await interaction.followup.send("You have already upvoted this post!", ephemeral=True)
                return

            elif str(interaction.user.id) in poll_data['downvotes']:
                data = await self.db.polls.update_one(
                    {"message_id": interaction.message.id, f"upvotes.{interaction.user.id}": {"$exists": False}},
                    {"$pull": {"downvotes": str(interaction.user.id)}, "$push": {"upvotes": str(interaction.user.id)}}
                )

            else:
                data = await self.db.polls.update_one(
                    {"message_id": interaction.message.id, f"upvotes.{interaction.user.id}": {"$exists": False}},
                    {"$push": {"upvotes": str(interaction.user.id)}}
                )

            if data.modified_count > 0:
                view = await self.update_poll(interaction.message.id)
                await interaction.message.edit(view=view)
                await interaction.followup.send("Successfully upvoted the post!", ephemeral=True)

            else:
                await interaction.followup.send(
                    "Failed to upvote. Report this issue to the Smoothie support team if it persists.",
                    ephemeral=True
                )

        elif button_content[1] == "downvote":
            poll_data = await self.db.polls.find_one({"message_id": interaction.message.id})

            if 'required_role' in poll_data:
                found = self.user_has_role(interaction, poll_data)

                if found is False:
                    await interaction.followup.send(
                        f"You can't vote on this poll. You need the role <@&{poll_data['required_role']}>",
                        ephemeral=True
                    )
                    return

            if poll_data is None:
                await interaction.followup.send("It appears this poll no longer exists!", ephemeral=True)
                return

            if str(interaction.user.id) in poll_data['downvotes']:
                await interaction.followup.send("You have already upvoted this post!", ephemeral=True)
                return

            elif str(interaction.user.id) in poll_data['upvotes']:
                data = await self.db.polls.update_one(
                    {"message_id": interaction.message.id, f"downvotes.{interaction.user.id}": {"$exists": False}},
                    {"$pull": {"upvotes": str(interaction.user.id)}, "$push": {"downvotes": str(interaction.user.id)}}
                )

            else:
                data = await self.db.polls.update_one(
                    {"message_id": interaction.message.id, f"downvotes.{interaction.user.id}": {"$exists": False}},
                    {"$push": {"downvotes": str(interaction.user.id)}}
                )

            if data.modified_count > 0:
                view = await self.update_poll(interaction.message.id)
                await interaction.message.edit(view=view)
                await interaction.followup.send("Successfully downvoted the post!", ephemeral=True)

            else:
                await interaction.followup.send(
                    "Failed to downvote. Report this issue to the Smoothie support team if it persists.",
                    ephemeral=True
                )

    async def update_poll(self, message_id):
        poll_data = await self.db.polls.find_one({"message_id": message_id})
        view = View()

        if 'upvote' in poll_data:
            if len(poll_data['upvotes']) > len(poll_data['downvotes']):
                view.add_item(
                    Button(
                        label=f"Upvote ({len(poll_data['upvotes'])})",
                        style=discord.ButtonStyle.green,
                        emoji=emojis.UPVOTE,
                        custom_id="poll_upvote"
                    )
                )
                view.add_item(
                    Button(
                        label=f"Downvote ({len(poll_data['downvotes'])})",
                        style=discord.ButtonStyle.gray,
                        emoji=emojis.DOWNVOTE,
                        custom_id="poll_downvote"
                    )
                )

            elif len(poll_data['upvotes']) < len(poll_data['downvotes']):
                view.add_item(
                    Button(
                        label=f"Upvote ({len(poll_data['upvotes'])})",
                        style=discord.ButtonStyle.gray,
                        emoji=emojis.UPVOTE,
                        custom_id="poll_upvote"
                    )
                )
                view.add_item(
                    Button(
                        label=f"Downvote ({len(poll_data['downvotes'])})",
                        style=discord.ButtonStyle.red,
                        emoji=emojis.DOWNVOTE,
                        custom_id="poll_downvote"
                    )
                )

            else:
                view.add_item(
                    Button(
                        label=f"Upvote ({len(poll_data['upvotes'])})",
                        style=discord.ButtonStyle.gray,
                        emoji=emojis.UPVOTE,
                        custom_id="poll_upvote"
                    )
                )

                view.add_item(
                    Button(
                        label=f"Downvote ({len(poll_data['downvotes'])})",
                        style=discord.ButtonStyle.gray,
                        emoji=emojis.DOWNVOTE,
                        custom_id="poll_downvote"
                    )
                )

        elif 'vote' in poll_data:
            if len(poll_data['upvotes']) > len(poll_data['downvotes']):
                view.add_item(
                    Button(
                        label=f"Upvote ({len(poll_data['upvotes'])})",
                        style=discord.ButtonStyle.green,
                        emoji=emojis.UPVOTE,
                        custom_id="poll_upvote"
                    )
                )
                view.add_item(
                    Button(
                        label=f"Downvote ({len(poll_data['downvotes'])})",
                        style=discord.ButtonStyle.gray,
                        emoji=emojis.DOWNVOTE,
                        custom_id="poll_downvote"
                    )
                )

            elif len(poll_data['upvotes']) < len(poll_data['downvotes']):
                view.add_item(
                    Button(
                        label=f"Upvote ({len(poll_data['upvotes'])})",
                        style=discord.ButtonStyle.gray,
                        emoji=emojis.UPVOTE,
                        custom_id="poll_upvote"
                    )
                )
                view.add_item(
                    Button(
                        label=f"Downvote ({len(poll_data['downvotes'])})",
                        style=discord.ButtonStyle.red,
                        emoji=emojis.DOWNVOTE,
                        custom_id="poll_downvote"
                    )
                )

            else:
                view.add_item(
                    Button(
                        label=f"Upvote ({len(poll_data['upvotes'])})",
                        style=discord.ButtonStyle.gray,
                        emoji=emojis.UPVOTE,
                        custom_id="poll_upvote"
                    )
                )

                view.add_item(
                    Button(
                        label=f"Downvote ({len(poll_data['downvotes'])})",
                        style=discord.ButtonStyle.gray,
                        emoji=emojis.DOWNVOTE,
                        custom_id="poll_downvote"
                    )
                )

        return view

    @app_commands.command(
        name="poll",
        description="Create a poll!"
    )
    async def create_poll(
        self,
        interaction: discord.Interaction,
        poll_type: Literal['upvote'],
        required_role: Optional[discord.Role]
    ):
        if poll_type == "upvote":
            await interaction.response.send_modal(CreateUpvotePoll(self.bot, self.db, required_role))

        else:
            await interaction.response.send_modal(CreateNumberedPoll(self.bot, self.db, required_role))


async def setup(bot):
    await bot.add_cog(Poll(bot))
