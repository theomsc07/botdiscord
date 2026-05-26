import discord
from discord.ext import commands
import asyncio
import os
import json
import io
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

LOG_CHANNEL_ID = 1508595464168013965
GERANT_STAFF_ID = 968588191055642624

ROLE_STAFF = 1504792759679057951

TICKET_PANEL = 1504792916772786298
TICKET_CAT = 1504792910892109935
ARCHIVE = 1507694850282100000

# =========================
# SANCTIONS
# =========================

FILE = "sanctions.json"

def load():
    if os.path.exists(FILE):
        with open(FILE, "r") as f:
            return defaultdict(list, {int(k): v for k, v in json.load(f).items()})
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

async def dm(member, msg):
    try:
        await member.send(msg)
    except:
        pass

# =========================
# CLEAR CONFIRM
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

    data = sanctions.get(member.id, [])

    if not data:
        return await ctx.send("Aucune sanction")

    await ctx.send("\n".join(data))

@bot.command()
async def clear_sanctions(ctx, member: discord.Member):

    sanctions[member.id] = []
    save()

    await ctx.send(f"🧹 sanctions supprimées {member.mention}")

# =========================
# WARN
# =========================

@bot.command()
async def warn(ctx, member: discord.Member, *, reason="Aucune raison"):

    sanctions[member.id].append(reason)
    save()

    await dm(member, f"⚠️ Warn : {reason}")

    await log(ctx.guild, "⚠️ WARN", f"{member.mention} | {reason}", discord.Color.orange(), "⚠️")

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

    await dm(member, "🔇 tu as été mute")

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

async def set_rank(ctx, member, role_id, name):

    role = ctx.guild.get_role(role_id)

    if role:
        await member.add_roles(role)

    staff = ctx.guild.get_role(ROLE_STAFF)
    if staff:
        await member.add_roles(staff)

    await log(ctx.guild, "👤 RANK", f"{member.mention} → {name}", discord.Color.blue(), "👤")

@bot.command()
async def modotest(ctx, member: discord.Member):
    await set_rank(ctx, member, ROLE_STAFF, "Modo Test")

# =========================
# DERANK
# =========================

@bot.command()
async def derank(ctx, member: discord.Member):

    for role in member.roles:
        if role.name != "@everyone":
            await member.remove_roles(role)

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

    embed = discord.Embed(title="📊 Server Info", color=discord.Color.green())
    embed.add_field(name="Owner", value=g.owner, inline=False)
    embed.add_field(name="Members", value=g.member_count, inline=False)
    embed.add_field(name="Created", value=g.created_at.strftime("%d/%m/%Y"), inline=False)

    await ctx.send(embed=embed)

@bot.command()
async def staffinfo(ctx, member: discord.Member):

    embed = discord.Embed(title="👤 Staff Info", color=discord.Color.orange())
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
    embed.add_field(name="+close", value="🎫 tickets", inline=False)

    await ctx.send(embed=embed)

# =========================
# TICKET SYSTEM FIX
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
            title="📋 Candidature Staff",
            description="Merci de remplir correctement.",
            color=discord.Color.purple()
        )

        await ch.send(embed=embed)

# =========================
# READY
# =========================

@bot.event
async def on_ready():

    print("BOT ONLINE")

    bot.add_view(Ticket())

# =========================
# RUN
# =========================

bot.run(TOKEN)
