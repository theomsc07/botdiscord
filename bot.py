import discord
from discord.ext import commands
import asyncio
import json
import os
from collections import defaultdict
from datetime import datetime

# =========================
# BOT SETUP
# =========================

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="+", intents=intents)

TOKEN = os.getenv("DISCORD_TOKEN")

# =========================
# IDS
# =========================

GERANT_STAFF_ID = 968588191055642624
LOG_CHANNEL_ID = 1508595464168013965

TICKET_CAT = 1504792910892109935
TICKET_PANEL = 1504792916772786298
ARCHIVE = 1507694850282100000

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
# LOG SYSTEM
# =========================

async def log(guild, title, desc, color, emoji="📌"):

    ch = guild.get_channel(LOG_CHANNEL_ID)
    if not ch:
        return

    embed = discord.Embed(
        title=f"{emoji} {title}",
        description=desc,
        color=color,
        timestamp=datetime.utcnow()
    )

    await ch.send(embed=embed)

# =========================
# SAFE DM
# =========================

async def dm(user, msg):
    try:
        await user.send(msg)
    except:
        pass

# =========================
# CLEAR (CONFIRM 50+)
# =========================

@bot.command()
async def clear(ctx, amount: int):

    if amount >= 50:
        await ctx.send("⚠️ Supprimer 50+ messages ? (oui/non)")

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        msg = await bot.wait_for("message", check=check)

        if msg.content.lower() != "oui":
            return await ctx.send("❌ annulé")

    await ctx.channel.purge(limit=amount + 1)

    await log(ctx.guild, "🧹 CLEAR", f"{ctx.author.mention} a supprimé {amount}", discord.Color.greyple(), "🧹")

# =========================
# SANCTIONS
# =========================

@bot.command()
async def sanctions(ctx, member: discord.Member):

    data = sanctions.get(str(member.id), [])

    embed = discord.Embed(title="📋 SANCTIONS", color=discord.Color.orange())
    embed.add_field(name="👤 Membre", value=member.mention, inline=False)

    if not data:
        embed.add_field(name="📌", value="Aucune sanction", inline=False)
    else:
        embed.add_field(name="📌", value="\n".join(data), inline=False)

    await ctx.send(embed=embed)

@bot.command()
async def clear_sanctions(ctx, member: discord.Member):

    sanctions[str(member.id)] = []
    save()

    await ctx.send(f"🧹 sanctions supprimées {member.mention}")

# =========================
# WARN
# =========================

@bot.command()
async def warn(ctx, member: discord.Member, *, reason="Aucune raison"):

    sanctions[str(member.id)].append(reason)
    save()

    await dm(member, f"⚠️ Warn : {reason}")

    await log(ctx.guild, "⚠️ WARN", f"{member.mention} | {reason}", discord.Color.orange(), "⚠️")

    await ctx.send(f"⚠️ {member.mention}")

# =========================
# BAN / UNBAN
# =========================

@bot.command()
async def ban(ctx, member: discord.Member, *, reason="Aucune raison"):

    await dm(member, f"🔨 Ban : {reason}")

    await member.ban(reason=reason)

    await log(ctx.guild, "🔨 BAN", f"{member.mention}", discord.Color.red(), "🔨")

@bot.command()
async def unban(ctx, user_id: int):

    user = await bot.fetch_user(user_id)

    await ctx.guild.unban(user)

    await log(ctx.guild, "♻️ UNBAN", f"{user}", discord.Color.green(), "♻️")

# =========================
# MUTE / TEMPMUTE
# =========================

@bot.command()
async def mute(ctx, member: discord.Member):

    role = discord.utils.get(ctx.guild.roles, name="Muted")
    if not role:
        role = await ctx.guild.create_role(name="Muted")

    await member.add_roles(role)

    await dm(member, "🔇 mute")

    await log(ctx.guild, "🔇 MUTE", f"{member.mention}", discord.Color.dark_grey(), "🔇")

@bot.command()
async def tempmute(ctx, member: discord.Member, time: int):

    role = discord.utils.get(ctx.guild.roles, name="Muted")
    if not role:
        role = await ctx.guild.create_role(name="Muted")

    await member.add_roles(role)

    await dm(member, f"⏳ tempmute {time}s")

    await log(ctx.guild, "⏳ TEMPMUTE", f"{member.mention} | {time}s", discord.Color.blurple(), "⏳")

    await asyncio.sleep(time)

    await member.remove_roles(role)

# =========================
# STAFF RANKS
# =========================

@bot.command()
async def rank_t(ctx, member: discord.Member):
    role = discord.utils.get(ctx.guild.roles, name="Modo Test")
    if role:
        await member.add_roles(role)

    await log(ctx.guild, "👤 RANK-T", f"{member.mention}", discord.Color.blue(), "👤")

@bot.command()
async def derank(ctx, member: discord.Member):

    for r in member.roles:
        if r.name != "@everyone":
            await member.remove_roles(r)

    await log(ctx.guild, "⬇️ DERANK", f"{member.mention}", discord.Color.orange(), "⬇️")

# =========================
# INFO COMMANDS
# =========================

@bot.command()
async def ping(ctx):
    await ctx.send(f"🏓 {round(bot.latency * 1000)}ms")

@bot.command()
async def serverinfo(ctx):

    g = ctx.guild

    embed = discord.Embed(title="📊 SERVER INFO", color=discord.Color.green())
    embed.add_field(name="Owner", value=g.owner, inline=False)
    embed.add_field(name="Members", value=g.member_count, inline=False)
    embed.add_field(name="Created", value=g.created_at.strftime("%d/%m/%Y"), inline=False)

    await ctx.send(embed=embed)

@bot.command()
async def staffinfo(ctx, member: discord.Member):

    embed = discord.Embed(title="👤 STAFF INFO", color=discord.Color.orange())
    embed.add_field(name="User", value=member.mention)
    embed.add_field(name="Roles", value=", ".join([r.name for r in member.roles]))

    await ctx.send(embed=embed)

@bot.command()
async def help_staff(ctx):

    embed = discord.Embed(title="📘 HELP STAFF", color=discord.Color.blurple())

    embed.add_field(name="+warn", value="⚠️ warn", inline=False)
    embed.add_field(name="+ban", value="🔨 ban", inline=False)
    embed.add_field(name="+mute", value="🔇 mute", inline=False)
    embed.add_field(name="+tempmute", value="⏳ tempmute", inline=False)
    embed.add_field(name="+clear", value="🧹 clear", inline=False)
    embed.add_field(name="+sanctions", value="📋 sanctions", inline=False)
    embed.add_field(name="+close", value="🎫 ticket", inline=False)

    await ctx.send(embed=embed)

# =========================
# TICKET SYSTEM FIX (IMPORTANT)
# =========================

class Ticket(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🎫 Ouvrir candidature", style=discord.ButtonStyle.green, custom_id="ticket")
    async def open(self, interaction, button):

        user = interaction.user
        guild = interaction.guild

        cat = guild.get_channel(TICKET_CAT)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }

        ch = await guild.create_text_channel(
            name=f"candidature-{user.name}",
            category=cat,
            overwrites=overwrites
        )

        await ch.send(f"<@{GERANT_STAFF_ID}>")

        embed = discord.Embed(
            title="📋 CANDIDATURE STAFF",
            description="Remplis correctement ta candidature.",
            color=discord.Color.purple()
        )

        await ch.send(embed=embed)

# =========================
# CLOSE (FULL FIX DELETE + LOG + DM)
# =========================

@bot.command()
async def close(ctx):

    await ctx.send("1️⃣ Accepté / 2️⃣ Refusé")

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    msg = await bot.wait_for("message", check=check)

    now = datetime.now().strftime("%H:%M:%S")

    opener = ctx.channel.name.replace("candidature-", "")

    if msg.content == "1":
        status = "ACCEPTÉ"
        dm_msg = "🎉 accepté"
        color = discord.Color.green()
    else:
        status = "REFUSÉ"
        dm_msg = "❌ refusé"
        color = discord.Color.red()

    await dm(ctx.author, dm_msg)
    await dm(await bot.fetch_user(GERANT_STAFF_ID), f"{status} | {opener}")

    embed = discord.Embed(
        title=f"📋 {status}",
        color=color
    )

    embed.add_field(name="Membre", value=opener)
    embed.add_field(name="Staff", value=ctx.author.mention)
    embed.add_field(name="Heure", value=now)

    logch = bot.get_channel(ARCHIVE)
    if logch:
        await logch.send(embed=embed)

    await ctx.channel.delete()

# =========================
# RUN
# =========================

bot.run(TOKEN)
