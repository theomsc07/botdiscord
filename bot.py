import discord
from discord.ext import commands
import asyncio
import os
from datetime import datetime

# --- CONFIGURATION INITIALE ---
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="+", intents=intents)

TOKEN = os.getenv("DISCORD_TOKEN")

# --- IDs CONFIG ---
LOG_CH_ID = 1508595464168013965
GERANT_STAFF_ID = 1504792751777255545
ROLE_STAFF = 1504810257715822722
TICKET_CAT_ID = 1504792910892109935
R_T, R_C, R_PLUS, R_SENIOR, R_ADMIN = 1504792771977023591, 1504792768088903931, 1504792764448116776, 1504792759679057951, 1504792748098715660

# --- LOGS ET MODÉRATION ---
async def send_log(action, ctx, target, reason="Aucune"):
    log_ch = bot.get_channel(LOG_CH_ID)
    if log_ch:
        e = discord.Embed(title=f"◈ LOG : {action} ◈", color=0x3498DB, timestamp=datetime.now())
        if target: e.set_thumbnail(url=target.display_avatar.url)
        e.add_field(name="Cible", value=target.mention if target else "N/A", inline=True)
        e.add_field(name="Staff", value=ctx.author.mention, inline=True)
        e.add_field(name="Détails", value=reason, inline=False)
        await log_ch.send(embed=e)

# --- COMMANDES MODÉRATION ---
@bot.command()
@commands.has_permissions(ban_members=True)
async def unban(ctx, user_id: int):
    user = await bot.fetch_user(user_id)
    await ctx.guild.unban(user)
    await ctx.send(f"✅ {user.name} a été débanni.")
    await send_log("UNBAN", ctx, user)

@bot.command()
@commands.has_permissions(manage_roles=True)
async def unmute(ctx, m: discord.Member):
    for ch in ctx.guild.text_channels:
        await ch.set_permissions(m, send_messages=None)
    await ctx.send(f"✅ {m.mention} est unmute.")
    await send_log("UNMUTE", ctx, m)

# --- COMMANDES GRADES (Ranks) ---
@bot.command()
@commands.has_permissions(administrator=True)
async def rank_t(ctx, m: discord.Member):
    r = ctx.guild.get_role(R_T)
    await m.add_roles(r, ctx.guild.get_role(ROLE_STAFF))
    await ctx.send(f"✅ {m.mention} est {r.mention} !")
    await send_log("RANK-T", ctx, m)

@bot.command()
@commands.has_permissions(administrator=True)
async def rank_c(ctx, m: discord.Member):
    r = ctx.guild.get_role(R_C)
    await m.add_roles(r)
    await ctx.send(f"✅ {m.mention} est {r.mention} !")
    await send_log("RANK-C", ctx, m)

@bot.command()
@commands.has_permissions(administrator=True)
async def rank_plus(ctx, m: discord.Member):
    r = ctx.guild.get_role(R_PLUS)
    await m.add_roles(r)
    await ctx.send(f"✅ {m.mention} est {r.mention} !")
    await send_log("RANK-PLUS", ctx, m)

@bot.command()
@commands.has_permissions(administrator=True)
async def rank_senior(ctx, m: discord.Member):
    r = ctx.guild.get_role(R_SENIOR)
    await m.add_roles(r)
    await ctx.send(f"✅ {m.mention} est {r.mention} !")
    await send_log("RANK-SENIOR", ctx, m)

@bot.command()
@commands.has_permissions(administrator=True)
async def rank_admin(ctx, m: discord.Member):
    r = ctx.guild.get_role(R_ADMIN)
    await m.add_roles(r)
    await ctx.send(f"✅ {m.mention} est {r.mention} !")
    await send_log("RANK-ADMIN", ctx, m)

@bot.command()
@commands.has_permissions(administrator=True)
async def derank(ctx, m: discord.Member):
    for r_id in [ROLE_STAFF, R_T, R_C, R_PLUS, R_SENIOR, R_ADMIN]:
        role = ctx.guild.get_role(r_id)
        if role: await m.remove_roles(role)
    await ctx.send(f"🐉 {m.mention} a été dégradé.")
    await send_log("DERANK", ctx, m)

# --- COMMANDES TICKET ---
@bot.command()
@commands.has_role(GERANT_STAFF_ID)
async def del(ctx):
    await ctx.channel.delete()

@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, n: int):
    await ctx.message.delete()
    await ctx.channel.purge(limit=n)

@bot.event
async def on_ready():
    print("✅ Bot opérationnel.")

bot.run(TOKEN)
    
