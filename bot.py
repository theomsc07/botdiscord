import discord
from discord.ext import commands
import os
import asyncio
from datetime import datetime

# ==============================================================================
# CONFIGURATION
# ==============================================================================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="+", intents=intents)
TOKEN = os.getenv("DISCORD_TOKEN")

# IDs (À REMPLACER)
LOG_CHANNEL_ID = 1508482233219022992
TICKET_CATEGORY_ID = 1504792910892109935
GERANT_STAFF_ID = 968588191055642624
ROLE_STAFF = 1504810257715822722
ROLE_T, ROLE_C, ROLE_PLUS, ROLE_SENIOR, ROLE_ADMIN = 1504792771977023591, 1504792768088903931, 1504792764448116776, 1504792759679057951, 1504792748098715660

# ==============================================================================
# ESTHÉTIQUE & UTILS
# ==============================================================================
def create_embed(title, desc, color):
    e = discord.Embed(title=f"◈ {title} ◈", description=desc, color=color, timestamp=datetime.now())
    e.set_footer(text="MHA RP | White Wolf Corp")
    e.set_thumbnail(url=bot.user.display_avatar.url)
    return e

async def send_dm(member, title, desc, color):
    try:
        e = discord.Embed(title=f"Notification : {title}", description=desc, color=color)
        e.set_thumbnail(url=member.guild.icon.url)
        await member.send(embed=e)
    except: pass

async def clean_staff_roles(member):
    roles = [ROLE_T, ROLE_C, ROLE_PLUS, ROLE_SENIOR, ROLE_ADMIN, ROLE_STAFF]
    for r_id in roles:
        r = member.guild.get_role(r_id)
        if r and r in member.roles: await member.remove_roles(r)

# ==============================================================================
# TICKETS : VERDICTS ET FERMETURE AUTO
# ==============================================================================
class VerdictModal(discord.ui.Modal, title="Verdict du Recrutement"):
    reason = discord.ui.TextInput(label="Message personnalisé", style=discord.TextStyle.paragraph, required=True)
    def __init__(self, member, decision): super().__init__(); self.member = member; self.decision = decision
    async def on_submit(self, i: discord.Interaction):
        color = discord.Color.green() if self.decision == "ACCEPTÉ" else discord.Color.red()
        await send_dm(self.member, f"CANDIDATURE {self.decision}", self.reason.value, color)
        if self.decision == "ACCEPTÉ": await self.member.add_roles(i.guild.get_role(ROLE_T))
        else: await clean_staff_roles(self.member)
        await i.response.send_message("✅ Verdict envoyé, fermeture...", ephemeral=True)
        await asyncio.sleep(2); await i.channel.delete()

class VerdictView(discord.ui.View):
    def __init__(self, member): super().__init__(timeout=None); self.member = member
    @discord.ui.button(label="✅ Accepter", style=discord.ButtonStyle.green)
    async def acc(self, i: discord.Interaction, b): await i.response.send_modal(VerdictModal(self.member, "ACCEPTÉ"))
    @discord.ui.button(label="❌ Refuser", style=discord.ButtonStyle.danger)
    async def rej(self, i: discord.Interaction, b): await i.response.send_modal(VerdictModal(self.member, "REFUSÉ"))

# ==============================================================================
# COMMANDES : MODÉRATION & STAFF
# ==============================================================================
@bot.command()
@commands.has_permissions(kick_members=True)
async def warn(ctx, m: discord.Member, *, r="Aucune"):
    await send_dm(m, "AVERTISSEMENT", f"Averti sur {ctx.guild.name}.\nRaison : {r}", discord.Color.orange())
    await ctx.send(embed=create_embed("Warn", f"{m.mention} averti.", discord.Color.orange()))
    log_ch = ctx.guild.get_channel(LOG_CHANNEL_ID)
    if log_ch: await log_ch.send(embed=create_embed("LOG : Warn", f"Membre : {m.mention}\nRaison : {r}", discord.Color.orange()))

@bot.command()
@commands.has_permissions(manage_roles=True)
async def tempmute(ctx, m: discord.Member, s: int):
    for ch in ctx.guild.text_channels: await ch.set_permissions(m, send_messages=False)
    await send_dm(m, "MUTE TEMPORAIRE", f"Vous avez été muet sur {ctx.guild.name} pendant {s} secondes.", discord.Color.red())
    await ctx.send(f"⏳ {m.mention} muet pour {s}s.")
    await asyncio.sleep(s)
    for ch in ctx.guild.text_channels: await ch.set_permissions(m, send_messages=None)
    await ctx.send(f"✅ {m.mention} a retrouvé la parole.")

@bot.command()
@commands.has_permissions(administrator=True)
async def derank(ctx, m: discord.Member): await clean_staff_roles(m); await ctx.send(f"❌ {m.mention} est maintenant un simple mortel.")

@bot.command()
@commands.has_role(ROLE_STAFF)
async def helpstaff(ctx):
    e = create_embed("🔮 HELP STAFF", "Outils MHA RP :", discord.Color.dark_purple())
    e.add_field(name="Modération", value="`+warn` `+tempmute` `+kick` `+ban` `+unban`", inline=False)
    e.add_field(name="Tickets", value="`+setup_ticket` `+add` `+del` `+rename` `+close`", inline=False)
    e.add_field(name="Grades", value="`+rank-t/c/plus/senior/admin` `+derank`", inline=False)
    await ctx.send(embed=e)

class TicketPanel(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="📝 Ouvrir candidature MHA RP", style=discord.ButtonStyle.blurple, custom_id="open_ticket_button")
    async def open_ticket(self, i: discord.Interaction, b):
        over = {i.guild.default_role: discord.PermissionOverwrite(view_channel=False), i.user: discord.PermissionOverwrite(view_channel=True, send_messages=True), i.guild.get_role(ROLE_STAFF): discord.PermissionOverwrite(view_channel=True, send_messages=True)}
        ch = await i.guild.create_text_channel(name=f"recrut-{i.user.name}", category=i.guild.get_channel(TICKET_CATEGORY_ID), overwrites=over)
        await ch.send(f"{i.user.mention} | <@{GERANT_STAFF_ID}> | <@&{ROLE_STAFF}>", embed=create_embed("NOUVELLE CANDIDATURE", "Présente ton formulaire ici.", discord.Color.blue()), view=VerdictView(i.user))
        await i.response.send_message(f"✅ Ticket ouvert : {ch.mention}", ephemeral=True)

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_ticket(ctx): await ctx.send(embed=create_embed("🪐 RECRUTEMENT MHA RP", "Cliquez ci-dessous.", discord.Color.dark_gray()), view=TicketPanel())

@bot.event
async def on_ready(): bot.add_view(TicketPanel()); print(f"✅ Bot prêt : {bot.user}")
bot.run(TOKEN)
    
