import discord
from discord import app_commands
from discord.ext import commands, tasks
from database import Database
from time import time
from handlers import get


class Timer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()
        self.find_ended_reminders.start()

    @tasks.loop(seconds=5)
    async def find_ended_reminders(self):
        """Ends active reminders automatically"""
        async def find_reminders():
            search = self.db.reminder.find({"timer": {"$lte": time()}})
            expired_reminders = await search.to_list(length=100)
            return expired_reminders

        expired_reminders = await find_reminders()
        while len(expired_reminders) > 0:
            for reminder in expired_reminders:
                try:
                    channel = await self.bot.fetch_channel(reminder['channel_id'])
                    embed = discord.Embed(
                        title="Reminder",
                        description=f"This is a reminder for: {reminder['reminder']}.",
                        color=await get.embed_color(reminder['user_id'])
                    )

                    await channel.send(f"Hey, <@{reminder['user_id']}>! I'm here to remind you. 😊", embed=embed)

                except discord.Forbidden:
                    pass

                except discord.NotFound:
                    pass

                except Exception as e:
                    print("Issue with reminder system:", e)

                await self.db.reminder.delete_one({"_id": reminder['_id']})

            expired_reminders = await find_reminders()

    @app_commands.command(name="reminder", description="Remind yourself of something!")
    async def reminder(self, interaction: discord.Interaction, duration: str, reminder: str = "No Reminder Specified"):
        try:
            await interaction.response.defer()
            remind_duration = int(get.determined_time(duration) + time())
            if remind_duration <= int(time()):
                return await interaction.followup.send(
                    "The duration needs to be something like: 30d 20h 10s. Minimum 120",
                    ephemeral=True
                )

            await interaction.followup.send(
                f"Alright {interaction.user.mention}. I will set a reminder for you!",
                embed=discord.Embed(
                    title="Reminder",
                    description=(
                        f"You will be reminded in <t:{remind_duration}:R>\n"
                        f"- {reminder}"
                    ),
                    color=await get.embed_color(interaction.user.id)
                )
            )

            await self.db.reminder.insert_one({
                "user_id": interaction.user.id,
                "timer": remind_duration,
                "reminder": reminder,
                "channel_id": interaction.channel.id
            })

        except Exception as e:
            print("Issue with reminder cmd:", e)

    @app_commands.command(name="timer", description="Set a timer!")
    async def timer(self, interaction: discord.Interaction, duration: str, reminder: str = "No Reminder Specified"):
        try:
            await interaction.response.defer()
            remind_duration = int(get.determined_time(duration) + time())
            if remind_duration <= int(time()):
                return await interaction.followup.send(
                    "The duration needs to be something like: 30d 20h 10s. Minimum 120",
                    ephemeral=True
                )

            await interaction.followup.send(
                f"Alright {interaction.user.mention}. I will set a timer for you!",
                embed=discord.Embed(
                    title="Timer",
                    description=(
                        f"You will be reminded in <t:{remind_duration}:R>\n"
                        f"- {reminder}"
                    ),
                    color=await get.embed_color(interaction.user.id)
                )
            )

            await self.db.reminder.insert_one({
                "user_id": interaction.user.id,
                "timer": remind_duration,
                "reminder": reminder,
                "channel_id": interaction.channel.id
            })

        except Exception as e:
            print("Issue with reminder cmd:", e)


async def setup(bot):
    await bot.add_cog(Timer(bot))
