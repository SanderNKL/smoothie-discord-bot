import discord
from discord.ext import commands
from discord import app_commands
from googletrans import Translator
from cogs.translations import flags
from handlers import get
import json

google = Translator()


class Translation(commands.Cog):
    def __init__(self, bot: commands.AutoShardedBot):
        self.bot = bot

        self.ctx_menu = app_commands.ContextMenu(
            name='Translate',
            callback=self.translate_menu,
        )
        self.bot.tree.add_command(self.ctx_menu)

    async def translate_menu(
        self,
        interaction: discord.Interaction,
        message: discord.Message,
    ):
        text = ""
        embeds = ""
        if message.content != "":
            text += f"\n{message.content}"

        if message.embeds:
            if message.embeds[0].title:
                embeds += f"\nTitle: {message.embeds[0].title}"

            if message.embeds[0].description:
                embeds += f"\nDescription: {message.embeds[0].description}"

            if message.embeds[0].footer:
                embeds += f"\nFooter: {message.embeds[0].footer.text}"

            text += f"\n\n**Embed Content**:{embeds}"

        await interaction.response.defer(ephemeral=True)
        embed = await self.translate(interaction, text, "english")
        embed.add_field(
            name="Original Message",
            value="[Click here to jump]({})".format(
                message.jump_url
            )
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(
        name="translate",
        description="Translate a sentence!"
    )
    async def translate_command(
        self,
        interaction: discord.Interaction,
        sentence: str,
        language: str = "english",
    ):
        await interaction.response.defer()
        embed = await self.translate(interaction, sentence, language)
        await interaction.followup.send(embed=embed)

    def get_language_key(
        self,
        input
    ):
        with open('cogs/translations/languages.json', 'r') as f:
            supported_languages = json.load(f)

        language_key = None
        for lan in supported_languages:
            if input == supported_languages[lan]:
                language_key = lan.lower()
                break

            elif input == lan:
                language_key = lan.lower()
                break

        return language_key

    async def translate(
        self,
        interaction: discord.Interaction,
        sentence: str,
        language: str
    ):
        try:
            language = language.lower()
            language_key = self.get_language_key(language)

            if not language_key or language_key == language:
                try:
                    language_key = self.get_language_key(google.translate(language).text.lower())

                except Exception as e:
                    print("Issue translating language key:", e)
                    language_key = language

            # Language key is still nothing useful.
            if not language_key:
                language_key = language

            translation = google.translate(sentence, dest=language_key)
            language_flag_to = flags.flag(translation.dest)
            language_flag_from = flags.flag(translation.src)

            embed = discord.Embed(
                title=f"Translation {translation.dest.upper()} {language_flag_to}",
                description=translation.text,
                color=await get.embed_color(interaction.user.id)
            )

            embed.set_footer(
                text=f"Smoothie translated this from {translation.src.upper()} {language_flag_from}",
                icon_url=self.bot.application.icon.url
            )

            return embed
        
        except Exception as e:
            print("Issue with translating:", e)
            return await interaction.followup.send("Failed to translate text... Check that you spelt the language name correctly!")


async def setup(bot):
    await bot.add_cog(Translation(bot))
