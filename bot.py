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

# ---------------- DATA ----------------
sanctions = defaultdict(list)

# ---------------- READY ----------------
@bot.event
async def on_ready():
    print(f"Bot connecté : {bot.user}")

# ---------------- LOG ----------------
async def send_log(guild, message):
    try:
        channel = guild.get_channel(LOG_CHANNEL_ID)
        if channel:
            await channel.send(message)
    except:
        pass

# ---------------- PING ----------------
@bot.command()
async def ping(ctx):
    await ctx.send("Pong 🏓")

# ---------------- CLEAR ----------------
@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int):
    await ctx.channel.purge(limit=amount + 1)
    await ctx.send(f"🧹 {amount} messages supprimés", delete_after=3)

# ---------------- WARN ----------------
@bot.command()
@commands.has_permissions(kick_members=True)
async def warn(ctx, member: discord.Member, *, reason="Aucune raison"):

    sanctions[member.id].append(reason)

    await ctx.send(f"⚠️ {member.mention} warn : {reason}")
    await send_log(ctx.guild, f"WARN | {member} | {reason}")

# ---------------- SANCTIONS ----------------
@bot.command()
async def sanctions(ctx, member: discord.Member):

    if len(sanctions[member.id]) == 0:
        return await ctx.send("❌ Aucune sanction")

    msg = "\n".join([f"- {s}" for s in sanctions[member.id]])
    await ctx.send(f"📌 Sanctions de {member}:\n{msg}")

# ---------------- CLEAR SANCTIONS ----------------
@bot.command()
@commands.has_permissions(kick_members=True)
async def clear_sanctions(ctx, member: discord.Member):

    sanctions[member.id].clear()

    await ctx.send(f"🧹 Sanctions supprimées pour {member.mention}")
    await send_log(ctx.guild, f"CLEAR_SANCTIONS | {member}")

# ---------------- BAN ----------------
@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason="Aucune raison"):

    try:
        await member.ban(reason=reason)
        await ctx.send(f"🔨 {member} ban : {reason}")
        await send_log(ctx.guild, f"BAN | {member} | {reason}")
    except:
        await ctx.send("❌ Impossible de ban")

# ---------------- UNBAN ----------------
@bot.command()
@commands.has_permissions(ban_members=True)
async def unban(ctx, user_id: int):

    try:
        user = await bot.fetch_user(user_id)
        await ctx.guild.unban(user)

        await ctx.send(f"♻️ Unban {user}")
        await send_log(ctx.guild, f"UNBAN | {user}")

    except:
        await ctx.send("❌ Erreur unban")

# ---------------- MUTE ----------------
@bot.command()
@commands.has_permissions(manage_roles=True)
async def mute(ctx, member: discord.Member):

    role = discord.utils.get(ctx.guild.roles, name="Muted")

    if not role:
        role = await ctx.guild.create_role(name="Muted")
        for channel in ctx.guild.channels:
            await channel.set_permissions(role, send_messages=False, speak=False)

    await member.add_roles(role)

    await ctx.send(f"🔇 {member} mute")
    await send_log(ctx.guild, f"MUTE | {member}")

# ---------------- UNMUTE ----------------
@bot.command()
@commands.has_permissions(manage_roles=True)
async def unmute(ctx, member: discord.Member):

    role = discord.utils.get(ctx.guild.roles, name="Muted")

    if role:
        await member.remove_roles(role)

    await ctx.send(f"🔊 {member} unmute")
    await send_log(ctx.guild, f"UNMUTE | {member}")

# ---------------- TEMPMUTE ----------------
@bot.command()
@commands.has_permissions(manage_roles=True)
async def tempmute(ctx, member: discord.Member, time: int):

    role = discord.utils.get(ctx.guild.roles, name="Muted")

    if not role:
        role = await ctx.guild.create_role(name="Muted")
        for channel in ctx.guild.channels:
            await channel.set_permissions(role, send_messages=False, speak=False)

    await member.add_roles(role)

    await ctx.send(f"⏳ {member} mute {time}s")

    await asyncio.sleep(time)

    await member.remove_roles(role)

    await ctx.send(f"🔊 {member} unmute auto")

# ---------------- REMOVE ROLES ----------------
async def remove_staff(member):
    role_ids = [ROLE_T, ROLE_C, ROLE_PLUS, ROLE_SENIOR, ROLE_ADMIN, ROLE_STAFF]

    for role_id in role_ids:
        role = member.guild.get_role(role_id)
        if role and role in member.roles:
            try:
                await member.remove_roles(role)
            except:
                pass

# ---------------- RANK T ----------------
@bot.command(name="rank-t")
@commands.has_permissions(manage_roles=True)
async def rank_t(ctx, member: discord.Member):

    await remove_staff(member)

    role = ctx.guild.get_role(ROLE_T)
    if role:
        await member.add_roles(role)

    await ctx.send(f"📌 {member.mention} → Modo Test")

# ---------------- RANK C ----------------
@bot.command(name="rank-c")
@commands.has_permissions(manage_roles=True)
async def rank_c(ctx, member: discord.Member):

    await remove_staff(member)

    role = ctx.guild.get_role(ROLE_C)
    if role:
        await member.add_roles(role)

    await ctx.send(f"📌 {member.mention} → Modo Confirmé")

# ---------------- RANK PLUS ----------------
@bot.command(name="rank-plus")
@commands.has_permissions(manage_roles=True)
async def rank_plus(ctx, member: discord.Member):

    await remove_staff(member)

    role = ctx.guild.get_role(ROLE_PLUS)
    if role:
        await member.add_roles(role)

    await ctx.send(f"📌 {member.mention} → Modo +")

# ---------------- RANK SENIOR ----------------
@bot.command(name="rank-s")
@commands.has_permissions(manage_roles=True)
async def rank_s(ctx, member: discord.Member):

    await remove_staff(member)

    role = ctx.guild.get_role(ROLE_SENIOR)
    if role:
        await member.add_roles(role)

    await ctx.send(f"📌 {member.mention} → Senior")

# ---------------- RANK ADMIN ----------------
@bot.command(name="rank-admin")
@commands.has_permissions(manage_roles=True)
async def rank_admin(ctx, member: discord.Member):

    await remove_staff(member)

    role = ctx.guild.get_role(ROLE_ADMIN)
    if role:
        await member.add_roles(role)

    await ctx.send(f"👑 {member.mention} → Admin")

# ---------------- DERANK ----------------
@bot.command()
@commands.has_permissions(manage_roles=True)
async def derank(ctx, member: discord.Member):

    await remove_staff(member)

    await ctx.send(f"⬇️ {member.mention} derank effectué")
    await send_log(ctx.guild, f"DERANK | {member} | {ctx.author}")

# ---------------- START BOT ----------------
if not TOKEN:
    print("❌ DISCORD_TOKEN manquant")
else:
    bot.run(TOKEN)
