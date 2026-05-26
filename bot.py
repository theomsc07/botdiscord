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

# ---------------- DATA STORE DURANT RUN ----------------
TICKET_OWNERS = {}
db_sanctions = defaultdict(list)

# ---------------- READY ----------------
@bot.event
async def on_ready():
    print(f"Bot connecté : {bot.user}")
    channel = bot.get_channel(TICKET_PANEL_CHANNEL)
    if channel:
        try:
            embed_panel = discord.Embed(
                title="🪐 RECRUTEMENT DE L'ÉQUIPE STAFF",
                description=(
                    "Vous souhaitez vous investir dans le développement du projet ? "
                    "L'équipe de modération ouvre ses portes !\n\n"
                    f"👑 **Responsable des recrutements :** <@{GERANT_STAFF_ID}>\n"
                    "💼 **Poste à pourvoir :** Modérateur Test\n\n"
                    "Cliquez sur le bouton ci-dessous pour ouvrir votre dossier."
                ),
                color=discord.Color.dark_purple()
            )
            if bot.user.display_avatar:
                embed_panel.set_thumbnail(url=bot.user.display_avatar.url)
            embed_panel.set_footer(text="Tout abus ou ticket inutile sera lourdement sanctionné.")
            
            await channel.purge(limit=5)
            await channel.send(embed=embed_panel, view=TicketView())
            print("✅ Panel Pro Envoyé !")
        except Exception as e:
            print(f"❌ Erreur panel : {e}")
    bot.add_view(TicketView())

# ---------------- LOG SYSTEM ----------------
async def send_log(guild, message_text, embed=None):
    try:
        channel = guild.get_channel(LOG_CHANNEL_ID)
        if not channel:
            channel = await bot.fetch_channel(LOG_CHANNEL_ID)
        if channel:
            if embed:
                await channel.send(content=message_text, embed=embed)
            else:
                await channel.send(message_text)
    except Exception as e:
        print(f"❌ Impossible d'envoyer le log : {e}")

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
    
    try:
        embed_mp = discord.Embed(
            title="⚠️ AVERTISSEMENT OFFICIEL", 
            description=f"Un avertissement vous a été attribué sur **{ctx.guild.name}**.\n\n*Si vous pensez c'est une erreurs merci de contacter @theo_msc en mp !*", 
            color=discord.Color.orange(),
            timestamp=datetime.now()
        )
        embed_mp.add_field(name="👮 Modérateur", value=ctx.author.name, inline=True)
        embed_mp.add_field(name="📄 Raison", value=reason, inline=True)
        if bot.user.display_avatar:
            embed_mp.set_thumbnail(url=bot.user.display_avatar.url)
        await member.send(embed=embed_mp)
    except:
        pass

    await ctx.send(f"⚠️ Avertissement appliqué à {member.mention} pour : `{reason}`")
    await send_log(ctx.guild, f"⚠️ **WARN** | {member.mention} | Raison: {reason} | Par : {ctx.author.mention}")

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
    await send_log(ctx.guild, f"🧼 **CLEAR_SANCTIONS** | {member.mention} | Par : {ctx.author.mention}")

# ---------------- KICK ----------------
@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason="Aucune raison"):
    try:
        try:
            embed_mp = discord.Embed(
                title="☄️ EXPULSION DU SERVEUR", 
                description=f"Vous avez été expulsé du serveur **{ctx.guild.name}**.\n\n*Si vous pensez c'est une erreurs merci de contacter @theo_msc en mp !*", 
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            embed_mp.add_field(name="👮 Modérateur", value=ctx.author.name, inline=True)
            embed_mp.add_field(name="📄 Raison", value=reason, inline=True)
            if bot.user.display_avatar:
                embed_mp.set_thumbnail(url=bot.user.display_avatar.url)
            await member.send(embed=embed_mp)
        except:
            pass

        await member.kick(reason=reason)
        await ctx.send(f"☄️ {member.name} expulsé pour : `{reason}`")
        await send_log(ctx.guild, f"☄️ **KICK** | {member.mention} | Raison: {reason} | Par : {ctx.author.mention}")
    except:
        await ctx.send("🛑 Permissions insuffisantes.")

# ---------------- BAN ----------------
@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason="Aucune raison"):
    try:
        try:
            embed_mp = discord.Embed(
                title="💥 BANNISSEMENT DÉFINITIF", 
                description=f"Vous avez été banni définitivement du serveur **{ctx.guild.name}**.\n\n*Si vous pensez c'est une erreurs merci de contacter @theo_msc en mp !*", 
                color=discord.Color.dark_red(),
                timestamp=datetime.now()
            )
            embed_mp.add_field(name="👮 Modérateur", value=ctx.author.name, inline=True)
            embed_mp.add_field(name="📄 Raison", value=reason, inline=True)
            if bot.user.display_avatar:
                embed_mp.set_thumbnail(url=bot.user.display_avatar.url)
            await member.send(embed=embed_mp)
        except:
            pass

        await member.ban(reason=reason)
        await ctx.send(f"💥 {member.name} banni définitivement pour : `{reason}`")
        await send_log(ctx.guild, f"💥 **BAN** | {member.mention} | Raison: {reason} | Par : {ctx.author.mention}")
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
        await send_log(ctx.guild, f"🧬 **UNBAN** | ID: {user_id} | Par : {ctx.author.mention}")
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

    try:
        embed_mp = discord.Embed(
            title="🤫 SOURDINE GLOBALE", 
            description=f"Vos permissions de parole vous ont été retirées sur **{ctx.guild.name}**.\n\n*Si vous pensez c'est une erreurs merci de contacter @theo_msc en mp !*", 
            color=discord.Color.red(),
            timestamp=datetime.now()
        )
        embed_mp.add_field(name="👮 Modérateur", value=ctx.author.name, inline=True)
        if bot.user.display_avatar:
            embed_mp.set_thumbnail(url=bot.user.display_avatar.url)
        await member.send(embed=embed_mp)
    except:
        pass

    await ctx.send(f"🤫 {member.mention} est maintenant muet.")
    await send_log(ctx.guild, f"🤫 **MUTE** | {member.mention} | Par : {ctx.author.mention}")

# ---------------- UNMUTE ----------------
@bot.command()
@commands.has_permissions(manage_roles=True)
async def unmute(ctx, member: discord.Member):
    role = discord.utils.get(ctx.guild.roles, name="Muted")
    if role and role in member.roles:
        await member.remove_roles(role)
        try:
            embed_mp = discord.Embed(
                title="📣 SOURDINE LEVÉE", 
                description=f"Votre droit de parole a été rétabli sur **{ctx.guild.name}**.", 
                color=discord.Color.green(),
                timestamp=datetime.now()
            )
            if bot.user.display_avatar:
                embed_mp.set_thumbnail(url=bot.user.display_avatar.url)
            await member.send(embed=embed_mp)
        except:
            pass

    await ctx.send(f"📣 {member.mention} peut de nouveau parler.")
    await send_log(ctx.guild, f"📣 **UNMUTE** | {member.mention} | Par : {ctx.author.mention}")

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

    try:
        embed_mp = discord.Embed(
            title="⏳ SOURDINE TEMPORAIRE", 
            description=f"Vous avez été rendu muet temporairement sur **{ctx.guild.name}**.\n\n*Si vous pensez c'est une erreurs merci de contacter @theo_msc en mp !*", 
            color=discord.Color.orange(),
            timestamp=datetime.now()
        )
        embed_mp.add_field(name="👮 Modérateur", value=ctx.author.name, inline=True)
        embed_mp.add_field(name="⏰ Durée", value=f"{time} secondes", inline=True)
        if bot.user.display_avatar:
            embed_mp.set_thumbnail(url=bot.user.display_avatar.url)
        await member.send(embed=embed_mp)
    except:
        pass

    await ctx.send(f"⏳ {member.mention} muet pour `{time}s`.")
    await send_log(ctx.guild, f"⏳ **TEMPMUTE** | {member.mention} | Durée: {time}s | Par : {ctx.author.mention}")
    
    await asyncio.sleep(time)
    
    if role in member.roles:
        await member.remove_roles(role)
        try:
            embed_mp = discord.Embed(
                title="🔊 PAROLE RÈTABLIE", 
                description=f"Votre sourdine temporaire est terminée sur **{ctx.guild.name}**.", 
                color=discord.Color.green(),
                timestamp=datetime.now()
            )
            if bot.user.display_avatar:
                embed_mp.set_thumbnail(url=bot.user.display_avatar.url)
            await member.send(embed=embed_mp)
        except:
            pass
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
    await send_log(ctx.guild, f"🛠️ **RANK-T** | {member.mention} | Par : {ctx.author.mention}")

@bot.command(name="rank-c")
@commands.has_permissions(manage_roles=True)
async def rank_c(ctx, member: discord.Member):
    await remove_staff(member)
    r, s = ctx.guild.get_role(ROLE_C), ctx.guild.get_role(ROLE_STAFF)
    if r: await member.add_roles(r)
    if s: await member.add_roles(s)
    await ctx.send(f"💎 {member.mention} est maintenant Modo Confirmé.")
    await send_log(ctx.guild, f"💎 **RANK-C** | {member.mention} | Par : {ctx.author.mention}")

@bot.command(name="rank-plus")
@commands.has_permissions(manage_roles=True)
async def rank_plus(ctx, member: discord.Member):
    await remove_staff(member)
    r, s = ctx.guild.get_role(ROLE_PLUS), ctx.guild.get_role(ROLE_STAFF)
    if r: await member.add_roles(r)
    if s: await member.add_roles(s)
    await ctx.send(f"⚡ {member.mention} est maintenant Modo +.")
    await send_log(ctx.guild, f"⚡ **RANK-PLUS** | {member.mention} | Par : {ctx.author.mention}")

@bot.command(name="rank-s")
@commands.has_permissions(manage_roles=True)
async def rank_s(ctx, member: discord.Member):
    await remove_staff(member)
    r, s = ctx.guild.get_role(ROLE_SENIOR), ctx.guild.get_role(ROLE_STAFF)
    if r: await member.add_roles(r)
    if s: await member.add_roles(s)
    await ctx.send(f"🔮 {member.mention} est maintenant Senior.")
    await send_log(ctx.guild, f"🔮 **RANK-S** | {member.mention} | Par : {ctx.author.mention}")

@bot.command(name="rank-admin")
@commands.has_permissions(manage_roles=True)
async def rank_admin(ctx, member: discord.Member):
    await remove_staff(member)
    r, s = ctx.guild.get_role(ROLE_ADMIN), ctx.guild.get_role(ROLE_STAFF)
    if r: await member.add_roles(r)
    if s: await member.add_roles(s)
    await ctx.send(f"🪐 {member.mention} est maintenant Administrateur.")
    await send_log(ctx.guild, f"🪐 **RANK-ADMIN** | {member.mention} | Par : {ctx.author.mention}")

@bot.command()
@commands.has_permissions(manage_roles=True)
async def derank(ctx, member: discord.Member):
    await remove_staff(member)
    await ctx.send(f"📉 {member.mention} a été derank.")
    await send_log(ctx.guild, f"📉 **DERANK** | {member.mention} | Par : {ctx.author.mention}")


# =========================================================
# 🎫 TICKET SYSTEM VISUEL PRO & FIABLE
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
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True, embed_links=True),
            guild.get_role(ROLE_STAFF): discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }
        
        channel = await guild.create_text_channel(name=f"ticket-{user.name.lower()}", category=category, overwrites=overwrites)
        TICKET_OWNERS[channel.id] = user.id

        embed_welcome = discord.Embed(
            title="📂 DOSSIER DE CANDIDATURE INITIALISÉ",
            description=(
                f"Bonjour {user.mention},\n\n"
                "Votre espace de recrutement vient de s'ouvrir. Afin d'étudier au mieux votre profil, "
                "merci de nous fournir les éléments suivants :\n\n"
                "🔹 Votre âge ainsi que vos disponibilités.\n"
                "🔹 Vos motivations détaillées.\n"
                "🔹 Vos expériences passées dans la modération.\n\n"
                "Un membre de la direction étudiera votre dossier sous peu."
            ),
            color=discord.Color.purple(),
            timestamp=datetime.now()
        )
        if bot.user.display_avatar:
            embed_welcome.set_thumbnail(url=bot.user.display_avatar.url)
        embed_welcome.set_footer(text="Gestion des Candidatures • Utilisez +close pour statuer")
        
        await channel.send(content=f"{user.mention} 🔔 <@{GERANT_STAFF_ID}>", embed=embed_welcome)
        await interaction.response.send_message(f"✅ Votre dossier a été créé : {channel.mention}", ephemeral=True)


class CloseTicketModal(discord.ui.Modal):
    def __init__(self, status: str, color: discord.Color, channel_name: str, member: discord.Member):
        super().__init__(title=f"Verdict : {status}")
        self.status, self.color, self.channel_name, self.member = status, color, channel_name, member
        self.reason = discord.ui.TextInput(label="Motif", placeholder="Raison principale du choix...", required=True)
        self.custom_msg = discord.ui.TextInput(label="Message détaillé au candidat", style=discord.TextStyle.paragraph, required=True)
        self.add_item(self.reason)
        self.add_item(self.custom_msg)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        embed_mp = discord.Embed(
            title=f"📬 RÉSULTAT DE VOTRE CANDIDATURE : {self.status}",
            description=f"Bonjour {self.member.mention},\nVotre dossier sur **{interaction.guild.name}** a été traité par notre équipe.",
            color=self.color,
            timestamp=datetime.now()
        )
        embed_mp.add_field(name="📌 Décision", value=f"**{self.status}**", inline=True)
        embed_mp.add_field(name="👮 Recruteur", value=interaction.user.mention, inline=True)
        embed_mp.add_field(name="📝 Motif", value=str(self.reason.value), inline=False)
        embed_mp.add_field(name="💬 Message", value=str(self.custom_msg.value), inline=False)
        
        if self.member:
            try: await self.member.send(embed=embed_mp)
            except: pass

        transcript = interaction.guild.get_channel(TRANSCRIPT_CHANNEL_ID)
        if transcript:
            embed_trans = discord.Embed(title="📄 TRANSCRIPT RECRUTEMENT", color=self.color, timestamp=datetime.now())
            embed_trans.add_field(name="Salon", value=self.channel_name, inline=True)
            embed_trans.add_field(name="Candidat", value=self.member.mention, inline=True)
            embed_trans.add
        
