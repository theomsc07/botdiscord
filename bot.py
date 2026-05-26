# ==================================================
# BOT STAFF COMPLET
# Theo - Créateur du bot
# ==================================================

import discord
from discord.ext import commands
import asyncio
import os
import json
from collections import defaultdict
from datetime import datetime

# ==================================================
# INTENTS
# ==================================================

intents = discord.Intents.all()

bot = commands.Bot(
    command_prefix="+",
    intents=intents
)

# ==================================================
# TOKEN
# ==================================================

TOKEN = os.getenv("DISCORD_TOKEN")

# ==================================================
# SAVE SANCTIONS
# ==================================================

SANCTIONS_FILE = "sanctions.json"

def load_sanctions():

    if os.path.exists(SANCTIONS_FILE):

        with open(SANCTIONS_FILE, "r") as f:

            data = json.load(f)

            return defaultdict(
                list,
                {int(k): v for k, v in data.items()}
            )

    return defaultdict(list)

sanctions = load_sanctions()

def save_sanctions():

    with open(SANCTIONS_FILE, "w") as f:

        json.dump(
            dict(sanctions),
            f,
            indent=4
        )

# ==================================================
# IDS
# ==================================================

LOG_CHANNEL_ID = 1508595464168013965

ROLE_GERANT_STAFF = 1504792751777255545
ROLE_STAFF = 1504810257715822722

ROLE_T = 1504792771977023591
ROLE_C = 1504792768088903931
ROLE_PLUS = 1504792764448116776
ROLE_SENIOR = 1504792759679057951
ROLE_ADMIN = 1504792748098715660

# ==================================================
# TICKETS
# ==================================================

TICKET_PANEL_CHANNEL = 1504792916772786298
TICKET_CATEGORY = 1504792910892109935
ARCHIVES_CHANNEL = 1507694850282094683
LOGS_CATEGORY = 1507737677062213732

# ==================================================
# ACTIVE TICKETS
# ==================================================

active_tickets = defaultdict(int)

# ==================================================
# STAFF STATS
# ==================================================

staff_stats = defaultdict(lambda: {

    "warns": 0,
    "mutes": 0,
    "clears": 0,
    "bans": 0
})

# ==================================================
# LOGS
# ==================================================

async def send_log(

    guild,
    title,
    description,
    color=discord.Color.red()

):

    channel = guild.get_channel(
        LOG_CHANNEL_ID
    )

    if not channel:
        return

    embed = discord.Embed(

        title=title,
        description=description,
        color=color,
        timestamp=datetime.utcnow()
    )

    await channel.send(embed=embed)

# ==================================================
# REMOVE STAFF ROLES
# ==================================================

async def remove_staff_roles(member):

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

# ==================================================
# TICKET VIEW
# ==================================================

class TicketView(discord.ui.View):

    def __init__(self):

        super().__init__(timeout=None)

    @discord.ui.button(

        label="🎫 Ouvrir une candidature",
        style=discord.ButtonStyle.green,
        custom_id="open_ticket_button"
    )

    async def open_ticket(

        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        user = interaction.user
        guild = interaction.guild

        if active_tickets[user.id] >= 2:

            return await interaction.response.send_message(

                "❌ Tu as déjà 2 candidatures ouvertes.",

                ephemeral=True
            )

        category = guild.get_channel(
            TICKET_CATEGORY
        )

        overwrites = {

            guild.default_role:
                discord.PermissionOverwrite(
                    view_channel=False
                ),

            user:
                discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True
                ),

            guild.get_role(
                ROLE_GERANT_STAFF
            ):
                discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True
                )
        }

        ticket = await guild.create_text_channel(

            name=f"candidature-{user.name}",

            category=category,

            overwrites=overwrites
        )

        active_tickets[user.id] += 1

        embed = discord.Embed(

            title="👋 Candidature Staff",

            description=(
                "Merci d'avoir ouvert une candidature.\n\n"
                "📝 Merci de remplir correctement votre candidature.\n\n"
                "👮 Le rôle Gérant Staff a été prévenu."
            ),

            color=discord.Color.blurple()
        )

        await ticket.send(

            content=f"<@&{ROLE_GERANT_STAFF}>",

            embed=embed
        )

        await interaction.response.send_message(

            f"✅ Ticket créé : {ticket.mention}",

            ephemeral=True
        )

# ==================================================
# READY
# ==================================================

@bot.event
async def on_ready():

    print(f"{bot.user} connecté ✅")

    bot.add_view(TicketView())

    channel = bot.get_channel(
        TICKET_PANEL_CHANNEL
    )

    if channel:

        embed = discord.Embed(

            title="📢 Candidatures Staff",

            description=(
                "👮 Les candidatures staff sont ouvertes.\n\n"
                "Clique sur le bouton ci-dessous "
                "pour ouvrir une candidature.\n\n"
                "📌 Géré uniquement par le rôle Gérant Staff."
            ),

            color=discord.Color.purple()
        )

        await channel.send(

            embed=embed,
            view=TicketView()
        )

# ==================================================
# PING
# ==================================================

@bot.command()
async def ping(ctx):

    embed = discord.Embed(

        title="🏓 Pong",

        description=(
            f"👤 {ctx.author.mention}\n"
            f"📡 {round(bot.latency * 1000)}ms"
        ),

        color=discord.Color.green()
    )

    await ctx.send(embed=embed)

# ==================================================
# WARN
# ==================================================

@bot.command()
@commands.has_permissions(manage_messages=True)

async def warn(

    ctx,
    member: discord.Member,
    *,
    reason="Aucune raison"
):

    sanctions[member.id].append(reason)

    save_sanctions()

    staff_stats[ctx.author.id]["warns"] += 1

    embed = discord.Embed(

        title="⚠️ Warn effectué",

        description=(
            f"👤 Membre : {member.mention}\n"
            f"👮 Staff : {ctx.author.mention}\n"
            f"📌 Raison : {reason}"
        ),

        color=discord.Color.orange()
    )

    await ctx.send(embed=embed)

    await send_log(

        ctx.guild,

        "⚠️ WARN",

        (
            f"👤 Membre : {member.mention}\n"
            f"👮 Staff : {ctx.author.mention}\n"
            f"📌 Raison : {reason}"
        ),

        discord.Color.orange()
    )

# ==================================================
# SANCTIONS
# ==================================================

@bot.command(name="sanctions")

async def sanctions_cmd(

    ctx,
    member: discord.Member
):

    user_sanctions = sanctions.get(member.id)

    if not user_sanctions:

        embed = discord.Embed(

            title="✅ Aucune sanction",

            description=(
                f"{member.mention} "
                "n'a aucune sanction."
            ),

            color=discord.Color.green()
        )

        return await ctx.send(embed=embed)

    msg = "\n".join([

        f"{i+1}. {s}"

        for i, s in enumerate(user_sanctions)
    ])

    embed = discord.Embed(

        title=f"📋 Sanctions de {member}",

        description=msg,

        color=discord.Color.orange()
    )

    await ctx.send(embed=embed)

# ==================================================
# CLEAR SANCTIONS
# ==================================================

@bot.command()
@commands.has_permissions(administrator=True)

async def clear_sanctions(

    ctx,
    member: discord.Member
):

    sanctions[member.id] = []

    save_sanctions()

    embed = discord.Embed(

        title="🧹 Sanctions supprimées",

        description=(
            f"Les sanctions de "
            f"{member.mention} "
            f"ont été supprimées."
        ),

        color=discord.Color.green()
    )

    await ctx.send(embed=embed)

# ==================================================
# CLEAR
# ==================================================

@bot.command()
@commands.has_permissions(manage_messages=True)

async def clear(ctx, amount: int):

    await ctx.channel.purge(
        limit=amount + 1
    )

    staff_stats[ctx.author.id]["clears"] += 1

    msg = await ctx.send(
        f"🧹 {amount} messages supprimés."
    )

    await asyncio.sleep(5)

    await msg.delete()

# ==================================================
# MUTE
# ==================================================

@bot.command()
@commands.has_permissions(manage_roles=True)

async def mute(

    ctx,
    member: discord.Member
):

    role = discord.utils.get(

        ctx.guild.roles,

        name="Muted"
    )

    if not role:

        role = await ctx.guild.create_role(
            name="Muted"
        )

        for channel in ctx.guild.channels:

            await channel.set_permissions(

                role,

                send_messages=False,

                speak=False
            )

    await member.add_roles(role)

    staff_stats[ctx.author.id]["mutes"] += 1

    embed = discord.Embed(

        title="🔇 Mute effectué",

        description=(
            f"👤 Membre : {member.mention}\n"
            f"👮 Staff : {ctx.author.mention}"
        ),

        color=discord.Color.red()
    )

    await ctx.send(embed=embed)

# ==================================================
# UNMUTE
# ==================================================

@bot.command()
@commands.has_permissions(manage_roles=True)

async def unmute(

    ctx,
    member: discord.Member
):

    role = discord.utils.get(

        ctx.guild.roles,

        name="Muted"
    )

    if role and role in member.roles:

        await member.remove_roles(role)

    embed = discord.Embed(

        title="🔊 Unmute effectué",

        description=f"{member.mention} a été unmute.",

        color=discord.Color.green()
    )

    await ctx.send(embed=embed)

# ==================================================
# TEMPMUTE
# ==================================================

@bot.command()
@commands.has_permissions(manage_roles=True)

async def tempmute(

    ctx,
    member: discord.Member,
    time: int
):

    role = discord.utils.get(

        ctx.guild.roles,

        name="Muted"
    )

    if not role:

        role = await ctx.guild.create_role(
            name="Muted"
        )

        for channel in ctx.guild.channels:

            await channel.set_permissions(

                role,

                send_messages=False,

                speak=False
            )

    await member.add_roles(role)

    embed = discord.Embed(

        title="⏳ TempMute effectué",

        description=(
            f"👤 Membre : {member.mention}\n"
            f"⏱️ Temps : {time} secondes\n"
            f"👮 Staff : {ctx.author.mention}"
        ),

        color=discord.Color.orange()
    )

    await ctx.send(embed=embed)

    await asyncio.sleep(time)

    if role in member.roles:

        await member.remove_roles(role)

# ==================================================
# ADD USER
# ==================================================

@bot.command()

async def add(

    ctx,
    member: discord.Member
):

    await ctx.channel.set_permissions(

        member,

        view_channel=True,

        send_messages=True
    )

    await ctx.send(
        f"➕ {member.mention} ajouté au ticket."
    )

# ==================================================
# DEL USER
# ==================================================

@bot.command(name="del")

async def del_user(

    ctx,
    member: discord.Member
):

    await ctx.channel.set_permissions(

        member,

        overwrite=None
    )

    await ctx.send(
        f"➖ {member.mention} retiré du ticket."
    )

# ==================================================
# RENAME
# ==================================================

@bot.command()

async def rename(

    ctx,
    *,
    name
):

    await ctx.channel.edit(name=name)

    await ctx.send(
        f"✏️ Ticket renommé en : {name}"
    )

# ==================================================
# CLOSE
# ==================================================

@bot.command()

async def close(ctx):

    def check(m):

        return (

            m.author == ctx.author

            and m.channel == ctx.channel
        )

    await ctx.send(

        "📋 La candidature est-elle :\n\n"

        "1️⃣ Acceptée\n"

        "2️⃣ Refusée\n\n"

        "Réponds avec 1 ou 2"
    )

    try:

        reply = await bot.wait_for(

            "message",

            timeout=60,

            check=check
        )

    except:

        return await ctx.send(
            "❌ Temps écoulé."
        )

    if reply.content == "1":

        status = "✅ ACCEPTÉE"

        dm_message = (
            "🎉 Bonjour,\n\n"
            "Votre candidature staff "
            "a été ACCEPTÉE.\n\n"
            "Bienvenue dans le staff !! 👮✨"
        )

    elif reply.content == "2":

        status = "❌ REFUSÉE"

        dm_message = (
            "📋 Bonjour,\n\n"
            "Votre candidature staff "
            "a été REFUSÉE.\n\n"
            "Merci quand même "
            "d'avoir tenté votre chance ❤️"
        )

    else:

        return await ctx.send(
            "❌ Choix invalide."
        )

    user = None

    for member in ctx.channel.members:

        if member.bot:
            continue

        if ROLE_GERANT_STAFF in [
            r.id for r in member.roles
        ]:
            continue

        user = member
        break

    if user:

        try:
            await user.send(dm_message)
        except:
            pass

    archive = bot.get_channel(
        ARCHIVES_CHANNEL
    )

    embed = discord.Embed(

        title="📋 Candidature fermée",

        description=(
            f"👤 Candidat : "
            f"{user.mention if user else 'Inconnu'}\n\n"

            f"📌 Statut : {status}\n"

            f"👮 Staff : "
            f"{ctx.author.mention}\n\n"

            f"🕒 Date : {datetime.utcnow()}"
        ),

        color=discord.Color.orange()
    )

    if archive:

        await archive.send(embed=embed)

    category = bot.get_channel(
        LOGS_CATEGORY
    )

    await ctx.channel.edit(
        category=category
    )

    await ctx.send(
        "📂 Ticket déplacé dans recrutements logs."
    )

# ==================================================
# RUN
# ==================================================

bot.run(TOKEN)
