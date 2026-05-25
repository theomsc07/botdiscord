import discord
from discord.ext import commands
import os

# ----------------
# INTENTS
# ----------------
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="+", intents=intents)

# ----------------
# CONFIG
# ----------------
LOG_CHANNEL_ID = 1508482233219022992

ROLE_T = 1504792771977023591
ROLE_C = 1504792768088903931
ROLE_PLUS = 1504792764448116776
ROLE_SENIOR = 1504792759679057951
ROLE_ADMIN = 1504792748098715660


# ----------------
# READY
# ----------------
@bot.event
async def on_ready():
    print(f"Bot connecté : {bot.user}")


# ----------------
# LOG SYSTEM SAFE
# ----------------
async def send_log(guild, message):
    if not guild:
        return

    channel = guild.get_channel(LOG_CHANNEL_ID)
    if channel:
        await channel.send(message)


# ----------------
# REMOVE STAFF ROLES SAFE
# ----------------
async def remove_all_staff_roles(member):
    role_ids = [ROLE_T, ROLE_C, ROLE_PLUS, ROLE_SENIOR, ROLE_ADMIN]

    for role_id in role_ids:
        role = member.guild.get_role(role_id)
        if role and role in member.roles:
            try:
                await member.remove_roles(role)
            except:
                pass


# ----------------
# PING
# ----------------
@bot.command()
async def ping(ctx):
    await ctx.send("Pong 🏓")


# ----------------
# DERANK
# ----------------
@bot.command()
@commands.has_permissions(manage_roles=True)
async def derank(ctx, member: discord.Member):

    await remove_all_staff_roles(member)

    await ctx.send(f"⬇️ {member.mention} derank effectué")
    await send_log(ctx.guild, f"DERANK | {member} | {ctx.author}")


# ----------------
# RANK T
# ----------------
@bot.command(name="rank-t")
@commands.has_permissions(manage_roles=True)
async def rank_t(ctx, member: discord.Member):

    await remove_all_staff_roles(member)

    role = ctx.guild.get_role(ROLE_T)
    if not role:
        return await ctx.send("❌ Rôle introuvable (Modo Test)")

    await member.add_roles(role)

    await ctx.send(f"📌 {member.mention} → Modo Test")
    await send_log(ctx.guild, f"RANK-T | {member} | {ctx.author}")


# ----------------
# RANK C
# ----------------
@bot.command(name="rank-c")
@commands.has_permissions(manage_roles=True)
async def rank_c(ctx, member: discord.Member):

    await remove_all_staff_roles(member)

    role = ctx.guild.get_role(ROLE_C)
    if not role:
        return await ctx.send("❌ Rôle introuvable (Modo Confirmé)")

    await member.add_roles(role)

    await ctx.send(f"📌 {member.mention} → Modo Confirmé")
    await send_log(ctx.guild, f"RANK-C | {member} | {ctx.author}")


# ----------------
# RANK +
# ----------------
@bot.command(name="rank-+")
@commands.has_permissions(manage_roles=True)
async def rank_plus(ctx, member: discord.Member):

    await remove_all_staff_roles(member)

    role = ctx.guild.get_role(ROLE_PLUS)
    if not role:
        return await ctx.send("❌ Rôle introuvable (Modo +)")

    await member.add_roles(role)

    await ctx.send(f"📌 {member.mention} → Modo +")
    await send_log(ctx.guild, f"RANK-+ | {member} | {ctx.author}")


# ----------------
# RANK SENIOR
# ----------------
@bot.command(name="rank-s")
@commands.has_permissions(manage_roles=True)
async def rank_s(ctx, member: discord.Member):

    await remove_all_staff_roles(member)

    role = ctx.guild.get_role(ROLE_SENIOR)
    if not role:
        return await ctx.send("❌ Rôle introuvable (Senior)")

    await member.add_roles(role)

    await ctx.send(f"📌 {member.mention} → Modo Senior")
    await send_log(ctx.guild, f"RANK-S | {member} | {ctx.author}")


# ----------------
# RANK ADMIN
# ----------------
@bot.command(name="rank-admin")
@commands.has_permissions(manage_roles=True)
async def rank_admin(ctx, member: discord.Member):

    await remove_all_staff_roles(member)

    role = ctx.guild.get_role(ROLE_ADMIN)
    if not role:
        return await ctx.send("❌ Rôle introuvable (Admin)")

    await member.add_roles(role)

    await ctx.send(f"👑 {member.mention} → Admin")
    await send_log(ctx.guild, f"RANK-ADMIN | {member} | {ctx.author}")


# ----------------
# BOT RUN SAFE (IMPORTANT RAILWAY)
# ----------------
token = os.getenv("DISCORD_TOKEN")

if not token:
    print("❌ TOKEN manquant (DISCORD_TOKEN)")
else:
    bot.run(token)
