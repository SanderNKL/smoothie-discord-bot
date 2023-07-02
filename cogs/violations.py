import discord
from discord.ext import commands
from discord import app_commands
from database import Database
import config as config
from handlers import logging
import math
from discord.ui import Button, View


class Violation(commands.Cog):
    """
    VIOLATION COG

    This cog allows users to see their/others violations.
    Shows everything from warns, mutes, kicks and bans.
    """

    def __init__(self, bot):
        self.bot = bot
        self.db = Database()

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        """Detects when a user clicks a button or uses a slash command"""

        # Ensures that the interaction is a button, and not a slash commabd
        if interaction.type.name != "component":
            return
        
        button = interaction.data["custom_id"].split("_")
        if button[0] != "violation":
            return

        await interaction.response.defer()  # Let's discord know we are processing it
        
        # Get User Data from Buttons
        if button[2] != "none":
            user = await self.bot.fetch_user(int(button[2]))

        else:
            user = None

        if button[3] != "none":
            moderator = await self.bot.fetch_user(int(button[3]))
        
        else:
            moderator = None

        last_page = math.ceil(
            await logging.total_violations(interaction.guild, user, moderator)  # Amount of Violations
            /
            10
        )

        if button[1] == "first":
            page = 1

        elif button[1] == "prev":
            page = int(interaction.message.embeds[0].footer.text.split(" ")[2]) - 1
            if page < 1:
                page = last_page

        elif button[1] == "next":
            page = int(interaction.message.embeds[0].footer.text.split(" ")[2]) + 1
            if page > last_page:
                page = 1

        elif button[1] == "last":
            page = last_page

        else:
            # We should never end up here
            # But if we do, this is a safety net
            page = 1

        embed, view = await self.get_violations(
            interaction,
            user,
            interaction.user,
            page
        )

        await interaction.followup.edit_message(
            interaction.message.id,
            embed=embed,
            view=view
        )

    async def get_violations(
        self,
        interaction: discord.Interaction,
        user: discord.User,
        moderator: discord.User,
        page: int
    ):
        user_id = "none"
        moderator_id = "none"
        if user:
            user_id = user.id

        if moderator:
            moderator_id = moderator.id

        embed = discord.Embed(
            title="Registered Violations",
            description="Shows the 10 most recent violations given to a user (or) given by a moderator.",
            color=config.COLOR_SMOOTHIE
        )

        embed.set_footer(
            text=f"Viewing Page: {page}"
        )

        violations = await logging.get_violations(interaction.guild, user, moderator, page-1)
        for i in range(0, len(violations)):
            embed.add_field(
                name=f"Violation #{(i + 1) + ((page - 1) * 10)}",
                value=(
                    "```"
                    "Action: {}\n"
                    "User: {} ({})\n"
                    "Moderator: {} ({})\n"
                    "Reason: {}\n"
                    "Timestamp: {}"
                    "```"
                    .format(
                        list(violations)[i]['action'].capitalize(),
                        list(violations)[i]['violator_name'],
                        list(violations)[i]['violator_id'],
                        list(violations)[i]['moderator_name'],
                        list(violations)[i]['moderator_id'],
                        list(violations)[i]['reason'],
                        list(violations)[i]['timestamp']
                    )
                ),
                inline=False
            )

        if len(violations) == 0:
            embed.add_field(
                name="No Records",
                value="""```There appears to be no records!```"""
            )

        view = View()
        view.add_item(
            Button(
                label="First Page",
                style=discord.ButtonStyle.blurple,
                custom_id=f"violation_first_{user_id}_{moderator_id}"
            )
        )

        view.add_item(
            Button(
                label="Previous Page",
                style=discord.ButtonStyle.blurple,
                custom_id=f"violation_prev_{user_id}_{moderator_id}"
            )
        )

        view.add_item(
            Button(
                label="Next Page",
                style=discord.ButtonStyle.blurple,
                custom_id=f"violation_next_{user_id}_{moderator_id}"
            )
        )

        view.add_item(
            Button(
                label="Last Page",
                style=discord.ButtonStyle.blurple,
                custom_id=f"violation_last_{user_id}_{moderator_id}"
            )
        )

        return embed, view

    @app_commands.command(
        name="violations",
        description="See all of the violations of a user, and the actions taken.",
    )
    @app_commands.default_permissions(manage_messages=True)
    async def violation_command(
        self,
        interaction: discord.Interaction,
        user: discord.User = None,
        moderator: discord.User = None,
    ):
        if not user and not moderator:
            await interaction.response.send_message(
                "You need to specify a **User** or a **Moderator**.",
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)
        embed, view = await self.get_violations(
            interaction,
            user,
            moderator,
            1
        )

        await interaction.followup.send(
            embed=embed,
            view=view,
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(Violation(bot))
