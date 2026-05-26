import discord
from discord.ext import commands
import os
import asyncio
from collections import defaultdict
from datetime import datetime

# ---------------- CONFIG ----------------
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="+", intents=intents)

TOKEN = os.getenv("DISCORD_TOKEN")

# IDs (Remplace par tes vrais IDs)
LOG_CHANNEL_ID = 1508482233219022992
TRANSCRIPT_CHANNEL_ID = 1507694850282094683
TICKET_CATEGORY_ID = 1504792910892109935
GERANT_STAFF_ID = 968588191055642624
ROLE_STAFF = 1504810257715822722

# DATA
TICKET_OWNERS = {}

# ---------------- UTILS PREMIUM ----------------
def create_embed(title, desc, color):
    embed = discord.Embed(title=title, description=desc, color=color, timestamp=datetime.now())
    embed.set_footer(text="Système Premium | Administration")
    return embed

async def send_dm(member, title, desc, color):
    try: await member.send(embed=create_embed(title, desc, color))
    except: pass

# ---------------- READY ----------------
@bot.event
async def on_ready():
    bot.add_view(TicketView())
    print(f"✅ Bot connecté : {bot.user}")

# ---------------- COMMANDES GÉNÉRALES ----------------
@bot.command()
async def ping(ctx):
    await ctx.send(embed=create_embed("⚡ Latence", f"Ping : `{round(bot.latency * 1000)}ms`", discord.Color.purple()))

@bot.command(name="helpstaff")
@commands.has_role(ROLE_STAFF)
async def helpstaff(ctx):
    embed = create_embed("🔮 COMMANDES STAFF", "Outils de modération activés :", discord.Color.dark_purple())
    embed.add_field(name="🛡️ Modération", value="`+warn` `+mute` `+tempmute` `+kick` `+ban` `+unban`", inline=False)
    embed.add_field(name="🎫 Tickets", value="`+close`", inline=False)
    await ctx.send(embed=embed)

# ---------------- MODÉRATION ----------------
@bot.command()
@commands.has_permissions(kick_members=True)
async def warn(ctx, member: discord.Member, *, reason="Aucune raison"):
    await send_dm(member, "⚠️ Avertissement", f"Vous avez été averti sur **{ctx.guild.name}**.\nRaison : {reason}", discord.Color.orange())
    await ctx.send(embed=create_embed("⚠️ Avertissement", f"{member.mention} averti.", discord.Color.orange()))
    log_ch = ctx.guild.get_channel(LOG_CHANNEL_ID)
    if log_ch:
        embed = create_embed("📊 Log : Warn", f"Membre: {member.mention}\nModo: {ctx.author.mention}\nRaison: {reason}", discord.Color.orange())
        embed.set_thumbnail(url=member.display_avatar.url)
        await log_ch.send(embed=embed)

@bot.command()
@commands.has_permissions(manage_roles=True)
async def mute(ctx, member: discord.Member):
    for channel in ctx.guild.text_channels:
        await channel.set_permissions(member, send_messages=False)
    await ctx.send(embed=create_embed("🤫 Mute", f"{member.mention} est muet.", discord.Color.red()))

@bot.command()
@commands.has_permissions(manage_roles=True)
async def tempmute(ctx, member: discord.Member, seconds: int):
    await ctx.send(embed=create_embed("⏳ TempMute", f"{member.mention} muet pour {seconds}s.", discord.Color.orange()))
    for channel in ctx.guild.text_channels:
        await channel.set_permissions(member, send_messages=False)
    await asyncio.sleep(seconds)
    for channel in ctx.guild.text_channels:
        await channel.set_permissions(member, send_messages=None)
    await ctx.send(f"✅ {member.mention} a retrouvé ses droits.")

@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason="Aucune raison"):
    await member.kick(reason=reason)
    await ctx.send(embed=create_embed("☄️ Kick", f"{member.name} a été expulsé.", discord.Color.red()))

@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason="Aucune raison"):
    await member.ban(reason=reason)
    await ctx.send(embed=create_embed("💥 Ban", f"{member.name} a été banni.", discord.Color.dark_red()))

@bot.command()
@commands.has_permissions(ban_members=True)
async def unban(ctx, user_id: int):
    try:
        user = await bot.fetch_user(user_id)
        await ctx.guild.unban(user)
        await ctx.send(embed=create_embed("🔓 Unban", f"{user.name} a été débanni.", discord.Color.green()))
    except:
        await ctx.send(embed=create_embed("❌ Erreur", "ID invalide ou utilisateur non banni.", discord.Color.red()))

# ---------------- TICKETS ----------------
class TicketView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    
    @discord.ui.button(label="📝 Ouvrir candidature", style=discord.ButtonStyle.blurple, custom_id="open_ticket")
    async def open(self, i: discord.Interaction, b):
        overwrites = {i.guild.default_role: discord.PermissionOverwrite(view_channel=False), i.user: discord.PermissionOverwrite(view_channel=True, send_messages=True)}
        ch = await i.guild.create_text_channel(name=f"ticket-{i.user.name}", category=i.guild.get_channel(TICKET_CATEGORY_ID), overwrites=overwrites)
        TICKET_OWNERS[ch.id] = i.user.id
        await ch.send(f"{i.user.mention} 🔔 <@{GERANT_STAFF_ID}>")
        await ch.send(embed=create_embed("🔔 Nouveau Ticket", "Le staff arrive.", discord.Color.blue()))
        await i.response.send_message(f"✅ Ticket ouvert : {ch.mention}", ephemeral=True)

class CloseButtonsView(discord.ui.View):
    def __init__(self, member):
        super().__init__(timeout=60); self.member = member
    
    @discord.ui.button(label="✅ Accepter", style=discord.ButtonStyle.green)
    async def acc(self, i, b): 
        tr = i.guild.get_channel(TRANSCRIPT_CHANNEL_ID)
        if tr: await tr.send(embed=create_embed("📄 Verdict", f"Candidat: {self.member.mention}\nDécision: **ACCEPTÉ**", discord.Color.green()))
        await i.channel.delete()

    @discord.ui.button(label="❌ Refuser", style=discord.ButtonStyle.danger)
    async def rej(self, i, b):
        tr = i.guild.get_channel(TRANSCRIPT_CHANNEL_ID)
        if tr: await tr.send(embed=create_embed("📄 Verdict", f"Candidat: {self.member.mention}\nDécision: **REFUSÉ**", discord.Color.red()))
        await i.channel.delete()

@bot.command()
@commands.has_permissions(manage_channels=True)
async def close(ctx):
    member = ctx.guild.get_member(TICKET_OWNERS.get(ctx.channel.id))
    await ctx.send("Décision :", view=CloseButtonsView(member))

# ---------------- RUN ----------------
bot.run(TOKEN)
    
