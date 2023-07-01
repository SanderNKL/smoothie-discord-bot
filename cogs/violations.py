import discord
from discord.ext import commands
from discord import app_commands
from database import Database
import config as config
from handlers import logging


class Violation(commands.Cog):
    """
    VIOLATION COG

    This cog allows users to see their/others violations.
    Shows everything from warns, mutes, kicks and bans.
    """

    def __init__(self, bot):
        self.bot = bot
        self.db = Database()

    async def get_violations(
        self,
        interaction: discord.Interaction,
        user: discord.User,
        moderator: discord.User,
        page: int
    ):
        embed = discord.Embed(
            title="Registered Violations",
            description="Shows the 10 most recent violations given to a user (or) given by a moderator.",
            color=config.COLOR_ERROR
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

        return embed

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

        await interaction.response.defer()
        embed = await self.get_violations(interaction, user, moderator, 1)
        await interaction.followup.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Violation(bot))
