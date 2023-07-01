from datetime import timedelta
import discord
from discord.ext import commands
from discord import app_commands, Member, utils
import emojis as emojis
from database import Database
import config as config
from typing import Literal, Optional
from io import StringIO
import asyncio
from time import time
from handlers import logging, get


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()

    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        guild_id = guild.id
        server = await self.db.get_server(str(guild_id))

        # Check that the server supports leave logs
        if 'logs' in server and 'moderation' in server['logs']:
            try:  # We try to load the join channel
                channel = await self.bot.fetch_channel(server['logs']['moderation'])

            except discord.Forbidden:
                await self.db.update_server(str(guild_id), "logs.moderation", 1, delete=True)

            except discord.NotFound:
                await self.db.update_server(str(guild_id), "logs.moderation", 1, delete=True)

            except Exception as e:  # If we fail, we delete the logs channel since it doesn't work.
                print("Issue with fetching channel in on_member_unban:", e)
                return

        else:
            return

        try:
            await channel.send(
                f"{emojis.MAJOR_WARNING} **{user}** (`{user.id}`) "
                f"was unbanned!"  # noqa"
            )

        except discord.Forbidden:
            await self.db.update_server(str(guild_id), "logs.moderation", 1, delete=True)
            return

        except Exception as e:  # If we fail, we delete the logs channel since it doesn't work.
            print("Issue with sending message in channel in on_member_unban:", e)
            #  await self.db.update_server(str(guild_id), "logs.moderation", 1, delete=True)

    @app_commands.command(
        name="purge",
        description="Delete messages from a channel!",
    )
    @app_commands.default_permissions(manage_messages=True)
    async def purge_command(
        self, interaction: discord.Interaction, amount: int
    ):
        permissions = interaction.channel.permissions_for(interaction.guild.me)

        if permissions.manage_messages and permissions.read_message_history:  # Check if the bot has the needed perms
            guild_id = interaction.guild.id
            server = await self.db.get_server(str(guild_id))

            await interaction.response.send_message(
                f"Deleting `{amount}` messages... This may take a while!", ephemeral=True
            )

            deleted = await interaction.channel.purge(limit=amount)
            await interaction.followup.send(
                f"**{interaction.user.mention} "
                f"deleted `{len(deleted)}` messages from {interaction.channel.mention}!**"
            )

            if 'logs' in server and 'moderation' in server['logs']:
                try:  # We try to load the join channel
                    channel = await self.bot.fetch_channel(server['logs']['moderation'])

                    file = StringIO()

                    file.write(f"This chat was purged by: {interaction.user} ({interaction.user.id})\n")
                    for message in deleted:
                        file.write(
                            f"\n[{message.created_at}] "
                            f"{message.author}: "
                            f"{message.content}"
                        )

                        await asyncio.sleep(0.5)

                    file.seek(0)

                    embed = discord.Embed(
                        color=config.COLOR_SMOOTHIE
                    )

                    embed.add_field(
                        name="View Channel",
                        value=f"[**Click here to go to channel**]({interaction.channel.jump_url})",
                        inline=False
                    )

                    embed.add_field(
                        name="Moderator",
                        value=f"{interaction.user.mention}",
                        inline=False
                    )

                    embed.add_field(
                        name="Messages Deleted",
                        value=f"{amount}",
                        inline=False
                    )

                    embed.set_thumbnail(url=interaction.guild.icon)

                    await channel.send(
                        f"{emojis.MAJOR_WARNING} {interaction.user} (`{interaction.user.id}`) "
                        f"purged {interaction.channel.mention}!",
                        embed=embed,
                        file=discord.File(file, f'message-history-{interaction.user.id}-{interaction.channel.name}')
                    )

                except discord.Forbidden:
                    await self.db.update_server(str(guild_id), "logs.moderation", 1, delete=True)
                    return

                except Exception as e:  # If we fail, we delete the logs channel since it doesn't work.
                    print("Issue with purge command:", e)
                    await self.db.update_server(str(guild_id), "logs.moderation", 1, delete=True)
                    return

            else:
                return

        else:
            await interaction.response.send_message(
                "I'm lacking permissions! Give me the `manage messages` and `read message history` permission!",
                ephemeral=True
            )
            return

    @app_commands.command(
        name="ban",
        description="Get rid of baddies from your server, even if they left!",
    )
    @app_commands.default_permissions(ban_members=True)
    async def ban_command(
        self, interaction: discord.Interaction, user: discord.User, reason: str,
        delete_messages: Literal[
            "Don't delete any", "Previous 24 Hours", "Previous 2 Days",
            "Previous 3 Days", "Previous 4 Days", "Previous 5 Days", "Previous 6 Days",
            "Previous 7 Days"
        ] = "Don't delete any"
    ):
        try:
            permissions = interaction.channel.permissions_for(interaction.guild.me)
            await interaction.response.defer()

            if (
                    permissions.ban_members
            ):  # Check if the bot has the needed permissions

                if reason == "":
                    reason = "No Reason Provided"

                amount = 0
                delete_messages = delete_messages.lower()

                if delete_messages == "previous 24 hours":
                    amount = 1

                elif delete_messages == "previous 2 days":
                    amount = 2

                elif delete_messages == "previous 3 days":
                    amount = 3

                elif delete_messages == "previous 4 days":
                    amount = 4

                elif delete_messages == "previous 5 days":
                    amount = 5

                elif delete_messages == "previous 6 days":
                    amount = 6

                elif delete_messages == "previous 7 days":
                    amount = 7

                if user == interaction.user:
                    await interaction.followup.send(
                        embed=discord.Embed(
                                title=f"{emojis.MAJOR_WARNING} Failure!",
                                description="You cannot ban yourself!",
                                color=config.COLOR_ERROR
                            )
                        )

                    return
                    return

                if user.guild_permissions.administrator or interaction.user.id == self.bot.application.id:
                    await interaction.followup.send(
                        embed=discord.Embed(
                                title=f"{emojis.MAJOR_WARNING} Failure!",
                                description=f"I don't have permission to ban {user.mention}!",
                                color=config.COLOR_ERROR
                            )
                        )

                    return

                # Try to ban the user. If it fails, error log it and stop.
                try:
                    embed = discord.Embed(
                        title="You have been banned!",
                        description=(
                            f"You have been banned from the server **{interaction.guild}**\n"
                            f"Reason: `{reason}`"
                        ),
                        color=config.COLOR_ERROR
                    )

                    embed.set_thumbnail(url=interaction.guild.icon)
                    await self.user_violation_dm(interaction.guild, user, "banned", reason)

                except Exception as e:
                    print("Issue with sending user a message:", e)

                try:
                    await interaction.guild.ban(user, reason=reason, delete_message_days=amount)
                except discord.Forbidden:
                    await interaction.followup.send(
                        embed=discord.Embed(
                                title=f"{emojis.MAJOR_WARNING} Failure!",
                                description=f"I don't have permission to ban {user.mention}!",
                                color=config.COLOR_ERROR
                            )
                        )
                    return

                embed = discord.Embed(
                    description=reason,
                    color=config.COLOR_ERROR
                )

                embed.set_author(
                    name=f"{user.name} has been banned!",
                    icon_url=get.user_avatar(user)
                )

                await interaction.followup.send(
                    embed=embed
                )

                await logging.moderation_logging(
                    self.bot,
                    interaction.guild,
                    user,
                    interaction.user,
                    "banned",
                    reason
                )

            else:
                await interaction.followup.send(
                    f"{emojis.ERROR} I don't have permission to ban "
                    f"since I'm missing the **Ban Members** permission!",
                    ephemeral=True
                )
                return

        except Exception as e:
            print("Issue with banning user:", e)

    async def user_violation_dm(self, guild: discord.Guild, user: discord.User, action: str, reason: str):
        try:
            embed = discord.Embed(
                title=f"You have been {action}",
                description=reason,
                color=config.COLOR_ERROR
            )

            embed.set_footer(text=f"You were moderated in {guild.name}", icon_url=guild.icon.url)

            await user.send(embed=embed)

        except discord.Forbidden:
            pass

        except discord.NotFound:
            pass

        except Exception as e:
            print("Issue with user DM:", e)

    @app_commands.command(
        name="warn",
        description="Warn a user, giving them a violation.",
    )
    @app_commands.default_permissions(kick_members=True)
    async def warn_command(
        self, interaction: discord.Interaction, user: discord.User, reason: str,
    ):
        try:
            if reason in ["", " "]:
                await interaction.response.send_message("You need to provide a reason!", ephemeral=True)
                return

            embed = discord.Embed(
                description=f"{reason}",
                color=config.COLOR_ERROR
            )

            embed.set_author(
                name=f"{user.name} has been warned!",
                icon_url=get.user_avatar(user)
            )

            await interaction.response.send_message(embed=embed)
            await self.user_violation_dm(interaction.guild, user, "warned", reason)

            await logging.moderation_logging(
                self.bot,
                interaction.guild,
                user,
                interaction.user,
                "warned",
                reason
            )

        except Exception as e:
            print("Issue with warning user:", e)

    @app_commands.command(
        name="mute",
        description="Mute a user",
    )
    @app_commands.default_permissions(moderate_members=True)
    @app_commands.describe(
        user="The user you wish to mute",
        duration="How long you want the user to be muted for",
        reason="Why you muted the user"
    )
    async def mute_command(
        self, interaction: discord.Interaction, user: Member, duration: Optional[str], reason: Optional[str],
    ):
        try:
            permissions = interaction.channel.permissions_for(interaction.guild.me)
            await interaction.response.defer()

            if (
                permissions.moderate_members
            ):  # Check if the bot has the needed permissions
                if not reason:
                    reason = "No reason were provided."

                if not duration:
                    duration = "1d"

                try:
                    real_duration = get.determined_time(duration)
                    if real_duration == 0:
                        await interaction.followup.send(
                            "Invalid time. Time must be something like: 4w, 3d, 2h 1s",
                            ephemeral=True
                        )
                        return

                except Exception as e:
                    print("Issue with mute:", e)

                if user.guild_permissions.administrator or interaction.user.id == self.bot.application.id:
                    await interaction.followup.send(
                        embed=discord.Embed(
                                title=f"{emojis.MAJOR_WARNING} Failure!",
                                description=f"I don't have permission to mute {user.mention}!",
                                color=config.COLOR_ERROR
                            )
                        )

                    return

                try:
                    await user.timeout(utils.utcnow() + timedelta(seconds=real_duration), reason=reason)
                    await logging.moderation_logging(
                        self.bot,
                        interaction.guild,
                        user,
                        interaction.user,
                        "muted",
                        reason
                    )

                except discord.Forbidden:
                    await interaction.followup.send(
                        f"I'm not allowed to mute {user.mention}!", ephemeral=True
                    )
                    return

                except Exception as e:
                    print("Issue with mute command:", e)

                embed = discord.Embed(
                    description=f"{reason}\n\n**Ends**: <t:{int(time() + real_duration)}:R>",
                    color=config.COLOR_ERROR
                )

                embed.set_author(
                    name=f"{user.name} has been muted!",
                    icon_url=get.user_avatar(user)
                )

                await interaction.followup.send(embed=embed)
                await self.user_violation_dm(interaction.guild, user, "muted", reason)

            else:
                await interaction.followup.send(
                    f"{emojis.ERROR} I don't have permission to mute "
                    f"since I'm missing the **Timout Members** permission!",
                    ephemeral=True
                )
                return

        except Exception as e:
            print("Issue with muting user:", e)

    @app_commands.command(
        name="unmute",
        description="Unmute a user",
    )
    @app_commands.default_permissions(moderate_members=True)
    @app_commands.describe(
        user="The user you wish to mute",
        reason="Why you unmuted the user"
    )
    async def unmute_command(
        self, interaction: discord.Interaction, user: Member, reason: Optional[str],
    ):
        try:
            permissions = interaction.channel.permissions_for(interaction.guild.me)
            await interaction.response.defer()

            if (
                    permissions.moderate_members
            ):  # Check if the bot has the needed permissions
                if not reason:
                    reason = "No reason were provided."

                try:
                    if user.is_timed_out():
                        await user.timeout(None, reason=reason)
                        await interaction.response.send_message(
                            "{} was unmuted by {}! (`{}`)".format(
                                user.mention,
                                interaction.user.mention,
                                reason
                            )
                        )

                    else:
                        await interaction.response.send_message(
                            "That user is not muted!", ephemeral=True
                        )
                    return

                except discord.Forbidden:
                    await interaction.response.send_message(
                        f"I'm not allowed to unmute {user.mention}!", ephemeral=True
                    )
                    return

                except Exception as e:
                    print("Issue with mute command:", e)
                    return

            else:
                await interaction.followup.send(
                    f"{emojis.ERROR} I don't have permission to unmute "
                    f"since I'm missing the **Timeout Members** permission!",
                    ephemeral=True
                )
                return

        except Exception as e:
            print("Issue with muting user:", e)


async def setup(bot):
    await bot.add_cog(Moderation(bot))
