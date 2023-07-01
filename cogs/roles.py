import discord
from typing import Literal
from discord.ui import Button, View, Select
from discord.ext import commands
from discord import app_commands
from database import Database
from handlers import get


class ReactionRoles(
    discord.ui.Modal,
    title='Create Roles for your server!'
):
    def __init__(self, bot, server_id, color, channel, button_type):
        super().__init__()
        self.bot = bot
        self.db = Database()
        self.server_id = server_id
        self.color = color
        self.channel = channel
        self.button_type = button_type

    name = discord.ui.TextInput(
        label='Title',
        placeholder='Message Title',
        required=True,
        max_length=100
    )

    description = discord.ui.TextInput(
        label='Description',
        placeholder='Put something informative here',
        required=True,
        style=discord.TextStyle.long,
        max_length=1000
    )

    async def on_submit(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title=self.name.value,
            description=self.description.value,
            color=self.color
        )

        message = await self.channel.send(embed=embed)
        await interaction.response.send_message(
            f"Great! Now to add roles, use `/button_roles add` then select the role you want. "
            f"Here is the message ID you must use: `{message.id}`", ephemeral=True
        )

        await Database().update_server(
            self.server_id, f"reaction_roles.{message.id}", {
                "channel_id": self.channel.id,
                "button_type": self.button_type,
                "buttons": {}
            }
        )

    async def on_error(self, error: Exception, interaction: discord.Interaction) -> None:
        await interaction.response.send_message('Oops! Something went wrong.', ephemeral=True)

        # Make sure we know what the error actually is
        print(error.__traceback__)


class Roles(commands.GroupCog, name="button_roles"):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()

    async def uses_reactions(self, interaction: discord.Interaction, server, message_id):
        if "reaction_roles" not in server:
            await interaction.followup.send("You don't use button roles, so there is none to delete")
            return False

        if message_id not in server['reaction_roles']:
            await interaction.followup.send(
                f"`{message_id}` is not registered as a role menu. "
                "Please check if the id is right, or create a new menu.\n"
                "To create a menu, use the `/roles create` command"
            )
            return False

        return True

    async def fetch_menu(self, interaction: discord.Interaction, server, message_id, guild_id):
        # We will now try to find the channel.
        try:
            channel = await interaction.guild.fetch_channel(
                server['reaction_roles'][message_id]['channel_id']
            )

            # We will now try to find the message in the channel
            if channel:
                try:
                    message = await channel.fetch_message(int(message_id))

                    # If we found the message, try deleting it
                    if message:
                        try:
                            return message

                        except discord.Forbidden:
                            await interaction.followup.send(
                                "I am not allowed to delete message... "
                                "I have instead deleted the message from my registry, "
                                "and you can now manually delete the message yourself."
                            )
                            return False

                except discord.NotFound:
                    await interaction.followup.send(
                        "I am not able to find a message with this id. "
                        "Make sure I am allowed to see the message, or check if the ID is correct!"
                    )
                    return False

                except discord.Forbidden:
                    await interaction.followup.send(
                        "I am not allowed to see the message... "
                        "Please give me the necessary permissions"
                    )
                    return False

                except Exception as e:
                    print("Issue with finding channel:", e)
                    return False

        except discord.NotFound:
            await interaction.followup.send(
                "I am not able to find the channel you put the message in. "
                "I have therefore deleted the menu from my registry!"
            )
            return False

        except discord.Forbidden:
            await interaction.followup.send(
                "I am not allowed to see the channel you put the role menu in... "
                "Please give me the necessary permissions"
            )
            return False

        except Exception as e:
            print("Issue with finding channel:", e)
            return False

    @app_commands.command(name="delete", description="Delete a role menu")
    @app_commands.default_permissions(manage_guild=True)
    async def delete_menu(self, interaction: discord.Interaction, message_id: str):
        """Deletes a reaction role message"""

        await interaction.response.defer()  # Let discord know we are processing it

        guild_id = str(interaction.guild.id)
        server = await Database().get_server(guild_id)

        # Check if they use reactions, and that the message is in our records
        if await self.uses_reactions(interaction, server, message_id) is False:
            return

        message = await self.fetch_menu(interaction, server, message_id, guild_id)
        if message in [None, False]:
            return

        await message.edit(view=None)
        await interaction.followup.send("I have now deleted the role menu!")
        await self.db.update_server(guild_id, f"reaction_roles.{message_id}", 1, delete=True)

    def add_buttons(self, server, buttons, message_id):
        role_buttons = list()
        for button in server['reaction_roles'][message_id]["buttons"]:
            if "emoji" not in server['reaction_roles'][message_id]['buttons'][button]:
                button_emoji = None

            else:
                button_emoji = server['reaction_roles'][message_id]['buttons'][button]['emoji']

            if server['reaction_roles'][message_id]['button_type'] == "buttons":
                buttons.append(
                    Button(
                        emoji=button_emoji,
                        label=f"{server['reaction_roles'][message_id]['buttons'][button]['name']}",
                        style=get.button_color(server['reaction_roles'][message_id]['buttons'][button]['color']),
                        custom_id=f"reaction_role_add_{button}",
                    )
                )

            else:
                role_buttons.append(
                    discord.SelectOption(
                        value=button,
                        label=server['reaction_roles'][message_id]["buttons"][button]['name'],
                        description='Select this role to receive it', emoji=button_emoji  # noqa
                    ),
                )

        if len(role_buttons) > 0:
            buttons.append(
                Select(
                    placeholder="Select your roles here",
                    min_values=0,
                    max_values=len(role_buttons),
                    custom_id=f"reaction_role_menu_{message_id}",
                    options=role_buttons
                )
            )

        return buttons

    @app_commands.command(name="add", description="Add a role to a role menu")
    @app_commands.default_permissions(manage_guild=True)
    async def add_role(
        self, interaction: discord.Interaction, role: discord.Role, message_id: str, emoji: str = None,
        color: Literal["gray", "blue", "red", "green"] = "gray",
    ):
        """Adds a role to a menu"""
        hard_limit = 20
        free_limit = 5

        await interaction.response.defer(ephemeral=True)  # Let discord know we're processing it

        # Load in the server data
        server = await Database().get_server(str(interaction.guild.id), True)

        user_id = str(interaction.user.id)
        guild_id = str(interaction.guild.id)
        tier = await self.user_membership_tier(user_id)

        if await self.uses_reactions(interaction, server, message_id) is False:
            return

        if len(server['reaction_roles'][message_id]['buttons']) >= hard_limit:
            await interaction.followup.send(
                "You have reached discords button limit of 20. Therefore, you can't add more!"
            )
            return

        if len(server['reaction_roles'][message_id]['buttons']) > free_limit and tier < 2:
            await interaction.followup.send(
                f"You have reached the free limit of `{free_limit}`. "
                "Consider purchasing Premium or making a new message!"
            )
            return

        if await self.uses_reactions(interaction, server, message_id) is False:
            return

        # If they already have added the role, let them know
        # if str(role.id) in server['reaction_roles'][message_id]['buttons']:
        #     await interaction.followup.send("This role is already added", ephemeral=True)
        #     return

        message = await self.fetch_menu(interaction, server, message_id, guild_id)
        if message in [None, False]:
            return

        buttons = []

        await self.db.update_server(guild_id, f"reaction_roles.{message_id}.buttons.{role.id}", {
            "name": role.name,
            "color": color,
            "emoji": emoji
        })

        server['reaction_roles'][message_id]['buttons'][str(role.id)] = {
            "name": role.name,
            "color": color,
            "emoji": emoji
        }

        buttons = self.add_buttons(server, buttons, message_id)

        view = View()
        for button in buttons:
            view.add_item(button)

        try:
            await message.edit(view=view)

        except Exception as e:
            print("Issue editing role menu message:", e)
            return

        await interaction.followup.send(f"Added the role {role.mention} to the menu!", ephemeral=True)

    @app_commands.command(name="menu_type", description="Change the menu type")
    @app_commands.default_permissions(manage_guild=True)
    async def swap_menu_type(
        self, interaction: discord.Interaction, type: Literal["buttons", "dropdown"], message_id: str
    ):
        """Adds a role to a menu"""

        await interaction.response.defer(ephemeral=True)  # Let discord know we're processing it

        user_id = str(interaction.user.id)
        guild_id = str(interaction.guild.id)
        if type == "dropdown" and await self.user_membership_tier(user_id) < 2:
            await interaction.response.send_message(
                "This feature is a premium feature. Go to our patreon at: https://www.patreon.com/ultimaterpg "
                "and purchase a tier to gain access!"
            )

            return

        server = await Database().get_server(str(interaction.guild.id), True)  # Just making sure it exists

        if await self.uses_reactions(interaction, server, message_id) is False:
            return

        message = await self.fetch_menu(interaction, server, message_id, guild_id)
        if message in [None, False]:
            return

        buttons = []

        await self.db.update_server(guild_id, f"reaction_roles.{message_id}.button_type", type)
        server['reaction_roles'][message_id]["button_type"] = type

        buttons = self.add_buttons(server, buttons, message_id)

        view = View()
        for button in buttons:
            view.add_item(button)

        try:
            await message.edit(view=view)

        except Exception as e:
            print("Issue editing role menu message:", e)
            return

        await interaction.followup.send(f"Swapped the menu type of {message_id} to {type}!", ephemeral=True)

    @app_commands.command(name="remove", description="Remove a role to a role menu")
    @app_commands.default_permissions(manage_guild=True)
    async def remove_role(self, interaction: discord.Interaction, role: discord.Role, message_id: str):
        await interaction.response.defer(ephemeral=True)  # Let discord know we're processing it

        server = await Database().get_server(str(interaction.guild.id), True)  # Just making sure it exists
        guild_id = str(interaction.guild.id)

        # Check if they use reactions, and that the message is in our records
        if await self.uses_reactions(interaction, server, message_id) is False:
            return

        # If they already have added the role, let them know
        if str(role.id) not in server['reaction_roles'][message_id]['buttons']:
            await interaction.followup.send("This role is not added so there is nothing to removed.", ephemeral=True)
            return

        await self.db.update_server(
            str(interaction.guild.id), f"reaction_roles.{message_id}.buttons.{role.id}", 1, delete=True
        )

        message = await self.fetch_menu(interaction, server, message_id, guild_id)
        if message in [None, False]:
            return

        server['reaction_roles'][message_id]['buttons'].pop(str(role.id))

        buttons = []
        buttons = self.add_buttons(server, buttons, message_id)

        view = View()
        for button in buttons:
            view.add_item(button)

        try:
            await message.edit(view=view)

        except Exception as e:
            print("Issue editing role menu message:", e)
            return

        await interaction.followup.send(f"Removed the role {role.mention} from the menu!", ephemeral=True)

    # @app_commands.command(name="list", description="find your active button role menus")
    # @app_commands.default_permissions(manage_guild=True)
    # async def setup_reaction_roles(
    #     self, interaction: discord.Interaction, type: Literal["buttons", "dropdown"],
    #     channel: discord.TextChannel = None, message_id: str = None
    # ):
    #     """Creates a button role message"""

    @app_commands.command(name="create", description="Create a new button role menu")
    @app_commands.default_permissions(manage_guild=True)
    async def setup_reaction_roles(
        self, interaction: discord.Interaction, type: Literal["buttons", "dropdown"],
        channel: discord.TextChannel = None, message_id: str = None
    ):
        """Creates a button role message"""

        guild_id = str(interaction.guild.id)
        if channel is None:
            channel = interaction.channel

        # Make sure the bot has the permissions it needs
        permissions = channel.permissions_for(interaction.guild.me)
        allowed = False

        if (
            permissions.send_messages and permissions.view_channel
            and permissions.read_message_history and permissions.read_messages
            and permissions.use_external_emojis
        ):  # Check if the bot has the needed permissions
            allowed = True

        if allowed is False:
            await interaction.response.send_message("It appears I am not allowed to send messages to that channel...")
            return

        server = await Database().get_server(guild_id)
        user_id = str(interaction.user.id)

        allowed_reaction_role_messages = 3

        if type == "dropdown":
            if await self.user_membership_tier(user_id) < 2:
                await interaction.response.send_message(
                    "This feature is a premium feature. Go to our patreon at: https://www.patreon.com/ultimaterpg "
                    "and purchase a tier to gain access!", ephemeral=True
                )

                return

        # We check if they have the reaction roles set up.
        # If they don't set the active value to 0 so they can create it
        if 'reaction_roles' not in server:
            active_reaction_roles = 0

        # Otherwise, they must have active reaction roles.
        # Set the active value to this amount so we can check it.
        else:
            active_reaction_roles = len(server['reaction_roles'])

        # If the active value is less than how many they may have
        # They are allowed to create a new reaction role
        if active_reaction_roles < allowed_reaction_role_messages:
            if message_id is None:
                await interaction.response.send_modal(
                    ReactionRoles(
                        self.bot,
                        str(interaction.guild.id),
                        await get.embed_color(interaction.user.id),
                        channel,
                        type
                    )
                )
                return

            else:
                await interaction.response.defer()
                message = await channel.fetch_message(int(message_id))
                if message.author.id != self.bot.user.id:
                    await interaction.followup.send("I don't own that message, so I cannot add buttons to it!")
                    return

                if message:
                    await Database().update_server(
                        guild_id, f"reaction_roles.{message_id}", {
                            "channel_id": channel.id,
                            "button_type": type,
                            "buttons": {}
                        }
                    )

                    await interaction.followup.send(f"Great, I've added a menu to the message: `{message_id}`!")

                else:
                    await interaction.followup.send(f"I couldn't find a message with the id: `{message_id}`!")

        else:
            await interaction.response.send_message(
                "You have reached your free limit of button roles for this server.\n"
                "If you want to make another one, consider deleting a button role menu, or purchasing premium!"
            )

            return


async def setup(bot):
    await bot.add_cog(Roles(bot))
