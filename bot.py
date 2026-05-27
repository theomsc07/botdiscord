import discord
from discord.ext import commands
import asyncio
import os
from datetime import datetime

# ==============================================================================
# CONFIGURATION
# ==============================================================================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="+", intents=intents)

TOKEN = os.getenv("DISCORD_TOKEN")

# IDs
LOG_CH_ID = 1508595464168013965
GERANT_STAFF_ID = 1504792751777255545
ROLE_STAFF = 1504810257715822722
TICKET_CAT_ID = 1504792910892109935
R_T, R_C, R_PLUS, R_SENIOR, R_ADMIN = 1504792771977023591, 1504792768088903931, 1504792764448116776, 1504792759679057951, 1504792748098715660

# --- UTILS (LOGS + MP) ---
async def send_dm_and_log(ctx, action, target, reason):
    log_ch = bot.get_channel(LOG_CH_ID)
    e = discord.Embed(title=f"◈ LOG : {action} ◈", color=0x3498DB, timestamp=datetime.now())
    e.add_field(name="Cible", value=f"{target.mention}", inline=True)
    e.add_field(name="Staff", value=ctx.author.mention, inline=True)
    e.add_field(name="Raison", value=reason, inline=False)
    e.set_thumbnail(url=bot.user.display_avatar.url)
    if log_ch: await log_ch.send(embed=e)
    try:
        dm = discord.Embed(title=f"◈ Notification : {action} ◈", description=f"Sanction sur {ctx.guild.name}", color=0xFF0000, timestamp=datetime.now())
        dm.add_field(name="Staff", value=ctx.author.name, inline=True)
        dm.add_field(name="Raison", value=reason, inline=False)
        dm.set_thumbnail(url=bot.user.display_avatar.url)
        await target.send(embed=dm)
    except: pass

# --- TICKETS SYSTEM ---
class DecisionModal(discord.ui.Modal):
    def __init__(self, target, decision):
        super().__init__(title=f"Réponse à {target.name}")
        self.target = target
        self.decision = decision
        self.msg = discord.ui.TextInput(label="Message personnalisé", style=discord.TextStyle.paragraph)
        self.add_item(self.msg)
    async def on_submit(self, i: discord.Interaction):
        try: await self.target.send(f"◈ **Candidature {self.decision}** ◈\n{self.msg.value}"); await i.response.send_message("✅ MP envoyé.", ephemeral=True)
        except: await i.response.send_message("❌ MP bloqué.", ephemeral=True)

class TicketView(discord.ui.View):
    def __init__(self, member):
        super().__init__(timeout=None)
        self.member = member
    @discord.ui.button(label="Accepter", style=discord.ButtonStyle.green)
    async def acc(self, i, b): await i.response.send_modal(DecisionModal(self.member, "ACCEPTÉE"))
    @discord.ui.button(label="Refuser", style=discord.ButtonStyle.red)
    async def ref(self, i, b): await i.response.send_modal(DecisionModal(self.member, "REFUSÉE"))

class TicketPanel(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="Poser ma candidature", style=discord.ButtonStyle.primary, emoji="🛡️", custom_id="candid_btn")
    async def open_ticket(self, i: discord.Interaction, b):
        over = {i.guild.default_role: discord.PermissionOverwrite(view_channel=
    
