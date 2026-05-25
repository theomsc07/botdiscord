import discord
from discord.ext import commands
import asyncio
import os
from collections import defaultdict

# =========================
# INTENTS
# =========================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="+", intents=intents)

# =========================
# SANCTIONS
# =========================
sanctions = defaultdict(list)

# =========================
# IDS
# =========================

# LOGS
LOG_CHANNEL_ID = 1508595464168013965

# ROLE STAFF GENERAL
ROLE_STAFF = 1504810257715822722

# ROLES STAFF
ROLE_T = 1504792771977023591
ROLE_C = 1504792768088903931
ROLE_PLUS = 1504792764448116776
ROLE_SENIOR = 1504792759679057951
ROLE_ADMIN = 1504792748098715660

# =========================
# READY
# =========================
@bot.event
async def on_ready():
    print(f"{bot.user} connecté ✅")

# =========================
# LOGS
# =========================
async def send_log(guild, title, description):

    channel = guild.get_channel(LOG_CHANNEL_ID)

    if not channel:
        return

    embed = discord.Embed(
        title=title,
        description=description,
        color=discord.Color.red()
    )

    await channel.send(embed=embed)

# =========================
# REMOVE STAFF ROLES
# =========================
async def remove_all_staff_roles(member):

    roles = [
        ROLE_T,
        ROLE_C,
        ROLE_PLUS,
        ROLE_SENIOR,
        ROLE_ADMIN
    ]

    for role_id in roles:

        role = member.guild.get_role(role_id)

        if role and role in member.roles:
            await member.remove_roles(role)

# =========================
# PING
# =========================
@bot.command()
async def ping(ctx):

    await ctx.send(
        f"🏓 {ctx.author.mention} Pong !"
    )

# =========================
# WARN
# =========================
@bot.command()
@commands.has_permissions(manage_messages=True)
async def warn(ctx, member: discord.Member, *, reason="Aucune raison"):

    sanctions[member.id].append(reason)

    await ctx.send(
        f"⚠️ {member.mention} a été warn\n📌 Raison : {reason}"
    )

    await send_log(
        ctx.guild,
        "⚠️ WARN",
        f"""
👮 Staff : {ctx.author.mention}
👤 Membre : {member.mention}
📌 Raison : {reason}
"""
    )

# =========================
# SANCTIONS
# =========================
@bot.command(name="sanctions")
@commands.has_permissions(manage_messages=True)
async def sanctions_cmd(ctx, member: discord.Member):

    user_sanctions = sanctions.get(member.id)

    if not user_sanctions:

        return await ctx.send(
            f"✅ {member.mention} n'a aucune sanction"
        )

    msg = "\n".join(
        [f"{i+1}. {s}" for i, s in enumerate(user_sanctions)]
    )

    await ctx.send(
        f"📋 Sanctions de {member.mention} :\n{msg}"
    )

# =========================
# CLEAR SANCTIONS
# =========================
@bot.command()
@commands.has_permissions(administrator=True)
async def clear_sanctions(ctx, member: discord.Member):

    sanctions[member.id] = []

    await ctx.send(
        f"🧹 Les sanctions de {member.mention} ont été supprimées"
    )

    await send_log(
        ctx.guild,
        "🧹 CLEAR SANCTIONS",
        f"""
👮 Staff : {ctx.author.mention}
👤 Membre : {member.mention}
📌 Toutes les sanctions ont été supprimées
"""
    )

# =========================
# CLEAR
# =========================
@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int):

    await ctx.channel.purge(limit=amount + 1)

    msg = await ctx.send(
        f"🧹 {ctx.author.mention} a supprimé {amount} messages"
    )

    await send_log(
        ctx.guild,
        "🧹 CLEAR",
        f"""
👮 Staff : {ctx.author.mention}
📌 Messages supprimés : {amount}
📍 Salon : {ctx.channel.mention}
"""
    )

    await asyncio.sleep(3)
    await msg.delete()

# =========================
# MUTE
# =========================
@bot.command()
@commands.has_permissions(manage_roles=True)
async def mute(ctx, member: discord.Member):

    role = discord.utils.get(ctx.guild.roles, name="Muted")

    if not role:
        role = await ctx.guild.create_role(name="Muted")

    await member.add_roles(role)

    await ctx.send(
        f"🔇 {member.mention} a été mute"
    )

    await send_log(
        ctx.guild,
        "🔇 MUTE",
        f"""
👮 Staff : {ctx.author.mention}
👤 Membre : {member.mention}
"""
    )

# =========================
# UNMUTE
# =========================
@bot.command()
@commands.has_permissions(manage_roles=True)
async def unmute(ctx, member: discord.Member):

    role = discord.utils.get(ctx.guild.roles, name="Muted")

    if role in member.roles:
        await member.remove_roles(role)

    await ctx.send(
        f"🔊 {member.mention} a été unmute"
    )

    await send_log(
        ctx.guild,
        "🔊 UNMUTE",
        f"""
👮 Staff : {ctx.author.mention}
👤 Membre : {member.mention}
"""
    )

# =========================
# TEMPMUTE
# =========================
@bot.command()
@commands.has_permissions(manage_roles=True)
async def tempmute(ctx, member: discord.Member, time: int):

    role = discord.utils.get(ctx.guild.roles, name="Muted")

    if not role:
        role = await ctx.guild.create_role(name="Muted")

    await member.add_roles(role)

    await ctx.send(
        f"⏳ {member.mention} mute pendant {time} secondes"
    )

    await send_log(
        ctx.guild,
        "⏳ TEMPMUTE",
        f"""
👮 Staff : {ctx.author.mention}
👤 Membre : {member.mention}
⏱️ Temps : {time} secondes
"""
    )

    await asyncio.sleep(time)

    if role in member.roles:
        await member.remove_roles(role)

    await ctx.send(
        f"🔊 {member.mention} n'est plus mute"
    )

# =========================
# DERANK
# =========================
@bot.command()
@commands.has_permissions(administrator=True)
async def derank(ctx, member: discord.Member):

    await remove_all_staff_roles(member)

    staff_role = ctx.guild.get_role(ROLE_STAFF)

    if staff_role and staff_role in member.roles:
        await member.remove_roles(staff_role)

    await ctx.send(
        f"⬇️ {member.mention} a été derank"
    )

    await send_log(
        ctx.guild,
        "⬇️ DERANK",
        f"""
👮 Staff : {ctx.author.mention}
👤 Membre : {member.mention}
"""
    )

# =========================
# RANK FUNCTION
# =========================
async def rank_member(ctx, member, role_id, role_name):

    await remove_all_staff_roles(member)

    role = ctx.guild.get_role(role_id)

    if role:
        await member.add_roles(role)

    # ROLE STAFF
    staff_role = ctx.guild.get_role(ROLE_STAFF)

    if staff_role:
        await member.add_roles(staff_role)

    await ctx.send(
        f"📌 {member.mention} est maintenant {role_name}"
    )

    await send_log(
        ctx.guild,
        "📌 RANK",
        f"""
👮 Staff : {ctx.author.mention}
👤 Membre : {member.mention}
📌 Nouveau grade : {role_name}
"""
    )

# =========================
# RANKS
# =========================
@bot.command(name="rank-t")
@commands.has_permissions(administrator=True)
async def rank_t(ctx, member: discord.Member):
    await rank_member(ctx, member, ROLE_T, "Modo Test")

@bot.command(name="rank-c")
@commands.has_permissions(administrator=True)
async def rank_c(ctx, member: discord.Member):
    await rank_member(ctx, member, ROLE_C, "Modo Confirmé")

@bot.command(name="rank-plus")
@commands.has_permissions(administrator=True)
async def rank_plus(ctx, member: discord.Member):
    await rank_member(ctx, member, ROLE_PLUS, "Modo +")

@bot.command(name="rank-s")
@commands.has_permissions(administrator=True)
async def rank_s(ctx, member: discord.Member):
    await rank_member(ctx, member, ROLE_SENIOR, "Modo Senior")

@bot.command(name="rank-admin")
@commands.has_permissions(administrator=True)
async def rank_admin(ctx, member: discord.Member):
    await rank_member(ctx, member, ROLE_ADMIN, "Admin")

# =========================
# TOKEN
# =========================
token = os.getenv("DISCORD_TOKEN")

bot.run(token)
