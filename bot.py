# ==================================================
# IMPORTS
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
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="+", intents=intents)

# ==================================================
# SANCTIONS SAVE
# ==================================================
SANCTIONS_FILE = "sanctions.json"

def load_sanctions():
    if os.path.exists(SANCTIONS_FILE):
        with open(SANCTIONS_FILE, "r") as f:
            data = json.load(f)
            return defaultdict(list, {int(k): v for k, v in data.items()})
    return defaultdict(list)

sanctions = load_sanctions()

def save_sanctions():
    with open(SANCTIONS_FILE, "w") as f:
        json.dump(dict(sanctions), f, indent=4)

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
# TICKETS IDS
# ==================================================
CATEGORY_TICKETS = 1504792916772786298
FORM_CHANNEL_ID = 1504792913249570937
ARCHIVES_CHANNEL = 1507694850282094683
LOGS_CATEGORY = 1507737677062213732

# ==================================================
# STATS
# ==================================================
staff_stats = defaultdict(lambda: {
    "warns": 0,
    "mutes": 0,
    "clears": 0,
    "bans": 0
})

# ==================================================
# ACTIVE TICKETS
# ==================================================
active_tickets = defaultdict(int)

# ==================================================
# READY
# ==================================================
@bot.event
async def on_ready():

    print(f"{bot.user} connecté ✅")

    channel = bot.get_channel(FORM_CHANNEL_ID)

    if channel:

        embed = discord.Embed(
            title="📢 Candidatures Staff",
            description=(
                "👮 Les candidatures staff sont ouvertes.\n\n"
                "Clique sur le bouton ci-dessous pour ouvrir "
                "ta candidature.\n\n"
                "📌 Géré uniquement par le rôle Gérant Staff."
            ),
            color=discord.Color.purple()
        )

        view = TicketView()

        await channel.send(
            embed=embed,
            view=view
        )

# ==================================================
# LOG SYSTEM
# ==================================================
async def send_log(guild, title, desc, color=discord.Color.red()):

    channel = guild.get_channel(LOG_CHANNEL_ID)

    if not channel:
        return

    embed = discord.Embed(
        title=title,
        description=desc,
        color=color,
        timestamp=datetime.utcnow()
    )

    embed.set_footer(text=f"{guild.name} • Logs Staff")

    await channel.send(embed=embed)

# ==================================================
# REMOVE STAFF ROLES
# ==================================================
async def remove_all_staff_roles(member):

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
        label="🎫 Ouvrir candidature",
        style=discord.ButtonStyle.green
    )
    async def open_ticket(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        user = interaction.user

        if active_tickets[user.id] >= 2:

            return await interaction.response.send_message(
                "❌ Tu as déjà 2 candidatures ouvertes.",
                ephemeral=True
            )

        guild = interaction.guild

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

        category = guild.get_channel(
            CATEGORY_TICKETS
        )

        channel = await guild.create_text_channel(
            name=f"candidature-{user.name}",
            category=category,
            overwrites=overwrites
        )

        active_tickets[user.id] += 1

        embed = discord.Embed(
            title="👋 Candidature Staff",
            description=(
                "Merci de remplir votre candidature.\n\n"
                "👮 Le staff va bientôt traiter votre demande."
            ),
            color=discord.Color.blue()
        )

        await channel.send(
            content=f"<@&{ROLE_GERANT_STAFF}>",
            embed=embed
        )

        await interaction.response.send_message(
            f"✅ Ticket créé : {channel.mention}",
            ephemeral=True
        )

# ==================================================
# PING
# ==================================================
@bot.command()
async def ping(ctx):

    embed = discord.Embed(
        title="🏓 Pong !",
        description=f"👤 {ctx.author.mention}",
        color=discord.Color.green()
    )

    await ctx.send(embed=embed)

# ==================================================
# WARN
# ==================================================
@bot.command()
@commands.has_permissions(manage_messages=True)
async def warn(ctx, member: discord.Member, *, reason="Aucune raison"):

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

    try:

        await member.send(
            f"""
⚠️ Vous avez été warn sur {ctx.guild.name}

👮 Staff : {ctx.author}
📌 Raison : {reason}

📩 Contact : theo_msc
"""
        )

    except:
        pass

# ==================================================
# SANCTIONS
# ==================================================
@bot.command(name="sanctions")
async def sanctions_cmd(ctx, member: discord.Member):

    user_sanctions = sanctions.get(member.id)

    if not user_sanctions:

        embed = discord.Embed(
            title="✅ Aucune sanction",
            description=f"{member.mention} n'a aucune sanction.",
            color=discord.Color.green()
        )

        return await ctx.send(embed=embed)

    msg = "\n".join(
        [f"{i+1}. {s}" for i, s in enumerate(user_sanctions)]
    )

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
async def clear_sanctions(ctx, member: discord.Member):

    sanctions[member.id] = []
    save_sanctions()

    embed = discord.Embed(
        title="🧹 Sanctions supprimées",
        description=(
            f"Les sanctions de {member.mention} "
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

    await ctx.channel.purge(limit=amount + 1)

    embed = discord.Embed(
        title="🧹 Clear effectué",
        description=(
            f"👮 Staff : {ctx.author.mention}\n"
            f"📌 Messages supprimés : {amount}"
        ),
        color=discord.Color.red()
    )

    msg = await ctx.send(embed=embed)

    await asyncio.sleep(5)
    await msg.delete()

# ==================================================
# MUTE
# ==================================================
@bot.command()
@commands.has_permissions(manage_roles=True)
async def mute(ctx, member: discord.Member):

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
async def unmute(ctx, member: discord.Member):

    role = discord.utils.get(
        ctx.guild.roles,
        name="Muted"
    )

    if role and role in member.roles:
        await member.remove_roles(role)

    embed = discord.Embed(
        title="🔊 Unmute effectué",
        description=f"{member.mention} peut reparler.",
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

    if role and role in member.roles:
        await member.remove_roles(role)

# ==================================================
# STAFFSTATS
# ==================================================
@bot.command()
async def staffstats(
    ctx,
    member: discord.Member = None
):

    if member is None:
        member = ctx.author

    stats = staff_stats[member.id]

    embed = discord.Embed(
        title=f"📊 Stats de {member}",
        color=discord.Color.purple()
    )

    embed.add_field(
        name="⚠️ Warns",
        value=stats["warns"]
    )

    embed.add_field(
        name="🔇 Mutes",
        value=stats["mutes"]
    )

    embed.add_field(
        name="🧹 Clears",
        value=stats["clears"]
    )

    embed.add_field(
        name="🔨 Bans",
        value=stats["bans"]
    )

    await ctx.send(embed=embed)

# ==================================================
# USERINFO
# ==================================================
@bot.command()
async def userinfo(
    ctx,
    member: discord.Member = None
):

    if member is None:
        member = ctx.author

    roles = [
        role.mention
        for role in member.roles
        if role.name != "@everyone"
    ]

    embed = discord.Embed(
        title=f"👤 Infos de {member}",
        color=discord.Color.blue()
    )

    embed.set_thumbnail(
        url=member.display_avatar.url
    )

    embed.add_field(
        name="🆔 ID",
        value=member.id,
        inline=False
    )

    embed.add_field(
        name="🎭 Rôles",
        value=", ".join(roles),
        inline=False
    )

    await ctx.send(embed=embed)

# ==================================================
# SERVERINFO
# ==================================================
@bot.command()
async def serverinfo(ctx):

    guild = ctx.guild

    embed = discord.Embed(
        title="🌍 Infos Serveur",
        color=discord.Color.blue()
    )

    embed.add_field(
        name="👥 Membres",
        value=guild.member_count
    )

    embed.add_field(
        name="💬 Salons",
        value=len(guild.channels)
    )

    embed.add_field(
        name="🚀 Boosts",
        value=guild.premium_subscription_count
    )

    await ctx.send(embed=embed)

# ==================================================
# RANK SYSTEM
# ==================================================
async def rank_member(
    ctx,
    member,
    role_id,
    role_name
):

    await remove_all_staff_roles(member)

    role = ctx.guild.get_role(role_id)

    if role:
        await member.add_roles(role)

    staff_role = ctx.guild.get_role(ROLE_STAFF)

    if staff_role:
        await member.add_roles(staff_role)

    embed = discord.Embed(
        title="📌 Promotion Staff",
        description=(
            f"👤 Membre : {member.mention}\n"
            f"🏆 Nouveau grade : {role_name}\n"
            f"👮 Par : {ctx.author.mention}"
        ),
        color=discord.Color.blue()
    )

    await ctx.send(embed=embed)

@bot.command(name="rank-t")
async def rank_t(ctx, member: discord.Member):
    await rank_member(ctx, member, ROLE_T, "Modo Test")

@bot.command(name="rank-c")
async def rank_c(ctx, member: discord.Member):
    await rank_member(ctx, member, ROLE_C, "Modo Confirmé")

@bot.command(name="rank-plus")
async def rank_plus(ctx, member: discord.Member):
    await rank_member(ctx, member, ROLE_PLUS, "Modo +")

@bot.command(name="rank-s")
async def rank_s(ctx, member: discord.Member):
    await rank_member(ctx, member, ROLE_SENIOR, "Modo Senior")

@bot.command(name="rank-admin")
async def rank_admin(ctx, member: discord.Member):
    await rank_member(ctx, member, ROLE_ADMIN, "Admin")

# ==================================================
# DERANK
# ==================================================
@bot.command()
async def derank(ctx, member: discord.Member):

    await remove_all_staff_roles(member)

    staff_role = ctx.guild.get_role(
        ROLE_STAFF
    )

    if staff_role and staff_role in member.roles:
        await member.remove_roles(staff_role)

    embed = discord.Embed(
        title="⬇️ Derank effectué",
        description=f"{member.mention} a été derank.",
        color=discord.Color.red()
    )

    await ctx.send(embed=embed)

# ==================================================
# ADD USER
# ==================================================
@bot.command()
async def add(ctx, member: discord.Member):

    await ctx.channel.set_permissions(
        member,
        view_channel=True,
        send_messages=True
    )

    await ctx.send(
        f"➕ {member.mention} ajouté au ticket"
    )

# ==================================================
# DEL USER
# ==================================================
@bot.command(name="del")
async def deluser(ctx, member: discord.Member):

    await ctx.channel.set_permissions(
        member,
        overwrite=None
    )

    await ctx.send(
        f"➖ {member.mention} retiré du ticket"
    )

# ==================================================
# RENAME
# ==================================================
@bot.command()
async def rename(ctx, *, name):

    await ctx.channel.edit(name=name)

    await ctx.send(
        f"✏️ Ticket renommé en {name}"
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
            "❌ Temps écoulé"
        )

    if reply.content == "1":

        status = "✅ ACCEPTÉE"

        dm_message = (
            "🎉 Bonjour,\n\n"
            "Votre candidature staff a été ACCEPTÉE.\n\n"
            "Bienvenue dans le staff !! 👮✨\n\n"
            f"👮 Gérée par : {ctx.author}"
        )

    elif reply.content == "2":

        status = "❌ REFUSÉE"

        dm_message = (
            "📋 Bonjour,\n\n"
            "Votre candidature staff a été REFUSÉE.\n\n"
            "Merci quand même d'avoir tenté votre chance ❤️\n\n"
            f"👮 Gérée par : {ctx.author}"
        )

    else:

        return await ctx.send(
            "❌ Choix invalide"
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
            f"👮 Staff responsable : "
            f"{ctx.author.mention}\n\n"

            f"💬 Message envoyé au candidat :\n"

            f"“{'Bienvenue dans le staff !! 👮✨' if reply.content == '1' else 'Merci quand même d’avoir tenté votre chance ❤️'}”\n\n"

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
        category=category,
        sync_permissions=True
    )

    await ctx.send(
        "📂 Ticket déplacé dans recrutements logs"
    )

# ==================================================
# HELP STAFF
# ==================================================
@bot.command()
async def helpstaff(ctx):

    embed = discord.Embed(
        title="👮 Commandes Staff",
        description=(
            "⚠️ +warn\n"
            "📋 +sanctions\n"
            "🧹 +clear_sanctions\n"
            "🧹 +clear\n"
            "🔇 +mute\n"
            "🔊 +unmute\n"
            "⏳ +tempmute\n"
            "📊 +staffstats\n"
            "👤 +userinfo\n"
            "🌍 +serverinfo\n"
            "📌 +rank-t\n"
            "📌 +rank-c\n"
            "📌 +rank-plus\n"
            "📌 +rank-s\n"
            "📌 +rank-admin\n"
            "⬇️ +derank\n"
            "➕ +add\n"
            "➖ +del\n"
            "✏️ +rename\n"
            "🔒 +close"
        ),
        color=discord.Color.green()
    )

    await ctx.send(embed=embed)

# ==================================================
# TOKEN
# ==================================================
token = os.getenv("DISCORD_TOKEN")

if token is None:
    print("TOKEN MANQUANT ❌")

bot.run(token)
