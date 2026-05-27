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
        over = {i.guild.default_role: discord.PermissionOverwrite(view_channel=False), i.user: discord.PermissionOverwrite(view_channel=True, send_messages=True), i.guild.get_role(GERANT_STAFF_ID): discord.PermissionOverwrite(view_channel=True, send_messages=True)}
        ch = await i.guild.create_text_channel(name=f"recrut-{i.user.name}", category=i.guild.get_channel(TICKET_CAT_ID), overwrites=over)
        e = discord.Embed(title="◈ CANDIDATURE ◈", description=f"Bonjour {i.user.mention}, posez votre formulaire ici.", color=0x2C2F33)
        e.set_thumbnail(url=bot.user.display_avatar.url)
        await ch.send(content=f"{i.user.mention} | <@&{GERANT_STAFF_ID}>", embed=e, view=TicketView(i.user))
        await i.response.send_message(f"✅ Ticket : {ch.mention}", ephemeral=True)

# --- COMMANDES ---
@bot.command(aliases=['del'])
@commands.has_role(GERANT_STAFF_ID)
async def close(ctx): await ctx.channel.delete()
@bot.command()
@commands.has_role(GERANT_STAFF_ID)
async def rename(ctx, name: str): await ctx.channel.edit(name=name); await ctx.send("✅ Renommé.")
@bot.command()
@commands.has_role(GERANT_STAFF_ID)
async def add(ctx, m: discord.Member): await ctx.channel.set_permissions(m, view_channel=True); await ctx.send(f"✅ {m.name} ajouté.")
@bot.command()
@commands.has_role(GERANT_STAFF_ID)
async def remove(ctx, m: discord.Member): await ctx.channel.set_permissions(m, view_channel=False); await ctx.send(f"✅ {m.name} retiré.")

# Modération
@bot.command()
@commands.has_permissions(kick_members=True)
async def warn(ctx, m: discord.Member, *, r="Aucune"): await send_dm_and_log(ctx, "WARN", m, r); await ctx.send("✅")
@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, m: discord.Member, *, r="Aucune"): await send_dm_and_log(ctx, "KICK", m, r); await m.kick(reason=r)
@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, m: discord.Member, *, r="Aucune"): await send_dm_and_log(ctx, "BAN", m, r); await m.ban(reason=r)
@bot.command()
@commands.has_permissions(ban_members=True)
async def unban(ctx, uid: int): u = await bot.fetch_user(uid); await ctx.guild.unban(u); await ctx.send("🔓 Débanni.")
@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, n: int): await ctx.channel.purge(limit=n+1)
@bot.command()
@commands.has_permissions(manage_roles=True)
async def tempmute(ctx, m: discord.Member, s: int):
    for ch in ctx.guild.text_channels: await ch.set_permissions(m, send_messages=False)
    await ctx.send(f"🔇 {m.name} muet pour {s}s."); await asyncio.sleep(s)
    for ch in ctx.guild.text_channels: await ch.set_permissions(m, send_messages=None)
@bot.command()
@commands.has_permissions(manage_roles=True)
async def unmute(ctx, m: discord.Member):
    for ch in ctx.guild.text_channels: await ch.set_permissions(m, send_messages=None)
    await ctx.send(f"✅ {m.name} est unmute.")

# Grades
@bot.command()
@commands.has_permissions(administrator=True)
async def rank_t(ctx, m: discord.Member): await m.add_roles(ctx.guild.get_role(R_T), ctx.guild.get_role(ROLE_STAFF)); await ctx.send("✅")
@bot.command()
@commands.has_permissions(administrator=True)
async def rank_c(ctx, m: discord.Member): await m.add_roles(ctx.guild.get_role(R_C)); await ctx.send("✅")
@bot.command()
@commands.has_permissions(administrator=True)
async def rank_plus(ctx, m: discord.Member): await m.add_roles(ctx.guild.get_role(R_PLUS)); await ctx.send("✅")
@bot.command()
@commands.has_permissions(administrator=True)
async def rank_senior(ctx, m: discord.Member): await m.add_roles(ctx.guild.get_role(R_SENIOR)); await ctx.send("✅")
@bot.command()
@commands.has_permissions(administrator=True)
async def rank_admin(ctx, m: discord.Member): await m.add_roles(ctx.guild.get_role(R_ADMIN)); await ctx.send("✅")
@bot.command()
@commands.has_permissions(administrator=True)
async def derank(ctx, m: discord.Member):
    for r in [ROLE_STAFF, R_T, R_C, R_PLUS, R_SENIOR, R_ADMIN]: await m.remove_roles(ctx.guild.get_role(r))
    await ctx.send("❌")

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_ticket(ctx):
    e = discord.Embed(title="◈ RECRUTEMENT MHA RP ◈", description="Cliquez ci-dessous.", color=0x000000)
    e.set_thumbnail(url=bot.user.display_avatar.url)
    await ctx.send(embed=e, view=TicketPanel())

@bot.event
async def on_ready(): bot.add_view(TicketPanel()); print("✅ Bot prêt.")
bot.run(TOKEN)
        
