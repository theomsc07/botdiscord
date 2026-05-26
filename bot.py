import discord
from discord.ext import commands
import asyncio
import json
from collections import defaultdict
from datetime import datetime
import os

# =========================
# CONFIG
# =========================

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="+", intents=intents)

TOKEN = os.getenv("DISCORD_TOKEN")

# =========================
# IDS SERVEUR
# =========================

GERANT_STAFF_ID = 968588191055642624

TICKET_PANEL_CHANNEL = 1504792916772786298
TICKET_CATEGORY_ID = 1504792910892109935
ARCHIVE_CHANNEL_ID = 1507694850282100000
LOG_CHANNEL_ID = 1508595464168013965

# =========================
# SANCTIONS SYSTEM
# =========================

FILE = "sanctions.json"

def load():
    try:
        with open(FILE, "r") as f:
            return defaultdict(list, json.load(f))
    except:
        return defaultdict(list)

sanctions = load()

def save():
    with open(FILE, "w") as f:
        json.dump(dict(sanctions), f, indent=4)

# =========================
# SAFE DM
# =========================

async def dm(user, msg):
    try:
        await user.send(msg)
    except:
        pass

# =========================
# LOG SYSTEM
# =========================

async def log(guild, title, desc, color):
    ch = guild.get_channel(LOG_CHANNEL_ID)
    if ch:
        embed = discord.Embed(
            title=title,
            description=desc,
            color=color,
            timestamp=datetime.utcnow()
        )
        await ch.send(embed=embed)

# =========================
# CLEAR
# =========================

@bot.command()
async def clear(ctx, amount: int):

    if amount >= 50:
        await ctx.send("⚠️ Confirmer suppression (oui/non)")

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        msg = await bot.wait_for("message", check=check)

        if msg.content.lower() != "oui":
            return await ctx.send("❌ annulé")

    await ctx.channel.purge(limit=amount + 1)

    await log(ctx.guild, "🧹 CLEAR", f"{ctx.author.mention} a supprimé {amount}", discord.Color.greyple())

# =========================
# SANCTIONS
# =========================

@bot.command()
async def sanctions(ctx, member: discord.Member):

    data = sanctions.get(str(member.id), [])

    embed = discord.Embed(title="📋 SANCTIONS", color=discord.Color.orange())
    embed.add_field(name="Membre", value=member.mention, inline=False)

    if not data:
        embed.add_field(name="Status", value="Aucune sanction", inline=False)
    else:
        embed.add_field(name="Liste", value="\n".join(data), inline=False)

    await ctx.send(embed=embed)

@bot.command()
async def clear_sanctions(ctx, member: discord.Member):

    sanctions[str(member.id)] = []
    save()

    await ctx.send(f"🧹 sanctions supprimées {member.mention}")

# =========================
# MODERATION
# =========================

@bot.command()
async def warn(ctx, member: discord.Member, *, reason="aucune raison"):

    sanctions[str(member.id)].append(reason)
    save()

    await dm(member, f"⚠️ Warn : {reason}")
    await ctx.send(f"⚠️ {member.mention} warn")

    await log(ctx.guild, "⚠️ WARN", f"{ctx.author.mention} → {member.mention} | {reason}", discord.Color.orange())

@bot.command()
async def ban(ctx, member: discord.Member, *, reason="aucune raison"):

    await dm(member, f"🔨 Ban : {reason}")
    await member.ban(reason=reason)

    await ctx.send(f"🔨 {member.mention} ban")

    await log(ctx.guild, "🔨 BAN", f"{ctx.author.mention} → {member.mention}", discord.Color.red())

@bot.command()
async def unban(ctx, user_id: int):

    user = await bot.fetch_user(user_id)
    await ctx.guild.unban(user)

    await ctx.send("♻️ unban effectué")

    await log(ctx.guild, "♻️ UNBAN", str(user), discord.Color.green())

@bot.command()
async def mute(ctx, member: discord.Member):

    role = discord.utils.get(ctx.guild.roles, name="Muted")
    if not role:
        role = await ctx.guild.create_role(name="Muted")

    await member.add_roles(role)

    await dm(member, "🔇 mute")
    await ctx.send(f"🔇 {member.mention} mute")

@bot.command()
async def tempmute(ctx, member: discord.Member, time: int):

    role = discord.utils.get(ctx.guild.roles, name="Muted")
    if not role:
        role = await ctx.guild.create_role(name="Muted")

    await member.add_roles(role)

    await dm(member, f"⏳ mute {time}s")

    await ctx.send(f"⏳ {member.mention} mute {time}s")

    await asyncio.sleep(time)

    await member.remove_roles(role)

    await ctx.send(f"🔊 unmute {member.mention}")

# =========================
# RANK SYSTEM
# =========================

@bot.command()
async def rank_t(ctx, member: discord.Member):

    role = discord.utils.get(ctx.guild.roles, name="Modo Test")
    if not role:
        role = await ctx.guild.create_role(name="Modo Test")

    await member.add_roles(role)
    await ctx.send(f"🟢 {member.mention} → Modo Test")

@bot.command()
async def rank_c(ctx, member: discord.Member):

    role = discord.utils.get(ctx.guild.roles, name="Modo Confirmé")
    if not role:
        role = await ctx.guild.create_role(name="Modo Confirmé")

    await member.add_roles(role)
    await ctx.send(f"🟡 {member.mention} → Modo Confirmé")

@bot.command()
async def rank_plus(ctx, member: discord.Member):

    role = discord.utils.get(ctx.guild.roles, name="Modo +")
    if not role:
        role = await ctx.guild.create_role(name="Modo +")

    await member.add_roles(role)
    await ctx.send(f"🔵 {member.mention} → Modo +")

@bot.command()
async def rank_s(ctx, member: discord.Member):

    role = discord.utils.get(ctx.guild.roles, name="Modo Senior")
    if not role:
        role = await ctx.guild.create_role(name="Modo Senior")

    await member.add_roles(role)
    await ctx.send(f"🔴 {member.mention} → Senior")

@bot.command()
async def rank_admin(ctx, member: discord.Member):

    role = discord.utils.get(ctx.guild.roles, name="Admin Staff")
    if not role:
        role = await ctx.guild.create_role(name="Admin Staff")

    await member.add_roles(role)
    await ctx.send(f"👑 {member.mention} → Admin")

@bot.command()
async def derank(ctx, member: discord.Member):

    for r in member.roles:
        if r.name != "@everyone":
            await member.remove_roles(r)

    await ctx.send(f"⬇️ {member.mention} derank")

    await log(ctx.guild, "DERANK", f"{ctx.author} → {member}", discord.Color.orange())

# =========================
# INFOS
# =========================

@bot.command()
async def ping(ctx):
    await ctx.send(f"🏓 {round(bot.latency*1000)}ms")

@bot.command()
async def serverinfo(ctx):

    g = ctx.guild

    embed = discord.Embed(title="📊 SERVER INFO", color=discord.Color.green())
    embed.add_field(name="Nom", value=g.name, inline=False)
    embed.add_field(name="Membres", value=g.member_count, inline=False)
    embed.add_field(name="Owner", value=g.owner, inline=False)

    await ctx.send(embed=embed)

@bot.command()
async def staffinfo(ctx, member: discord.Member):

    roles = ", ".join([r.name for r in member.roles if r.name != "@everyone"])

    embed = discord.Embed(title="👤 STAFF INFO", color=discord.Color.orange())
    embed.add_field(name="User", value=member.mention)
    embed.add_field(name="Roles", value=roles)

    await ctx.send(embed=embed)

@bot.command()
async def help_staff(ctx):

    embed = discord.Embed(title="📘 HELP STAFF", color=discord.Color.blurple())

    embed.add_field(name="Modération", value="+warn +ban +unban +mute +tempmute")
    embed.add_field(name="Gestion", value="+clear +sanctions +clear_sanctions")
    embed.add_field(name="Ranks", value="+rank_t +rank_c +rank_plus +rank_s +rank_admin +derank")
    embed.add_field(name="Infos", value="+ping +serverinfo +staffinfo")
    embed.add_field(name="Tickets", value="Bouton + +close +add +del +rename")

    await ctx.send(embed=embed)

# =========================
# TICKETS
# =========================

class Ticket(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🎫 Ouvrir ticket", style=discord.ButtonStyle.green, custom_id="ticket")
    async def open(self, interaction, button):

        user = interaction.user
        guild = interaction.guild

        cat = guild.get_channel(TICKET_CATEGORY_ID)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            guild.get_member(GERANT_STAFF_ID): discord.PermissionOverwrite(view_channel=True)
        }

        channel = await guild.create_text_channel(
            name=f"ticket-{user.name}",
            category=cat,
            overwrites=overwrites
        )

        await channel.send(f"{user.mention} <@{GERANT_STAFF_ID}>")

        await channel.send("📋 ticket ouvert")

        await log(guild, "TICKET OPEN", str(user), discord.Color.green())

# =========================
# CLOSE TICKET
# =========================

@bot.command()
async def close(ctx):

    await ctx.send("1️⃣ Accepté / 2️⃣ Refusé")

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    msg = await bot.wait_for("message", check=check)

    opener = ctx.channel.name.replace("ticket-", "")

    if msg.content == "1":
        status = "ACCEPTÉ"
        color = discord.Color.green()
        dm_msg = "accepté"
    else:
        status = "REFUSÉ"
        color = discord.Color.red()
        dm_msg = "refusé"

    for m in ctx.guild.members:
        if m.name == opener:
            await dm(m, dm_msg)

    await ctx.send(f"📌 {status}")

    archive = ctx.guild.get_channel(ARCHIVE_CHANNEL_ID)
    if archive:
        await archive.send(f"{status} | {opener}")

    await log(ctx.guild, "TICKET CLOSE", status, color)

    await ctx.channel.delete()

# =========================
# PANEL AUTO
# =========================

@bot.event
async def on_ready():

    print("BOT ONLINE")

    channel = bot.get_channel(TICKET_PANEL_CHANNEL)

    if channel:
        await channel.purge(limit=10)

        embed = discord.Embed(
            title="🎫 CANDIDATURE STAFF",
            description="Clique pour ouvrir un ticket",
            color=discord.Color.purple()
        )

        await channel.send(embed=embed, view=Ticket())

    bot.add_view(Ticket())

# =========================
# RUN
# =========================

bot.run(TOKEN)
