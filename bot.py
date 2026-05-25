import discord
from discord.ext import commands
import asyncio
import os

# INTENTS
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="+", intents=intents)

warnings = {}

log_channel_id = 1508482233219022992


# ----------------
# READY
# ----------------
@bot.event
async def on_ready():
    print("Bot staff connecté OK")


# ----------------
# LOG SYSTEM
# ----------------
async def send_log(guild, message):
    if log_channel_id:
        channel = guild.get_channel(log_channel_id)
        if channel:
            await channel.send(message)


# ----------------
# ROLES IDS
# ----------------
ROLE_T = 1504792771977023591
ROLE_C = 1504792768088903931
ROLE_PLUS = 1504792764448116776
ROLE_SENIOR = 1504792759679057951
ROLE_ADMIN = 1504792748098715660


# ----------------
# AUTO DERANK (STAFF CONSERVÉ)
# ----------------
async def remove_all_staff_roles(member):
    role_ids = [
        ROLE_T,
        ROLE_C,
        ROLE_PLUS,
        ROLE_SENIOR,
        ROLE_ADMIN
    ]

    for role_id in role_ids:
        role = member.guild.get_role(role_id)
        if role and role in member.roles:
            await member.remove_roles(role)


# ----------------
# PING
# ----------------
@bot.command()
async def ping(ctx):
    await ctx.send("Pong 🏓")


# ----------------
# DERANK MANUEL
# ----------------
@bot.command()
@commands.has_permissions(manage_roles=True)
async def derank(ctx, member: discord.Member):

    await remove_all_staff_roles(member)

    await ctx.send(f"⬇️ {member} derank effectué (STAFF conservé)")
    await send_log(ctx.guild, f"DERANK | {member} | {ctx.author}")


# ----------------
# RANK T
# ----------------
@bot.command(name="rank-t")
@commands.has_permissions(manage_roles=True)
async def rank_t(ctx, member: discord.Member):

    await remove_all_staff_roles(member)

    role = ctx.guild.get_role(ROLE_T)
    await member.add_roles(role)

    await ctx.send(f"📌 {member} → Modo Test")
    await send_log(ctx.guild, f"RANK-T | {member} | {ctx.author}")


# ----------------
# RANK C
# ----------------
@bot.command(name="rank-c")
@commands.has_permissions(manage_roles=True)
async def rank_c(ctx, member: discord.Member):

    await remove_all_staff_roles(member)

    role = ctx.guild.get_role(ROLE_C)
    await member.add_roles(role)

    await ctx.send(f"📌 {member} → Modo Confirmé")
    await send_log(ctx.guild, f"RANK-C | {member} | {ctx.author}")


# ----------------
# RANK +
# ----------------
@bot.command(name="rank-+")
@commands.has_permissions(manage_roles=True)
async def rank_plus(ctx, member: discord.Member):

    await remove_all_staff_roles(member)

    role = ctx.guild.get_role(ROLE_PLUS)
    await member.add_roles(role)

    await ctx.send(f"📌 {member} → Modo +")
    await send_log(ctx.guild, f"RANK-+ | {member} | {ctx.author}")


# ----------------
# RANK SENIOR
# ----------------
@bot.command(name="rank-s")
@commands.has_permissions(manage_roles=True)
async def rank_s(ctx, member: discord.Member):

    await remove_all_staff_roles(member)

    role = ctx.guild.get_role(ROLE_SENIOR)
    await member.add_roles(role)

    await ctx.send(f"📌 {member} → Modo Senior")
    await send_log(ctx.guild, f"RANK-S | {member} | {ctx.author}")


# ----------------
# RANK ADMIN
# ----------------
@bot.command(name="rank-admin")
@commands.has_permissions(manage_roles=True)
async def rank_admin(ctx, member: discord.Member):

    await remove_all_staff_roles(member)

    role = ctx.guild.get_role(ROLE_ADMIN)
    await member.add_roles(role)

    await ctx.send(f"👑 {member} → Admin")
    await send_log(ctx.guild, f"RANK-ADMIN | {member} | {ctx.author}")


# ----------------
# BOT RUN
# ----------------
token = os.getenv("DISCORD_TOKEN")
bot.run(token)
