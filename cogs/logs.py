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


class Logs(commands.GroupCog, name="log"):
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
    async def on_presence_update(self, before, after):
        print(before, after)
    
    @commands.Cog.listener()
    async def on_guild_role_update(self, before, after):
        server = await self.db.get_server(str(after.guild.id))
        if not server:
            return

        if 'logs' not in server or 'role' not in server['logs']:
            return

        embed = discord.Embed(color=config.COLOR_EMPTY)
        if before.name != after.name:
            embed.add_field(name="Previous Name:", value=f"`{before.name}`")
            embed.add_field(name="Current Name:", value=f"`{after.name}`")
        
        if before.color != after.color:
            embed.add_field(name="Previous Color:", value=f"`{before.color}`")
            embed.add_field(name="Current Color:", value=f"`{after.color}`")
        
        if before.permissions != after.permissions:
            before_permissions = ""
            after_permissions = ""
            for permission in before.permissions:
                print(dict(after.permissions))
                if permission[1] != dict(after.permissions)[permission[0]]:
                    before_permissions += f"- {before.permissions[permission[0]][0]}: `{before.permissions[permission[0]][1]}`"
                    after_permissions += f"- {after.permissions[permission[0]][0]}: `{after.permissions[permission[0]][1]}`"

            embed.add_field(name="Previous Permissions:", value=f"{before_permissions}")
            embed.add_field(name="Current Permissions:", value=f"`{after_permissions}`")

        async for entry in after.guild.audit_logs(action=discord.AuditLogAction.role_update):
            embed.set_author(name=f"Updated by {entry.user}", icon_url=get.user_avatar(entry.user))
            embed.set_thumbnail(url=after.guild.icon)

        try:
            channel = await self.bot.fetch_channel(server['logs']['role'])
            await channel.send(
                f"{emojis.MAJOR_WARNING} A **role** was recently updated", embed=embed
            )

        except discord.Forbidden:
            await self.db.update_server(str(before.guild.id), "logs.role", 1, delete=True)
            return

        except discord.NotFound:
            await self.db.update_server(str(before.guild.id), "logs.role", 1, delete=True)
            return

        except Exception as e:
            print("Issue with fetching channel in on_guild_role_update:", e)
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

        if len(before.roles) < len(after.roles):
            new_change = True
            roles = ""
            for role in after.roles:
                if role not in before.roles:
                    roles += f"\n- Added Role: {role}"

            for role in before.roles:
                if role not in after.roles:
                    roles += f"\n- Removed Role: {role}"


            embed.add_field(
                name="Updated Roles",
                value=(
                    roles
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
                name=f"{emojis.MAJOR_WARNING} NEW ACCOUNT",
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
    async def on_member_join(self, member):
        server = await self.db.get_server(str(member.guild.id))

        # If the server wants to log user joins, log it.
        if 'logs' in server and 'join' in server['logs']:
            await self.log_user_join(server, member)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        server = await self.db.get_server(str(member.guild.id))
        if 'logs' in server and 'join' in server['logs']:
            try:  # We try to load the join channel
                channel = await self.bot.fetch_channel(server['logs']['leave'])

            except discord.Forbidden:
                await self.db.update_server(str(member.guild.id), "logs.leave", 1, True)
                return

            except discord.NotFound:
                await self.db.update_server(str(member.guild.id), "logs.leave", 1, True)
                return

            except Exception as e:  # If we fail, we delete the logs channel since it doesn't work.
                print(f"Issue with fetching channel in on_member_leave (Server: {server})", e)
                return

            embed = discord.Embed(color=config.COLOR_EMPTY)
            embed.timestamp = datetime.datetime.utcnow()
            embed.set_footer(text=f"User ID: {member.id}")

            embed.add_field(name="User", value=f"{member.mention}")
            embed.add_field(name="Created", value=f"{self.how_long_ago(member.created_at.timestamp())} ago")
            embed.add_field(name="Server Count", value=member.guild.member_count)
            embed.set_author(name=f"{member}", icon_url=get.user_avatar(member))
            embed.set_thumbnail(url=member.guild.icon)

            try:  # We try to send the message in the channel
                await channel.send(
                    f"{emojis.DOWNVOTE} A member **left** the server",
                    embed=embed
                )

            except discord.Forbidden:
                await self.db.update_server(str(member.guild.id), "logs.join", 1, True)
                return

            except discord.NotFound:
                await self.db.update_server(str(member.guild.id), "logs.leave", 1, True)
                return

            except Exception as e:  # If we fail, we delete the logs channel since it doesn't work.
                print("Issue with sending message in channel in on_member_join:", e)
                return

    async def setup_logs(self, interaction: discord.Interaction, user_id, channel, log_type):
        try:  # We try to send a message that auto deletes to ensure the bot has permissions
            await channel.send("This is a test message. Auto deletes in 2 seconds...", delete_after=2)

        except discord.Forbidden:
            await interaction.followup.send(
                f"Failed to send messages to <#{channel.id}>.\n"
                "Give me `Send messages` permission and try again!",
                ephemeral=True
            )
            return

        await self.db.update_server(interaction.guild.id, f"logs.{log_type}", channel.id)

        await interaction.followup.send(
            f"Great work <@{user_id}>! You will now have {log_type} messages logged for your server!",
        )

    @app_commands.command(
        name="activate",
        description="Allow smoothie to log server events"
    )
    @app_commands.default_permissions(manage_guild=True)
    async def activate(
        self, interaction: discord.Interaction,
        category: Literal[
            "join logs", "leave logs", "role logs", "edit logs",
            "user logs", "delete logs", "moderation logs"
        ], channel: discord.TextChannel = None
    ):
        permissions = interaction.channel.permissions_for(interaction.guild.me)

        if (
            permissions.send_messages and permissions.view_channel
            and permissions.read_message_history and permissions.read_messages
            and permissions.use_external_emojis
        ):  # Check if the bot has the needed permissions
            user_id = str(interaction.user.id)
            if not channel:
                channel = interaction.channel

            await interaction.response.defer()
            await self.setup_logs(interaction, user_id, channel, category.split(" ")[0])

            server = await Database().get_server(str(interaction.guild.id))
            if 'logs' in server and 'moderation' in server['logs']:
                try:  # We try to load the join channel
                    channel = await self.bot.fetch_channel(server['logs']['moderation'])
                    await channel.send(
                        f"{emojis.MAJOR_WARNING} **{interaction.user}** (`{interaction.user.id}`) enabled **{category}**"
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
                "`Read Message History`, `View Channel` and `Use External Emojis` permission!",
                ephemeral=True
            )
            return

    @app_commands.command(
        name="deactivate",
        description="Prevent smoothie from logging server events"
    )
    @app_commands.default_permissions(manage_guild=True)
    async def deactivate_command(
        self, interaction: discord.Interaction,
        category: Literal[
            "suggestions", "join logs", "leave logs", "edit logs",
            "user logs", "delete logs", "moderation logs", "button roles",
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

            elif category == "join logs":
                await self.db.update_server(str(interaction.guild.id), "logs.join", 1, True)

            elif category == "leave logs":
                await self.db.update_server(str(interaction.guild.id), "logs.leave", 1, True)

            elif category == "edit logs":
                await self.db.update_server(str(interaction.guild.id), "logs.edit", 1, True)

            elif category == "delete logs":
                await self.db.update_server(str(interaction.guild.id), "logs.delete", 1, True)

            elif category == "moderation logs":
                await self.db.update_server(str(interaction.guild.id), "logs.moderation", 1, True)

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
                
                except discord.NotFound:
                    await self.db.update_server(str(interaction.guild.id), "logs.moderation", 1, delete=True)

                except discord.Forbidden:
                    await self.db.update_server(str(interaction.guild.id), "logs.moderation", 1, delete=True)

                except Exception as e:  # If we fail, we delete the logs channel since it doesn't work.
                    print("Issue with fetching channel in moderation logging:", e)
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
    await bot.add_cog(Logs(bot))
