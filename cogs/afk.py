import discord
from discord import app_commands
from discord.ext import commands
from database import Database
import config as config
from handlers import get


class AFK(commands.Cog):
    """
    AFK COG

    This cog allows users to go AFK on discord.
    The user types /afk and the bot will let anyone who pings them
    know that they are busy, as well as providing the user a link
    to all of these messages when they return.
    """

    def __init__(self, bot):
        self.bot = bot
        self.db = Database()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.guild is None or message.author.bot:
            return

        if not message.mentions:
            return

        for mention in message.mentions:
            if mention.id == message.author.id:
                continue

            data = await self.db.afk.find_one({"user_id": mention.id})
            if data and data['active']:
                await message.channel.send(
                    f"{mention.display_name} is busy, so please don't disturb them! {message.author.mention}\n"
                    "I have logged your message so that they can find it when they return 😋"
                )

                await self.db.afk.update_one(
                    {"user_id": mention.id},
                    {"$push": {
                        "messages": {
                            "author": message.author.id, "message": message.content, "jump": message.jump_url
                        }
                    }}
                )

    @app_commands.command(name="afk", description="Turn on Do Not Disturb Mode")
    async def afk_command(self, interaction: discord.Interaction):
        data = await self.db.afk.find_one({"user_id": interaction.user.id})

        enabled = False
        if data:
            enabled = data['active']

        if enabled:
            enabled = False

            if 'messages' in data and len(data['messages']) > 0:
                pings = ""

                i = 0
                for message in data['messages']:
                    if i >= 15:
                        if i - 15 > 0:
                            pings += f"\nand {len(data['messages']) - 15} more pings..."
                        break

                    pings += "\n\n[Click to Jump]({}) - <@{}> - {}".format(
                        message['jump'],
                        message['author'],
                        message['message']
                    )

                    i += 1

                embed = discord.Embed(
                    title="Recent Messages",
                    description=pings,
                    color=config.COLOR_EMPTY
                )

            await interaction.response.send_message(
                f"{interaction.user.mention} is no longer AFK!",
                embed=embed
            )
            await self.db.afk.delete_one({"user_id": interaction.user.id})

        else:
            enabled = True
            embed = discord.Embed(
                description="Please do not disturb them!",
                color=config.COLOR_EMPTY
            )

            embed.set_author(name=f"{interaction.user.name} is now AFK!", icon_url=get.user_avatar(interaction.user))
            await self.db.afk.update_one({"user_id": interaction.user.id}, {"$set": {"active": enabled}}, upsert=True)
            await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(AFK(bot))
