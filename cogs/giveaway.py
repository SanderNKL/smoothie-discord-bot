from time import time
from typing import Optional
import discord
from discord.ext import commands, tasks
from discord import app_commands
from database import Database
from discord.ui import Button, View
import random
import emojis as emojis
import config as config
from handlers import get


class Giveaway(commands.GroupCog, name="giveaway"):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()
        self.find_ended_giveaways.start()
        self.find_expired_giveaways.start()

    def giveaway_embed(self, data):
        embed = discord.Embed(
            title=f"{data['prize']}",
            description=(
                f"Hosted by: <@{data['host']}>\n"
                f"Possible Winners: `{data['winners']}`\n"
                f"Participants: `{len(data['participants'])}`\n\n"
                f"Ends in: <t:{data['duration']}:R> (<t:{int(data['duration'])}:F>)"
            ),
            color=config.COLOR_SMOOTHIE
        )

        if 'required_role' in data:
            data["required_role"] = data['required_role']
            embed.add_field(
                name="Required Role",
                value=f"You must have the role <@&{data['required_role']}> to enter",
            )

        if 'required_messages' in data:
            data["required_messages"] = data['required_messages']
            embed.add_field(
                name="Required Messages",
                value=f"You must have sent **{data['required_messages']}** messages to enter",
            )

        if 'required_invites' in data:
            data["required_invites"] = data['required_invites']
            embed.add_field(
                name="Required Invites",
                value=f"You must have **{data['required_invites']}** invites to enter",
            )

        embed.set_thumbnail(url="https://i.imgur.com/Wd9fv4D.png")

        buttons = [
            Button(
                label="Join Giveaway",
                style=discord.ButtonStyle.green,
                custom_id="giveaway_join"
            ),
            Button(
                label="View Participants",
                style=discord.ButtonStyle.blurple,
                custom_id=f"giveaway_view_{data['host']}"
            ),
            Button(
                label="Force End",
                style=discord.ButtonStyle.red,
                custom_id="giveaway_end"
            )
        ]

        view = View()
        for button in buttons:
            view.add_item(button)

        return embed, view

    async def send_winner_message(self, channel, winners, data):
        try:
            original_response = await channel.fetch_message(data['message_id'])
            await channel.send(
                f"Congratulations to {winners}! You won **{data['prize']}**", reference=original_response
            )

        except discord.errors.Forbidden:
            return winners

        except Exception as e:
            print("Issue with announcing giveaway winenrs:", e)

    async def announce_winners(self, channel, data, drawn_users):
        winners = ""
        all_winners = ""

        n = 0
        for user in drawn_users:
            if n >= 50:
                await self.send_winner_message(channel, winners, data)
                winners = ""
                n = 0

            if winners == "":
                all_winners += f"<@{user}>"
                winners += f"<@{user}>"

            else:
                all_winners += f", <@{user}>"
                winners += f", <@{user}>"

            n += 1

        if n > 0 and winners != "":
            await self.send_winner_message(channel, winners, data)

        return all_winners

    def draw_winners(self, amount_of_winners, participants):
        drawn_users = list()

        # If there are less participants than winners, we set the winners to
        # The amount of participants. This does not alter how many actual winners there could be.
        # It only determines how many we actually draw
        if len(participants) < amount_of_winners:
            amount_of_winners = len(participants)

        # We draw a winner, remove it from the list, then redraw
        # For as long as we need until we have drawn the total amount of possible winners
        for i in range(amount_of_winners):
            winner = random.choice(participants)
            participants.remove(winner)
            drawn_users.append(str(winner))

        return drawn_users

    async def fetch_giveaway_message(self, data):
        try:
            channel = await self.bot.fetch_channel(data['channel_id'])
            message = await channel.fetch_message(data['message_id'])

            return channel, message

        except discord.errors.Forbidden:
            return None, None

        except discord.errors.NotFound:
            return None, None

        except Exception as e:
            print("Issue with giveaway:", e)
            return None, None

    async def delete_giveaway(self, data):
        # We try to delete the giveaway
        # If we fail, we notify the code by returning True/False
        if await self.db.end_giveaway(data['_id']) is True:
            return True

        else:
            return False

    async def create_giveaway(
        self,
        interaction: discord.Interaction,
        duration,
        winners,
        prize,
        required_role: discord.Role,
        required_messages: int,
        required_invites: int
    ):
        data = {
            "winners": winners,
            "prize": prize,
            "duration": int(duration + time()),
            "participants": [],
            "ended": False,
            "host": str(interaction.user.id)
        }

        if required_role:
            data["required_role"] = required_role.id

        if required_messages:
            data["required_messages"] = required_messages

        if required_invites:
            data["required_invites"] = required_invites

        embed, view = self.giveaway_embed(data)

        await interaction.followup.send(embed=embed, view=view)
        message = await interaction.original_response()

        data["channel_id"] = message.channel.id
        data["message_id"] = message.id

        await Database().create_giveaway(data)
        return

    async def end_giveaway(self, data, winner):
        """Ends or deletes the giveaway"""

        # If we had no winner, we go straight to deletion
        if winner is None:
            await self.delete_giveaway(data)
            return

        else:
            await self.db.update_giveaway(data['_id'], "winner", winner, True)
            await self.db.update_giveaway(data['_id'], "duration", time(), True)
            await self.db.update_giveaway(data['_id'], "ended", True, True)

    async def update_giveaway_message(self, data, message, winners):
        buttons = [
            Button(
                label="Join Giveaway",
                style=discord.ButtonStyle.green,
                disabled=True,
                custom_id="giveaway_join"
            ),
            Button(
                label="View Participants",
                style=discord.ButtonStyle.blurple,
                custom_id=f"giveaway_view_{data['host']}"
            )
        ]

        if len(data['participants']) > 1:
            buttons.append(
                Button(
                    label="Reroll",
                    style=discord.ButtonStyle.blurple,
                    custom_id="giveaway_reroll"
                )
            )

        else:
            # If there weren't enough participants, we disable the button, and delete the giveaway
            # There is NO need to keep it in memory since there is no point in interacting with it

            buttons.append(
                Button(
                    label="Reroll",
                    style=discord.ButtonStyle.blurple,
                    disabled=True,
                    custom_id="giveaway_reroll"
                )
            )

        view = View()
        for button in buttons:
            view.add_item(button)

        await message.edit(view=view, embed=await self.updated_giveaway(data, winners, True))

    @tasks.loop(seconds=20)
    async def find_ended_giveaways(self):
        """Ends active giveaways automatically"""
        giveaways = await self.db.find_ended_giveaways(time(), False)

        while len(giveaways) > 0:
            giveaways = await self.db.find_ended_giveaways(time(), False)

            for data in giveaways:
                try:
                    # We load in the channel and message. If they are none, we do nothing
                    channel, message = await self.fetch_giveaway_message(data)

                    # If the channel or message is None, the giveaway can't be ended visually anyways.
                    # The channel or message may be deleted, or permissions restrict us from seeing it.
                    # Therefore we delete it from memory to save space.
                    if channel is None or message is None:
                        await self.end_giveaway(data, None)  # By using none, we delete the giveaway
                        return

                    # If there weren't enough participants, we end and delete the giveaway
                    if len(data['participants']) < 1:
                        winners = None
                        await self.end_giveaway(data, None)  # By using none, we delete the giveaway

                    # Otherwise, we announce the winners
                    else:
                        winners = await self.announce_winners(
                            channel,
                            data,
                            self.draw_winners(
                                int(data['winners']),
                                data['participants'].copy()
                            )
                        )

                        await self.end_giveaway(data, winners)  # By using none, we delete the giveaway

                except Exception as e:
                    print("Issue with finding ended giveaways:", e)
                    await self.db.update_giveaway(data['_id'], "ended", True, True)

            # After we determined what to do with the giveaway, we update the final message
            await self.update_giveaway_message(data, message, winners)

    @tasks.loop(seconds=20)
    async def find_expired_giveaways(self):
        """Deletes expired giveaways automatically"""

        # Search for giveaways that has ended after the expired time.
        # Remember that time is always the latest, so we need to remove the time frame we want it to end after.
        giveaways = await self.db.find_ended_giveaways(time() - config.GIVEAWAY_EXPIRE, True)

        while len(giveaways) > 0:
            for data in giveaways:
                try:
                    channel, message = await self.fetch_giveaway_message(data)

                    # If the channel or message is None, the giveaway can't be ended visually anyways.
                    # The channel or message may be deleted, or permissions restrict us from seeing it.
                    # Therefore we delete it from memory to save space.
                    if channel is None or message is None:
                        await self.delete_giveaway(data)
                        return

                    # We update the buttons to be disabled. The giveaway has ended after all
                    buttons = [
                        Button(
                            label="Join Giveaway",
                            style=discord.ButtonStyle.green,
                            disabled=True,
                            custom_id="giveaway_join"
                        ),
                        Button(
                            label="View Participants",
                            style=discord.ButtonStyle.blurple,
                            disabled=True
                        ),
                        Button(
                            label="Reroll",
                            style=discord.ButtonStyle.blurple,
                            disabled=True,
                            custom_id="giveaway_reroll"
                        )
                    ]

                    view = View()
                    for button in buttons:
                        view.add_item(button)

                    # We delete the giveaway, and update the message.
                    await self.delete_giveaway(data)
                    await message.edit(view=view, embed=await self.updated_giveaway(data, data['winner'], True))

                except Exception as e:
                    print("Issue with finding expired giveaways:", e)
                    await self.delete_giveaway(data)

            # We now do a new search for more expired giveaways
            giveaways = await self.db.find_ended_giveaways(time() - config.GIVEAWAY_EXPIRE, True)

    async def updated_giveaway(self, data, winner=None, complete=False):
        if winner is None:
            winner = "Not enough people participated..."

        if complete:
            embed = discord.Embed(
                title=f"{data['prize']}",
                description=(
                    f"Giveaway ended: <t:{int(time())}:R> (<t:{int(time())}:f>)\n"
                    f"Hosted by: <@{data['host']}>\n\n"
                    f"**Winners**\n{winner}"
                ),
                color=config.COLOR_SMOOTHIE
            )

        else:
            embed, view = self.giveaway_embed(data)

        return embed

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        """Detects when a user clicks a button or uses a slash command"""
        # Ensures that the interaction is a button, and not a slash commabd
        if interaction.type.name != "component":
            return

        button = interaction.data["custom_id"]
        button_content = button.split("_")
        # We make sure the button is a minigame button

        if button[0:8] != "giveaway":
            return

        user_id = str(interaction.user.id)

        if button_content[1] == "view":
            await interaction.response.defer()  # Let's discord know we are processing it
            if button_content[2] != str(interaction.user.id):
                await interaction.followup.send("Only the host can see the participants!", ephemeral=True)
                return

            data = await self.db.get_giveaway(interaction.message.id)

            n = 0
            winners = ""
            for user in data["participants"]:
                if n >= 50:
                    await interaction.followup.send(f"Participants: {winners}", ephemeral=True)
                    n = 0
                    winners = ""

                if winners == "":
                    winners += f"<@{user}>"

                else:
                    winners += f", <@{user}>"

                n += 1

            await interaction.followup.send(f"Participants: {winners}", ephemeral=True)

        if button == "giveaway_end":
            await interaction.response.defer()  # Let's discord know we are processing it
            data = await self.db.get_giveaway(interaction.message.id)

            if data is None:
                print(f"User: {user_id} tries to end: {interaction.message.id}")
                await interaction.followup.send(
                    "Unable to stop the giveaway. Most likely it has ended. Contact support!\n", ephemeral=True
                )
                return

            if user_id != data['host']:
                await interaction.followup.send(
                    "Hah, very funny. Only the host can end the giveaway!\n", ephemeral=True
                )
                return

            channel, message = await self.fetch_giveaway_message(data)

            # If the channel or message is None, the giveaway can't be ended visually anyways.
            # The channel or message may be deleted, or permissions restrict us from seeing it.
            # Therefore we delete it from memory to save space.
            if channel is None or message is None:
                await interaction.followup.send(
                    "I don't have permission to see this message and are therefore not able to end the giveaway.\n"
                    "Give me access to send and read messages!", ephemeral=True
                )

                return

            # If there weren't enough participants, we end and delete the giveaway
            if len(data['participants']) < 1:
                winners = None
                await self.end_giveaway(data, None)  # By using none, we delete the giveaway

            # Otherwise, we announce the winners
            else:
                winners = await self.announce_winners(
                    channel,
                    data,
                    self.draw_winners(
                        int(data['winners']),
                        data['participants'].copy()
                    )
                )

                await self.end_giveaway(data, winners)  # By using none, we delete the giveaway

            # After we determined what to do with the giveaway, we update the final message
            await self.update_giveaway_message(data, message, winners)
            await interaction.followup.send(
                "Successfully ended the giveaway!", ephemeral=True
            )

        if button == "giveaway_reroll":
            giveaway_id = interaction.message.id
            await interaction.response.defer()  # Let's discord know we are processing it

            # We load the data to ensure the giveaway is not expired or to see
            # If the user is the host
            data = await self.db.get_giveaway(giveaway_id)

            # If the giveaway is deleted from the DB, say so
            if data is None:
                await interaction.followup.send("This giveaway is no longer active!", ephemeral=True)
                return

            # If you are the host, reroll
            if user_id == data['host']:
                if len(data['participants']) > 1:
                    await interaction.followup.send(
                        f"The new winner is <@{random.choice(data['participants'])}>! Congratulations."
                    )
                    await self.db.update_giveaway(data['_id'], "duration", time(), True)
                    return

                else:
                    await interaction.followup.send(
                        "You can't reroll this giveaway. There are no participants!", ephemeral=True
                    )
                    return

            else:
                await interaction.followup.send(
                    "Hah, very funny. Only the host can reroll the giveaway!\n", ephemeral=True
                )
                return

        if button == "giveaway_join":
            giveaway_id = interaction.message.id
            await interaction.response.defer()  # Let's discord know we are processing it

            # We load the data to ensure the giveaway is not expired or to see
            # If the user already is in the giveaway.
            data = await self.db.get_giveaway(giveaway_id)

            # If the giveaway is deleted from the DB, say so
            if data is None:
                await interaction.followup.send("This giveaway is no longer active!", ephemeral=True)
                return

            # If you are already in the giveaway, say so
            elif str(user_id) in data['participants']:
                await interaction.followup.send("You've already participated!", ephemeral=True)
                return

            # Otherwise, Add them.
            else:
                if 'required_role' in data:
                    found = False
                    for role in interaction.user.roles:
                        if role.id == data['required_role']:
                            found = True
                            break

                    if found is False:
                        await interaction.followup.send(
                            f"You can't enter this giveaway. You need the role <@&{data['required_role']}>",
                            ephemeral=True
                        )
                        return

                if 'required_messages' in data:
                    message_count = await get.user_messages(interaction.user, interaction.guild)
                    if message_count < data['required_messages']:
                        return await interaction.followup.send(
                            f"You can't enter this giveaway. "
                            f"You need to send **{data['required_messages']}** messages to enter",
                            ephemeral=True
                        )

                if 'required_invites' in data:
                    invite_data = await get.user_invites(interaction.user, interaction.guild)
                    if invite_data["joins"] < data['required_invites']:
                        return await interaction.followup.send(
                            f"You can't enter this giveaway. "
                            f"You need to have **{data['required_invites']}** invites to enter",
                            ephemeral=True
                        )

                if await self.db.add_to_giveaway(giveaway_id, user_id) is False:
                    # Should it fail, we will not do further actions.
                    return

                data = await self.db.get_giveaway(giveaway_id)
                embed = await self.updated_giveaway(data)

                await interaction.followup.edit_message(
                    interaction.message.id, embed=embed
                )

                await interaction.followup.send(
                    f"Woohoo! You entered the giveaway for a chance to win **{data['prize']}**!", ephemeral=True
                )

    @app_commands.command(
        name="revoke",
        description="Remove role or user access to create giveaways",
    )
    @app_commands.default_permissions(administrator=True)
    async def revoke_access(
        self,
        interaction: discord.Interaction,
        role: Optional[discord.Role],
        user: Optional[discord.User]
    ):
        if not interaction.user.guild_permissions.administrator:
            return

        await interaction.response.defer()
        if not user and not role:
            await interaction.followup.send("You specify a role or a user!")

        server_data = await self.db.server_data.find_one({"_server_id": str(interaction.guild.id)})
        if server_data is None or 'giveaway_access' not in server_data:
            await interaction.followup.send("That role and/or user does not have access. There is nothing to remove.")
            return

        query_data = {
            "$pull": {}
        }

        checks = {
            "_server_id": str(interaction.guild.id)
        }

        embed = discord.Embed(
            title="Access Granted!",
            description="Use /giveaway revoke to remove access to a user or role."
        )

        if user and 'users' in server_data['giveaway_access'] and str(user.id) in server_data['giveaway_access']['users']:
            query_data["$pull"]["giveaway_access.users"] = str(user.id)
            embed.add_field(
                name="Revoked User Access!",
                value=f"{user.mention} no longer has access!"
            )

        if role and 'roles' in server_data['giveaway_access'] and str(role.id) in server_data['giveaway_access']['roles']:  # noqa
            query_data["$pull"]["giveaway_access.roles"] = str(role.id)
            embed.add_field(
                name="Revoked Role Access!",
                value=f"{role.mention} no longer has access!"
            )

        if len(query_data["$pull"]) < 1:
            await interaction.followup.send("No roles or users found, so nothing were removed.")
            return

        data = await self.db.server_data.update_one(
            checks,
            query_data
        )

        if data.modified_count > 0 or 'upserted' in data.raw_result:
            await interaction.followup.send(embed=embed)

    def check_giveaway_access(self, server_data, id, category):
        if server_data is None:
            return False

        elif 'giveaway_access' not in server_data:
            return False

        elif category not in server_data['giveaway_access']:
            return False

        for item in server_data['giveaway_access'][category]:
            if item == id:
                return True

        return False

    @app_commands.command(
        name="grant",
        description="Grant roles or users access to create giveaways",
    )
    @app_commands.default_permissions(administrator=True)
    async def grant(
        self,
        interaction: discord.Interaction,
        role: Optional[discord.Role],
        user: Optional[discord.User]
    ):
        if not interaction.user.guild_permissions.administrator:
            return

        await interaction.response.defer()
        if not user and not role:
            return await interaction.followup.send("You must give access to a role or a user!")

        query_data = {"$push": {}}
        checks = {"_server_id": str(interaction.guild.id)}

        embed = discord.Embed(
            title="Access Granted!",
            description="Use /giveaway revoke to remove access to a user or role."
        )

        if user:
            query_data["$push"]["giveaway_access.users"] = str(user.id)
            checks[f"giveaway_access.users.{user.id}"] = {"$exists": False}
            embed.add_field(
                name="Added new user!",
                value=f"{user.mention} has now been granted access!"
            )

        if role:
            query_data["$push"]["giveaway_access.roles"] = str(role.id)
            checks[f"giveaway_access.roles.{role.id}"] = {"$exists": False}
            embed.add_field(
                name="Added new role!",
                value=f"{role.mention} has now been granted access!"
            )

        if len(query_data["$push"]) < 1:
            return await interaction.followup.send("Duplicates found, so nothing were added.")

        data = await self.db.server_data.update_one(
            checks,
            query_data,
            upsert=True
        )

        if data.modified_count > 0 or 'upserted' in data.raw_result:
            await interaction.followup.send(embed=embed)

        else:
            await interaction.followup.send(f"{emojis.ERROR} Something went wrong... Contact support!")

    @app_commands.command(
        name="access",
        description="See who has access to posting giveaways",
    )
    @app_commands.default_permissions(administrator=True)
    async def access(
        self,
        interaction: discord.Interaction,
    ):
        if not interaction.user.guild_permissions.administrator:
            return

        await interaction.response.defer()
        server_data = await self.db.server_data.find_one({"_server_id": str(interaction.guild.id)})

        embed = discord.Embed(
            title="Giveaway Managers",
            description="Use /giveaway revoke/grant to remove/add access to a user or role."
        )

        if server_data and 'giveaway_access' in server_data:
            for category in server_data['giveaway_access']:
                access = ""
                for item in server_data['giveaway_access'][category]:
                    if category == "roles":
                        access += f"\n- <@&{item}>"

                    else:
                        access += f"\n- <@{item}>"

                embed.add_field(name=category.upper(), value=access)

        await interaction.followup.send(embed=embed)

    async def check_access(self, interaction: discord.Interaction):
        """
        Checks if the user is an admin or has role/user access
        """

        access = False
        server_data = await self.db.server_data.find_one({"_server_id": str(interaction.guild.id)})
        for role in interaction.user.roles:
            if self.check_giveaway_access(server_data, str(role.id), "roles"):
                access = True

        if self.check_giveaway_access(server_data, str(interaction.user.id), "users"):
            access = True

        return access

    @app_commands.command(
        name="create",
        description="Create your own giveaway!",
    )
    async def create(
        self,
        interaction: discord.Interaction,
        duration: str,
        winners: int,
        prize: str,
        required_role: discord.Role = None,
        required_messages: int = None,
        required_invites: int = None
    ):
        await interaction.response.defer()

        access = await self.check_access(interaction)
        if not access and not interaction.user.guild_permissions.administrator:
            await interaction.followup.send(
                "You need to have special access to use this command! Ask your server admin to give it to you.",
                ephemeral=True
            )
            return

        # Check and validate the time
        duration = get.determined_time(duration)
        if duration < 10:
            await interaction.followup.send(
                "Invalid Time. Example: 10y 10d 10s. This will set the time to 10 years, 10 days and 10 seconds.",
                ephemeral=True
            )

        # Check that the bot has the necessary permissions to manage the giveaway
        permissions = interaction.channel.permissions_for(interaction.guild.me)
        if (
            permissions.send_messages and permissions.view_channel
            and permissions.read_message_history and permissions.read_messages
        ):
            return await self.create_giveaway(
                interaction,
                duration,
                winners,
                prize,
                required_role,
                required_messages,
                required_invites
            )

        else:
            await interaction.followup.send(
                "I'm lacking permissions! Give me the `Send Messages`, `Read Messages`, "
                "`Read Message History`, `View Channel` permission!",
                ephemeral=True
            )
            return


async def setup(bot):
    await bot.add_cog(Giveaway(bot))
