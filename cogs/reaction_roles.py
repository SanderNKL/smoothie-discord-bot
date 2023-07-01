import discord
from discord.ui import Button, View
from discord.ext import commands
from database import Database
import emojis as emojis
import config as config
from handlers import get

class CustomSuggestionEmojis(discord.ui.Modal, title='Select your Custom Emojis!'):
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
            print(f"Issue getting role: {self.role.value}", e)
            await interaction.response.send_message(
                "That was not a valid role! Please enable developer mode and copy the role id or name.\n"
                "Need help? Come meet my creators in: https://discord.com/invite/WTfaSnPMBw", ephemeral=True
            )
            return

        # We add the setup buttons. They must be re-added each edit. (Unless finished)
        buttons = [
            Button(
                label="Add Role",
                style=discord.ButtonStyle.gray,
                custom_id=f"setup_add_role_{interaction.user.id}"
            ),
            Button(
                label="Undo Previous Role",
                style=discord.ButtonStyle.gray,
                custom_id=f"setup_undo_role_{interaction.user.id}"
            ),
            Button(
                label="Finish Setup",
                style=discord.ButtonStyle.gray,
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
                        custom_id=f"setup_role_{button}",
                    )
                )

            buttons.append(
                Button(
                    label=f"{self.button_name.value}",
                    style=color,
                    custom_id=f"setup_role_{role.id}"
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


class ReactionRoles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()

    async def missing_perm_alert(self, interaction, server):
        try:
            if 'logs' in server and 'moderation' in server['logs']:
                channel = await self.bot.fetch_channel(server['logs']['moderation'])
                embed = discord.Embed(
                    description=(
                        f"I failed to give **{interaction.user}** (`{interaction.user.id}`) their role!\n"
                        "Make sure that I have permission to assign roles and that I am higher\n"
                        "in the role hierarchy!"
                    ),
                    color=config.COLOR_ERROR
                )

                embed.set_image(url="https://i.imgur.com/CSNYUBo.png")
                await channel.send(embed=embed)

        except discord.Forbidden:
            await self.db.update_server(str(interaction.guild.id), "logs.moderation", 1, delete=True)
            return

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        """Detects when a user clicks a button or uses a slash command"""

        # Ensures that the interaction is a button, and not a slash commabd
        if interaction.type.name != "component":
            return

        button = interaction.data["custom_id"]
        # We make sure the button is a minigame button
        if button[0:13] != "reaction_role":
            return

        await interaction.response.defer()  # Let's discord know we are processing it

        if button[0:18] == "reaction_role_menu":
            server = await self.db.get_server(str(interaction.guild.id))
            message_id = str(interaction.message.id)

            if 'reaction_roles' not in server or message_id not in server['reaction_roles']:
                return

            roles = []

            guild_roles = await interaction.guild.fetch_roles()
            for guild_role in guild_roles:
                if str(guild_role.id) in server['reaction_roles'][message_id]['buttons']:
                    roles.append(guild_role)

            for role in roles:
                if str(role.id) in interaction.data['values']:
                    add_role = True

                else:
                    add_role = False

                try:
                    if add_role is None:
                        await interaction.followup.send(
                            "Woopsies. Something wen't wrong here... Perhaps the role no longer exists?", ephemeral=True
                        )
                        return

                    elif add_role is True:
                        try:
                            await interaction.user.add_roles(role)

                        except discord.Forbidden:
                            await interaction.followup.send(
                                f"Well, this is embarrassing... I don't have permission to give you {role}...",
                                ephemeral=True
                            )

                            await self.missing_perm_alert(interaction, server)

                        except Exception as e:
                            print("Issue removing role:", e)

                    elif add_role is False:
                        try:
                            await interaction.user.remove_roles(role)

                        except discord.Forbidden:
                            await interaction.followup.send(
                                f"Well, this is embarrassing... I don't have permission to remove {role}...",
                                ephemeral=True
                            )

                            await self.missing_perm_alert(interaction, server)

                        except Exception as e:
                            print("Issue removing role:", e)

                except Exception as e:
                    print("issue adding role to user in setup:", e)
                    await self.db.update_server(str(interaction.guild.id), f"reaction_roles.{message_id}", 1, delete=True)

            await interaction.followup.send(
                "**Your roles have been updated!**\n"
                "Keep in mind that the roles you **did not select** have been removed from you.\n"
                "If you want all of the roles, please select all of them.", ephemeral=True
            )

        #  user_id = str(interaction.user.id
        if button[0:17] == "reaction_role_add":
            server = await self.db.get_server(str(interaction.guild.id))
            message_id = str(interaction.message.id)

            if 'reaction_roles' not in server or message_id not in server['reaction_roles']:
                return

            role_id = button[18:]
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
                    await interaction.followup.send(
                        "Woopsies. Something wen't wrong here... Perhaps the role no longer exists?", ephemeral=True
                    )
                    return

                elif add_role is True:
                    await interaction.user.add_roles(role)
                    await interaction.followup.send(f"You now have the role: {role.mention}", ephemeral=True)

                elif add_role is False:
                    await interaction.user.remove_roles(role)
                    await interaction.followup.send(
                        f"You no longer have the role: {role.mention}", ephemeral=True
                    )

            except discord.Forbidden:
                await interaction.followup.send(
                    "Well, this is embarrassing... I don't have permission to give you this role...", ephemeral=True
                )

                await self.missing_perm_alert(interaction, server)

            except Exception as e:
                print("issue adding role to user in setup:", e)
                await self.db.update_server(str(interaction.guild.id), f"reaction_roles.{message_id}", 1, delete=True)


async def setup(bot):
    await bot.add_cog(ReactionRoles(bot))
