import discord
from discord.ext import commands, tasks
from discord import app_commands
from database import Database
import config as config
from handlers import get
from time import time


class ChannelLock(commands.Cog):
    """
    AFK COG

    This cog allows admins/mods to lock a channel.
    The channel may still be viewed, but users without special
    perms may not chat there. This is useful for things like raids.
    """

    def __init__(self, bot):
        self.bot = bot
        self.db = Database()
        self.timed_locks.start()

    async def update_channel_permissions(
        self, channel: discord.TextChannel, default_role, send_messages
    ):
        # We load in the channels overwrites so that we don't override any existing settings
        try:
            overwrites = channel.overwrites
            role_overwrites = overwrites.get(default_role, discord.PermissionOverwrite())

            # We now manually override the send_message permission
            role_overwrites.send_messages = send_messages

            await channel.set_permissions(default_role, overwrite=role_overwrites)

        except discord.Forbidden:
            pass

        except discord.NotFound:
            pass

        except Exception as e:
            print("Issue updating channel permissions:", e)

    @tasks.loop(seconds=2)
    async def timed_locks(self):
        """Locks or unlocks channels after (x) time"""

        channels = await self.db.find_ended_channel_lock(time(), False)
        while len(channels) > 0:
            channels = await self.db.find_ended_channel_lock(time(), False)

            for data in channels:
                try:
                    # We load in the channel and message. If they are none, we do nothing
                    channel = await self.bot.fetch_channel(data['channel_id'])
                    default_role = channel.guild.default_role

                    if channel is not None:
                        if data['lock_type'] == "lock":
                            await self.update_channel_permissions(channel, default_role, False)
                            description = "This channel is now locked!"
                            color = config.COLOR_ERROR

                        else:
                            description = "This channel is no longer locked!"
                            color = config.COLOR_ACCEPTED
                            await self.update_channel_permissions(channel, default_role, True)

                        embed = discord.Embed(
                            description=description,
                            color=color
                        )

                        try:
                            await channel.send(embed=embed)

                        except discord.Forbidden:
                            pass

                        except discord.NotFound:
                            pass

                        except Exception as e:
                            print("Issue with sending message to channel:", e)

                    # Delete the channel from memory

                    await self.db.delete_channel_data(data['_id'])

                except Exception as e:
                    print("Issue with changing channel permissions (lock/unlock):", e)
                    await self.db.delete_channel_data(data['_id'])

    @app_commands.command(
        name="lock",
        description="Lock a channel for a certain period of time",
    )
    @app_commands.default_permissions(manage_messages=True)
    async def lock_command(
        self,
        interaction: discord.Interaction,
        duration: str = "0s",
        channel: discord.TextChannel = None,
    ):
        await interaction.response.defer(ephemeral=True)  # Just let discord know that we're processing it

        # if the channel is being processed in our DB, delete it.
        # Otherwise the bot will override this change
        exists = await self.db.locked_channels.find_one({"channel_id": interaction.channel.id})
        if exists:
            await self.db.delete_channel_data(exists['_id'])

        if channel is None:
            channel = interaction.channel

        permissions = channel.permissions_for(interaction.guild.me)

        if duration.isdigit() is False:
            duration = int(get.determined_time(duration))

        else:
            duration = int(duration)

        if duration <= 0:
            time_description = "This channel has been locked!"

        else:
            time_description = (
                f"This channel will be available <t:{int(duration + time())}:R> (<t:{int(duration + time())}:F>)"
            )

            await self.db.add_lock_channel(
                {'channel_id': channel.id, 'lock_type': "unlock", 'duration': int(duration + time())}
            )

        if permissions.manage_channels:  # Check if the bot has the needed perms
            embed = discord.Embed(
                description=f"{time_description}",
                color=config.COLOR_ERROR
            )

            await channel.send(embed=embed)
            await interaction.followup.send(f"Channel {channel.mention} is now locked.", ephemeral=True)
            await self.update_channel_permissions(channel, interaction.guild.default_role, False)

        else:
            await interaction.followup.send(
                "I'm lacking permissions! Give me the `manage channels` permission!",
                ephemeral=True
            )
            return

    @app_commands.command(
        name="unlock",
        description="Unlock a channel that has been locked!",
    )
    @app_commands.default_permissions(manage_messages=True)
    async def unlock_command(
        self, interaction: discord.Interaction, duration: str = "0s", channel: discord.TextChannel = None
    ):
        await interaction.response.defer(ephemeral=True)

        # if the channel is being processed in our DB, delete it.
        # Otherwise the bot will override this change
        exists = await self.db.locked_channels.find_one({"channel_id": interaction.channel.id})
        if exists:
            await self.db.delete_channel_data(exists['_id'])

        if channel is None:
            channel = interaction.channel

        permissions = channel.permissions_for(interaction.guild.me)

        if duration.isdigit() is False:
            duration = int(get.determined_time(duration))

        else:
            duration = int(duration)

        if duration > 0:
            time_description = (
                f"This channel will be locked <t:{int(duration + time())}:R> (<t:{int(duration + time())}:F>)"
            )

            await self.db.add_lock_channel(
                {'channel_id': channel.id, 'lock_type': "lock", 'duration': int(duration + time())}
            )

        else:
            time_description = "This channel is now available!"

        if permissions.manage_channels:  # Check if the bot has the needed perms
            embed = discord.Embed(
                description=time_description,
                color=config.COLOR_ACCEPTED
            )

            await channel.send(
                embed=embed
            )

            await interaction.followup.send(f"Channel {channel.mention} is now available.", ephemeral=True)
            await self.update_channel_permissions(channel, interaction.guild.default_role, True)

        else:
            await interaction.followup.send(
                "I'm lacking permissions! Give me the `manage channel` permission!",
                ephemeral=True
            )
            return


async def setup(bot):
    await bot.add_cog(ChannelLock(bot))
