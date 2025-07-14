import discord
from discord.ext import commands
from discord import app_commands, ui, Interaction, ButtonStyle, Embed, Permissions
import re
import os
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup

load_dotenv()
TOKEN = os.getenv("TOKEN")
ID_SALON_SUGGESTIONS = 1380874512505110626
ID_SALON_INFO = 1370855056823419042

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Connecté en tant que {bot.user}")
    bot.add_view(SuggestionView())
    channel = bot.get_channel(ID_SALON_INFO)
    if channel:
        deja_envoye = False
        async for msg in channel.history(limit=20):
            if msg.author == bot.user and msg.embeds:
                embed = msg.embeds[0]
                if embed.title == "Suggestions de jeux":
                    deja_envoye = True
                    break
        if not deja_envoye:
            embed = Embed(
                title="Suggestions de jeux",
                description="Pour faire une suggestion, utilisez le bouton ci-dessous. Entrez les informations nécessaires (nom, description, lien Steam) et j'examinerai votre suggestion au plus vite.",
                color=0x00ff00
            )
            view = SuggestionView()
            await channel.send(embed=embed, view=view)

class SuggestionModal(ui.Modal, title="Nouvelle suggestion de jeu"):
    nom = ui.TextInput(label="Nom du jeu", max_length=100)
    lien = ui.TextInput(label="Lien Steam", max_length=200)

    async def on_submit(self, interaction: Interaction):
        channel = bot.get_channel(ID_SALON_SUGGESTIONS)
        steam_id = None
        match = re.search(r"store\.steampowered\.com/app/(\d+)", self.lien.value)
        if match:
            steam_id = match.group(1)
        description_steam = "Description non trouvée."
        if steam_id:
            try:
                url = f"https://store.steampowered.com/app/{steam_id}"
                response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
                soup = BeautifulSoup(response.text, "html.parser")
                desc_div = soup.find("div", {"class": "game_description_snippet"})
                if desc_div:
                    description_steam = desc_div.text.strip()
            except Exception as e:
                description_steam = f"Erreur lors de la récupération: {e}"
        embed = Embed(
            title=f"🚀 Nouvelle suggestion de jeu",
            description=(
                f"**Nom du jeu:**\n{self.nom.value}\n\n"
                f"**Description:**\n{description_steam}\n\n"
                f"**Lien Steam:**\n{self.lien.value}\n\n"
                f"_Suggéré par {interaction.user.mention}_"
            ),
            color=0x3498db
        )
        if steam_id:
            image_url = f"https://cdn.cloudflare.steamstatic.com/steam/apps/{steam_id}/header.jpg"
            embed.set_image(url=image_url)
        view = AdminView()
        await channel.send(content="<@1181255979225071626>", embed=embed, view=view)
        await interaction.response.send_message("Ta suggestion a bien été envoyée !", ephemeral=True)

class SuggestionView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="Créer une suggestion", style=ButtonStyle.green, custom_id="suggestion_create")
    async def create_suggestion(self, interaction: Interaction, button: ui.Button):
        await interaction.response.send_modal(SuggestionModal())

class AdminView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="Accepter", style=ButtonStyle.success)
    async def accept(self, interaction: Interaction, button: ui.Button):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("Seuls les admins peuvent accepter.", ephemeral=True)
            return
        await interaction.message.edit(embed=self._update_embed(interaction.message.embeds[0], "✅ Acceptée", 0x2ecc71), view=None)
        await interaction.response.send_message("Suggestion acceptée.", ephemeral=True)

    @ui.button(label="Refuser", style=ButtonStyle.danger)
    async def refuse(self, interaction: Interaction, button: ui.Button):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("Seuls les admins peuvent refuser.", ephemeral=True)
            return
        await interaction.message.edit(embed=self._update_embed(interaction.message.embeds[0], "❌ Refusée", 0xe74c3c), view=None)
        await interaction.response.send_message("Suggestion refusée.", ephemeral=True)

    def _update_embed(self, embed, status, color):
        embed = embed.copy()
        embed.add_field(name="Statut", value=status, inline=False)
        embed.color = color
        return embed

bot.run(TOKEN)
