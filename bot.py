import discord
from discord.ext import commands
import os
import asyncio
from collections import defaultdict
import discord.ui

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

GERANT_STAFF_ID = 968588191055642624

TICKET_PANEL_CHANNEL = 1504792916772786298
TICKET_CATEGORY_ID = 1504792910892109935
TRANSCRIPT_CHANNEL_ID = 1507694850282094683

# ---------------- DATA ----------------
sanctions = defaultdict(list)

# ---------------- SAFE UTIL ----------------
async def log(guild, message):
    ch = guild.get_channel(LOG_CHANNEL_ID)
    if ch:
        try:
            await ch.send(message)
        except:
            pass

async def dm(user, title, desc, color):
    try:
        await user.send(embed=discord.Embed(title=title, description=desc, color=color))
    except:
        pass

# ---------------- READY ----------------
@bot.event
async def on_ready():
    print(f"Bot connecté : {bot.user}")

    channel = bot.get_channel(TICKET_PANEL_CHANNEL)

    if channel:
        await channel.purge(limit=10)

        embed = discord.Embed(
            title="🎫 OUVERTURE TICKET",
            description="Clique pour ouvrir un ticket staff",
            color=discord.Color.purple()
        )

        await channel.send(embed=embed, view=TicketView())

    bot.add_view(TicketView())

# ---------------- WARN FIX ----------------
@bot.command()
@commands.has_permissions(kick_members=True)
async def warn(ctx, member: discord.Member, *, reason="Aucune raison"):

    sanctions[member.id].append(reason)

    await dm(member, "⚠️ WARN", reason, discord.Color.orange())

    await ctx.send(f"⚠️ {member.mention} warn")

    await log(ctx.guild, f"WARN | {member} | {ctx.author} | {reason}")

# ---------------- TEMPMUTE FIX ----------------
@bot.command()
@commands.has_permissions(manage_roles=True)
async def tempmute(ctx, member: discord.Member, time: int):

    role = discord.utils.get(ctx.guild.roles, name="Muted")

    if not role:
        role = await ctx.guild.create_role(name="Muted")
        for ch in ctx.guild.channels:
            await ch.set_permissions(role, send_messages=False, speak=False)

    await member.add_roles(role)

    await dm(member, "⏳ TEMPMUTE", f"{time}s", discord.Color.red())

    await ctx.send(f"⏳ {member.mention} mute {time}s")

    await log(ctx.guild, f"TEMPMUTE | {member} | {time}s")

    await asyncio.sleep(time)

    if role in member.roles:
        await member.remove_roles(role)

    await dm(member, "🔊 UNMUTE", "Auto unmute", discord.Color.green())

    await log(ctx.guild, f"UNMUTE AUTO | {member}")

# ---------------- MUTE ----------------
@bot.command()
@commands.has_permissions(manage_roles=True)
async def mute(ctx, member: discord.Member):

    role = discord.utils.get(ctx.guild.roles, name="Muted")

    if not role:
        role = await ctx.guild.create_role(name="Muted")
        for ch in ctx.guild.channels:
            await ch.set_permissions(role, send_messages=False)

    await member.add_roles(role)

    await dm(member, "🔇 MUTE", "Tu es mute", discord.Color.red())

    await ctx.send(f"🔇 {member.mention} mute")

    await log(ctx.guild, f"MUTE | {member}")

# ---------------- UNMUTE ----------------
@bot.command()
@commands.has_permissions(manage_roles=True)
async def unmute(ctx, member: discord.Member):

    role = discord.utils.get(ctx.guild.roles, name="Muted")

    if role and role in member.roles:
        await member.remove_roles(role)

    await dm(member, "🔊 UNMUTE", "Tu n'es plus mute", discord.Color.green())

    await ctx.send(f"🔊 {member.mention} unmute")

    await log(ctx.guild, f"UNMUTE | {member}")

# ---------------- ADD / DEL / RENAME ----------------
@bot.command()
async def add(ctx, member: discord.Member):
    await ctx.channel.set_permissions(member, view_channel=True, send_messages=True)
    await ctx.send(f"➕ {member.mention}")

@bot.command(name="del")
async def remove(ctx, member: discord.Member):
    await ctx.channel.set_permissions(member, view_channel=False)
    await ctx.send(f"➖ {member.mention}")

@bot.command()
async def rename(ctx, *, name):
    await ctx.channel.edit(name=name)
    await ctx.send(f"✏️ {name}")

# ---------------- CLOSE FIX ----------------
@bot.command()
async def close(ctx):

    await ctx.send("1️⃣ Accepté / 2️⃣ Refusé")

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    msg = await bot.wait_for("message", check=check)

    member = discord.utils.find(lambda m: m.name in ctx.channel.name, ctx.guild.members)

    if msg.content == "1":
        status = "ACCEPTÉ"
        color = discord.Color.green()
        txt = "Bienvenue staff"
    else:
        status = "REFUSÉ"
        color = discord.Color.red()
        txt = "Refusé"

    if member:
        await dm(member, status, txt, color)

    gerant = ctx.guild.get_member(GERANT_STAFF_ID)
    if gerant:
        await dm(gerant, "📋 RESULT", f"{member} → {status}", color)

    transcript = ctx.guild.get_channel(TRANSCRIPT_CHANNEL_ID)
    if transcript:
        await transcript.send(f"📄 {ctx.channel.name} | {status} | {ctx.author}")

    await log(ctx.guild, f"CLOSE | {member} | {status}")

    await asyncio.sleep(2)
    await ctx.channel.delete()

# ---------------- TICKET SYSTEM ----------------
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
            user: discord.PermissionOverwrite(view_channel=True),
            guild.get_role(ROLE_STAFF): discord.PermissionOverwrite(view_channel=True)
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

        await dm(user, "🎫 Ticket ouvert", channel.mention, discord.Color.green())

        await log(guild, f"TICKET OPEN | {user}")

# ---------------- RUN ----------------
if not TOKEN:
    print("DISCORD_TOKEN manquant")
else:
    bot.run(TOKEN)
