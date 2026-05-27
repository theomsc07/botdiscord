import discord
from discord.ext import commands
import asyncio
import os
from datetime import datetime

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

# --- SYSTÈME LOGS & MP ---
async def log_and_mp(ctx, title, m, reason):
    if m.id not in sanctions_db: sanctions_db[m.id] = []
    sanctions_db[m.id].append(f"• **{title}** | Raison: {reason}")
    e = discord.Embed(title=f"◈ {title} ◈", color=0x2f3136, timestamp=datetime.now())
    e.add_field(name="Membre", value=m.mention, inline=True)
    e.add_field(name="Staff", value=ctx.author.mention, inline=True)
    e.add_field(name="Raison", value=reason, inline=False)
    e.set_thumbnail(url=m.display_avatar.url)
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
        await ch.send(f"{i.user.mention} | <@&{GERANT_STAFF_ID}>", embed=discord.Embed(title="◈ DOSSIER ◈", description="Exposez votre demande.", color=0x5865f2))
        await i.response.send_message("✅", ephemeral=True)

# --- COMMANDES ---
@bot.command()
async def rank_t(ctx, m: discord.Member): await m.add_roles(ctx.guild.get_role(R_T), ctx.guild.get_role(ROLE_STAFF)); await log_and_mp(ctx, "RANK-T", m, "Promotion")
@bot.command()
async def rank_c(ctx, m: discord.Member): await m.add_roles(ctx.guild.get_role(R_C)); await log_and_mp(ctx, "RANK-C", m, "Promotion")
@bot.command()
async def rank_plus(ctx, m: discord.Member): await m.add_roles(ctx.guild.get_role(R_PLUS)); await log_and_mp(ctx, "RANK-PLUS", m, "Promotion")
@bot.command()
async def rank_senior(ctx, m: discord.Member): await m.add_roles(ctx.guild.get_role(R_SENIOR)); await log_and_mp(ctx, "RANK-SENIOR", m, "Promotion")
@bot.command()
async def rank_admin(ctx, m: discord.Member): await m.add_roles(ctx.guild.get_role(R_ADMIN)); await log_and_mp(ctx, "RANK-ADMIN", m, "Promotion")
@bot.command()
async def derank(ctx, m: discord.Member):
    for r in [ROLE_STAFF, R_T, R_C, R_PLUS, R_SENIOR, R_ADMIN]: 
        role = ctx.guild.get_role(r)
        if role: await m.remove_roles(role)
    await log_and_mp(ctx, "DERANK", m, "Dégradation")

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
async def clear(ctx, n: int): await ctx.channel.purge(limit=n+1)
@bot.command()
async def clear_sanctions(ctx, n: int): await bot.get_channel(LOG_CH_ID).purge(limit=n)

@bot.command()
async def setup_ticket(ctx): await ctx.send("◈ RECRUTEMENT ◈", view=TicketPanel())
@bot.command()
async def add(ctx, m: discord.Member): await ctx.channel.set_permissions(m, view_channel=True, send_messages=True)
@bot.command()
async def remove(ctx, m: discord.Member): await ctx.channel.set_permissions(m, view_channel=False)
@bot.command()
async def rename(ctx, *, nom: str): await ctx.channel.edit(name=nom)
@bot.command()
async def close(ctx): await ctx.channel.delete()

@bot.event
async def on_ready(): bot.add_view(TicketPanel()); print("✅ Bot actif.")
bot.run(TOKEN)
            
