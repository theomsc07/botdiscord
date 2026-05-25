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
# SAVE SANCTIONS
# ==================================================
SANCTIONS_FILE = "sanctions.json"

def load_sanctions():
    if os.path.exists(SANCTIONS_FILE):
        with open(SANCTIONS_FILE, "r") as f:
            data = json.load(f)
            return defaultdict(list, {int(k): v for k, v in data.items()})
    return defaultdict(list)

def save_sanctions():
    with open(SANCTIONS_FILE, "w") as f:
        json.dump(dict(sanctions), f, indent=4)

sanctions = load_sanctions()

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
# IDS
# ==================================================
LOG_CHANNEL_ID = 1508595464168013965

ROLE_STAFF = 1504810257715822722

ROLE_T = 1504792771977023591
ROLE_C = 1504792768088903931
ROLE_PLUS = 1504792764448116776
ROLE_SENIOR = 1504792759679057951
ROLE_ADMIN = 1504792748098715660

# ==================================================
# READY
# ==================================================
@bot.event
async def on_ready():
    print(f"{bot.user} connecté ✅")

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
        title="⚠️・Warn effectué",
        description=(
            f"👤 **Membre :** {member.mention}\n"
            f"👮 **Staff :** {ctx.author.mention}\n"
            f"📌 **Raison :** {reason}"
        ),
        color=discord.Color.orange()
    )

    await ctx.send(embed=embed)

    try:
        await member.send(
            f"""
⚠️ Vous avez été warn sur le serveur : {ctx.guild.name}

👮 Staff : {ctx.author}
📌 Raison : {reason}

Si vous pensez que c'est une erreur, merci de venir en MP avec : theo_msc
"""
        )
    except:
        pass

    await send_log(
        ctx.guild,
        "⚠️ WARN",
        f"""
👮 Staff : {ctx.author.mention}
👤 Membre : {member.mention}
📌 Raison : {reason}
📍 Salon : {ctx.channel.mention}
"""
    )

# ==================================================
# SANCTIONS
# ==================================================
@bot.command(name="sanctions")
async def sanctions_cmd(ctx, member: discord.Member):

    user_sanctions = sanctions.get(member.id)

    if not user_sanctions:

        embed = discord.Embed(
            title="✅ Aucune sanction",
            description=f"{member.mention} n'a aucune sanction",
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
        description=f"Les sanctions de {member.mention} ont été supprimées",
        color=discord.Color.green()
    )

    await ctx.send(embed=embed)

# ==================================================
# CLEAR
# ==================================================
@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int):

    if amount >= 50:

        confirm = await ctx.send(
            f"⚠️ {ctx.author.mention} confirme le clear avec ✅"
        )

        await confirm.add_reaction("✅")

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) == "✅"

        try:
            await bot.wait_for("reaction_add", timeout=15, check=check)
        except:
            return await ctx.send("❌ Clear annulé")

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

    await send_log(
        ctx.guild,
        "🧹 CLEAR",
        f"""
👮 Staff : {ctx.author.mention}
📌 Nombre : {amount}
📍 Salon : {ctx.channel.mention}
"""
    )

    await asyncio.sleep(5)
    await msg.delete()

# ==================================================
# MUTE
# ==================================================
@bot.command()
@commands.has_permissions(manage_roles=True)
async def mute(ctx, member: discord.Member):

    role = discord.utils.get(ctx.guild.roles, name="Muted")

    if not role:

        role = await ctx.guild.create_role(name="Muted")

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
            f"👤 **Membre :** {member.mention}\n"
            f"👮 **Staff :** {ctx.author.mention}"
        ),
        color=discord.Color.red()
    )

    await ctx.send(embed=embed)

    try:
        await member.send(
            f"""
🔇 Vous avez été mute sur le serveur : {ctx.guild.name}

👮 Staff : {ctx.author}

Si vous pensez que c'est une erreur, merci de venir en MP avec : theo_msc
"""
        )
    except:
        pass

# ==================================================
# UNMUTE
# ==================================================
@bot.command()
@commands.has_permissions(manage_roles=True)
async def unmute(ctx, member: discord.Member):

    role = discord.utils.get(ctx.guild.roles, name="Muted")

    if role and role in member.roles:
        await member.remove_roles(role)

    embed = discord.Embed(
        title="🔊 Unmute effectué",
        description=f"{member.mention} peut reparler",
        color=discord.Color.green()
    )

    await ctx.send(embed=embed)

# ==================================================
# TEMPMUTE
# ==================================================
@bot.command()
@commands.has_permissions(manage_roles=True)
async def tempmute(ctx, member: discord.Member, time: int):

    role = discord.utils.get(ctx.guild.roles, name="Muted")

    if not role:

        role = await ctx.guild.create_role(name="Muted")

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
            f"👤 **Membre :** {member.mention}\n"
            f"⏱️ **Temps :** {time} secondes\n"
            f"👮 **Staff :** {ctx.author.mention}"
        ),
        color=discord.Color.orange()
    )

    await ctx.send(embed=embed)

    try:
        await member.send(
            f"""
⏳ Vous avez été tempmute sur le serveur : {ctx.guild.name}

👮 Staff : {ctx.author}
⏱️ Temps : {time} secondes

Si vous pensez que c'est une erreur, merci de venir en MP avec : theo_msc
"""
        )
    except:
        pass

    await asyncio.sleep(time)

    if role and role in member.roles:
        await member.remove_roles(role)

# ==================================================
# USERINFO
# ==================================================
@bot.command()
async def userinfo(ctx, member: discord.Member = None):

    if member is None:
        member = ctx.author

    roles = [role.mention for role in member.roles if role.name != "@everyone"]

    embed = discord.Embed(
        title=f"👤 Infos de {member}",
        color=discord.Color.blue()
    )

    embed.set_thumbnail(url=member.display_avatar.url)

    embed.add_field(name="🆔 ID", value=member.id, inline=False)
    embed.add_field(name="📅 Création", value=member.created_at.strftime("%d/%m/%Y"), inline=False)
    embed.add_field(name="📥 Arrivée", value=member.joined_at.strftime("%d/%m/%Y"), inline=False)
    embed.add_field(name="🎭 Rôles", value=", ".join(roles) if roles else "Aucun", inline=False)

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

    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)

    embed.add_field(name="👑 Owner", value=guild.owner.mention, inline=False)
    embed.add_field(name="👥 Membres", value=guild.member_count, inline=False)
    embed.add_field(name="💬 Salons", value=len(guild.channels), inline=False)
    embed.add_field(name="🚀 Boosts", value=guild.premium_subscription_count, inline=False)

    await ctx.send(embed=embed)

# ==================================================
# STAFFSTATS
# ==================================================
@bot.command()
async def staffstats(ctx, member: discord.Member = None):

    if member is None:
        member = ctx.author

    stats = staff_stats[member.id]

    embed = discord.Embed(
        title=f"📊 Stats de {member}",
        color=discord.Color.purple()
    )

    embed.add_field(name="⚠️ Warns", value=stats["warns"])
    embed.add_field(name="🔇 Mutes", value=stats["mutes"])
    embed.add_field(name="🧹 Clears", value=stats["clears"])
    embed.add_field(name="🔨 Bans", value=stats["bans"])

    await ctx.send(embed=embed)

# ==================================================
# RANK FUNCTION
# ==================================================
async def rank_member(ctx, member, role_id, role_name):

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
            f"👤 **Membre :** {member.mention}\n"
            f"🏆 **Nouveau grade :** {role_name}\n"
            f"👮 **Par :** {ctx.author.mention}"
        ),
        color=discord.Color.blue()
    )

    await ctx.send(embed=embed)

# ==================================================
# RANKS
# ==================================================
@bot.command(name="rank-t")
@commands.has_permissions(administrator=True)
async def rank_t(ctx, member: discord.Member):
    await rank_member(ctx, member, ROLE_T, "Modo Test")

@bot.command(name="rank-c")
@commands.has_permissions(administrator=True)
async def rank_c(ctx, member: discord.Member):
    await rank_member(ctx, member, ROLE_C, "Modo Confirmé")

@bot.command(name="rank-plus")
@commands.has_permissions(administrator=True)
async def rank_plus(ctx, member: discord.Member):
    await rank_member(ctx, member, ROLE_PLUS, "Modo +")

@bot.command(name="rank-s")
@commands.has_permissions(administrator=True)
async def rank_s(ctx, member: discord.Member):
    await rank_member(ctx, member, ROLE_SENIOR, "Modo Senior")

@bot.command(name="rank-admin")
@commands.has_permissions(administrator=True)
async def rank_admin(ctx, member: discord.Member):
    await rank_member(ctx, member, ROLE_ADMIN, "Admin")

# ==================================================
# DERANK
# ==================================================
@bot.command()
@commands.has_permissions(administrator=True)
async def derank(ctx, member: discord.Member):

    await remove_all_staff_roles(member)

    staff_role = ctx.guild.get_role(ROLE_STAFF)

    if staff_role and staff_role in member.roles:
        await member.remove_roles(staff_role)

    embed = discord.Embed(
        title="⬇️ Derank effectué",
        description=f"{member.mention} a été derank",
        color=discord.Color.red()
    )

    await ctx.send(embed=embed)

# ==================================================
# HELP STAFF
# ==================================================
@bot.command()
async def helpstaff(ctx):

    embed = discord.Embed(
        title="👮 Commandes Staff",
        description="""
⚠️ +warn
📋 +sanctions
🧹 +clear_sanctions
🧹 +clear
🔇 +mute
🔊 +unmute
⏳ +tempmute
📊 +staffstats
👤 +userinfo
🌍 +serverinfo
📌 +rank-t
📌 +rank-c
📌 +rank-plus
📌 +rank-s
📌 +rank-admin
⬇️ +derank
""",
        color=discord.Color.green()
    )

    await ctx.send(embed=embed)

# ==================================================
# TOKEN
# ==================================================
token = os.getenv("DISCORD_TOKEN")

if token is None:
    print("TOKEN MANQUANT ❌")

try:
    bot.run(token)
except Exception as e:
    print(e)
