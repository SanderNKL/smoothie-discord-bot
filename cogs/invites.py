import discord
from discord import app_commands
from discord.ext import commands
from database import Database
from handlers import get, checks
import emojis as emojis


class Invite(commands.Cog):
    """
    INVITE COG

    This cog allows users and/or servers to track user invites.
    This may also be used in other cogs to restrict certain usage.
    """

    def __init__(self, bot):
        self.bot = bot
        self.db = Database()

    @commands.Cog.listener()
    async def on_invite_create(
        self,
        invite: discord.Invite
    ):
        await self.db.invites.insert_one(
            {
                "guild_id": str(invite.guild.id),
                "user_id": str(invite.inviter.id),
                "invite_id": str(invite.id),
                "joins": {},
                "leaves": {},
                "uses": 0
            }
        )

    @commands.Cog.listener()
    async def on_member_remove(
        self,
        user: discord.User
    ):
        logged_invite = await self.db.invites.find_one({
            "guild_id": str(user.guild.id),
            f"joins.{user.id}": {"$exists": True}
        })

        fake = checks.is_account_fake(user)

        if logged_invite:
            await self.db.invites.update_one(
                {
                    "guild_id": str(user.guild.id),
                    "user_id": logged_invite["user_id"],
                    "invite_id": logged_invite["invite_id"]
                },
                {
                    "$unset": {
                        f"joins.{user.id}": 1
                    },
                    "$set": {
                        f"leaves.{user.id}": {"fake": fake}
                    }
                }
            )

    async def add_invite(
        self,
        guild:
        discord.Guild,
        user: discord.User,
        invite: discord.Invite
    ):
        await self.db.invites.update_one(
            {
                "guild_id": str(guild.id),
                "user_id": str(user.id),
                "invite_id": str(invite.id),
            },
            {
                "$set": {
                    "leaves": {},
                    "joins": {},
                    "uses": invite.uses
                }
            }, upsert=True
        )

    @commands.Cog.listener()
    async def on_member_join(
        self,
        user: discord.User
    ):
        try:
            if not user.guild.me.guild_permissions.manage_guild:
                return

            fake = checks.is_account_fake(user)
            tracked_invites = []

            # LIST OF INVITES
            for guild_invite in await user.guild.invites():
                invite = await self.db.invites.find_one({
                    "invite_id": str(guild_invite.id),
                    "guild_id": str(user.guild.id),
                    "user_id": str(guild_invite.inviter.id)
                })

                # Invite found. Check if it has been updated
                if invite:
                    if guild_invite.uses > invite["uses"]:
                        tracked_invites.append({
                            "invite_id": guild_invite.id,
                            "guild_id": str(user.guild.id),
                            "user_id": str(guild_invite.inviter.id),
                            "uses": guild_invite.uses
                        })

                # Invite not found. Add it to the database
                else:
                    await self.add_invite(
                        user.guild,
                        guild_invite.inviter,
                        guild_invite
                    )

            # CHECK AND UPDATE TRACKED INVITES
            if len(tracked_invites) == 0:
                pass

            # Only one invite changed. We assume they joined using this one.
            elif len(tracked_invites) == 1:
                await self.db.invites.update_one(
                    {
                        "guild_id": str(user.guild.id),
                        "user_id": tracked_invites[0]["user_id"],
                        "invite_id": tracked_invites[0]["invite_id"]
                    },
                    {
                        "$set": {
                            f"joins.{user.id}": {"fake": fake},  # Add the user to join
                            "uses": tracked_invites[0]["uses"]  # Increase the use to the current
                        },
                        "$unset": {
                            f"leaves.{user.id}": 1  # Remove the user from leave, if they are there.
                        },
                    }
                )

            # Invites are more than one, so we don't know which one they joined with.
            # We update these records to make sure we can in the future.
            else:
                for invite in tracked_invites:
                    await self.db.invites.update_one(
                        {
                            "guild_id": str(user.guild.id),
                            "user_id": invite["user_id"],
                            "invite_id": invite["invite_id"]
                        },
                        {
                            "$set": {
                                "uses": invite["uses"]
                            }
                        }
                    )

        except discord.Forbidden as e:
            print("issue with on_member_join permissions:", e)

        except Exception as e:
            print("Issue with on_member_join in invite tracking:", e)

    # See the Invites you have
    @app_commands.command(
        name="invites",
        description="See how many invites a user has"
    )
    async def invites_command(
        self, interaction: discord.Interaction,
        user: discord.User = None
    ):
        await interaction.response.defer()

        # Check if the bot has access to manage invites
        if not interaction.guild.me.guild_permissions.manage_guild:
            return await interaction.followup.send(
                f"{emojis.ERROR} I don't have `MANAGE SERVER` permissions so I cannot manage invites!",
                ephemeral=True
            )

        if not user:
            user = interaction.user

        await self.db.sync_invites(interaction.guild)
        data = await get.user_invites(user, interaction.guild)

        joins = data['joins'] - data['leaves']
        if joins < 0:
            joins = 0

        if user.id != interaction.user.id:
            description = (
                f"They have: **{joins} invites** (**{data['joins']} joins**, "
                f"**{data['leaves']} leaves** and **{data['fake']} fake/suspicious **)"
            )

        else:
            description = (
                f"You have: **{joins} invites** (**{data['joins']} joins**, "
                f"**{data['leaves']} leaves** and **{data['fake']} fake/suspicious **)"
            )

        embed = discord.Embed(
            description=description,
            color=await get.embed_color(user.id)
        )

        embed.set_author(
            name=f"{user.name.capitalize()}'s Invites",
            icon_url=get.user_avatar(user)
        )

        embed.set_footer(
            text=self.bot.user.name,
            icon_url=self.bot.user.display_avatar
        )

        await interaction.followup.send(
            embed=embed
        )


async def setup(bot):
    await bot.add_cog(Invite(bot))
