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

sanctions_db = {} # Format: {member_id: [liste_des_raisons]}

# ==============================================================================
# NOTIFICATIONS & LOGS
# ==============================================================================
async def send_sanction_dm(member, action, author, reason):
    try:
        e = discord.Embed(title=f"◈ Notification : {action} ◈", description=f"**Raison :** {reason}\n\n**Sanctionné par :** {author.mention}", color=0xFF0000)
        await member.send(embed=e)
    except: pass

async def log_action(ctx, action, target, reason):
    log_ch = bot.get_channel(LOG_CH_ID)
    if log_ch:
        e = discord.Embed(title=f"◈ LOG : {action} ◈", color=0x3498DB, timestamp=datetime.now())
        e.add_field(name="Cible", value=f"{target.mention}", inline=True)
        e.add_field(name="Modo", value=ctx.author.mention, inline=True)
        e.add_field(name="Raison", value=reason, inline=False)
        await log_ch.send(embed=e)

# ==============================================================================
# TICKETS
# ==============================================================================
class VerdictModal(discord.ui.Modal, title="Verdict"):
    reason = discord.ui.TextInput(label="Message au candidat", style=discord.TextStyle.paragraph, required=True)
    def __init__(self, member, decision, author): super().__init__(); self.member = member; self.decision = decision; self.author = author
    async def on_submit(self, i: discord.Interaction):
        color = 0x2ECC71 if self.decision == "ACCEPTÉ" else 0xE74C3C
        e = discord.Embed(title=f"◈ RÉSULTAT : {self.decision} ◈", description=f"**Verdict :** {self.reason.value}\n\n**Traité par :** {i.user.mention}", color=color)
        try: await self.member.send(embed=e)
        except: pass
        await i.response.send_message("✅ Verdict envoyé.", ephemeral=True)
        await asyncio.sleep(2); await i.channel.delete()

class TicketPanel(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="Devenir Modo Test", style=discord.ButtonStyle.secondary, emoji="🛡️")
    async def open_ticket(self, i: discord.Interaction, b):
        over = {i.guild.default_role: discord.PermissionOverwrite(view_channel=False), i.user: discord.PermissionOverwrite(view_channel=True, send_messages=True), i.guild.get_role(ROLE_STAFF): discord.PermissionOverwrite(view_channel=True, send_messages=True)}
        ch = await i.guild.create_text_channel(name=f"recrut-{i.user.name}", category=i.guild.get_channel(TICKET_CAT_ID), overwrites=over)
        await ch.send(f"{i.user.mention} | <@&{GERANT_STAFF_ID}>", embed=discord.Embed(title="CANDIDATURE", description="Présentez vos motivations.", color=0x2C2F33), view=VerdictView(i.user))
        await i.response.send_message(f"✅ Ticket ouvert : {ch.mention}", ephemeral=True)

class VerdictView(discord.ui.View):
    def __init__(self, member): super().__init__(timeout=None); self.member = member
    @discord.ui.button(label="Accepter", style=discord.ButtonStyle.success)
    async def acc(self, i, b): await i.response.send_modal(VerdictModal(self.member, "ACCEPTÉ", i.user))
    @discord.ui.button(label="Refuser", style=discord.ButtonStyle.danger)
    async def rej(self, i, b): await i.response.send_modal(VerdictModal(self.member, "REFUSÉ", i.user))

# ==============================================================================
# COMMANDES
# ==============================================================================
@bot.command()
@commands.has_role(ROLE_STAFF)
async def helpstaff(ctx):
    e = discord.Embed(title="🔮 HELP STAFF", color=0x2C2F33)
    e.add_field(name="🛡️ Modération", value="`+warn` `+kick` `+ban` `+unban` `+tempmute` `+unmute` `+clear`", inline=False)
    e.add_field(name="⚠️ Sanctions", value="`+sanctions @user` `+clear-sanctions @user`", inline=False)
    e.add_field(name="👑 Grades", value="`+rank-t` `+derank`", inline=False)
    e.add_field(name="🎫 Tickets", value="`+setup_ticket`", inline=False)
    await ctx.send(embed=e)

# Sanctions & Modération
@bot.command()
@commands.has_role(ROLE_STAFF)
async def sanctions(ctx, m: discord.Member):
    s = sanctions_db.get(m.id, [])
    e = discord.Embed(title=f"Sanctions de {m.name}", description="\n".join(s) if s else "Aucune sanction.", color=0xFFFF00)
    await ctx.send(embed=e)

@bot.command()
@commands.has_role(ROLE_STAFF)
async def clear_sanctions(ctx, m: discord.Member):
    sanctions_db[m.id] = []
    await ctx.send(f"✅ Sanctions de {m.name} effacées.")

@bot.command()
@commands.has_permissions(kick_members=True)
async def warn(ctx, m: discord.Member, *, r="Aucune"): sanctions_db.setdefault(m.id, []).append(r); await send_sanction_dm(m, "WARN", ctx.author, r); await log_action(ctx, "WARN", m, r); await ctx.send("✅")
@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, m: discord.Member, *, r="Aucune"): await m.kick(reason=r); await log_action(ctx, "KICK", m, r)
@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, m: discord.Member, *, r="Aucune"): await m.ban(reason=r); await log_action(ctx, "BAN", m, r)
@bot.command()
@commands.has_permissions(ban_members=True)
async def unban(ctx, uid: int): u = await bot.fetch_user(uid); await ctx.guild.unban(u); await log_action(ctx, "UNBAN", u, "Débanni"); await ctx.send("🔓")
@bot.command()
@commands.has_permissions(administrator=True)
async def rank_t(ctx, m: discord.Member): await m.add_roles(ctx.guild.get_role(R_T), ctx.guild.get_role(ROLE_STAFF)); await ctx.send("✅")
@bot.command()
@commands.has_permissions(administrator=True)
async def derank(ctx, m: discord.Member): await m.remove_roles(ctx.guild.get_role(ROLE_STAFF)); await ctx.send("❌")
@bot.command()
@commands.has_permissions(administrator=True)
async def setup_ticket(ctx): await ctx.send(embed=discord.Embed(title="RECRUTEMENT", color=0), view=TicketPanel())

@bot.event
async def on_ready(): bot.add_view(TicketPanel()); print("✅ Bot en ligne.")
bot.run(TOKEN)
                                  
