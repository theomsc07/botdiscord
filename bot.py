import discord
from discord.ext import commands
import os
import asyncio
from collections import defaultdict
import discord.ui
from datetime import datetime

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

TICKET_PANEL_CHANNEL = 1504792916772786298
TICKET_CATEGORY_ID = 1504792910892109935
TRANSCRIPT_CHANNEL_ID = 1507694850282094683

# ---------------- DATA ----------------
sanctions = defaultdict(list)

# =========================================================
# 🔧 UTIL LOG + DM (FIX GLOBAL)
# =========================================================

async def log(guild, message):
    channel = guild.get_channel(LOG_CHANNEL_ID)
    if channel:
        try:
            await channel.send(message)
        except:
            pass


async def dm(user, title, desc, color):
    try:
        await user.send(embed=discord.Embed(
            title=title,
            description=desc,
            color=color
        ))
    except:
        pass

# =========================================================
# READY + TICKET PANEL
# =========================================================

@bot.event
async def on_ready():
    print(f"Bot connecté : {bot.user}")

    channel = bot.get_channel(TICKET_PANEL_CHANNEL)

    if channel:
        await channel.purge(limit=10)

        embed = discord.Embed(
            title="🎫 OUVERTURE TICKET",
            description="Clique pour ouvrir un ticket staff",
            color=discord.Color.purple()
        )

        await channel.send(embed=embed, view=TicketView())

    bot.add_view(TicketView())

# =========================================================
# 📊 PING
# =========================================================

@bot.command()
async def ping(ctx):
    await ctx.send("Pong 🏓")

# =========================================================
# 🧹 CLEAR
# =========================================================

@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int):
    await ctx.channel.purge(limit=amount + 1)
    await ctx.send(f"🧹 {amount} messages supprimés", delete_after=3)
    await log(ctx.guild, f"CLEAR | {ctx.author} | {amount}")

# =========================================================
# ⚠️ WARN FIX
# =========================================================

@bot.command()
@commands.has_permissions(kick_members=True)
async def warn(ctx, member: discord.Member, *, reason="Aucune raison"):

    sanctions[member.id].append(reason)

    await dm(member, "⚠️ WARN", reason, discord.Color.orange())

    await ctx.send(f"⚠️ {member.mention} warn : {reason}")

    await log(ctx.guild, f"⚠️ WARN | {member.mention} | {ctx.author.mention} | {reason}")

# =========================================================
# 📜 SANCTIONS
# =========================================================

@bot.command()
async def sanctions(ctx, member: discord.Member):

    if len(sanctions[member.id]) == 0:
        return await ctx.send("❌ Aucune sanction")

    msg = "\n".join([f"- {s}" for s in sanctions[member.id]])
    await ctx.send(f"📌 Sanctions de {member}:\n{msg}")

# =========================================================
# 🧹 CLEAR SANCTIONS
# =========================================================

@bot.command()
@commands.has_permissions(kick_members=True)
async def clear_sanctions(ctx, member: discord.Member):

    sanctions[member.id].clear()

    await ctx.send(f"🧹 Sanctions supprimées pour {member.mention}")
    await log(ctx.guild, f"CLEAR_SANCTIONS | {member}")

# =========================================================
# 🔨 BAN
# =========================================================

@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason="Aucune raison"):

    try:
        await member.ban(reason=reason)

        await dm(member, "🔨 BAN", reason, discord.Color.red())

        await ctx.send(f"🔨 {member} ban : {reason}")

        await log(ctx.guild, f"BAN | {member} | {ctx.author} | {reason}")

    except:
        await ctx.send("❌ Impossible de ban")

# =========================================================
# ♻️ UNBAN
# =========================================================

@bot.command()
@commands.has_permissions(ban_members=True)
async def unban(ctx, user_id: int):

    try:
        user = await bot.fetch_user(user_id)
        await ctx.guild.unban(user)

        await ctx.send(f"♻️ Unban {user}")

        await log(ctx.guild, f"UNBAN | {user}")

    except:
        await ctx.send("❌ Erreur unban")

# =========================================================
# 🔇 MUTE FIX
# =========================================================

@bot.command()
@commands.has_permissions(manage_roles=True)
async def mute(ctx, member: discord.Member):

    role = discord.utils.get(ctx.guild.roles, name="Muted")

    if not role:
        role = await ctx.guild.create_role(name="Muted")
        for channel in ctx.guild.channels:
            await channel.set_permissions(role, send_messages=False, speak=False)

    await member.add_roles(role)

    await dm(member, "🔇 MUTE", "Tu es mute", discord.Color.red())

    await ctx.send(f"🔇 {member} mute")

    await log(ctx.guild, f"MUTE | {member}")

# =========================================================
# 🔊 UNMUTE FIX
# =========================================================

@bot.command()
@commands.has_permissions(manage_roles=True)
async def unmute(ctx, member: discord.Member):

    role = discord.utils.get(ctx.guild.roles, name="Muted")

    if role and role in member.roles:
        await member.remove_roles(role)

    await dm(member, "🔊 UNMUTE", "Tu n'es plus mute", discord.Color.green())

    await ctx.send(f"🔊 {member} unmute")

    await log(ctx.guild, f"UNMUTE | {member}")

# =========================================================
# ⏳ TEMPMUTE FIX
# =========================================================

@bot.command()
@commands.has_permissions(manage_roles=True)
async def tempmute(ctx, member: discord.Member, time: int):

    role = discord.utils.get(ctx.guild.roles, name="Muted")

    if not role:
        role = await ctx.guild.create_role(name="Muted")
        for channel in ctx.guild.channels:
            await channel.set_permissions(role, send_messages=False, speak=False)

    await member.add_roles(role)

    await dm(member, "⏳ TEMPMUTE", f"{time}s mute", discord.Color.red())

    await ctx.send(f"⏳ {member} mute {time}s")

    await log(ctx.guild, f"TEMPMUTE | {member} | {time}s")

    await asyncio.sleep(time)

    if role in member.roles:
        await member.remove_roles(role)

    await dm(member, "🔊 UNMUTE", "Auto unmute", discord.Color.green())

    await log(ctx.guild, f"UNMUTE AUTO | {member}")

# =========================================================
# ➕ ADD
# =========================================================

@bot.command()
async def add(ctx, member: discord.Member):
    await ctx.channel.set_permissions(member, view_channel=True, send_messages=True)
    await ctx.send(f"➕ {member.mention}")

# =========================================================
# ➖ DEL
# =========================================================

@bot.command(name="del")
async def remove(ctx, member: discord.Member):
    await ctx.channel.set_permissions(member, view_channel=False)
    await ctx.send(f"➖ {member.mention}")

# =========================================================
# ✏️ RENAME
# =========================================================

@bot.command()
async def rename(ctx, *, name):
    await ctx.channel.edit(name=name)
    await ctx.send(f"✏️ {name}")

# =========================================================
# 👮 RANK SYSTEM + STAFF ROLE AUTO
# =========================================================

async def remove_staff(member):
    roles = [ROLE_T, ROLE_C, ROLE_PLUS, ROLE_SENIOR, ROLE_ADMIN, ROLE_STAFF]
    for r in roles:
        role = member.guild.get_role(r)
        if role and role in member.roles:
            await member.remove_roles(role)

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

    await dm(member, "📌 RANK", "Modo Test", discord.Color.green())
    await log(ctx.guild, f"RANK-T | {member}")

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

    await dm(member, "📌 RANK", "Modo Confirmé", discord.Color.green())
    await log(ctx.guild, f"RANK-C | {member}")

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

    await dm(member, "📌 RANK", "Modo +", discord.Color.green())
    await log(ctx.guild, f"RANK-PLUS | {member}")

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

    await dm(member, "📌 RANK", "Senior", discord.Color.green())
    await log(ctx.guild, f"RANK-S | {member}")

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

    await dm(member, "👑 RANK", "Admin", discord.Color.green())
    await log(ctx.guild, f"RANK-ADMIN | {member}")

# =========================================================
# ❌ DERANK FIX
# =========================================================

@bot.command()
@commands.has_permissions(manage_roles=True)
async def derank(ctx, member: discord.Member):

    await remove_staff(member)

    await dm(member, "⬇️ DERANK", "Tu n'es plus staff", discord.Color.red())

    await ctx.send(f"⬇️ {member.mention}")

    await log(ctx.guild, f"DERANK | {member} | {ctx.author}")

# =========================================================
# 🎫 TICKET SYSTEM
# =========================================================

class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🎫 Ouvrir ticket", style=discord.ButtonStyle.green)
    async def open(self, interaction: discord.Interaction, button: discord.ui.Button):

        guild = interaction.guild
        user = interaction.user

        category = guild.get_channel(TICKET_CATEGORY_ID)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True),
            guild.get_role(ROLE_STAFF): discord.PermissionOverwrite(view_channel=True)
        }

        channel = await guild.create_text_channel(
            name=f"ticket-{user.name}",
            category=category,
            overwrites=overwrites
        )

        embed = discord.Embed(
            title="📋 CANDIDATURE STAFF",
            description="+add +del +rename +close",
            color=discord.Color.purple()
        )

        embed.add_field(name="👤 Candidat", value=user.mention)
        embed.add_field(name="👮 Gérant Staff", value=f"<@{GERANT_STAFF_ID}>")

        await channel.send(content=f"{user.mention} <@{GERANT_STAFF_ID}>", embed=embed)

        await dm(user, "🎫 TICKET", channel.mention, discord.Color.green())

# =========================================================
# 🔥 RUN BOT
# =========================================================

if not TOKEN:
    print("DISCORD_TOKEN manquant")
else:
    bot.run(TOKEN)
