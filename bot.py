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

# ---------------- AJOUT TICKET IDS ----------------
GERANT_STAFF_ID = 968588191055642624

TICKET_PANEL_CHANNEL = 1504792916772786298
TICKET_CATEGORY_ID = 1504792910892109935
TRANSCRIPT_CHANNEL_ID = 1507694850282094683

# ---------------- DATA ----------------
sanctions = defaultdict(list)

# ---------------- READY ----------------
@bot.event
async def on_ready():
    print(f"Bot connecté : {bot.user}")

    # PANEL TICKET (AJOUT)
    channel = bot.get_channel(TICKET_PANEL_CHANNEL)

    if channel:
        await channel.purge(limit=10)

        embed = discord.Embed(
            title="🎫 OUVERTURE TICKET",
            description="Clique sur le bouton pour ouvrir un ticket staff",
            color=discord.Color.purple()
        )

        await channel.send(embed=embed, view=TicketView())

    bot.add_view(TicketView())

# ---------------- LOG ----------------
async def send_log(guild, message):
    try:
        channel = guild.get_channel(LOG_CHANNEL_ID)
        if channel:
            await channel.send(message)
    except:
        pass

# ---------------- PING ----------------
@bot.command()
async def ping(ctx):
    await ctx.send("Pong 🏓")

# ---------------- CLEAR ----------------
@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int):
    await ctx.channel.purge(limit=amount + 1)
    await ctx.send(f"🧹 {amount} messages supprimés", delete_after=3)

# ---------------- WARN ----------------
@bot.command()
@commands.has_permissions(kick_members=True)
async def warn(ctx, member: discord.Member, *, reason="Aucune raison"):

    sanctions[member.id].append(reason)

    await ctx.send(f"⚠️ {member.mention} warn : {reason}")
    await send_log(ctx.guild, f"WARN | {member} | {reason}")

# ---------------- SANCTIONS ----------------
@bot.command()
async def sanctions(ctx, member: discord.Member):

    if len(sanctions[member.id]) == 0:
        return await ctx.send("❌ Aucune sanction")

    msg = "\n".join([f"- {s}" for s in sanctions[member.id]])
    await ctx.send(f"📌 Sanctions de {member}:\n{msg}")

# ---------------- CLEAR SANCTIONS ----------------
@bot.command()
@commands.has_permissions(kick_members=True)
async def clear_sanctions(ctx, member: discord.Member):

    sanctions[member.id].clear()

    await ctx.send(f"🧹 Sanctions supprimées pour {member.mention}")
    await send_log(ctx.guild, f"CLEAR_SANCTIONS | {member}")

# ---------------- BAN ----------------
@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason="Aucune raison"):

    try:
        await member.ban(reason=reason)
        await ctx.send(f"🔨 {member} ban : {reason}")
        await send_log(ctx.guild, f"BAN | {member} | {reason}")
    except:
        await ctx.send("❌ Impossible de ban")

# ---------------- UNBAN ----------------
@bot.command()
@commands.has_permissions(ban_members=True)
async def unban(ctx, user_id: int):

    try:
        user = await bot.fetch_user(user_id)
        await ctx.guild.unban(user)

        await ctx.send(f"♻️ Unban {user}")
        await send_log(ctx.guild, f"UNBAN | {user}")

    except:
        await ctx.send("❌ Erreur unban")

# ---------------- MUTE ----------------
@bot.command()
@commands.has_permissions(manage_roles=True)
async def mute(ctx, member: discord.Member):

    role = discord.utils.get(ctx.guild.roles, name="Muted")

    if not role:
        role = await ctx.guild.create_role(name="Muted")
        for channel in ctx.guild.channels:
            await channel.set_permissions(role, send_messages=False, speak=False)

    await member.add_roles(role)

    await ctx.send(f"🔇 {member} mute")
    await send_log(ctx.guild, f"MUTE | {member}")

# ---------------- UNMUTE ----------------
@bot.command()
@commands.has_permissions(manage_roles=True)
async def unmute(ctx, member: discord.Member):

    role = discord.utils.get(ctx.guild.roles, name="Muted")

    if role and role in member.roles:
        await member.remove_roles(role)

    await ctx.send(f"🔊 {member} unmute")
    await send_log(ctx.guild, f"UNMUTE | {member}")

# ---------------- TEMPMUTE ----------------
@bot.command()
@commands.has_permissions(manage_roles=True)
async def tempmute(ctx, member: discord.Member, time: int):

    role = discord.utils.get(ctx.guild.roles, name="Muted")

    if not role:
        role = await ctx.guild.create_role(name="Muted")
        for channel in ctx.guild.channels:
            await channel.set_permissions(role, send_messages=False, speak=False)

    await member.add_roles(role)

    await ctx.send(f"⏳ {member} mute {time}s")

    await asyncio.sleep(time)

    await member.remove_roles(role)

    await ctx.send(f"🔊 {member} unmute auto")

# ---------------- REMOVE ROLES ----------------
async def remove_staff(member):
    role_ids = [ROLE_T, ROLE_C, ROLE_PLUS, ROLE_SENIOR, ROLE_ADMIN, ROLE_STAFF]

    for role_id in role_ids:
        role = member.guild.get_role(role_id)
        if role and role in member.roles:
            try:
                await member.remove_roles(role)
            except:
                pass

# ---------------- RANK T ----------------
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

    await ctx.send(f"📌 {member.mention} → Modo Test")

# ---------------- RANK C ----------------
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

    await ctx.send(f"📌 {member.mention} → Modo Confirmé")

# ---------------- RANK PLUS ----------------
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

    await ctx.send(f"📌 {member.mention} → Modo +")

# ---------------- RANK SENIOR ----------------
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

    await ctx.send(f"📌 {member.mention} → Senior")

# ---------------- RANK ADMIN ----------------
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

    await ctx.send(f"👑 {member.mention} → Admin")

# ---------------- DERANK ----------------
@bot.command()
@commands.has_permissions(manage_roles=True)
async def derank(ctx, member: discord.Member):

    await remove_staff(member)

    await ctx.send(f"⬇️ {member.mention} derank effectué")
    await send_log(ctx.guild, f"DERANK | {member} | {ctx.author}")

# =========================================================
# 🎫 TICKET SYSTEM COMPLET (AJOUT FINAL)
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
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            guild.get_role(ROLE_STAFF): discord.PermissionOverwrite(view_channel=True, send_messages=True)
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

        await user.send(f"🎫 Ticket ouvert : {channel.mention}")

# ---------------- ADD ----------------
@bot.command()
async def add(ctx, member: discord.Member):
    await ctx.channel.set_permissions(member, view_channel=True, send_messages=True)
    await ctx.send(f"➕ {member.mention} ajouté")

# ---------------- DEL ----------------
@bot.command(name="del")
async def remove(ctx, member: discord.Member):
    await ctx.channel.set_permissions(member, view_channel=False, send_messages=False)
    await ctx.send(f"➖ {member.mention} retiré")

# ---------------- RENAME ----------------
@bot.command()
async def rename(ctx, *, name):
    await ctx.channel.edit(name=name)
    await ctx.send(f"✏️ renommé → {name}")

# ---------------- CLOSE ----------------
@bot.command()
async def close(ctx):

    await ctx.send("1️⃣ Accepté / 2️⃣ Refusé")

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    msg = await bot.wait_for("message", check=check)

    name = ctx.channel.name.replace("ticket-", "")

    member = discord.utils.find(lambda m: m.name == name, ctx.guild.members)

    if msg.content == "1":
        status = "ACCEPTÉ"
        color = discord.Color.green()
        txt = "Bienvenue dans le staff !!"
    else:
        status = "REFUSÉ"
        color = discord.Color.red()
        txt = "Refusé"

    if member:
        try:
            await member.send(embed=discord.Embed(title=status, description=txt, color=color))
        except:
            pass

    transcript = ctx.guild.get_channel(TRANSCRIPT_CHANNEL_ID)

    if transcript:
        await transcript.send(
            f"📄 TRANSCRIPT\n{ctx.channel.name}\n{status}\nStaff: {ctx.author.mention}"
        )

    staff = ctx.guild.get_member(GERANT_STAFF_ID)
    if staff:
        await staff.send(f"📋 Résultat ticket : {status}")

    await asyncio.sleep(2)
    await ctx.channel.delete()

# ---------------- RUN ----------------
if not TOKEN:
    print("DISCORD_TOKEN manquant")
else:
    bot.run(TOKEN)
