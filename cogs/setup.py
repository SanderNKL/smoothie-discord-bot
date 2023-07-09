from typing import Literal
import discord
from discord.ui import Button, View, Select
from discord.ext import commands
from discord import app_commands
from database import Database
import emojis as emojis
import time
import config as config
import datetime
from handlers import get


def button_color(input_color):
    color = discord.ButtonStyle.gray

    if input_color.lower() == "green":
        color = discord.ButtonStyle.green

    elif input_color.lower() == "red":
        color = discord.ButtonStyle.red

    elif input_color.lower() == "blue":
        color = discord.ButtonStyle.blurple

    return color


class CustomSuggestionEmojis(
    discord.ui.Modal,
    title='Select your Custom Emojis!'
):
    # Our modal classes MUST subclass `discord.ui.Modal`,
    # but the title can be whatever you want.

    # This will be a short input, where the user can enter their name
    # It will also have a placeholder, as denoted by the `placeholder` kwarg.
    # By default, it is required and is a short-style input which is exactly
    # what we want.

    def __init__(self, bot, db, server_id, emoji_type):
        super().__init__()
        self.bot = bot
        self.db = db
        self.server_id = server_id
        self.emoji_type = emoji_type

    upvote = discord.ui.TextInput(
        label='New Emoji',
        placeholder='Paste in the emoji id.',
        required=True,
        max_length=100
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            "Hurray! We've customised the emojis to your liking.\n"
            "To ensure that it works, please confirm that the emojis in this message are correct:\n"
            f"• {self.emoji_type.capitalize()} emoji: {self.upvote.value} (`{self.upvote.value}`)\n"
            "If the emojis don't work, no one will be able to send suggestions properly!"
        )

        await Database().update_server(self.server_id, f"suggestions.{self.emoji_type}_emoji", self.upvote.value)

    async def on_error(self, error: Exception, interaction: discord.Interaction) -> None:
        await interaction.response.send_message('Oops! Something went wrong.', ephemeral=True)

        # Make sure we know what the error actually is
        print(error.__traceback__)


class AddAutoRoles(
    discord.ui.Modal,
    title='Add a join role'
):
    # Our modal classes MUST subclass `discord.ui.Modal`,
    # but the title can be whatever you want.

    # This will be a short input, where the user can enter their name
    # It will also have a placeholder, as denoted by the `placeholder` kwarg.
    # By default, it is required and is a short-style input which is exactly
    # what we want.

    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    role = discord.ui.TextInput(
        label='Role Name/ID',
        placeholder='For example: member',
        required=True,
        max_length=100
    )

    async def on_submit(self, interaction: discord.Interaction):
        found_role = None

        for role in interaction.guild.roles:
            if str(role.id) == self.role.value or role.name.lower() == self.role.value.lower():
                found_role = role.id
                break

        if found_role:
            await interaction.response.send_message(
                f"Hurray! Members will now receive the <@&{found_role}> role!\n", ephemeral=True
            )

            await Database().get_server(str(interaction.guild.id), True)  # Just making sure it exists
            await Database().server_data.update_one(
                {"_server_id": str(interaction.guild.id)},
                {"$set": {f"autoroles.roles.{found_role}": {}}}
            )

        else:
            await interaction.response.send_message(
                f"Oh no! I couldn't find the role **{self.role.value}**!\n"
                "Make sure that you spelt it correctly, or use the correct ID!", ephemeral=True
            )

    async def on_error(self, error: Exception, interaction: discord.Interaction) -> None:
        await interaction.response.send_message('Oops! Something went wrong.', ephemeral=True)

        # Make sure we know what the error actually is
        print(error.__traceback__)


class RemoveAutoRoles(
    discord.ui.Modal,
    title='Remove a join role'
):
    # Our modal classes MUST subclass `discord.ui.Modal`,
    # but the title can be whatever you want.

    # This will be a short input, where the user can enter their name
    # It will also have a placeholder, as denoted by the `placeholder` kwarg.
    # By default, it is required and is a short-style input which is exactly
    # what we want.

    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    role = discord.ui.TextInput(
        label='Role Name/ID',
        placeholder='For example: member',
        required=True,
        max_length=100
    )

    async def on_submit(self, interaction: discord.Interaction):
        found_role = None

        for role in interaction.guild.roles:
            if str(role.id) == self.role.value or role.name.lower() == self.role.value.lower():
                found_role = role.id
                break

        if found_role:
            await interaction.response.send_message(
                f"Awww! Members will no longer receive the <@&{found_role}> role!\n", ephemeral=True
            )

            await Database().server_data.update_one(
                {"_server_id": str(interaction.guild.id)},
                {"$unset": {f"autoroles.roles.{found_role}": ""}}
            )

        else:
            await interaction.response.send_message(
                f"Oh no! I couldn't find the role **{self.role.value}**!\n"
                "Make sure that you spelt it correctly, or use the correct ID!", ephemeral=True
            )

    async def on_error(self, error: Exception, interaction: discord.Interaction) -> None:
        await interaction.response.send_message('Oops! Something went wrong.', ephemeral=True)

        # Make sure we know what the error actually is
        print(error.__traceback__)


class AddReactionRole(discord.ui.Modal, title='Add a role!'):
    # Our modal classes MUST subclass `discord.ui.Modal`,
    # but the title can be whatever you want.

    # This will be a short input, where the user can enter their name
    # It will also have a placeholder, as denoted by the `placeholder` kwarg.
    # By default, it is required and is a short-style input which is exactly
    # what we want.

    def __init__(self, bot, message, color, colored_buttons):
        super().__init__()
        self.bot = bot
        self.message = message
        self.color = color
        self.colored_buttons = colored_buttons

    role = discord.ui.TextInput(
        label='Role ID or Role Name',
        placeholder='Must be a valid role id or name.',
        required=True,
        max_length=100
    )

    button_name = discord.ui.TextInput(
        label='Button Name',
        placeholder='Name of button goes here...',
        required=True,
        max_length=80
    )

    button_color = discord.ui.TextInput(
        label='Button Color (Requires Premium)',
        placeholder='Blue, Green, Red, Gray',
        required=False,
        max_length=5
    )

    async def on_submit(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild.id)
        server = await Database().get_server(guild_id)
        message_id = str(self.message.id)

        # We attempt to find the role
        role = None  # If we don't find it, it is None.

        color = get.button_color(self.button_color.value)

        try:
            roles = await interaction.guild.fetch_roles()
            for guild_role in roles:
                if str(guild_role.id) == self.role.value or str(guild_role.name).lower() == self.role.value.lower():
                    role = guild_role
                    break

            if str(role.id) in server['reaction_roles'][message_id]["buttons"]:
                await interaction.response.send_message(
                    "This role is already added!\n", ephemeral=True
                )
                return

            if role is None:
                await interaction.response.send_message(
                    "That was not a valid role! Please enable developer mode and copy the role id or name.\n"
                    "Need help? Come meet my creators in: https://discord.com/invite/WTfaSnPMBw", ephemeral=True
                )
                return

        # If the role wasn't found, we get an exception

        except Exception as e:
            print("Issue with AddReactionRoles:", e)
            await interaction.response.send_message(
                "That was not a valid role! Please enable developer mode and copy the role id or name.\n"
                "Need help? Come meet my creators in: https://discord.com/invite/WTfaSnPMBw", ephemeral=True
            )
            return

        # We add the setup buttons. They must be re-added each edit. (Unless finished)
        buttons = [
            Button(
                label="Add Role",
                style=discord.ButtonStyle.green,
                custom_id=f"setup_add_role_{interaction.user.id}"
            ),
            Button(
                label="Undo Previous Role",
                style=discord.ButtonStyle.red,
                custom_id=f"setup_undo_role_{interaction.user.id}"
            ),
            Button(
                label="Finish Setup",
                style=discord.ButtonStyle.blurple,
                custom_id=f"setup_finish_{interaction.user.id}"
            )
        ]

        # double Check that the message id is in fact in the system
        if 'reaction_roles' in server and message_id in server['reaction_roles']:
            for button in server['reaction_roles'][message_id]["buttons"]:
                buttons.append(
                    Button(
                        label=f"{server['reaction_roles'][message_id]['buttons'][button]['name']}",
                        style=get.button_color(server['reaction_roles'][message_id]['buttons'][button]['color']),
                        custom_id=f"reaction_role_add_{button}",
                    )
                )

            buttons.append(
                Button(
                    label=f"{self.button_name.value}",
                    style=color,
                    custom_id=f"add_reaction_role{role.id}"
                )
            )

            await Database().update_server(guild_id, f"reaction_roles.{message_id}.buttons.{role.id}", {
                "name": self.button_name.value,
                "color": self.button_color.value
            })

        else:
            await interaction.response.send_message(
                "This message is apparently not in our system. Make a new one with /setup!\n"
                "Need help? Come meet my creators in: https://discord.com/invite/WTfaSnPMBw", ephemeral=True
            )
            return

        view = View()
        for button in buttons:
            view.add_item(button)

        embed = discord.Embed(
            title=self.message.embeds[0].title,
            description=self.message.embeds[0].description,
            color=self.message.embeds[0].color
        )

        await self.message.edit(
            embed=embed, view=view
        )

        await interaction.response.send_message(
            "Successfully added the button role! Click FINISH SETUP once you're done!", ephemeral=True
        )

    async def on_error(self, error: Exception, interaction: discord.Interaction) -> None:
        await interaction.response.send_message('Oops! Something went wrong.', ephemeral=True)

        # Make sure we know what the error actually is
        print(error.__traceback__)


class Setup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.guild is None:
            return

        guild_id = message.guild.id

        if message.author.bot:
            return

        if message.author.id == self.bot.application.id:
            return

        server = await self.db.get_server(str(guild_id))

        if 'logs' in server and 'delete' in server['logs']:
            try:  # We try to load the join channel
                channel = await self.bot.fetch_channel(server['logs']['delete'])

            except Exception as e:  # If we fail, we delete the logs channel since it doesn't work.
                print("Issue with fetching channel in on_message_delete:", e)
                await self.db.update_server(str(guild_id), "logs.delete", 1, delete=True)
                return

        else:
            return

        try:  # We try to send the message in the channel
            embed = discord.Embed(color=config.COLOR_EMPTY)
            embed.timestamp = datetime.datetime.utcnow()
            embed.set_footer(text=f"User ID: {message.author.id}")

            embed.add_field(name="Channel", value=message.channel.mention)
            embed.add_field(name="User", value=f"{message.author.mention}")
            embed.add_field(name="Message", value=message.content, inline=False)
            embed.set_author(name=f"{message.author}", icon_url=get.user_avatar(message))
            embed.set_thumbnail(url=message.guild.icon)
            await channel.send(
                f"{emojis.MAJOR_WARNING} A **message** was **deleted** in {message.channel.mention}",
                embed=embed
            )
            return

        except discord.Forbidden:
            await self.db.update_server(str(guild_id), "logs.delete", 1, delete=True)
            return

        except discord.NotFound:
            await self.db.update_server(str(guild_id), "logs.delete", 1, delete=True)
            return

        except Exception as e:  # If we fail, we delete the logs channel since it doesn't work.
            print("Issue with sending message in channel in on_message_delete:", e)
            return

    @commands.Cog.listener()
    async def on_message_edit(self, message_before, message_after):
        if message_before.guild is None:
            return

        guild_id = message_before.guild.id
        server = await self.db.get_server(str(guild_id))
        # Check that the server supports edit logs
        if 'logs' in server and 'edit' in server['logs']:
            try:  # We try to load the join channel
                channel = await self.bot.fetch_channel(server['logs']['edit'])

            except Exception as e:  # If we fail, we delete the logs channel since it doesn't work.
                print("Issue with fetching channel in on_message_edit:", e)
                await self.db.update_server(str(guild_id), "logs.edit", 1, delete=True)
                return

        else:
            return

        if message_before.author.bot:
            return

        if message_before.content == "" or message_after.content == "":
            return

        elif message_before.content == message_after.content:
            return

        embed = discord.Embed(color=config.COLOR_EMPTY)
        embed.timestamp = datetime.datetime.utcnow()
        embed.set_footer(text=f"User ID: {message_before.author.id}")

        embed.add_field(name="Channel", value=message_after.channel.mention)
        embed.add_field(name="User", value=f"{message_after.author.mention}")
        embed.set_author(name=f"{message_after.author}", icon_url=get.user_avatar(message_after))

        embed.add_field(
            name="View Message",
            value=f"[Click to view]({message_before.jump_url})"
        )

        embed.add_field(
            name="Before",
            value=message_before.content,
            inline=False
        )

        embed.add_field(
            name="After",
            value=message_after.content
        )

        embed.set_thumbnail(url=message_before.guild.icon)

        try:
            await channel.send(
                (
                    f"{emojis.MAJOR_WARNING} A **message** was **edited** in {message_before.channel.mention}\n" 
                ),
                embed=embed
            )

        except discord.Forbidden:
            await self.db.update_server(str(guild_id), "logs.edit", 1, delete=True)
            return

        except Exception as e:  # If we fail, we delete the logs channel since it doesn't work.
            print("Issue with sending message in channel in on_message_edit:", e)
            await self.db.update_server(str(guild_id), "logs.edit", 1, delete=True)

    @commands.Cog.listener()
    async def on_user_update(self, before, after):
        embed = discord.Embed(color=config.COLOR_EMPTY)
        embed.timestamp = datetime.datetime.utcnow()
        embed.set_footer(text=f"User ID: {after.id}")

        embed.add_field(name="User", value=f"{after.mention}")
        embed.set_author(name=f"{after}", icon_url=get.user_avatar(after))

        if before.name != after.name:
            embed.add_field(
                name="Name change",
                value=(
                    f"**Before:** {before.name}\n"
                    f"**After:** {after.name}"
                ),
                inline=False
            )

        if before.discriminator != after.discriminator:
            embed.add_field(
                name="User tag change",
                value=(
                    f"**Before:** {before.display_name}#{before.discriminator}\n"
                    f"**After:** {after.display_name}#{after.discriminator}"
                ),
                inline=False
            )

        if before.avatar != after.avatar:
            embed.add_field(
                name="Avatar change",
                value=(
                    "The user changed their avatar"
                ),
                inline=False
            )

            embed.set_thumbnail(url=get.user_avatar(after))

        for guild in after.mutual_guilds:
            server = await self.db.get_server(str(guild.id))
            if server:
                # Check that the server supports leave logs
                if 'logs' in server and 'user' in server['logs']:
                    try:
                        channel = await self.bot.fetch_channel(server['logs']['user'])
                        await channel.send(
                            f"{emojis.MAJOR_WARNING} A **user** changed their **profile**", embed=embed
                        )

                    except discord.Forbidden:
                        await self.db.update_server(str(guild.id), "logs.user", 1, delete=True)
                        continue

                    except discord.NotFound:
                        await self.db.update_server(str(guild.id), "logs.user", 1, delete=True)
                        continue

                    except Exception as e:
                        print("Issue with fetching channel in on_user_update:", e)
                        continue

                else:
                    continue
    
    @commands.Cog.listener()
    async def on_presence_update(self, before, after):
        embed = discord.Embed(color=config.COLOR_EMPTY)
        embed.timestamp = datetime.datetime.utcnow()
        embed.set_footer(text=f"User ID: {after.id}")
        embed.add_field(name="User", value=f"{after.mention}")
        embed.set_author(name=f"{after}", icon_url=get.user_avatar(after))

        new_change = False
        if before.display_name != after.display_name:
            new_change = True

            if after.nick:
                title = "Nickname added"

            elif after.nick is None:
                title = "Nickname removed"

            else:
                title = "Nickname changed"

            embed.add_field(
                name=f"{title}",
                value=(
                    f"**Before:** {before.display_name}\n"
                    f"**After:** {after.display_name}"
                ),
                inline=False
            )

        if before.display_avatar != after.display_avatar:
            new_change = True

            embed.add_field(
                name="Server avatar change",
                value=(
                    "The user changed their avatar for this server"
                ),
                inline=False
            )

            embed.set_thumbnail(url=get.user_avatar(after))

        if new_change is False:
            return

        server = await self.db.get_server(str(before.guild.id))
        if server:
            # Check that the server supports leave logs
            if 'logs' in server and 'user' in server['logs']:
                try:
                    channel = await self.bot.fetch_channel(server['logs']['user'])
                    await channel.send(
                        f"{emojis.MAJOR_WARNING} A **user** changed their **server profile**", embed=embed
                    )

                except discord.Forbidden:
                    await self.db.update_server(str(before.guild.id), "logs.user", 1, delete=True)
                    return

                except discord.NotFound:
                    await self.db.update_server(str(before.guild.id), "logs.user", 1, delete=True)
                    return

                except Exception as e:
                    print("Issue with fetching channel in on_member_update:", e)
                    return

            else:
                return

    async def log_user_join(self, server, member):
        try:  # We try to load the join channel
            channel = await self.bot.fetch_channel(server['logs']['join'])

        except discord.Forbidden:
            await self.db.update_server(str(member.guild.id), "logs.join", 1, True)

        except discord.NotFound:
            await self.db.update_server(str(member.guild.id), "logs.join", 1, True)

        except Exception as e:  # If we fail, we delete the logs channel since it doesn't work.
            print("Issue with fetching channel in on_member_join:", e)
            return

        account_age = member.created_at.timestamp()

        embed = discord.Embed(color=config.COLOR_EMPTY)
        embed.timestamp = datetime.datetime.utcnow()
        embed.set_footer(text=f"User ID: {member.id}")

        if time.time() - account_age < 2592000:
            embed.add_field(
                name=f"{emojis.WARNING} NEW ACCOUNT",
                value="This account was created recently!",
                inline=False
            )

        embed.add_field(name="User", value=f"{member.mention}")
        embed.add_field(name="Created", value=f"{self.how_long_ago(account_age)} ago")
        embed.add_field(name="Server Count", value=member.guild.member_count)
        embed.set_author(name=f"{member}", icon_url=get.user_avatar(member))
        embed.set_thumbnail(url=member.guild.icon)

        try:  # We try to send the message in the channel
            await channel.send(
                f"{emojis.UPVOTE} A member **joined** the server",
                embed=embed
            )

        except discord.Forbidden:
            await self.db.update_server(str(member.guild.id), "logs.join", 1, True)
            return

        except discord.NotFound:
            await self.db.update_server(str(member.guild.id), "logs.join", 1, True)
            return

        except Exception as e:  # If we fail, we delete the logs channel since it doesn't work.
            print("Issue with sending message in channel in on_member_join:", e)
            return

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        new_change = False

        embed = discord.Embed(color=config.COLOR_EMPTY)
        embed.timestamp = datetime.datetime.utcnow()
        embed.set_footer(text=f"User ID: {after.id}")

        embed.add_field(name="User", value=f"{after.mention}")
        embed.set_author(name=f"{after}", icon_url=get.user_avatar(after))

        if before.display_name != after.display_name:
            new_change = True

            if after.nick:
                title = "Nickname added"

            elif after.nick is None:
                title = "Nickname removed"

            else:
                title = "Nickname changed"

            embed.add_field(
                name=f"{title}",
                value=(
                    f"**Before:** {before.display_name}\n"
                    f"**After:** {after.display_name}"
                ),
                inline=False
            )

        if before.display_avatar != after.display_avatar:
            new_change = True

            embed.add_field(
                name="Server avatar change",
                value=(
                    "The user changed their avatar for this server"
                ),
                inline=False
            )

            embed.set_thumbnail(url=get.user_avatar(after))

        if new_change is False:
            return

        server = await self.db.get_server(str(before.guild.id))
        if server:
            # Check that the server supports leave logs
            if 'logs' in server and 'user' in server['logs']:
                try:
                    channel = await self.bot.fetch_channel(server['logs']['user'])
                    await channel.send(
                        f"{emojis.MAJOR_WARNING} A **user** changed their **server profile**", embed=embed
                    )

                except discord.Forbidden:
                    await self.db.update_server(str(before.guild.id), "logs.user", 1, delete=True)
                    return

                except discord.NotFound:
                    await self.db.update_server(str(before.guild.id), "logs.user", 1, delete=True)
                    return

                except Exception as e:
                    print("Issue with fetching channel in on_member_update:", e)
                    return

            else:
                return

    async def log_user_join(self, server, member):
        try:  # We try to load the join channel
            channel = await self.bot.fetch_channel(server['logs']['join'])

        except discord.Forbidden:
            await self.db.update_server(str(member.guild.id), "logs.join", 1, True)

        except discord.NotFound:
            await self.db.update_server(str(member.guild.id), "logs.join", 1, True)

        except Exception as e:  # If we fail, we delete the logs channel since it doesn't work.
            print("Issue with fetching channel in on_member_join:", e)
            return

        account_age = member.created_at.timestamp()

        embed = discord.Embed(color=config.COLOR_EMPTY)
        embed.timestamp = datetime.datetime.utcnow()
        embed.set_footer(text=f"User ID: {member.id}")

        if time.time() - account_age < 2592000:
            embed.add_field(
                name=f"{emojis.WARNING} NEW ACCOUNT",
                value="This account was created recently!",
                inline=False
            )

        embed.add_field(name="User", value=f"{member.mention}")
        embed.add_field(name="Created", value=f"{self.how_long_ago(account_age)} ago")
        embed.add_field(name="Server Count", value=member.guild.member_count)
        embed.set_author(name=f"{member}", icon_url=get.user_avatar(member))
        embed.set_thumbnail(url=member.guild.icon)

        try:  # We try to send the message in the channel
            await channel.send(
                f"{emojis.UPVOTE} A member **joined** the server",
                embed=embed
            )

        except discord.Forbidden:
            await self.db.update_server(str(member.guild.id), "logs.join", 1, True)
            return

        except discord.NotFound:
            await self.db.update_server(str(member.guild.id), "logs.join", 1, True)
            return

        except Exception as e:  # If we fail, we delete the logs channel since it doesn't work.
            print("Issue with sending message in channel in on_member_join:", e)
            return

    async def give_user_roles(self, server, member):
        guild_roles = await member.guild.fetch_roles()
        given_roles = 0

        # We look through all of the guild roles. If we find the role we want, give it to them.
        for guild_role in guild_roles:
            if str(guild_role.id) in server['autoroles']['roles']:
                try:
                    await member.add_roles(guild_role)
                    given_roles += 1

                # If we fail, try to log it in their mod channel to guide them!
                except discord.Forbidden:
                    try:
                        if 'logs' in server and 'moderation' in server['logs']:
                            channel = await self.bot.fetch_channel(server['logs']['moderation'])
                            embed = discord.Embed(
                                description=(
                                    f"I failed to give the user {member} (`{member.id}`) the <@&{guild_role.id}> role!"
                                    "Make sure that I have permission to assign roles and that I am higher\n"
                                    "in the role hierarchy!"
                                ),
                                color=config.COLOR_ERROR
                            )

                            embed.set_image(url="https://i.imgur.com/CSNYUBo.png")
                            await channel.send(embed=embed)

                    except discord.Forbidden:
                        await self.db.update_server(str(member.guild.id), "logs.moderation", 1, delete=True)
                        return

                    except Exception as e:  # If we fail, we delete the logs channel since it doesn't work.
                        print("Issue with fetching channel in on_member_join:", e)
                        return

                except Exception as e:
                    print("Issue adding Autorole!", e)

            # If they have been given as many as there are inside the list, stop searching
            if given_roles >= len(server['autoroles']['roles']):
                return

    @commands.Cog.listener()
    async def on_member_join(self, member):
        server = await self.db.get_server(str(member.guild.id))

        # If the server has Autoroles, give the user the roles
        if 'autoroles' in server and len(server['autoroles']) > 0:
            await self.give_user_roles(server, member)

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        """Detects when a user clicks a button or uses a slash command"""

        # Ensures that the interaction is a button, and not a slash commabd
        if interaction.type.name != "component":
            return

        button = interaction.data["custom_id"]
        # We make sure the button is a minigame button
        if button[0:5] != "setup":
            return

        user_id = str(interaction.user.id)

        if button == f"setup_autorole_add_{user_id}":
            server = await Database().get_server(str(interaction.guild.id), True)  # Just making sure it exists

            await interaction.response.send_modal(
                AddAutoRoles(
                    self.bot
                )
            )

            return

        elif button == f"setup_autorole_remove_{user_id}":
            await interaction.response.send_modal(
                RemoveAutoRoles(
                    self.bot
                )
            )

            return

        elif button == f"setup_autorole_view_{user_id}":
            server = await Database().server_data.find_one({"_server_id": str(interaction.guild.id)})

            if (
                server is None or 'autoroles' not in server
                or 'roles' not in server['autoroles'] or len(server['autoroles']['roles']) < 1
            ):
                roles = "\nNo roles added. :("

            else:
                list_of_roles = list()
                roles = ""

                # Check for roles in the guild and add them
                for role in interaction.guild.roles:
                    list_of_roles.append(str(role.id))

                # Check for and delete old roles in autoroles that are deleted
                for role in server['autoroles']['roles']:
                    if role not in list_of_roles:
                        await Database().server_data.update_one(
                            {"_server_id": str(interaction.guild.id)},
                            {"$unset": {f"autoroles.roles.{role}": ""}}
                        )

                    else:
                        roles += f"\n• <@&{role}>"

            buttons = [
                Button(
                    label="Give everyone these roles",
                    style=discord.ButtonStyle.blurple,
                    custom_id=f"setup_autorole_all_{interaction.user.id}"
                )
            ]

            view = View()
            for button in buttons:
                view.add_item(button)

            await interaction.response.send_message(
                f"Your members will receive these roles: {roles}", view=view, ephemeral=True
            )

        elif button == f"setup_autorole_all_{user_id}":
            server = await Database().server_data.find_one({"_server_id": str(interaction.guild.id)})

            if (
                server is None or 'autoroles' not in server
                or 'roles' not in server['autoroles'] or len(server['autoroles']['roles']) < 1
            ):
                await interaction.response.send_message(
                    "Sure, no roles will be given to your members! ... "
                    "Processing [0] roles ... Complete!\nAs promised, no roles were given. Happy?", ephemeral=True
                )
                return

            else:
                await interaction.response.send_message(
                    "Giving your members all autoroles. This may take a while!", ephemeral=True
                )

                # Search for all members in the guild, and give them the autoroles.
                give_these_roles = list()
                for check_role in interaction.guild.roles:
                    if str(check_role.id) in server['autoroles']['roles']:
                        give_these_roles.append(check_role)

                async for member in interaction.guild.fetch_members(limit=None):
                    for role in give_these_roles:
                        try:
                            await member.add_roles(role)

                        except discord.Forbidden:
                            await interaction.followup.send(
                                f"<@{interaction.user.id}> I don't have permission to update users roles!",
                                ephemeral=True
                            )   
                            return

                        except Exception as e:
                            print("Issue giving roles:", e)

            await interaction.followup.send(
                f"<@{interaction.user.id}> Hey, I'm done giving them the roles!", ephemeral=True
            )

        elif button == f"setup_upvote_{user_id}":
            custom_emojis = await self.load_user_perk(user_id, "custom_suggestion_emojis")

            if custom_emojis is False:
                await interaction.response.send_message(
                    f"{emojis.ERROR} You need premium to use this cosmetic feature.\n\n"
                    "Please consider supporting us with a **premium subscription** in order to unlock this.\n"
                    "You can buy premium [**here**]({}) or by using [**/premium**]({})".format(
                        "https://www.patreon.com/ultimaterpg",
                        "https://www.patreon.com/ultimaterpg"
                    ),
                    ephemeral=True
                )
                return

            await interaction.response.send_modal(
                CustomSuggestionEmojis(
                    self.bot,
                    Database,
                    str(interaction.guild.id),
                    "upvote"
                )
            )

        elif button == f"setup_undo_role_{user_id}":
            server = await self.db.get_server(str(interaction.guild.id))
            message_id = str(interaction.message.id)

            if 'reaction_roles' in server and message_id in server['reaction_roles']:
                buttons = [
                    Button(
                        label="Add Role",
                        style=discord.ButtonStyle.green,
                        custom_id=f"setup_add_role_{interaction.user.id}"
                    ),
                    Button(
                        label="Undo Previous Role",
                        style=discord.ButtonStyle.red,
                        custom_id=f"setup_undo_role_{interaction.user.id}"
                    ),
                    Button(
                        label="Finish Setup",
                        style=discord.ButtonStyle.blurple,
                        custom_id=f"setup_finish_{interaction.user.id}"
                    )
                ]

                for button in server['reaction_roles'][message_id]["buttons"]:
                    buttons.append(
                        Button(
                            label=f"{server['reaction_roles'][message_id]['buttons'][button]['name']}",
                            style=get.button_color(server['reaction_roles'][message_id]['buttons'][button]['color']),
                            custom_id=f"reaction_role_add_{button}",
                        )
                    )

                await self.db.update_server(
                    str(interaction.guild.id), f"reaction_roles.{message_id}.buttons.{button}", 1, delete=True
                )
                buttons.pop()

                view = View()
                for button in buttons:
                    view.add_item(button)

                embed = discord.Embed(
                    title=interaction.message.embeds[0].title,
                    description=interaction.message.embeds[0].description,
                    color=interaction.message.embeds[0].color
                )

                await interaction.message.edit(
                    embed=embed, view=view
                )

                await interaction.response.send_message(
                    "Undone! The previous role was removed! :)", ephemeral=True
                )
                return

        elif button == f"setup_finish_{user_id}":
            server = await self.db.get_server(str(interaction.guild.id))
            message_id = str(interaction.message.id)

            if 'reaction_roles' in server and message_id in server['reaction_roles']:
                buttons = []
                for button in server['reaction_roles'][message_id]["buttons"]:
                    buttons.append(
                        Button(
                            label=f"{server['reaction_roles'][message_id]['buttons'][button]['name']}",
                            style=get.button_color(server['reaction_roles'][message_id]['buttons'][button]['color']),
                            custom_id=f"reaction_role_add_{button}",
                        )
                    )

                view = View()
                for button in buttons:
                    view.add_item(button)

                embed = discord.Embed(
                    title=interaction.message.embeds[0].title,
                    description=interaction.message.embeds[0].description,
                    color=interaction.message.embeds[0].color
                )

                try:
                    await interaction.message.delete()
                    await self.db.update_server(
                        str(interaction.guild.id), f"reaction_roles.{message_id}", 1, delete=True
                    )

                    if 'header' in server["reaction_roles"][message_id]:
                        img_embed = discord.Embed(color=0x2F3136)
                        img_embed.set_image(url=server["reaction_roles"][message_id]['header'])
                        message = await interaction.channel.send(
                            embed=img_embed
                        )

                    message = await interaction.channel.send(
                        embed=embed, view=view
                    )

                    await self.db.update_server(
                        str(interaction.guild.id),
                        f"reaction_roles.{message.id}",
                        server['reaction_roles'][message_id]
                    )

                except discord.Forbidden:
                    await interaction.response.send_message(
                        "Uh-oh, it seems you've been naughty and removed my permissions...", ephemeral=True
                    )
                    return

                except Exception as e:
                    print("Issue with updating the reaction roles message:", e)

                await interaction.response.send_message(
                    "Completed! Should you regret it, simply delete the message and make a new one! :)"
                )
                return

        elif button[0:11] == "setup_role_":
            server = await self.db.get_server(str(interaction.guild.id))
            message_id = str(interaction.message.id)

            if 'reaction_roles' not in server or message_id not in server['reaction_roles']:
                return

            role_id = button[11:]
            roles = await interaction.guild.fetch_roles()

            add_role = None  # If true, we give them the role, if None, we ignore it
            for guild_role in roles:
                if str(guild_role.id) == role_id:
                    role = guild_role
                    add_role = True
                    break

            for user_role in interaction.user.roles:
                if user_role == guild_role:
                    add_role = False
                    break

            try:
                if add_role is None:
                    await interaction.response.send_message(
                        "Woopsies. Something wen't wrong here... Perhaps the role no longer exists?", ephemeral=True
                    )
                    return

                elif add_role is True:
                    await interaction.user.add_roles(role)
                    await interaction.response.send_message(f"You now have the role: {role.mention}", ephemeral=True)

                elif add_role is False:
                    await interaction.user.remove_roles(role)
                    await interaction.response.send_message(
                        f"You no longer have the role: {role.mention}", ephemeral=True
                    )

            except discord.Forbidden:
                await interaction.response.send_message(
                    "I don't have permission to give you the role... Mock your server admin!", ephemeral=True
                )
                pass

            except Exception as e:
                print("issue adding role to user in setup:", e)

        elif button == f"setup_add_role_{user_id}":
            guild_id = str(interaction.guild.id)
            message_id = str(interaction.message.id)
            server = await self.db.get_server(guild_id)

            # Check for premium limit
            allowed_reaction_roles = await self.load_user_perk(user_id, "reaction_roles")
            if allowed_reaction_roles is None or allowed_reaction_roles is False:
                allowed_reaction_roles = 4

            if len(server['reaction_roles'][message_id]['buttons']) >= allowed_reaction_roles:
                await interaction.response.send_message(
                    f"You've exceeded your limit! You can only have {allowed_reaction_roles} buttons"
                )
                return

            # Check that the message is in the system. Otherwise, we delete and skip it
            if 'reaction_roles' in server and message_id in server['reaction_roles']:
                await interaction.response.send_modal(
                    AddReactionRole(
                        self.bot,
                        interaction.message,
                        await get.embed_color(interaction.user.id),
                        True  # if they can add colored buttons
                    )
                )

            else:
                await self.db.update_server(str(guild_id), f"reaction_roles.{message_id}", 1, delete=True)
                return

        elif button == f"setup_downvote_{user_id}":
            custom_emojis = await self.load_user_perk(user_id, "custom_suggestion_emojis")

            if custom_emojis is False:
                await interaction.response.send_message(
                    f"{emojis.ERROR} You need premium to use this cosmetic feature.\n\n"
                    "Please consider supporting us with a **premium subscription** in order to unlock this.\n"
                    "You can buy premium [**here**]({}) or by using [**/premium**]({})".format(
                        "https://www.patreon.com/ultimaterpg",
                        "https://www.patreon.com/ultimaterpg"
                    ),
                    ephemeral=True
                )
                return

            await interaction.response.send_modal(
                CustomSuggestionEmojis(
                    self.bot,
                    Database,
                    str(interaction.guild.id),
                    "downvote"
                )
            )

    async def setup_suggestions(self, interaction: discord.Interaction, user_id, channel):
        try:  # We try to send a message that auto deletes to ensure the bot has permissions
            await channel.send("This is a test message. Auto deletes in 2 seconds...", delete_after=2)

        except discord.Forbidden:
            await interaction.response.send_message(
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

        await interaction.response.send_message(
            f"Great work <@{user_id}>! Your users can now use [**/suggest**](https://discord.com/invite/WTfaSnPMBw)",
            embed=embed,
            view=view
        )

    async def check_active_reaction_roles(self, server, interaction: discord.Interaction):
        guild_id = str(interaction.guild.id)
        active_messages = ""

        active_reaction_roles = 0
        for reaction_role in server['reaction_roles']:
            message = None
            try:
                channel = await interaction.guild.fetch_channel(
                    server['reaction_roles'][reaction_role]['channel_id']
                )

                message = await channel.fetch_message(reaction_role)

            except discord.Forbidden:
                await self.db.update_server(guild_id, f"reaction_roles.{reaction_role}", 1, delete=True)
                continue

            except discord.NotFound:
                await self.db.update_server(guild_id, f"reaction_roles.{reaction_role}", 1, delete=True)
                continue

            except Exception as e:
                print("issue with setup reaction roles:", e)

            if message is None:
                await self.db.update_server(guild_id, f"reaction_roles.{reaction_role}", 1, delete=True)

            else:
                active_reaction_roles += 1
                active_messages += f"\n`{message.id}` - [Click here to jump to message]({message.jump_url})"

        return active_reaction_roles, active_messages

    async def setup_levels(self, interaction: discord.Interaction, user_id):
        """Sets up autoroles for a server"""
        await interaction.response.defer()  # Let's discord know we are processing it

        embed = discord.Embed(
            title="Levels & Level Roles",
            description=(
                "It's time to make you server engaging!\n"
                "Set up levels, xp events and level roles for your server!"
            ),
            color=await get.embed_color(interaction.user.id)
        )

        embed.set_thumbnail(url="https://i.imgur.com/MVz7P9C.png")

        options = [
            Select(
                custom_id=f"level_admin_{user_id}",
                placeholder="Select an option to administrate",
                options=[
                    discord.SelectOption(label='XP per Message', description='Modify how much XP the bot gives per message', emoji=emojis.XP), # noqa
                    discord.SelectOption(label='XP Multiplier', description='How much XP should be given from boosts or events', emoji=emojis.UPVOTE), # noqa
                    discord.SelectOption(label='Allow Boosts', description='Allow users to spend Bytecoin to receive XP boosts!', emoji=emojis.BYTECOIN), # noqa
                    discord.SelectOption(label='Level Roles', description='Give users a role when they level up!', emoji=emojis.STAR), # noqa
                    discord.SelectOption(label='Profile Card Colors', description='Modify the color of profile cards!', emoji=emojis.COLORS["rainbow"]), # noqa
                ]
            )
        ]

        view = View()
        for option in options:
            view.add_item(option)

        await self.db.update_server(
            str(interaction.guild.id), "levels", {"enabled": True, "modifier": 1.1, "xp_event": 0}
        )

        await interaction.followup.send(embed=embed, view=view)

    async def setup_autoroles(self, interaction: discord.Interaction, user_id):
        """Sets up autoroles for a server"""
        await interaction.response.defer()  # Let's discord know we are processing it

        embed = discord.Embed(
            title="Autoroles",
            description=(
                "Make Smoothie give roles to users that join the server!"
            ),
            color=await get.embed_color(interaction.user.id)
        )

        embed.set_thumbnail(url="https://i.imgur.com/MVz7P9C.png")

        buttons = [
            Button(
                label="Add Role",
                style=discord.ButtonStyle.green,
                custom_id=f"setup_autorole_add_{interaction.user.id}"
            ),
            Button(
                label="Remove Role",
                style=discord.ButtonStyle.red,
                custom_id=f"setup_autorole_remove_{interaction.user.id}"
            ),
            Button(
                label="View Roles",
                style=discord.ButtonStyle.gray,
                custom_id=f"setup_autorole_view_{interaction.user.id}"
            )
        ]

        view = View()
        for button in buttons:
            view.add_item(button)

        await interaction.followup.send(embed=embed, view=view)

    @app_commands.command(
        name="setup",
        description="Allow smoothie to perform more server tasks"
    )
    @app_commands.default_permissions(manage_guild=True)
    async def setup_command(
        self, interaction: discord.Interaction,
        category: Literal[
            "suggestions",
            "button roles",
            "autoroles",
        ], channel: discord.TextChannel = None
    ):

        if channel is None:
            channel = interaction.channel

        user_id = str(interaction.user.id)
        permissions = interaction.channel.permissions_for(interaction.guild.me)

        if (
            permissions.send_messages and permissions.view_channel
            and permissions.read_message_history and permissions.read_messages
            and permissions.use_external_emojis
        ):  # Check if the bot has the needed permissions
            if category == "suggestions":
                await self.setup_suggestions(interaction, user_id, channel)

            elif category == "levels":
                await self.setup_levels(interaction, user_id)

            elif category == "button roles":
                await self.setup_reaction_roles(interaction, user_id, channel)

            elif category == "autoroles":
                await self.setup_autoroles(interaction, user_id)

        else:
            await interaction.response.send_message(
                "I'm lacking permissions! Give me the `Send Messages`, `Read Messages`, "
                "`Read Message History`, `View Channel` permission!",
                ephemeral=True
            )
            return

    @app_commands.command(
        name="deactivate",
        description="Prevent smoothie to perform more server tasks"
    )
    @app_commands.default_permissions(manage_guild=True)
    async def deactivate_command(
        self, interaction: discord.Interaction,
        category: Literal[
            "suggestions", "button roles",
            "autoroles", # "levels"
        ]
    ):
        permissions = interaction.channel.permissions_for(interaction.guild.me)

        if (
            permissions.send_messages and permissions.view_channel
            and permissions.read_message_history and permissions.read_messages
            and permissions.use_external_emojis
        ):  # Check if the bot has the needed permissions
            if category == "suggestions":
                await self.db.update_server(str(interaction.guild.id), "suggestions", 1, True)

            elif category == "levels":
                await self.db.update_server(str(interaction.guild.id), "levels", 1, True)

            elif category == "button roles":
                await self.db.update_server(str(interaction.guild.id), "reaction_roles", 1, True)

            elif category == "autoroles":
                await self.db.update_server(str(interaction.guild.id), "autoroles", 1, True)

            await interaction.response.send_message(
                f"{emojis.CHECKMARK} Deactivated: **{category}**. This feature will now be **disabled**!",
                ephemeral=True
            )

            server = await Database().get_server(str(interaction.guild.id))
            if 'logs' in server and 'moderation' in server['logs']:
                try:  # We try to load the join channel
                    channel = await self.bot.fetch_channel(server['logs']['moderation'])
                    await channel.send(
                        f"{emojis.MAJOR_WARNING} **{interaction.user}** (`{interaction.user.id}`) disabled **{category}**"
                    )

                except Exception as e:  # If we fail, we delete the logs channel since it doesn't work.
                    print("Issue with fetching channel in on_member_unban:", e)
                    await self.db.update_server(str(interaction.guild.id), "logs.moderation", 1, delete=True)
                    return

            else:
                return

        else:
            await interaction.response.send_message(
                "I'm lacking permissions! Give me the `Send Messages`, `Read Messages`, "
                "`Read Message History`, `View Channel` permission!",
                ephemeral=True
            )
            return


async def setup(bot):
    await bot.add_cog(Setup(bot))
