import validators
import discord
from discord import app_commands
from discord.ext import commands
from database import Database
from handlers import get


class MessagesPlugin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.guild is None or message.author.bot:
            return

        # Update the users message count
        await self.db.user_messages.update_one(
            {"user_id": str(message.author.id)},
            {"$inc": {f"guilds.{str(message.guild.id)}": 1}},
            upsert=True
        )

        if message.mentions:
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

    @app_commands.command(name="messages", description="See how many messages a user has")
    async def messages_command(self, interaction: discord.Interaction, user: discord.User = None):
        await interaction.response.defer()
        if not user:
            user = interaction.user

        message_count = await get.user_messages(user, interaction.guild)

        embed = discord.Embed(
            description=f"They have sent **{message_count}** messages in this server.",
            color=await get.embed_color(user.id)
        ).set_author(name=f"{user.name}'s Messages", icon_url=get.user_avatar(user))

        embed.set_footer(text=self.bot.user.name, icon_url=self.bot.user.display_avatar)

        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(MessagesPlugin(bot))
