import discord
from discord.ext import commands
import asyncio
from datetime import datetime
import os

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="+", intents=intents)

TOKEN = os.getenv("DISCORD_TOKEN")
LOG_CH_ID = 1508595464168013965
GERANT_STAFF_ID = 1504792751777255545
ROLE_STAFF = 1504810257715822722
ROLE_MUTED = 1509141375810011156
TICKET_CAT_ID = 1504792910892109935
R_T, R_C, R_PLUS, R_SENIOR, R_ADMIN = 1504792771977023591, 1504792768088903931, 1504792764448116776, 1504792759679057951, 1504792748098715660

sanctions_db = {}

async def log_and_mp(ctx, title, m, reason):
    if m.id not in sanctions_db: sanctions_db[m.id] = []
    sanctions_db[m.id].append(f"• **{title}** | Raison: {reason}")
    e = discord.Embed(title=f"◈ {title} ◈", color=0x2f3136, timestamp=datetime.now())
    e.add_field(name="👤 Membre", value=m.mention, inline=True)
    e.add_field(name="👮 Staff", value=ctx.author.mention, inline=True)
    e.add_field(name="📜 Raison", value=reason, inline=False)
    e.set_thumbnail(url=m.display_avatar.url)
    e.set_footer(text="Système de Modération", icon_url=bot.user.display_avatar.url)
    log_ch = bot.get_channel(LOG_CH_ID)
    if log_ch: await log_ch.send(embed=e)
    try: await m.send(embed=e)
    except: pass

class TicketPanel(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="Candidater", style=discord.ButtonStyle.primary, emoji="📩", custom_id="btn_candid")
    async def btn(self, i, b):
        over = {i.guild.default_role: discord.PermissionOverwrite(view_channel=False), i.user: discord.PermissionOverwrite(view_channel=True, send_messages=True), i.guild.get_role(GERANT_STAFF_ID): discord.PermissionOverwrite(view_channel=True, send_messages=True)}
        ch = await i.guild.create_text_channel(name=f"ticket-{i.user.name}", category=i.guild.get_channel(TICKET_CAT_ID), overwrites=over)
        e = discord.Embed(title="◈ DOSSIER ◈", description=f"Bonjour {i.user.mention}, le staff arrive.", color=0x5865f2); e.set_thumbnail(url=bot.user.display_avatar.url)
        await ch.send(content=f"{i.user.mention} | <@&{GERANT_STAFF_ID}>", embed=e)
        await i.response.send_message("✅ Dossier créé.", ephemeral=True)

@bot.command()
async def rank_t(ctx, m: discord.Member): await m.add_roles(ctx.guild.get_role(R_T), ctx.guild.get_role(ROLE_STAFF)); await log_and_mp(ctx, "RANK-T", m, "Promotion"); await ctx.send(f"✅ {m.mention} est Staff Test.")
@bot.command()
async def rank_c(ctx, m: discord.Member): await m.add_roles(ctx.guild.get_role(R_C)); await log_and_mp(ctx, "RANK-C", m, "Promotion"); await ctx.send(f"✅ {m.mention} est Confirmé.")
@bot.command()
async def rank_plus(ctx, m: discord.Member): await m.add_roles(ctx.guild.get_role(R_PLUS)); await log_and_mp(ctx, "RANK-PLUS", m, "Promotion"); await ctx.send(f"✅ {m.mention} est Staff+.")
@bot.command()
async def rank_senior(ctx, m: discord.Member): await m.add_roles(ctx.guild.get_role(R_SENIOR)); await log_and_mp(ctx, "RANK-SENIOR", m, "Promotion"); await ctx.send(f"✅ {m.mention} est Senior.")
@bot.command()
async def rank_admin(ctx, m: discord.Member): await m.add_roles(ctx.guild.get_role(R_ADMIN)); await log_and_mp(ctx, "RANK-ADMIN", m, "Promotion"); await ctx.send(f"✅ {m.mention} est Admin.")
@bot.command()
async def derank(ctx, m: discord.Member):
    for r in [ROLE_STAFF, R_T, R_C, R_PLUS, R_SENIOR, R_ADMIN]: 
        role = ctx.guild.get_role(r)
        if role: await m.remove_roles(role)
    await log_and_mp(ctx, "DERANK", m, "Dégradation"); await ctx.send(f"🐉 {m.mention} a été dégradé.")

@bot.command()
async def warn(ctx, m: discord.Member, *, r="Aucune"): await log_and_mp(ctx, "WARN", m, r); await ctx.send(f"⚠️ {m.mention} a été averti.")
@bot.command()
async def kick(ctx, m: discord.Member, *, r="Aucune"): await m.kick(reason=r); await log_and_mp(ctx, "KICK", m, r); await ctx.send(f"👢 {m.mention} expulsé.")
@bot.command()
async def ban(ctx, m: discord.Member, *, r="Aucune"): await m.ban(reason=r); await log_and_mp(ctx, "BAN", m, r); await ctx.send(f"🔨 {m.mention} banni.")
@bot.command()
async def unban(ctx, user_id: int):
    try:
        user = await bot.fetch_user(user_id)
        await ctx.guild.unban(user)
        await log_and_mp(ctx, "UNBAN", user, "Débannissement")
        await ctx.send(f"✅ {user.mention} a été débanni.")
    except: await ctx.send("❌ Utilisateur introuvable ou non banni.")

@bot.command()
async def tempmute(ctx, m: discord.Member, s: int):
    role = ctx.guild.get_role(ROLE_MUTED)
    if role: await m.add_roles(role); await log_and_mp(ctx, "TEMPMUTE", m, f"{s}s"); await ctx.send(f"🔇 {m.mention} muté pour {s}s.")
    await asyncio.sleep(s); await m.remove_roles(role)
@bot.command()
async def unmute(ctx, m: discord.Member): 
    await m.remove_roles(ctx.guild.get_role(ROLE_MUTED)); await log_and_mp(ctx, "UNMUTE", m, "Manuel"); await ctx.send(f"🔊 {m.mention} unmute.")

@bot.command()
async def setup_ticket(ctx): e = discord.Embed(title="◈ RECRUTEMENT ◈", description="Cliquez pour candidater.", color=0x2f3136); e.set_thumbnail(url=bot.user.display_avatar.url); await ctx.send(embed=e, view=TicketPanel())
@bot.command()
async def add(ctx, m: discord.Member): await ctx.channel.set_permissions(m, view_channel=True, send_messages=True); await ctx.send(f"✅ {m.mention} ajouté.")
@bot.command()
async def remove(ctx, m: discord.Member): await ctx.channel.set_permissions(m, view_channel=False); await ctx.send(f"✅ {m.mention} retiré.")
@bot.command()
async def rename(ctx, *, nom: str): await ctx.channel.edit(name=nom); await ctx.send(f"✅ Renommé en : {nom}")
@bot.command()
async def close(ctx): await ctx.channel.delete()

@bot.command()
async def clear(ctx, n: int): await ctx.channel.purge(limit=n+1); await ctx.send(f"🧹 {n} msgs effacés.")
@bot.command()
async def clear_sanctions(ctx, n: int): 
    log_ch = bot.get_channel(LOG_CH_ID)
    if log_ch: await log_ch.purge(limit=n); await ctx.send(f"🧹 {n} logs supprimés.")
@bot.command()
async def sanctions(ctx, m: discord.Member): await ctx.send(embed=discord.Embed(title=f"◈ Sanctions : {m.name} ◈", description="\n".join(sanctions_db.get(m.id, ["Aucune."])), color=0xed4245))

@bot.event
async def on_ready(): bot.add_view(TicketPanel()); print(f"✅ Bot prêt : {bot.user}")
bot.run(TOKEN)
