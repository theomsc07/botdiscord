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

# IDs (À REMPLACER)
LOG_CH_ID = 1508595464168013965
GERANT_STAFF_ID = 968588191055642624
ROLE_STAFF = 1504810257715822722
TICKET_CAT_ID = 1504792910892109935
R_T, R_C, R_PLUS, R_SENIOR, R_ADMIN = 1504792771977023591, 1504792768088903931, 1504792764448116776, 1504792759679057951, 1504792748098715660

sanctions_db = {}

# ==============================================================================
# FONCTIONS UTILITAIRES
# ==============================================================================
async def log_action(ctx, action, target, reason="Aucune"):
    log_ch = bot.get_channel(LOG_CH_ID)
    if log_ch:
        e = discord.Embed(title=f"◈ LOG : {action} ◈", color=discord.Color.blue(), timestamp=datetime.now())
        e.add_field(name="Cible", value=f"{target.mention}", inline=False)
        e.add_field(name="Modérateur", value=ctx.author.mention, inline=False)
        e.add_field(name="Raison", value=reason, inline=False)
        await log_ch.send(embed=e)

async def send_dm(member, action, author, reason):
    try:
        e = discord.Embed(title=f"Notification : {action}", description=f"Raison : {reason}\n\nSanctionné par : {author.mention}\nÀ : {datetime.now().strftime('%H:%M:%S')}", color=discord.Color.red())
        e.set_thumbnail(url=bot.user.display_avatar.url)
        await member.send(embed=e)
    except: pass

async def clean_grades(member):
    for r_id in [R_T, R_C, R_PLUS, R_SENIOR, R_ADMIN]:
        role = member.guild.get_role(r_id)
        if role and role in member.roles: await member.remove_roles(role)

# ==============================================================================
# TICKETS
# ==============================================================================
class VerdictModal(discord.ui.Modal, title="Verdict"):
    reason = discord.ui.TextInput(label="Message personnalisé", style=discord.TextStyle.paragraph, required=True)
    def __init__(self, member, decision, author): super().__init__(); self.member = member; self.decision = decision; self.author = author
    async def on_submit(self, i: discord.Interaction):
        await send_dm(self.member, f"CANDIDATURE {self.decision}", self.author, self.reason.value)
        await i.response.send_message("✅ Verdict envoyé.", ephemeral=True)
        await asyncio.sleep(2); await i.channel.delete()

class VerdictView(discord.ui.View):
    def __init__(self, member, author): super().__init__(timeout=None); self.member = member; self.author = author
    @discord.ui.button(label="✅ Accepter", style=discord.ButtonStyle.green)
    async def acc(self, i: discord.Interaction, b): await i.response.send_modal(VerdictModal(self.member, "ACCEPTÉ", i.user))
    @discord.ui.button(label="❌ Refuser", style=discord.ButtonStyle.danger)
    async def rej(self, i: discord.Interaction, b): await i.response.send_modal(VerdictModal(self.member, "REFUSÉ", i.user))

class TicketPanel(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="📝 Ouvrir candidature MHA RP", style=discord.ButtonStyle.blurple, custom_id="open_ticket")
    async def open_ticket(self, i: discord.Interaction, b):
        over = {i.guild.default_role: discord.PermissionOverwrite(view_channel=False), i.user: discord.PermissionOverwrite(view_channel=True, send_messages=True), i.guild.get_member(GERANT_STAFF_ID): discord.PermissionOverwrite(view_channel=True, send_messages=True)}
        ch = await i.guild.create_text_channel(name=f"recrut-{i.user.name}", category=i.guild.get_channel(TICKET_CAT_ID), overwrites=over)
        await ch.send(f"{i.user.mention} | <@{GERANT_STAFF_ID}>", view=VerdictView(i.user, i.user))
        await i.response.send_message(f"✅ Ticket ouvert.", ephemeral=True)

# ==============================================================================
# COMMANDES
# ==============================================================================
@bot.command()
@commands.has_role(ROLE_STAFF)
async def helpstaff(ctx):
    e = discord.Embed(title="🔮 MENU D'AIDE STAFF - MHA RP", color=discord.Color.dark_purple())
    e.add_field(name="🛡️ Modération", value="`+warn` `+kick` `+ban` `+unban` `+tempmute` `+unmute` `+clear`", inline=False)
    e.add_field(name="⚠️ Sanctions", value="`+sanctions` `+clear-sanctions`", inline=False)
    e.add_field(name="👑 Grades", value="`+rank-t` (T+Staff) | `+rank-c/plus/senior/admin` | `+derank`", inline=False)
    e.add_field(name="🎫 Tickets", value="`+setup_ticket` `+close`", inline=False)
    await ctx.send(embed=e)

@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, n: int): await ctx.channel.purge(limit=n+1); await log_action(ctx, "CLEAR", ctx.channel, f"{n} msg")
@bot.command()
@commands.has_permissions(kick_members=True)
async def warn(ctx, m: discord.Member, *, r="Aucune"): sanctions_db.setdefault(m.id, []).append(r); await send_dm(m, "AVERTISSEMENT", ctx.author, r); await log_action(ctx, "WARN", m, r); await ctx.send("✅ Averti.")
@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, m: discord.Member, *, r="Aucune"): await m.kick(reason=r); await log_action(ctx, "KICK", m, r); await ctx.send("☄️ Expulsé.")
@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, m: discord.Member, *, r="Aucune"): await m.ban(reason=r); await log_action(ctx, "BAN", m, r); await ctx.send("💥 Banni.")
@bot.command()
@commands.has_permissions(ban_members=True)
async def unban(ctx, uid: int): u = await bot.fetch_user(uid); await ctx.guild.unban(u); await log_action(ctx, "UNBAN", u, "Débannissement"); await ctx.send(f"🔓 {u.name} débanni.")
@bot.command()
@commands.has_permissions(manage_roles=True)
async def tempmute(ctx, m: discord.Member, s: int):
    for ch in ctx.guild.text_channels: await ch.set_permissions(m, send_messages=False)
    await send_dm(m, "MUTE TEMPORAIRE", ctx.author, f"{s}s"); await log_action(ctx, "TEMPMUTE", m, f"{s}s"); await asyncio.sleep(s)
    for ch in ctx.guild.text_channels: await ch.set_permissions(m, send_messages=None)
@bot.command()
@commands.has_permissions(manage_roles=True)
async def unmute(ctx, m: discord.Member):
    for ch in ctx.guild.text_channels: await ch.set_permissions(m, send_messages=None)
    await log_action(ctx, "UNMUTE", m, "Parole rendue"); await ctx.send("✅ Parole rendue.")

@bot.command()
@commands.has_permissions(administrator=True)
async def rank_t(ctx, m: discord.Member): await clean_grades(m); await m.add_roles(ctx.guild.get_role(R_T), ctx.guild.get_role(ROLE_STAFF)); await ctx.send("✅ T et Staff.")
@bot.command()
@commands.has_permissions(administrator=True)
async def derank(ctx, m: discord.Member): await clean_grades(m); s = ctx.guild.get_role(ROLE_STAFF); await m.remove_roles(s); await ctx.send("❌ Totalement dégradé.")
@bot.command()
@commands.has_permissions(administrator=True)
async def setup_ticket(ctx): await ctx.send(embed=discord.Embed(title="RECRUTEMENT", description="Ouvrir ticket.", color=discord.Color.dark_gray()), view=TicketPanel())

@bot.event
async def on_ready(): bot.add_view(TicketPanel()); print("✅ Bot opérationnel.")
bot.run(TOKEN)
                                                                                                                                       
