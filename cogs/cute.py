import discord
from discord import app_commands
from discord.ext import commands, tasks
from handlers import get
from discord.ui import Button, View


class Cute(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.fit_posts = get.random_reddit_post(['cute', 'aww'], get.reddit_connection())
        self.get_new_memes.start()

    @tasks.loop(seconds=10800)
    async def get_new_memes(self):
        self.fit_posts = get.random_reddit_post(['cute', 'aww'], get.reddit_connection())

    @app_commands.command(
        name="cute",
        description="Make Smoothie send you something cute!",

    )
    async def cute(self, interaction: discord.Interaction):
        """Get cute posts from reddit"""
        await interaction.response.defer()
        reddit_post = get.random_reddit_post(self.fit_posts)

        embed = discord.Embed(
            title=reddit_post['title'],
            color=await get.embed_color(interaction.user.id)
        )

        if len(reddit_post['text']) > 0:
            embed.description = reddit_post['text']

        embed.set_image(url=reddit_post['image_url'])

        view = View()
        view.add_item(
            Button(
                label="Source",
                url=f"https://reddit.com{reddit_post['permalink']}",
            )
        )

        await interaction.followup.send(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(Cute(bot))
