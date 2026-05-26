import discord
from discord.ext import commands
import asyncio
import os
import json
import io
from collections import defaultdict
from datetime import datetime

# =========================
# BOT
# =========================

intents = discord.Intents.all()

bot = commands.Bot(
    command_prefix="+",
    intents=intents
)

TOKEN = os.getenv("DISCORD_TOKEN")

# =========================
# IDS
# =========================

LOG_CHANNEL_ID = 1508595464168013965
GERANT_STAFF_ID = 968588191055642624

ROLE_STAFF = 1504792759679057951

ROLE_T = 1504792771977023591
ROLE_C = 1504792768088903931
ROLE_PLUS = 1504792764448116776
ROLE_SENIOR = 1504792759679057951
ROLE_ADMIN = 1504792748098715660

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

async def log(guild, title, desc, color):

    ch = guild.get_channel(LOG_CHANNEL_ID)

    if not ch:
        return

    embed = discord.Embed(
        title=title,
        description=desc,
        color=color,
        timestamp=datetime.utcnow()
    )

    await ch.send(embed=embed)

# =========================
# REMOVE ROLES
# =========================

async def remove_roles(member):

    for r in [ROLE_T, ROLE_C, ROLE_PLUS, ROLE_SENIOR, ROLE_ADMIN]:

        role = member.guild.get_role(r)

        if role in member.roles:

            await member.remove_roles(role)

# =========================
# RANK SYSTEM
# =========================

async def set_rank(ctx, member, role_id, name):

    await remove_roles(member)

    role = ctx.guild.get_role(role_id)

    if role:
        await member.add_roles(role)

    staff = ctx.guild.get_role(ROLE_STAFF)

    if staff:
        await member.add_roles(staff)

    await ctx.send(f"📌 {member.mention} → **{name}**")

    try:
        await member.send(f"📌 Tu es maintenant **{name}** sur {ctx.guild.name}")
    except:
        pass

# =========================
# TICKETS
# =========================

class Ticket(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🎫 Ouvrir candidature", style=discord.ButtonStyle.green)
    async def open(self, interaction, button):

        user = interaction.user
        guild = interaction.guild

        cat = guild.get_channel(TICKET_CAT)

        overwrites = {

            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            guild.get_role(ROLE_STAFF): discord.PermissionOverwrite(view_channel=True)
        }

        ch = await guild.create_text_channel(
            name=f"candidature-{user.name}",
            category=cat,
            overwrites=overwrites
        )

        await ch.send(f"<@&{ROLE_STAFF}>")

        await interaction.response.send_message(
            f"Ticket créé : {ch.mention}",
            ephemeral=True
        )

# =========================
# READY
# =========================

@bot.event
async def on_ready():

    print("BOT ONLINE")

    bot.add_view(Ticket())

    ch = bot.get_channel(TICKET_PANEL)

    if ch:

        await ch.send(
            embed=discord.Embed(
                title="📢 Candidatures Staff",
                description="Clique pour ouvrir une candidature",
                color=discord.Color.purple()
            ),
            view=Ticket()
        )

# =========================
# CLEAR
# =========================

@bot.command()
async def clear(ctx, amount: int):

    await ctx.channel.purge(limit=amount + 1)

    await log(
        ctx.guild,
        "CLEAR",
        f"{ctx.author} a supprimé {amount} messages",
        discord.Color.greyple()
    )

    await ctx.send(f"🧹 {amount}", delete_after=5)

# =========================
# ADD
# =========================

@bot.command()
async def add(ctx, member: discord.Member):

    await ctx.channel.set_permissions(
        member,
        view_channel=True,
        send_messages=True,
        read_message_history=True
    )

    await log(ctx.guild, "ADD TICKET", f"{member} ajouté par {ctx.author}", discord.Color.green())

    await ctx.send(f"➕ {member.mention}")

# =========================
# DEL
# =========================

@bot.command(name="del")
async def del_user(ctx, member: discord.Member):

    await ctx.channel.set_permissions(member, overwrite=None)

    await log(ctx.guild, "DEL TICKET", f"{member} retiré par {ctx.author}", discord.Color.red())

    await ctx.send(f"➖ {member.mention}")

# =========================
# RENAME
# =========================

@bot.command()
async def rename(ctx, *, name):

    await ctx.channel.edit(name=name)

    await log(ctx.guild, "RENAME", f"{ctx.author} → {name}", discord.Color.blurple())

    await ctx.send(f"✏️ {name}")

# =========================
# WARN
# =========================

@bot.command()
async def warn(ctx, member: discord.Member, *, reason="Aucune raison"):

    sanctions[member.id].append(reason)
    save()

    await log(ctx.guild, "WARN", f"{member} | {reason}", discord.Color.orange())

    try:
        await member.send(f"⚠️ Warn : {reason}")
    except:
        pass

    await ctx.send(f"⚠️ {member.mention}")

# =========================
# SANCTIONS
# =========================

@bot.command()
async def sanctions(ctx, member: discord.Member):

    data = sanctions.get(member.id, [])

    if not data:
        return await ctx.send("Aucune sanction")

    await ctx.send("\n".join(data))

# =========================
# CLEAR SANCTIONS
# =========================

@bot.command()
async def clear_sanctions(ctx, member: discord.Member):

    sanctions[member.id] = []
    save()

    await ctx.send(f"🧹 sanctions supprimées {member.mention}")

# =========================
# BAN
# =========================

@bot.command()
async def ban(ctx, member: discord.Member, *, reason="Aucune raison"):

    try:
        await member.send(f"🔨 Ban : {reason}")
    except:
        pass

    await member.ban(reason=reason)

    await log(ctx.guild, "BAN", f"{member} | {reason}", discord.Color.red())

    await ctx.send(f"🔨 {member}")

# =========================
# UNBAN
# =========================

@bot.command()
async def unban(ctx, user_id: int):

    user = await bot.fetch_user(user_id)

    await ctx.guild.unban(user)

    await log(ctx.guild, "UNBAN", f"{user}", discord.Color.green())

    await ctx.send(f"♻️ {user}")

# =========================
# MUTE
# =========================

@bot.command()
async def mute(ctx, member: discord.Member):

    role = discord.utils.get(ctx.guild.roles, name="Muted")

    if not role:
        role = await ctx.guild.create_role(name="Muted")

    await member.add_roles(role)

    await log(ctx.guild, "MUTE", f"{member}", discord.Color.dark_grey())

    try:
        await member.send(f"🔇 mute sur {ctx.guild.name}")
    except:
        pass

    await ctx.send(f"🔇 {member.mention}")

# =========================
# TEMPMUTE (FIX + LOG)
# =========================

@bot.command()
async def tempmute(ctx, member: discord.Member, time: int):

    role = discord.utils.get(ctx.guild.roles, name="Muted")

    if not role:
        role = await ctx.guild.create_role(name="Muted")

    await member.add_roles(role)

    await log(
        ctx.guild,
        "TEMPMUTE",
        f"{member} | {time}s | par {ctx.author}",
        discord.Color.blurple()
    )

    try:
        await member.send(f"⏳ tempmute {time}s")
    except:
        pass

    await ctx.send(f"⏳ {member.mention} {time}s")

    await asyncio.sleep(time)

    await member.remove_roles(role)

# =========================
# RANKS
# =========================

@bot.command()
async def modotest(ctx, member: discord.Member):
    await set_rank(ctx, member, ROLE_T, "Modo Test")

@bot.command()
async def modoc(ctx, member: discord.Member):
    await set_rank(ctx, member, ROLE_C, "Modo Confirmé")

@bot.command()
async def modoplus(ctx, member: discord.Member):
    await set_rank(ctx, member, ROLE_PLUS, "Modo +")

@bot.command()
async def senior(ctx, member: discord.Member):
    await set_rank(ctx, member, ROLE_SENIOR, "Senior")

@bot.command()
async def admin(ctx, member: discord.Member):
    await set_rank(ctx, member, ROLE_ADMIN, "Admin")

# =========================
# DERANK
# =========================

@bot.command()
async def derank(ctx, member: discord.Member):

    await remove_roles(member)

    staff = ctx.guild.get_role(ROLE_STAFF)

    if staff in member.roles:
        await member.remove_roles(staff)

    await ctx.send(f"⬇️ {member.mention}")

# =========================
# CLOSE TICKET
# =========================

@bot.command()
async def close(ctx):

    await ctx.send("1️⃣ Accepté / 2️⃣ Refusé")

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    msg = await bot.wait_for("message", check=check)

    if msg.content == "1":
        status = "ACCEPTÉ"
        dm = "Bienvenue dans le staff !!"
    else:
        status = "REFUSÉ"
        dm = "Refusé"

    try:
        await ctx.author.send(dm)
    except:
        pass

    try:
        g = await bot.fetch_user(GERANT_STAFF_ID)
        await g.send(f"📋 {status} | {ctx.author}")
    except:
        pass

    text = ""

    async for m in ctx.channel.history(limit=200):
        text += f"{m.author}: {m.content}\n"

    file = discord.File(io.BytesIO(text.encode()), "ticket.txt")

    logch = bot.get_channel(ARCHIVE)

    await logch.send(f"📋 {status}", file=file)

    await ctx.channel.delete()

# =========================
# RUN
# =========================

bot.run(TOKEN)
