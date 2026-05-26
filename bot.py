import discord
from discord.ext import commands
import asyncio
from datetime import datetime
import os

# =========================
# CONFIG
# =========================

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="+", intents=intents)

TOKEN = os.getenv("DISCORD_TOKEN")

# =========================
# IDS
# =========================

GERANT_STAFF_ID = 968588191055642624

TICKET_PANEL_CHANNEL = 1504792916772786298
TICKET_CATEGORY_ID = 1504792910892109935
ARCHIVE_CHANNEL_ID = 1507694850282100000
LOG_CHANNEL_ID = 1508595464168013965

STAFF_ROLE_ID = 1504810257715822722

MUTED_ROLE_NAME = "Muted"

RANKS = {
    "rank_t": "Modo Test",
    "rank_c": "Modo Confirmé",
    "rank_plus": "Modo +",
    "rank_s": "Modo Senior",
    "rank_admin": "Admin Staff"
}

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
# DM SYSTEM (SAFE + CLEAN)
# =========================

async def dm(user, title, desc, color):
    try:
        embed = discord.Embed(
            title=title,
            description=desc,
            color=color,
            timestamp=datetime.utcnow()
        )
        await user.send(embed=embed)
    except:
        pass

# =========================
# =========================
# TICKET SYSTEM
# =========================
# =========================

class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🎫 Ouvrir candidature", style=discord.ButtonStyle.green, custom_id="open_ticket")
    async def open(self, interaction: discord.Interaction, button: discord.ui.Button):

        user = interaction.user
        guild = interaction.guild

        category = guild.get_channel(TICKET_CATEGORY_ID)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            guild.get_member(GERANT_STAFF_ID): discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }

        channel = await guild.create_text_channel(
            name=f"candidature-{user.name}",
            category=category,
            overwrites=overwrites
        )

        embed = discord.Embed(
            title="📋 CANDIDATURE STAFF",
            description="Bienvenue ! Utilise les commandes :\n+add +del +rename +close",
            color=discord.Color.purple()
        )

        embed.add_field(name="👤 Membre", value=user.mention)
        embed.add_field(name="👑 Gérant Staff", value=f"<@{GERANT_STAFF_ID}>")

        await channel.send(content=f"{user.mention} <@{GERANT_STAFF_ID}>", embed=embed)

        await dm(user, "🎫 Ticket ouvert", "Ta candidature est créée.", discord.Color.green())

        await log(guild, "🎫 TICKET OPEN", f"{user.mention}", discord.Color.green())

# =========================
# CLOSE TICKET
# =========================

@bot.command()
async def close(ctx):

    await ctx.send("1️⃣ Accepté / 2️⃣ Refusé")

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    msg = await bot.wait_for("message", check=check)

    name = ctx.channel.name.replace("candidature-", "")
    member = discord.utils.find(lambda m: m.name == name, ctx.guild.members)

    if msg.content == "1":
        status = "ACCEPTÉ"
        color = discord.Color.green()
        title = "🎉 Accepté"
        desc = "Bienvenue dans le staff !!"
    else:
        status = "REFUSÉ"
        color = discord.Color.red()
        title = "❌ Refusé"
        desc = "Ta candidature est refusée."

    if member:
        await dm(member, title, desc, color)

    await dm(
        discord.utils.get(ctx.guild.members, id=GERANT_STAFF_ID),
        "📋 Résultat candidature",
        f"{status} → {name}",
        color
    )

    archive = ctx.guild.get_channel(ARCHIVE_CHANNEL_ID)

    if archive:
        embed = discord.Embed(
            title=f"📋 {status}",
            description=f"Membre : {name}\nStaff : {ctx.author.mention}",
            color=color,
            timestamp=datetime.utcnow()
        )
        await archive.send(embed=embed)

    await log(ctx.guild, "🎫 CLOSE TICKET", f"{name} → {status}", color)

    await ctx.channel.delete()

# =========================
# ADD / DEL / RENAME
# =========================

@bot.command()
async def add(ctx, member: discord.Member):
    await ctx.channel.set_permissions(member, view_channel=True, send_messages=True)
    await ctx.send(f"➕ {member.mention} ajouté")

@bot.command()
async def deluser(ctx, member: discord.Member):
    await ctx.channel.set_permissions(member, overwrite=None)
    await ctx.send(f"➖ {member.mention} retiré")

@bot.command()
async def rename(ctx, *, name):
    await ctx.channel.edit(name=name)
    await ctx.send(f"✏️ renommé → {name}")

# =========================
# MODERATION
# =========================

@bot.command()
async def warn(ctx, member: discord.Member, *, reason="aucune raison"):
    await dm(member, "⚠️ WARN", reason, discord.Color.orange())
    await ctx.send(f"⚠️ {member.mention} warn")
    await log(ctx.guild, "WARN", f"{member.mention} | {reason}", discord.Color.orange())

@bot.command()
async def ban(ctx, member: discord.Member, *, reason="aucune raison"):
    await dm(member, "🔨 BAN", reason, discord.Color.red())
    await member.ban(reason=reason)
    await ctx.send(f"🔨 {member.mention} ban")

@bot.command()
async def unban(ctx, user_id: int):
    user = await bot.fetch_user(user_id)
    await ctx.guild.unban(user)
    await ctx.send("♻️ unban")

# =========================
# MUTE SYSTEM FIX
# =========================

@bot.command()
async def mute(ctx, member: discord.Member):

    role = discord.utils.get(ctx.guild.roles, name=MUTED_ROLE_NAME)
    if not role:
        role = await ctx.guild.create_role(name=MUTED_ROLE_NAME)

    await member.add_roles(role)

    await dm(member, "🔇 MUTE", "Tu es mute", discord.Color.orange())
    await ctx.send(f"🔇 {member.mention} mute")

@bot.command()
async def unmute(ctx, member: discord.Member):

    role = discord.utils.get(ctx.guild.roles, name=MUTED_ROLE_NAME)

    if role and role in member.roles:
        await member.remove_roles(role)

        await dm(member, "🔊 UNMUTE", "Tu peux parler", discord.Color.green())
        await ctx.send(f"🔊 {member.mention} unmute")
    else:
        await ctx.send("❌ pas mute")

@bot.command()
async def tempmute(ctx, member: discord.Member, seconds: int):

    role = discord.utils.get(ctx.guild.roles, name=MUTED_ROLE_NAME)
    if not role:
        role = await ctx.guild.create_role(name=MUTED_ROLE_NAME)

    await member.add_roles(role)

    await ctx.send(f"⏳ {member.mention} mute {seconds}s")

    await asyncio.sleep(seconds)

    if role in member.roles:
        await member.remove_roles(role)

    await dm(member, "🔊 UNMUTE", "Mute terminé", discord.Color.green())

# =========================
# RANK SYSTEM FIX
# =========================

async def give_rank(ctx, member, role_name, label, emoji):

    role = discord.utils.get(ctx.guild.roles, name=role_name)

    if not role:
        role = await ctx.guild.create_role(name=role_name)

    await member.add_roles(role)

    await ctx.send(f"{emoji} {member.mention} → {label}")

    await log(ctx.guild, label.upper(), f"{ctx.author.mention} → {member.mention}", discord.Color.blurple())

@bot.command()
async def rank_t(ctx, member: discord.Member):
    await give_rank(ctx, member, RANKS["rank_t"], "Modo Test", "🟢")

@bot.command()
async def rank_c(ctx, member: discord.Member):
    await give_rank(ctx, member, RANKS["rank_c"], "Modo Confirmé", "🟡")

@bot.command()
async def rank_plus(ctx, member: discord.Member):
    await give_rank(ctx, member, RANKS["rank_plus"], "Modo +", "🔵")

@bot.command()
async def rank_s(ctx, member: discord.Member):
    await give_rank(ctx, member, RANKS["rank_s"], "Modo Senior", "🔴")

@bot.command()
async def rank_admin(ctx, member: discord.Member):
    await give_rank(ctx, member, RANKS["rank_admin"], "Admin Staff", "👑")

# =========================
# DERANK FIX
# =========================

@bot.command()
async def derank(ctx, member: discord.Member):

    removed = 0

    for role in member.roles:
        if role.name in RANKS.values():
            await member.remove_roles(role)
            removed += 1

    staff_role = ctx.guild.get_role(STAFF_ROLE_ID)

    if staff_role and staff_role in member.roles:
        await member.remove_roles(staff_role)

    await ctx.send(f"⬇️ {member.mention} derank ({removed})")

    await log(ctx.guild, "DERANK", f"{ctx.author.mention} → {member.mention}", discord.Color.orange())

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
    embed.add_field(name="Nom", value=g.name)
    embed.add_field(name="Membres", value=g.member_count)

    await ctx.send(embed=embed)

@bot.command()
async def staffinfo(ctx, member: discord.Member):

    roles = ", ".join([r.name for r in member.roles if r.name != "@everyone"])

    embed = discord.Embed(title="👤 STAFF INFO", color=discord.Color.orange())
    embed.add_field(name="Membre", value=member.mention)
    embed.add_field(name="Roles", value=roles)

    await ctx.send(embed=embed)

@bot.command()
async def help_staff(ctx):

    embed = discord.Embed(title="📘 HELP STAFF", color=discord.Color.blurple())

    embed.add_field(name="Tickets", value="+add +deluser +rename +close")
    embed.add_field(name="Modération", value="+warn +ban +unban +mute +tempmute +unmute")
    embed.add_field(name="Ranks", value="+rank_t +rank_c +rank_plus +rank_s +rank_admin +derank")
    embed.add_field(name="Infos", value="+serverinfo +staffinfo +ping")

    await ctx.send(embed=embed)

# =========================
# PANEL TICKET FIX FINAL
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

        await channel.send(embed=embed, view=TicketView())

    bot.add_view(TicketView())

# =========================
# RUN
# =========================

bot.run(TOKEN)
