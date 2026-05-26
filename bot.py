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
            # ENLEVÉ : Plus de purge automatique ici pour éviter le crash de l'hébergeur
            
            embed_panel = discord.Embed(
                title="🪐 RECRUTEMENT DE L'ÉQUIPE STAFF",
                description=(
                    "Vous souhaitez investir votre temps et participer à l'évolution du serveur ? "
                    "C'est ici que ça se passe !\n\n"
                    f"⚡ **Session gérée par :** <@{GERANT_STAFF_ID}>\n\n"
                    "➡️ **Pour postuler :** Cliquez simplement sur le bouton ci-dessous.\n"
                    "Un salon privé va s'ouvrir pour votre entretien."
                ),
                color=discord.Color.dark_purple()
            )
            if bot.user.display_avatar:
                embed_panel.set_thumbnail(url=bot.user.display_avatar.url)
            embed_panel.set_footer(text="Merci de ne pas ouvrir de ticket inutilement • Tout abus sera sanctionné.")

            await channel.send(embed=embed_panel, view=TicketView())
            print("✅ Panel envoyé sur Discord !")
        except Exception as e:
            print(f"❌ Erreur lors de l'envoi du panel : {e}")

    bot.add_view(TicketView())

# ---------------- LOG ----------------
async def send_log(guild, message):
    try:
        channel = guild.get_channel(LOG_CHANNEL_ID)
        if not channel:
            channel = await bot.fetch_channel(LOG_CHANNEL_ID)
        if channel:
            await channel.send(message)
    except Exception as e:
        print(f"Erreur d'envoi du log : {e}")

# ---------------- HELP STAFF ----------------
@bot.command(name="helpstaff")
@commands.has_role(ROLE_STAFF)
async def helpstaff(ctx):
    embed = discord.Embed(
        title="🔮 CENTRE DE COMMANDES STAFF",
        description="Bienvenue dans l'interface de gestion de ton équipe. Voici la liste complète des outils disponibles sur le serveur.",
        color=discord.Color.from_rgb(47, 49, 54),
        timestamp=datetime.now()
    )
    
    embed.add_field(
        name="🛡️ MODÉRATION",
        value=(
            "`+warn @membre [raison]` ➔ Assigne un avertissement\n"
            "`+sanctions @membre` ➔ Liste le casier d'un joueur\n"
            "`+clear_sanctions @membre` ➔ Remet le casier à zéro\n"
            "`+kick @membre [raison]` ➔ Expulse un utilisateur\n"
            "`+ban @membre [raison]` ➔ Bannit définitivement\n"
            "`+unban [ID]` ➔ Révoque un bannissement\n"
            "`+mute @membre` ➔ Rend muet indéfiniment\n"
            "`+unmute @membre` ➔ Redonne la parole\n"
            "`+tempmute @membre [temps]` ➔ Mute temporaire (en secondes)"
        ),
        inline=False
    )
    
    embed.add_field(
        name="🎫 TICKETS & CANDIDATURES",
        value=(
            "`+close` ➔ Lance la clôture (Verdict Accepté/Refusé par bouton)\n"
            "`+add @membre` ➔ Ajoute un utilisateur au ticket actuel\n"
            "`+del @membre` ➔ Retire un utilisateur du ticket actuel\n"
            "`+rename [nom]` ➔ Renomme proprement le salon actuel"
        ),
        inline=False
    )
    
    embed.add_field(
        name="👑 GESTION DES GRADES STAFF",
        value=(
            "`+rank-t @membre` ➔ Assigne le rôle Modo Test\n"
            "`+rank-c @membre` ➔ Assigne le rôle Modo Confirmé\n"
            "`+rank-plus @membre` ➔ Assigne le rôle Modo +\n"
            "`+rank-s @membre` ➔ Assigne le rôle Senior\n"
            "`+rank-admin @membre` ➔ Assigne le rôle Administrateur\n"
            "`+derank @membre` ➔ Destitue de l'intégralité des rôles staff"
        ),
        inline=False
    )
    
    embed.add_field(
        name="⚙️ UTILITAIRES",
        value=(
            "`+clear [nombre]` ➔ Purge les messages du salon\n"
            "`+ping` ➔ Affiche la latence du bot"
        ),
        inline=False
    )

    if bot.user.display_avatar:
        embed.set_thumbnail(url=bot.user.display_avatar.url)
        
    embed.set_footer(text=f"Demandé par {ctx.author.name} • Réservé à l'équipe Staff", icon_url=ctx.author.display_avatar.url if ctx.author.display_avatar else None)
    
    await ctx.send(embed=embed)

@helpstaff.error
async def helpstaff_error(ctx, error):
    if isinstance(error, commands.MissingRole):
        embed = discord.Embed(description="🛑 **Accès refusé** : Cette commande est strictement réservée aux membres de l'équipe Staff.", color=discord.Color.red())
        await ctx.send(embed=embed, delete_after=5)

# ---------------- PING ----------------
@bot.command()
async def ping(ctx):
    embed = discord.Embed(
        description=f"🌐 **Network** ➔ Latence mesurée à `{round(bot.latency * 1000)}ms` ⚡",
        color=discord.Color.teal()
    )
    await ctx.send(embed=embed)

# ---------------- CLEAR ----------------
@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int):
    await ctx.channel.purge(limit=amount + 1)
    embed = discord.Embed(
        description=f"🌌 **Nettoyage** ➔ `{amount} messages` balayés de la timeline.",
        color=discord.Color.dark_grey()
    )
    await ctx.send(embed=embed, delete_after=4)

# ---------------- WARN ----------------
@bot.command()
@commands.has_permissions(kick_members=True)
async def warn(ctx, member: discord.Member, *, reason="Aucune raison"):
    db_sanctions[member.id].append(reason)
    
    embed = discord.Embed(
        title="⚠️ ALERT / DOSSIER MISE À ZONE",
        description=f"Un avertissement officiel a été attribué à {member.mention}.",
        color=discord.Color.from_rgb(241, 196, 15)
    )
    embed.add_field(name="🧬 Cible", value=member.name, inline=True)
    embed.add_field(name="⚡ Opérateur", value=ctx.author.mention, inline=True)
    embed.add_field(name="📄 Motif", value=f"`{reason}`", inline=False)
    
    await ctx.send(embed=embed)
    await send_log(ctx.guild, f"⚠️ **WARN** | {member} | {reason} | Par : {ctx.author}")

# ---------------- SANCTIONS ----------------
@bot.command()
async def sanctions(ctx, member: discord.Member):
    if len(db_sanctions[member.id]) == 0:
        embed = discord.Embed(description=f"💎 **Casier propre** ➔ Aucun antécédent trouvé pour {member.mention}.", color=discord.Color.green())
        return await ctx.send(embed=embed)

    msg = "\n".join([f"📈 `{i+1}` ➔ {s}" for i, s in enumerate(db_sanctions[member.id])])
    
    embed = discord.Embed(
        title=f"🗂️ LOGS DE SÉCURITÉ : {member.name}",
        description=msg,
        color=discord.Color.orange()
    )
    await ctx.send(embed=embed)

# ---------------- CLEAR SANCTIONS ----------------
@bot.command()
@commands.has_permissions(kick_members=True)
async def clear_sanctions(ctx, member: discord.Member):
    db_sanctions[member.id].clear()
    
    embed = discord.Embed(
        description=f"🧼 **Réinitialisation** ➔ Le casier de {member.mention} a été entièrement purgé.",
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)
    await send_log(ctx.guild, f"🧼 **CLEAR_SANCTIONS** | {member} | Par : {ctx.author}")

# ---------------- KICK ----------------
@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason="Aucune raison"):
    try:
        await member.kick(reason=reason)
        embed = discord.Embed(
            title="☄️ EXPULSION IMMÉDIATE",
            description=f"Le sujet **{member.name}** a été déconnecté de la structure.",
            color=discord.Color.orange()
        )
        embed.add_field(name="📄 Motif", value=f"`{reason}`", inline=True)
        embed.add_field(name="⚡ Opérateur", value=ctx.author.mention, inline=True)
        
        await ctx.send(embed=embed)
        await send_log(ctx.guild, f"☄️ **KICK** | {member} | {reason} | Par : {ctx.author}")
    except:
        embed = discord.Embed(description="🛑 **Erreur** ➔ Autorisations insuffisantes.", color=discord.Color.red())
        await ctx.send(embed=embed)

# ---------------- BAN ----------------
@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason="Aucune raison"):
    try:
        await member.ban(reason=reason)
        embed = discord.Embed(
            title="💥 EXCLUSION DÉFINITIVE",
            description=f"L'accès au serveur a été révoqué à vie pour **{member.name}**.",
            color=discord.Color.red()
        )
        embed.add_field(name="📄 Motif", value=f"`{reason}`", inline=True)
        embed.add_field(name="⚡ Opérateur", value=ctx.author.mention, inline=True)
        
        await ctx.send(embed=embed)
        await send_log(ctx.guild, f"💥 **BAN** | {member} | {reason} | Par : {ctx.author}")
    except:
        embed = discord.Embed(description="🛑 **Erreur** ➔ Impossible de bannir cet utilisateur.", color=discord.Color.red())
        await ctx.send(embed=embed)

# ---------------- UNBAN ----------------
@bot.command()
@commands.has_permissions(ban_members=True)
async def unban(ctx, user_id: int):
    try:
        user = await bot.fetch_user(user_id)
        await ctx.guild.unban(user)
        embed = discord.Embed(
            description=f"🧬 **Réhabilitation** ➔ L'identifiant `{user.name}` a été débanni.",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
        await send_log(ctx.guild, f"🧬 **UNBAN** | {user} | Par : {ctx.author}")
    except:
        embed = discord.Embed(description="🛑 **Erreur** ➔ ID introuvable.", color=discord.Color.red())
        await ctx.send(embed=embed)

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
    embed = discord.Embed(description=f"🤫 **Mute** ➔ Les canaux d'écriture ont été verrouillés pour {member.mention}.", color=discord.Color.red())
    await ctx.send(embed=embed)
    await send_log(ctx.guild, f"🤫 **MUTE** | {member} | Par : {ctx.author}")

# ---------------- UNMUTE ----------------
@bot.command()
@commands.has_permissions(manage_roles=True)
async def unmute(ctx, member: discord.Member):
    role = discord.utils.get(ctx.guild.roles, name="Muted")
    if role and role in member.roles:
        await member.remove_roles(role)

    embed = discord.Embed(description=f"📣 **Unmute** ➔ Restrictions levées pour {member.mention}.", color=discord.Color.green())
    await ctx.send(embed=embed)
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
    embed = discord.Embed(description=f"⏳ **Tempmute** ➔ Isolation temporaire de {member.mention} pendant `{time}s`.", color=discord.Color.orange())
    await ctx.send(embed=embed)
    
    await asyncio.sleep(time)
    
    if role in member.roles:
        await member.remove_roles(role)
        embed_auto = discord.Embed(description=f"🔊 **Système** ➔ Rétablissement automatique de la parole pour {member.mention}.", color=discord.Color.green())
        await ctx.send(embed=embed_auto)

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
    role, staff = ctx.guild.get_role(ROLE_T), ctx.guild.get_role(ROLE_STAFF)
    if role: await member.add_roles(role)
    if staff: await member.add_roles(staff)
    embed = discord.Embed(description=f"🛠️ **Promotion** ➔ {member.mention} intègre l'équipe en tant que **Modo Test**.", color=discord.Color.teal())
    await ctx.send(embed=embed)

@bot.command(name="rank-c")
@commands.has_permissions(manage_roles=True)
async def rank_c(ctx, member: discord.Member):
    await remove_staff(member)
    role, staff = ctx.guild.get_role(ROLE_C), ctx.guild.get_role(ROLE_STAFF)
    if role: await member.add_roles(role)
    if staff: await member.add_roles(staff)
    embed = discord.Embed(description=f"💎 **Promotion** ➔ {member.mention} est titularisé au rang de **Modo Confirmé**.", color=discord.Color.blue())
    await ctx.send(embed=embed)

@bot.command(name="rank-plus")
@commands.has_permissions(manage_roles=True)
async def rank_plus(ctx, member: discord.Member):
    await remove_staff(member)
    role, staff = ctx.guild.get_role(ROLE_PLUS), ctx.guild.get_role(ROLE_STAFF)
    if role: await member.add_roles(role)
    if staff: await member.add_roles(staff)
    embed = discord.Embed(description=f"⚡ **Promotion** ➔ Évolution de {member.mention} affecté au poste de **Modo +**.", color=discord.Color.dark_blue())
    await ctx.send(embed=embed)

@bot.command(name="rank-s")
@commands.has_permissions(manage_roles=True)
async def rank_s(ctx, member: discord.Member):
    await remove_staff(member)
    role, staff = ctx.guild.get_role(ROLE_SENIOR), ctx.guild.get_role(ROLE_STAFF)
    if role: await member.add_roles(role)
    if staff: await member.add_roles(staff)
    embed = discord.Embed(description=f"✨ **Promotion** ➔ {member.mention} accède aux responsabilités de **Senior**.", color=discord.Color.purple())
    await ctx.send(embed=embed)

@bot.command(name="rank-admin")
@commands.has_permissions(manage_roles=True)
async def rank_admin(ctx, member: discord.Member):
    await remove_staff(member)
    role, staff = ctx.guild.get_role(ROLE_ADMIN), ctx.guild.get_role(ROLE_STAFF)
    if role: await member.add_roles(role)
    if staff: await member.add_roles(staff)
    embed = discord.Embed(description=f"🪐 **Haut-Commandement** ➔ {member.mention} prend ses fonctions d'**Administrateur**.", color=discord.Color.dark_purple())
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(manage_roles=True)
async def derank(ctx, member: discord.Member):
    await remove_staff(member)
    embed = discord.Embed(description=f"📉 **Destitution** ➔ {member.mention} a été démis de l'intégralité de ses fonctions.", color=discord.Color.light_grey())
    await ctx.send(embed=embed)
    await send_log(ctx.guild, f"📉 **DERANK** | {member} | Par : {ctx.author}")


# =========================================================
# 🎫 TICKET SYSTEM COMPLET 
# =========================================================

class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="📝 Ouvrir une candidature", 
        style=discord.ButtonStyle.blurple, 
        custom_id="ouvrir_ticket_permanent"
    )
    async def open(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        user = interaction.user
        category = guild.get_channel(TICKET_CATEGORY_ID)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True, embed_links=True),
            guild.get_role(ROLE_STAFF): discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True)
        }

        clean_name = user.name.lower().replace(" ", "-")
        channel = await guild.create_text_channel(
            name=f"ticket-{clean_name}",
            category=category,
            overwrites=overwrites
        )

        embed_welcome = discord.Embed(
            title=f"👋 Bienvenue sur ta candidature, {user.name} !",
            description=(
                f"Merci de l'intérêt que tu portes à **{guild.name}**.\n\n"
                "**📌 Prochaines étapes :**\n"
                "1. Présente-toi brièvement (âge, motivations, expériences).\n"
                "2. Reste patient, un membre de la direction va s'occuper de toi.\n\n"
                "📜 *Tout comportement inapproprié entraînera une sanction.*"
            ),
            color=discord.Color.purple(),
            timestamp=datetime.now()
        )
        embed_welcome.add_field(name="👤 Candidat", value=user.mention, inline=True)
        embed_welcome.add_field(name="👮 Responsable", value=f"<@{GERANT_STAFF_ID}>", inline=True)
        embed_welcome.set_footer(text="Commandes Staff : +add | +del | +rename | +close")

        await channel.send(content=f"{user.mention} 🔔 <@{GERANT_STAFF_ID}>", embed=embed_welcome)
        await interaction.response.send_message(f"✅ Ticket de candidature créé : {channel.mention}", ephemeral=True)


class CloseTicketModal(discord.ui.Modal):
    def __init__(self, status: str, color: discord.Color, channel_name: str, member: discord.Member):
        super().__init__(title=f"Traitement Candidature : {status}")
        self.status = status
        self.color = color
        self.channel_name = channel_name
        self.member = member

        self.reason = discord.ui.TextInput(label="Motif / Raison principale", placeholder="Ex: Excellent profil...", max_length=100, required=True)
        self.custom_msg = discord.ui.TextInput(label="Message personnalisé pour le candidat", style=discord.TextStyle.paragraph, placeholder="Écris ton message ici...", max_length=1000, required=True)

        self.add_item(self.reason)
        self.add_item(self.custom_msg)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        current_time = datetime.now().strftime("%d/%m/%Y à %H:%M")

        embed_mp = discord.Embed(
            title=f"📬 RÉSULTAT DE VOTRE CANDIDATURE : {self.status}",
            description=f"Bonjour {self.member.mention},\nVotre candidature sur le serveur **{interaction.guild.name}** a été traitée.",
            color=self.color,
            timestamp=datetime.now()
        )
        embed_mp.add_field(name="📋 Statut", value=f"**{self.status}**", inline=True)
        embed_mp.add_field(name="👮 Traité par", value=f"{interaction.user.mention}", inline=True)
        embed_mp.add_field(name
