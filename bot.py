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
TICKET_CAT_ID = 1504792910892109935
R_T, R_C, R_PLUS, R_SENIOR, R_ADMIN = 1504792771977023591, 1504792768088903931, 1504792764448116776, 1504792759679057951, 1504792748098715660

sanctions_db = {}

# --- SYSTÈME ESTHÉTIQUE & LOGS ---
async def send_mod_embed(title, m, staff, reason):
    e = discord.Embed(title=f"◈ {title} ◈", color=0x2f3136, timestamp=datetime.now())
    e.add_field(name="👤 Membre", value=m.mention, inline=True)
    e.add_field(name="👮 Staff", value=staff.mention, inline=True)
    e.add_field(name="📜 Raison", value=reason, inline=False)
    e.set_thumbnail(url=m.display_avatar.url)
    e.set_footer(text="Système de Modération", icon_url=bot.user.display_avatar.url)
    return e

async def log_and_mp(ctx, title, m, reason):
    if m.id not in sanctions_db: sanctions_db[m.id] = []
    sanctions_db[m.id].append(f"• **{title}** | Raison: {reason}")
    e = await send_mod_embed(title, m, ctx.author, reason)
    log_ch = bot.get_channel(LOG_CH_ID)
    if log_ch: await log_ch.send(embed=e)
    try: await m.send(embed=e)
    except: pass

# --- TICKETS ---
class TicketPanel(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="Candidater", style=discord.ButtonStyle.primary, emoji="📩", custom_id="btn_candid")
    async def btn(self, i, b):
        over = {i.guild.default_role: discord.PermissionOverwrite(view_channel=False), i.user: discord.PermissionOverwrite(view_channel=True, send_messages=True), i.guild.get_role(GERANT_STAFF_ID): discord.PermissionOverwrite(view_channel=True, send_messages=True)}
        ch = await i.guild.create_text_channel(name=f"ticket-{i.user.name}", category=i.guild.get_channel(TICKET_CAT_ID), overwrites=over)
        e = discord.Embed(title="◈ NOUVEAU DOSSIER ◈", description=f"Bonjour {i.user.mention}, le staff va vous aider.", color=0x5865f2)
        e.set_thumbnail(url=bot.user.display_avatar.url)
        await ch.send(content=f"{i.user.mention} | <@&{GERANT_STAFF_ID}>", embed=e)
        await i.response.send_message("✅ Dossier créé.", ephemeral=True)

# --- COMMANDES ---
@bot.command()
async def rank_t(ctx, m: discord.Member): await m.add_roles(ctx.guild.get_role(R_T), ctx.guild.get_role(ROLE_STAFF)); await log_and_mp(ctx, "RANK-T", m, "Promotion Test")
@bot.command()
async def rank_c(ctx, m: discord.Member): await m.add_roles(ctx.guild.get_role(R_C)); await log_and_mp(ctx, "RANK-C", m, "Promotion C")
@bot.command()
async def rank_plus(ctx, m: discord.Member): await m.add_roles(ctx.guild.get_role(R_PLUS)); await log_and_mp(ctx, "RANK-PLUS", m, "Promotion Plus")
@bot.command()
async def rank_senior(ctx, m: discord.Member): await m.add_roles(ctx.guild.get_role(R_SENIOR)); await log_and_mp(ctx, "RANK-SENIOR", m, "Promotion Senior")
@bot.command()
async def rank_admin(ctx, m: discord.Member): await m.add_roles(ctx.guild.get_role(R_ADMIN)); await log_and_mp(ctx, "RANK-ADMIN", m, "Promotion Admin")
@bot.command()
async def derank(ctx, m: discord.Member):
    for r in [ROLE_STAFF, R_T, R_C, R_PLUS, R_SENIOR, R_ADMIN]: 
        role = ctx.guild.get_role(r)
        if role: await m.remove_roles(role)
    await log_and_mp(ctx, "DERANK", m, "Dégradation totale")

@bot.command()
async def sanctions(ctx, m: discord.Member): await ctx.send(embed=discord.Embed(title=f"◈ Sanctions : {m.name} ◈", description="\n".join(sanctions_db.get(m.id, ["Aucune."])), color=0xed4245))
@bot.command()
async def warn(ctx, m: discord.Member, *, r="Aucune"): await log_and_mp(ctx, "WARN", m, r)
@bot.command()
async def kick(ctx, m: discord.Member, *, r="Aucune"): await m.kick(reason=r); await log_and_mp(ctx, "KICK", m, r)
@bot.command()
async def ban(ctx, m: discord.Member, *, r="Aucune"): await m.ban(reason=r); await log_and_mp(ctx, "BAN", m, r)
@bot.command()
async def unban(ctx, user_id: int): u = await bot.fetch_user(user_id); await ctx.guild.unban(u); await log_and_mp(ctx, "UNBAN", u, "Débanni")
@bot.command()
async def tempmute(ctx, m: discord.Member, s: int):
    await log_and_mp(ctx, "TEMPMUTE", m, f"{s}s"); [await ch.set_permissions(m, send_messages=False) for ch in ctx.guild.text_channels]
    await asyncio.sleep(s); [await ch.set_permissions(m, send_messages=None) for ch in ctx.guild.text_channels]
@bot.command()
async def unmute(ctx, m: discord.Member): [await ch.set_permissions(m, send_messages=None) for ch in ctx.guild.text_channels]; await log_and_mp(ctx, "UNMUTE", m, "Manual")

@bot.command()
async def setup_ticket(ctx): 
    e = discord.Embed(title="◈ RECRUTEMENT ◈", description="Cliquez ci-dessous pour ouvrir un ticket.", color=0x2f3136)
    e.set_thumbnail(url=bot.user.display_avatar.url)
    await ctx.send(embed=e, view=TicketPanel())
@bot.command()
async def add(ctx, m: discord.Member): await ctx.channel.set_permissions(m, view_channel=True, send_messages=True)
@bot.command()
async def remove(ctx, m: discord.Member): await ctx.channel.set_permissions(m, view_channel=False)
@bot.command()
async def rename(ctx, *, nom: str): await ctx.channel.edit(name=nom)
@bot.command()
async def close(ctx): await ctx.channel.delete()
@bot.command()
async def clear(ctx, n: int): await ctx.channel.purge(limit=n+1)
@bot.command()
async def clear_sanctions(ctx, n: int): await bot.get_channel(LOG_CH_ID).purge(limit=n)

@bot.event
async def on_ready(): bot.add_view(TicketPanel()); print(f"✅ Bot actif : {bot.user}")
bot.run(TOKEN)
    
