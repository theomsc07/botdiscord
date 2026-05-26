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
db_sanctions = defaultdict(list)

# ---------------- READY ----------------
@bot.event
async def on_ready():
    print(f"Bot connecté : {bot.user}")
    channel = bot.get_channel(TICKET_PANEL_CHANNEL)
    if channel:
        try:
            embed_panel = discord.Embed(
                title="🪐 RECRUTEMENT STAFF",
                description=f"Cliquez ci-dessous pour postuler. Session gérée par <@{GERANT_STAFF_ID}>.",
                color=discord.Color.dark_purple()
            )
            embed_panel.set_footer(text="Tout abus sera sanctionné.")
            await channel.send(embed=embed_panel, view=TicketView())
            print("✅ Panel envoyé !")
        except Exception as e:
            print(f"❌ Erreur panel : {e}")
    bot.add_view(TicketView())

# ---------------- LOG ----------------
async def send_log(guild, message):
    try:
        channel = guild.get_channel(LOG_CHANNEL_ID)
        if not channel:
            channel = await bot.fetch_channel(LOG_CHANNEL_ID)
        if channel:
            await channel.send(message)
    except:
        pass

# ---------------- HELP STAFF ----------------
@bot.command(name="helpstaff")
@commands.has_role(ROLE_STAFF)
async def helpstaff(ctx):
    embed = discord.Embed(title="🔮 COMMANDES STAFF", color=discord.Color.from_rgb(47, 49, 54))
    embed.add_field(name="🛡️ MOD", value="`+warn` `+sanctions` `+clear_sanctions` `+kick` `+ban` `+unban` `+mute` `+unmute` `+tempmute`")
    embed.add_field(name="🎫 TICKETS", value="`+close` `+add` `+del` `+rename`")
    embed.add_field(name="👑 GRADES", value="`+rank-t` `+rank-c` `+rank-plus` `+rank-s` `+rank-admin` `+derank`")
    embed.add_field(name="⚙️ UTILS", value="`+clear` `+ping`")
    await ctx.send(embed=embed)

# ---------------- PING ----------------
@bot.command()
async def ping(ctx):
    await ctx.send(f"⚡ Latence : `{round(bot.latency * 1000)}ms`")

# ---------------- CLEAR ----------------
@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int):
    await ctx.channel.purge(limit=amount + 1)
    await ctx.send(f"🌌 `{amount} messages` supprimés.", delete_after=3)

# ---------------- WARN ----------------
@bot.command()
@commands.has_permissions(kick_members=True)
async def warn(ctx, member: discord.Member, *, reason="Aucune raison"):
    db_sanctions[member.id].append(reason)
    await ctx.send(f"⚠️ Avertissement appliqué à {member.mention} pour : `{reason}`")
    await send_log(ctx.guild, f"⚠️ **WARN** | {member} | {reason} | Par : {ctx.author}")

# ---------------- SANCTIONS ----------------
@bot.command()
async def sanctions(ctx, member: discord.Member):
    if len(db_sanctions[member.id]) == 0:
        return await ctx.send(f"💎 Casier propre pour {member.mention}.")
    msg = "\n".join([f"`{i+1}` ➔ {s}" for i, s in enumerate(db_sanctions[member.id])])
    await ctx.send(f"🗂️ **Sanctions de {member.name}** :\n{msg}")

# ---------------- CLEAR SANCTIONS ----------------
@bot.command()
@commands.has_permissions(kick_members=True)
async def clear_sanctions(ctx, member: discord.Member):
    db_sanctions[member.id].clear()
    await ctx.send(f"🧼 Casier de {member.mention} nettoyé.")
    await send_log(ctx.guild, f"🧼 **CLEAR_SANCTIONS** | {member} | Par : {ctx.author}")

# ---------------- KICK ----------------
@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason="Aucune raison"):
    try:
        await member.kick(reason=reason)
        await ctx.send(f"☄️ {member.name} expulsé pour : `{reason}`")
        await send_log(ctx.guild, f"☄️ **KICK** | {member} | {reason} | Par : {ctx.author}")
    except:
        await ctx.send("🛑 Permissions insuffisantes.")

# ---------------- BAN ----------------
@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason="Aucune raison"):
    try:
        await member.ban(reason=reason)
        await ctx.send(f"💥 {member.name} banni définitivement pour : `{reason}`")
        await send_log(ctx.guild, f"💥 **BAN** | {member} | {reason} | Par : {ctx.author}")
    except:
        await ctx.send("🛑 Impossible de bannir ce membre.")

# ---------------- UNBAN ----------------
@bot.command()
@commands.has_permissions(ban_members=True)
async def unban(ctx, user_id: int):
    try:
        user = await bot.fetch_user(user_id)
        await ctx.guild.unban(user)
        await ctx.send(f"🧬 ID `{user.name}` débanni.")
        await send_log(ctx.guild, f"🧬 **UNBAN** | {user} | Par : {ctx.author}")
    except:
        await ctx.send("🛑 ID introuvable.")

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
    await ctx.send(f"🤫 {member.mention} est maintenant muet.")
    await send_log(ctx.guild, f"🤫 **MUTE** | {member} | Par : {ctx.author}")

# ---------------- UNMUTE ----------------
@bot.command()
@commands.has_permissions(manage_roles=True)
async def unmute(ctx, member: discord.Member):
    role = discord.utils.get(ctx.guild.roles, name="Muted")
    if role and role in member.roles:
        await member.remove_roles(role)
    await ctx.send(f"📣 {member.mention} peut de nouveau parler.")
    await send_log(ctx.guild, f"📣 **UNMUTE** | {member} | Par : {ctx.author}")

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
    await ctx.send(f"⏳ {member.mention} muet pour `{time}s`.")
    await asyncio.sleep(time)
    if role in member.roles:
        await member.remove_roles(role)
        await ctx.send(f"🔊 Parole rétablie pour {member.mention}.")

# ---------------- REMOVE ROLES ----------------
async def remove_staff(member):
    role_ids = [ROLE_T, ROLE_C, ROLE_PLUS, ROLE_SENIOR, ROLE_ADMIN, ROLE_STAFF]
    for role_id in role_ids:
        role = member.guild.get_role(role_id)
        if role and role in member.roles:
            try: await member.remove_roles(role)
            except: pass

# ---------------- RANKS SYSTEM ----------------
@bot.command(name="rank-t")
@commands.has_permissions(manage_roles=True)
async def rank_t(ctx, member: discord.Member):
    await remove_staff(member)
    r, s = ctx.guild.get_role(ROLE_T), ctx.guild.get_role(ROLE_STAFF)
    if r: await member.add_roles(r)
    if s: await member.add_roles(s)
    await ctx.send(f"🛠️ {member.mention} est maintenant Modo Test.")

@bot.command(name="rank-c")
@commands.has_permissions(manage_roles=True)
async def rank_c(ctx, member: discord.Member):
    await remove_staff(member)
    r, s = ctx.guild.get_role(ROLE_C), ctx.guild.get_role(ROLE_STAFF)
    if r: await member.add_roles(r)
    if s: await member.add_roles(s)
    await ctx.send(f"💎 {member.mention} est maintenant Modo Confirmé.")

@bot.command(name="rank-plus")
@commands.has_permissions(manage_roles=True)
async def rank_plus(ctx, member: discord.Member):
    await remove_staff(member)
    r, s = ctx.guild.get_role(ROLE_PLUS), ctx.guild.get_role(ROLE_STAFF)
    if r: await member.add_roles(r)
    if s: await member.add_roles(s)
    await ctx.send(f"⚡ {member.mention} est maintenant Modo +.")

@bot.command(name="rank-s")
@commands.has_permissions(manage_roles=True)
async def rank_s(ctx, member: discord.Member):
    await remove_staff(member)
    r, s = ctx.guild.get_role(ROLE_SENIOR), ctx.guild.get_role(ROLE_STAFF)
    if r: await member.add_roles(r)
    if s: await member.add_roles(s)
    await ctx.send(f"purple {member.mention} est maintenant Senior.")

@bot.command(name="rank-admin")
@commands.has_permissions(manage_roles=True)
async def rank_admin(ctx, member: discord.Member):
    await remove_staff(member)
    r, s = ctx.guild.get_role(ROLE_ADMIN), ctx.guild.get_role(ROLE_STAFF)
    if r: await member.add_roles(r)
    if s: await member.add_roles(s)
    await ctx.send(f"🪐 {member.mention} est maintenant Administrateur.")

@bot.command()
@commands.has_permissions(manage_roles=True)
async def derank(ctx, member: discord.Member):
    await remove_staff(member)
    await ctx.send(f"📉 {member.mention} a été derank.")
    await send_log(ctx.guild, f"📉 **DERANK** | {member} | Par : {ctx.author}")

# =========================================================
# 🎫 TICKET SYSTEM COMPLET
# =========================================================

class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="📝 Ouvrir une candidature", style=discord.ButtonStyle.blurple, custom_id="ouvrir_ticket_permanent")
    async def open(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        user = interaction.user
        category = guild.get_channel(TICKET_CATEGORY_ID)
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            guild.get_role(ROLE_STAFF): discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }
        channel = await guild.create_text_channel(name=f"ticket-{user.name.lower()}", category=category, overwrites=overwrites)
        await channel.send(f"👋 Bienvenue {user.mention}. Présente-toi ici. Support géré par <@{GERANT_STAFF_ID}>.")
        await interaction.response.send_message(f"✅ Ticket créé : {channel.mention}", ephemeral=True)

class CloseTicketModal(discord.ui.Modal):
    def __init__(self, status: str, color: discord.Color, channel_name: str, member: discord.Member):
        super().__init__(title=f"Verdict : {status}")
        self.status, self.color, self.channel_name, self.member = status, color, channel_name, member
        self.reason = discord.ui.TextInput(label="Motif", placeholder="Raison...", required=True)
        self.custom_msg = discord.ui.TextInput(label="Message au candidat", style=discord.TextStyle.paragraph, required=True)
        self.add_item(self.reason)
        self.add_item(self.custom_msg)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed_mp = discord.Embed(title=f"Candidature {self.status}", description=f"Votre profil a été traité sur {interaction.guild.name}.", color=self.color)
        embed_mp.add_field(name="Motif", value=str(self.reason.value))
        embed_mp.add_field(name="Message", value=str(self.custom_msg.value))
        if self.member:
            try: await self.member.send(embed=embed_mp)
            except: pass
        transcript = interaction.guild.get_channel(TRANSCRIPT_CHANNEL_ID)
        if transcript:
            await transcript.send(f"📄 **TRANSCRIPT** | {self.channel_name} | Candidat: {self.member.name} | Verdict: {self.status} | Recruteur: {interaction.user.name}")
        await interaction.channel.send("✅ Salon supprimé dans 3s...")
        await asyncio.sleep(3)
        await interaction.channel.delete()

class CloseButtonsView(discord.ui.View):
    def __init__(self, channel_name: str, member: discord.Member):
        super().__init__(timeout=60.0)
        self.channel_name, self.member = channel_name, member

    @discord.ui.button(label="✅ Accepter", style=discord.ButtonStyle.green)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(CloseTicketModal("ACCEPTÉ", discord.Color.green(), self.channel_name, self.member))

    @discord.ui.button(label="❌ Refuser", style=discord.ButtonStyle.danger)
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(CloseTicketModal("REFUSÉ", discord.Color.red(), self.channel_name, self.member))

@bot.command()
@commands.has_permissions(manage_channels=True)
async def close(ctx):
    name = ctx.channel.name.replace("ticket-", "")
    member = discord.utils.find(lambda m: m.name.lower() == name, ctx.guild.members)
    if not member:
        return await ctx.send("❌ Aucun membre trouvé pour ce ticket.")
    await ctx.send("🔒 Quel est le verdict ?", view=CloseButtonsView(ctx.channel.name, member))

# ---------------- ADD / DEL / RENAME ----------------
@bot.command()
async def add(ctx, member: discord.Member):
    await ctx.channel.set_permissions(member, view_channel=True, send_messages=True)
    await ctx.send(f"📥 {member.mention} ajouté.")

@bot.command(name="del")
async def remove(ctx, member: discord.Member):
    await ctx.channel.set_permissions(member, view_channel=False)
    await ctx.send(f"📤 {member.mention} retiré.")

@bot.command()
async def rename(ctx, *, name):
    await ctx.channel.edit(name=name)
    await ctx.send(f"🏷️ Salon renommé en `{name}`.")

# ---------------- RUN ----------------
if not TOKEN:
    print("DISCORD_TOKEN manquant")
else:
    bot.run(TOKEN)
    
