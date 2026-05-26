import discord
from discord.ext import commands
import asyncio
import json
from collections import defaultdict
from datetime import datetime
import os

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

TICKET_PANEL_CHANNEL = 1504792916772786298
TICKET_CATEGORY_ID = 1504792910892109935
ARCHIVE_CHANNEL_ID = 1507694850282100000

# =========================
# ROLES STAFF
# =========================

ROLE_IDS = {
    "t": 1504792771977023591,
    "c": 1504792768088903931,
    "plus": 1504792764448116776,
    "s": 1504792759679057951,
    "admin": 1504792748098715660
}

def get_role(guild, key):
    role_id = ROLE_IDS.get(key)
    return guild.get_role(role_id)

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

    await log(ctx.guild, "🧹 CLEAR", f"{ctx.author.mention} a supprimé {amount}", discord.Color.greyple(), "🧹")

# =========================
# SANCTIONS
# =========================

@bot.command()
async def warn(ctx, member: discord.Member, *, reason="Aucune raison"):

    sanctions[str(member.id)].append(reason)
    save()

    await dm(member, f"⚠️ Warn : {reason}")

    await log(ctx.guild, "⚠️ WARN", f"{ctx.author.mention} → {member.mention} | {reason}", discord.Color.orange(), "⚠️")

@bot.command()
async def sanctions(ctx, member: discord.Member):

    data = sanctions.get(str(member.id), [])

    embed = discord.Embed(title="📋 SANCTIONS", color=discord.Color.orange())
    embed.add_field(name="Membre", value=member.mention, inline=False)

    if not data:
        embed.add_field(name="Aucune", value="Aucune sanction")
    else:
        embed.add_field(name="Liste", value="\n".join(data))

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
async def ban(ctx, member: discord.Member, *, reason="Aucune raison"):

    await member.ban(reason=reason)

    await dm(member, f"🔨 Ban : {reason}")

    await log(ctx.guild, "🔨 BAN", f"{ctx.author.mention} → {member.mention}", discord.Color.red(), "🔨")

@bot.command()
async def unban(ctx, user_id: int):

    user = await bot.fetch_user(user_id)
    await ctx.guild.unban(user)

    await log(ctx.guild, "♻️ UNBAN", str(user), discord.Color.green(), "♻️")

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

    await asyncio.sleep(time)

    await member.remove_roles(role)

# =========================
# RANK SYSTEM
# =========================

@bot.command()
async def rank_t(ctx, member: discord.Member):
    await member.add_roles(get_role(ctx.guild, "t"))
    await ctx.send(f"🟢 {member.mention} → Modo Test")

@bot.command()
async def rank_c(ctx, member: discord.Member):
    await member.add_roles(get_role(ctx.guild, "c"))
    await ctx.send(f"🟡 {member.mention} → Confirmé")

@bot.command()
async def rank_plus(ctx, member: discord.Member):
    await member.add_roles(get_role(ctx.guild, "plus"))
    await ctx.send(f"🔵 {member.mention} → Modo +")

@bot.command()
async def rank_s(ctx, member: discord.Member):
    await member.add_roles(get_role(ctx.guild, "s"))
    await ctx.send(f"🔴 {member.mention} → Senior")

@bot.command()
async def rank_admin(ctx, member: discord.Member):
    await member.add_roles(get_role(ctx.guild, "admin"))
    await ctx.send(f"👑 {member.mention} → Admin")

@bot.command()
async def derank(ctx, member: discord.Member):

    for key in ROLE_IDS:
        role = get_role(ctx.guild, key)
        if role:
            await member.remove_roles(role)

    await ctx.send(f"⬇️ {member.mention} derank complet")

# =========================
# INFOS
# =========================

@bot.command()
async def ping(ctx):
    await ctx.send(f"🏓 {round(bot.latency * 1000)}ms")

@bot.command()
async def serverinfo(ctx):
    g = ctx.guild

    embed = discord.Embed(title="📊 SERVER INFO")
    embed.add_field(name="Owner", value=g.owner)
    embed.add_field(name="Members", value=g.member_count)

    await ctx.send(embed=embed)

@bot.command()
async def staffinfo(ctx, member: discord.Member):

    embed = discord.Embed(title="👤 STAFF INFO")
    embed.add_field(name="User", value=member.mention)
    embed.add_field(name="Roles", value=", ".join([r.name for r in member.roles]))

    await ctx.send(embed=embed)

# =========================
# TICKET SYSTEM
# =========================

class Ticket(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🎫 Ouvrir candidature", style=discord.ButtonStyle.green)
    async def open(self, interaction, button):

        user = interaction.user
        guild = interaction.guild

        cat = guild.get_channel(TICKET_CATEGORY_ID)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True)
        }

        channel = await guild.create_text_channel(
            name=f"ticket-{user.name}",
            category=cat,
            overwrites=overwrites
        )

        await channel.send(f"{user.mention} <@{GERANT_STAFF_ID}>")

        embed = discord.Embed(
            title="📋 CANDIDATURE",
            description="Remplis ton formulaire",
            color=discord.Color.purple()
        )

        await channel.send(embed=embed)

# =========================
# CLOSE
# =========================

@bot.command()
async def close(ctx):

    await ctx.send("1️⃣ accepté / 2️⃣ refusé")

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    msg = await bot.wait_for("message", check=check)

    user = ctx.channel.name

    if msg.content == "1":
        status = "ACCEPTÉ"
    else:
        status = "REFUSÉ"

    await dm(ctx.author, status)
    await log(ctx.guild, "🎫 CLOSE", f"{user} → {status}", discord.Color.blue(), "🎫")

    await ctx.channel.delete()

# =========================
# READY
# =========================

@bot.event
async def on_ready():
    print("BOT ONLINE")
    bot.add_view(Ticket())

bot.run(TOKEN)
