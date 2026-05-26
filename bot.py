import discord
from discord.ext import commands
import os
import asyncio
from collections import defaultdict

# ---------------- INTENTS ----------------
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="+", intents=intents)

# ---------------- TOKEN ----------------
TOKEN = os.getenv("DISCORD_TOKEN")

# ---------------- IDS ----------------
LOG_CHANNEL_ID = 1508482233219022992

ROLE_T = 1504792771977023591
ROLE_C = 1504792768088903931
ROLE_PLUS = 1504792764448116776
ROLE_SENIOR = 1504792759679057951
ROLE_ADMIN = 1504792748098715660
ROLE_STAFF = 1504810257715822722

GERANT_STAFF_ID = 968588191055642624

TICKET_CATEGORY_ID = 1504792910892109935
TRANSCRIPT_CHANNEL_ID = 1507694850282094683

# ---------------- DATA ----------------
sanctions = defaultdict(list)

# ---------------- LOG ----------------
async def send_log(guild, message):
    try:
        channel = guild.get_channel(LOG_CHANNEL_ID)
        if channel:
            await channel.send(message)
    except:
        pass

# ---------------- DM SAFE ----------------
async def dm(user, title, desc, color):
    try:
        embed = discord.Embed(title=title, description=desc, color=color)
        await user.send(embed=embed)
    except:
        pass

# ---------------- WARN FIX ----------------
@bot.command()
@commands.has_permissions(kick_members=True)
async def warn(ctx, member: discord.Member, *, reason="Aucune raison"):

    sanctions[member.id].append(reason)

    await dm(member, "⚠️ WARN", reason, discord.Color.orange())

    await ctx.send(f"⚠️ {member.mention} warn : {reason}")

    await send_log(ctx.guild, f"WARN | {ctx.author} → {member} | {reason}")

# ---------------- SANCTIONS ----------------
@bot.command()
async def sanctions(ctx, member: discord.Member):

    if len(sanctions[member.id]) == 0:
        return await ctx.send("❌ Aucune sanction")

    msg = "\n".join(sanctions[member.id])
    await ctx.send(f"📌 Sanctions {member}:\n{msg}")

# ---------------- CLEAR SANCTIONS ----------------
@bot.command()
@commands.has_permissions(kick_members=True)
async def clear_sanctions(ctx, member: discord.Member):

    sanctions[member.id].clear()

    await ctx.send(f"🧹 Sanctions supprimées {member.mention}")

    await send_log(ctx.guild, f"CLEAR_SANCTIONS | {member}")

# ---------------- BAN ----------------
@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason="Aucune raison"):

    await dm(member, "🔨 BAN", reason, discord.Color.red())

    await member.ban(reason=reason)

    await ctx.send(f"🔨 {member.mention} ban")

    await send_log(ctx.guild, f"BAN | {member} | {reason}")

# ---------------- UNBAN ----------------
@bot.command()
@commands.has_permissions(ban_members=True)
async def unban(ctx, user_id: int):

    user = await bot.fetch_user(user_id)
    await ctx.guild.unban(user)

    await ctx.send(f"♻️ unban {user}")

    await send_log(ctx.guild, f"UNBAN | {user}")

# ---------------- MUTE ----------------
@bot.command()
@commands.has_permissions(manage_roles=True)
async def mute(ctx, member: discord.Member):

    role = discord.utils.get(ctx.guild.roles, name="Muted")

    if not role:
        role = await ctx.guild.create_role(name="Muted")
        for ch in ctx.guild.channels:
            await ch.set_permissions(role, send_messages=False)

    await member.add_roles(role)

    await ctx.send(f"🔇 {member.mention} mute")

    await send_log(ctx.guild, f"MUTE | {member}")

# ---------------- UNMUTE FIX ----------------
@bot.command()
@commands.has_permissions(manage_roles=True)
async def unmute(ctx, member: discord.Member):

    role = discord.utils.get(ctx.guild.roles, name="Muted")

    if role and role in member.roles:
        await member.remove_roles(role)

        await ctx.send(f"🔊 {member.mention} unmute")

        await send_log(ctx.guild, f"UNMUTE | {member}")

    else:
        await ctx.send("❌ pas mute")

# ---------------- TEMPMUTE FIX ----------------
@bot.command()
@commands.has_permissions(manage_roles=True)
async def tempmute(ctx, member: discord.Member, time: int):

    role = discord.utils.get(ctx.guild.roles, name="Muted")

    if not role:
        role = await ctx.guild.create_role(name="Muted")
        for ch in ctx.guild.channels:
            await ch.set_permissions(role, send_messages=False)

    await member.add_roles(role)

    await ctx.send(f"⏳ {member.mention} mute {time}s")

    await asyncio.sleep(time)

    if role in member.roles:
        await member.remove_roles(role)

    await ctx.send(f"🔊 {member.mention} unmute auto")

# ---------------- REMOVE STAFF ----------------
async def remove_staff(member):

    role_ids = [ROLE_T, ROLE_C, ROLE_PLUS, ROLE_SENIOR, ROLE_ADMIN]

    for r in role_ids:
        role = member.guild.get_role(r)
        if role and role in member.roles:
            await member.remove_roles(role)

    # IMPORTANT FIX: garder rôle staff proprement géré ailleurs
    staff_role = member.guild.get_role(ROLE_STAFF)
    if staff_role and staff_role in member.roles:
        await member.remove_roles(staff_role)

# ---------------- RANKS FIX + STAFF ROLE ----------------

@bot.command(name="rank-t")
@commands.has_permissions(manage_roles=True)
async def rank_t(ctx, member: discord.Member):

    await remove_staff(member)

    role = ctx.guild.get_role(ROLE_T)
    staff = ctx.guild.get_role(ROLE_STAFF)

    if role:
        await member.add_roles(role)
    if staff:
        await member.add_roles(staff)

    await ctx.send(f"📌 {member.mention} → Modo Test")

@bot.command(name="rank-c")
@commands.has_permissions(manage_roles=True)
async def rank_c(ctx, member: discord.Member):

    await remove_staff(member)

    role = ctx.guild.get_role(ROLE_C)
    staff = ctx.guild.get_role(ROLE_STAFF)

    if role:
        await member.add_roles(role)
    if staff:
        await member.add_roles(staff)

    await ctx.send(f"📌 {member.mention} → Modo Confirmé")

@bot.command(name="rank-plus")
@commands.has_permissions(manage_roles=True)
async def rank_plus(ctx, member: discord.Member):

    await remove_staff(member)

    role = ctx.guild.get_role(ROLE_PLUS)
    staff = ctx.guild.get_role(ROLE_STAFF)

    if role:
        await member.add_roles(role)
    if staff:
        await member.add_roles(staff)

    await ctx.send(f"📌 {member.mention} → Modo +")

@bot.command(name="rank-s")
@commands.has_permissions(manage_roles=True)
async def rank_s(ctx, member: discord.Member):

    await remove_staff(member)

    role = ctx.guild.get_role(ROLE_SENIOR)
    staff = ctx.guild.get_role(ROLE_STAFF)

    if role:
        await member.add_roles(role)
    if staff:
        await member.add_roles(staff)

    await ctx.send(f"📌 {member.mention} → Senior")

@bot.command(name="rank-admin")
@commands.has_permissions(manage_roles=True)
async def rank_admin(ctx, member: discord.Member):

    await remove_staff(member)

    role = ctx.guild.get_role(ROLE_ADMIN)
    staff = ctx.guild.get_role(ROLE_STAFF)

    if role:
        await member.add_roles(role)
    if staff:
        await member.add_roles(staff)

    await ctx.send(f"👑 {member.mention} → Admin")

# ---------------- DERANK FIX ----------------
@bot.command()
@commands.has_permissions(manage_roles=True)
async def derank(ctx, member: discord.Member):

    await remove_staff(member)

    await ctx.send(f"⬇️ {member.mention} derank")

    await send_log(ctx.guild, f"DERANK | {member}")

# =========================
# 🔥 FIX CLOSE + DM + TRANSCRIPT
# =========================

@bot.command()
async def close(ctx):

    await ctx.send("1️⃣ Accepté / 2️⃣ Refusé")

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    msg = await bot.wait_for("message", check=check)

    channel = ctx.channel
    name = channel.name

    staff_channel = ctx.guild.get_channel(TRANSCRIPT_CHANNEL_ID)

    # récup membre approximatif
    member = None
    for m in ctx.guild.members:
        if m.name in name:
            member = m
            break

    if msg.content == "1":
        status = "ACCEPTÉ"
        color = discord.Color.green()
        txt = "Bienvenue dans le staff !!"
    else:
        status = "REFUSÉ"
        color = discord.Color.red()
        txt = "Refusé"

    # DM candidat FIX
    if member:
        await dm(member, status, txt, color)

    # DM gérant staff FIX
    gstaff = ctx.guild.get_member(GERANT_STAFF_ID)
    if gstaff:
        await dm(gstaff, "📋 Résultat ticket", f"{member} → {status}", color)

    # TRANSCRIPT LOG FIX
    if staff_channel:
        await staff_channel.send(
            f"📄 TRANSCRIPT\nChannel: {channel.name}\nStatus: {status}\nStaff: {ctx.author.mention}"
        )

    await ctx.send(f"📌 Ticket {status}")

    await asyncio.sleep(2)
    await ctx.channel.delete()

# ---------------- START ----------------
if not TOKEN:
    print("DISCORD_TOKEN manquant")
else:
    bot.run(TOKEN)
