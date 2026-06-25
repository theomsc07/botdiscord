import discord
from discord.ext import commands
import asyncio
from datetime import datetime
import os
import io

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CONFIGURATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="+", intents=intents)

TOKEN = os.getenv("DISCORD_TOKEN")

# Salons
LOG_CH_ID          = 1508595464168013965   # Salon logs général
TICKET_CAT_ID      = 1504792910892109935   # Catégorie tickets
TICKET_PANEL_CH_ID = 1504792916772786298   # Salon panneau recrutement
TRANSCRIPT_CH_ID   = 1507694850282094683   # Salon transcripts
ALERT_CH_ID        = 1507692397767954462   # Salon alerte protection

# Rôles
ROLE_STAFF   = 1504810257715822722
ROLE_MUTED   = 1509141375810011156
R_T          = 1504792771977023591
R_C          = 1504792768088903931
R_PLUS       = 1504792764448116776
R_SENIOR     = 1504792759679057951
R_ADMIN      = 1504792748098715660
ROLE_EXTRA1  = 1504823845981388860
ROLE_EXTRA2  = 1504792741811326986  # Fonda

# Gérant Staff (rôle à ping dans les tickets)
GERANT_STAFF_ID = 968588191055642624

# Membres protégés contre les sanctions
CO_FONDA_ID = 1504792745170960516
FONDA_ID    = 1504792741811326986   # ⚠️  C'est aussi l'ID d'un rôle (ROLE_EXTRA2) — ici c'est l'ID membre

# Tous les rôles staff à retirer lors d'un derank
ALL_STAFF_ROLES = [ROLE_STAFF, R_T, R_C, R_PLUS, R_SENIOR, R_ADMIN, ROLE_EXTRA1, ROLE_EXTRA2]

# Base de données des sanctions (en mémoire — perdu au redémarrage)
sanctions_db = {}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# UTILITAIRES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def now_str():
    """Retourne la date et l'heure formatées."""
    return datetime.now().strftime("%d/%m/%Y à %H:%M")

async def send_log(embed: discord.Embed):
    """Envoie un embed dans le salon de logs."""
    ch = bot.get_channel(LOG_CH_ID)
    if ch:
        await ch.send(embed=embed)

async def send_dm(member, embed: discord.Embed):
    """Envoie un DM à un membre. Silencieux en cas d'échec."""
    try:
        await member.send(embed=embed)
    except Exception:
        pass

def make_log_embed(title: str, color: int, author, member, reason: str = None, extra_fields: list = None) -> discord.Embed:
    """Crée un embed de log standard."""
    e = discord.Embed(title=title, color=color, timestamp=datetime.now())
    e.add_field(name="👤 Membre concerné", value=member.mention, inline=True)
    e.add_field(name="👮 Auteur de l'action", value=author.mention, inline=True)
    if reason:
        e.add_field(name="📜 Raison", value=reason, inline=False)
    if extra_fields:
        for name, value, inline in extra_fields:
            e.add_field(name=name, value=value, inline=inline)
    e.add_field(name="🕐 Date", value=now_str(), inline=False)
    e.set_thumbnail(url=member.display_avatar.url)
    e.set_footer(text="Système de Modération", icon_url=bot.user.display_avatar.url)
    return e

async def check_protected(ctx, member: discord.Member) -> bool:
    """
    Vérifie si le membre ciblé est un fondateur/co-fondateur protégé.
    Si oui :
      - Envoie une alerte dans ALERT_CH_ID avec ping des 2 rôles fondateurs.
      - Derank immédiat de l'auteur de la commande (sauf si c'est le owner).
    Retourne True si protégé (action bloquée), False sinon.
    """
    if member.id not in (CO_FONDA_ID, FONDA_ID):
        return False

    guild = ctx.guild

    # Le owner est exempt de toutes conséquences
    if ctx.author.id == guild.owner_id:
        await ctx.send("⛔ Cette personne est protégée et ne peut pas être sanctionnée.", delete_after=5)
        return True

    # Alerte dans le salon désigné
    alert_ch = bot.get_channel(ALERT_CH_ID)
    if alert_ch:
        embed_alert = discord.Embed(
            title="🚨 Tentative de sanction sur un Fondateur",
            description=(
                f"**{ctx.author.mention}** a tenté d'utiliser la commande `+{ctx.command.name}` "
                f"sur **{member.mention}**, qui est un membre fondateur protégé.\n\n"
                f"⚡ Un derank automatique a été appliqué à {ctx.author.mention}."
            ),
            color=0xff0000,
            timestamp=datetime.now()
        )
        embed_alert.add_field(name="🕐 Date", value=now_str(), inline=False)
        embed_alert.set_footer(text="Système de Protection", icon_url=bot.user.display_avatar.url)
        await alert_ch.send(
            content=f"<@&{CO_FONDA_ID}> <@&{FONDA_ID}>",
            embed=embed_alert
        )

    # Derank automatique de l'auteur
    for r_id in ALL_STAFF_ROLES:
        role = guild.get_role(r_id)
        if role and role in ctx.author.roles:
            await ctx.author.remove_roles(role)

    # Log du derank automatique
    embed_log = make_log_embed(
        title="⚡ DERANK AUTOMATIQUE — Protection Fondateur",
        color=0xff0000,
        author=bot.user,
        member=ctx.author,
        reason=f"Tentative de sanction sur un membre protégé ({member.mention})"
    )
    await send_log(embed_log)

    # DM à l'auteur sanctionné
    embed_dm = discord.Embed(
        title="⚡ Vous avez été dégradé automatiquement",
        description=(
            f"Vous avez tenté d'effectuer une action de modération sur un membre fondateur protégé.\n"
            f"En conséquence, **tous vos rôles staff ont été retirés automatiquement**."
        ),
        color=0xff0000,
        timestamp=datetime.now()
    )
    embed_dm.set_footer(text=guild.name)
    await send_dm(ctx.author, embed_dm)

    await ctx.send("⛔ Action bloquée. Cette personne est protégée. Un derank automatique a été appliqué.", delete_after=8)
    return True

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SYSTÈME DE TICKETS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TicketPanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Candidater",
        style=discord.ButtonStyle.primary,
        emoji="📩",
        custom_id="btn_candid"
    )
    async def btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        user  = interaction.user

        # Vérifier si l'utilisateur a déjà un ticket ouvert
        existing = discord.utils.get(guild.text_channels, name=f"ticket-{user.name.lower()}")
        if existing:
            await interaction.response.send_message(
                f"❌ Vous avez déjà un dossier ouvert : {existing.mention}",
                ephemeral=True
            )
            return

        category = guild.get_channel(TICKET_CAT_ID)
        gerant_role = guild.get_role(GERANT_STAFF_ID)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
        }
        if gerant_role:
            overwrites[gerant_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)

        channel = await guild.create_text_channel(
            name=f"ticket-{user.name.lower()}",
            category=category,
            overwrites=overwrites
        )

        embed = discord.Embed(
            title="◈ DOSSIER DE CANDIDATURE ◈",
            description=(
                f"Bonjour {user.mention}, bienvenue dans votre dossier de candidature.\n\n"
                f"Le staff prendra en charge votre demande dans les plus brefs délais.\n"
                f"Merci de patienter."
            ),
            color=0x5865f2,
            timestamp=datetime.now()
        )
        embed.set_thumbnail(url=guild.icon.url if guild.icon else bot.user.display_avatar.url)
        embed.set_footer(text=guild.name, icon_url=bot.user.display_avatar.url)

        ping_content = f"{user.mention}"
        if gerant_role:
            ping_content += f" | {gerant_role.mention}"

        await channel.send(content=ping_content, embed=embed)

        # DM au candidat
        embed_dm = discord.Embed(
            title="📩 Dossier de candidature ouvert",
            description=(
                f"Votre dossier de candidature sur **{guild.name}** a bien été créé.\n"
                f"Rendez-vous dans {channel.mention} pour suivre votre candidature."
            ),
            color=0x5865f2,
            timestamp=datetime.now()
        )
        embed_dm.set_footer(text=guild.name)
        await send_dm(user, embed_dm)

        # Log
        embed_log = discord.Embed(
            title="📩 TICKET OUVERT",
            color=0x5865f2,
            timestamp=datetime.now()
        )
        embed_log.add_field(name="👤 Candidat", value=user.mention, inline=True)
        embed_log.add_field(name="📁 Salon", value=channel.mention, inline=True)
        embed_log.add_field(name="🕐 Date", value=now_str(), inline=False)
        embed_log.set_footer(text="Système de Tickets", icon_url=bot.user.display_avatar.url)
        await send_log(embed_log)

        await interaction.response.send_message(
            f"✅ Votre dossier a été créé : {channel.mention}",
            ephemeral=True
        )

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ÉVÉNEMENTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@bot.event
async def on_ready():
    bot.add_view(TicketPanel())
    print(f"✅ Bot connecté : {bot.user} ({bot.user.id})")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRole):
        await ctx.send("❌ Vous n'avez pas les permissions nécessaires pour utiliser cette commande.", delete_after=6)
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ Vous n'avez pas les permissions nécessaires pour utiliser cette commande.", delete_after=6)
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send("❌ Membre introuvable. Vérifiez la mention ou l'identifiant.", delete_after=6)
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ Argument manquant : `{error.param.name}`. Vérifiez la syntaxe de la commande.", delete_after=6)
    elif isinstance(error, commands.BadArgument):
        await ctx.send("❌ Argument invalide. Vérifiez la syntaxe de la commande.", delete_after=6)
    else:
        raise error

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# COMMANDES — GESTION STAFF (Administrateurs)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@bot.command()
@commands.has_permissions(administrator=True)
async def rank_t(ctx, m: discord.Member):
    """Promeut un membre au rang Modérateur Test."""
    role_t    = ctx.guild.get_role(R_T)
    role_staff = ctx.guild.get_role(ROLE_STAFF)
    if role_t and role_staff:
        await m.add_roles(role_t, role_staff)

        embed_log = make_log_embed("⬆️ RANK-T — Modérateur Test", 0x57f287, ctx.author, m, "Promotion")
        await send_log(embed_log)

        embed_dm = discord.Embed(
            title="🎉 Félicitations — Promotion",
            description=f"Vous êtes désormais **Modérateur Test** sur **{ctx.guild.name}**.\nBienvenue dans l'équipe !",
            color=0x57f287, timestamp=datetime.now()
        )
        embed_dm.set_footer(text=ctx.guild.name)
        await send_dm(m, embed_dm)

        await ctx.send(f"✅ {m.mention} est désormais **Modérateur Test**.")

@bot.command()
@commands.has_permissions(administrator=True)
async def rank_c(ctx, m: discord.Member):
    """Promeut un membre au rang Modérateur Confirmé."""
    role = ctx.guild.get_role(R_C)
    if role:
        await m.add_roles(role)

        embed_log = make_log_embed("⬆️ RANK-C — Modérateur Confirmé", 0x57f287, ctx.author, m, "Promotion")
        await send_log(embed_log)

        embed_dm = discord.Embed(
            title="🎉 Félicitations — Promotion",
            description=f"Vous êtes désormais **Modérateur Confirmé** sur **{ctx.guild.name}**.",
            color=0x57f287, timestamp=datetime.now()
        )
        embed_dm.set_footer(text=ctx.guild.name)
        await send_dm(m, embed_dm)

        await ctx.send(f"✅ {m.mention} est désormais **Modérateur Confirmé**.")

@bot.command()
@commands.has_permissions(administrator=True)
async def rank_plus(ctx, m: discord.Member):
    """Promeut un membre au rang Modérateur+."""
    role = ctx.guild.get_role(R_PLUS)
    if role:
        await m.add_roles(role)

        embed_log = make_log_embed("⬆️ RANK-PLUS — Modérateur+", 0x57f287, ctx.author, m, "Promotion")
        await send_log(embed_log)

        embed_dm = discord.Embed(
            title="🎉 Félicitations — Promotion",
            description=f"Vous êtes désormais **Modérateur+** sur **{ctx.guild.name}**.",
            color=0x57f287, timestamp=datetime.now()
        )
        embed_dm.set_footer(text=ctx.guild.name)
        await send_dm(m, embed_dm)

        await ctx.send(f"✅ {m.mention} est désormais **Modérateur+**.")

@bot.command()
@commands.has_permissions(administrator=True)
async def rank_s(ctx, m: discord.Member):
    """Promeut un membre au rang Staff Senior."""
    role = ctx.guild.get_role(R_SENIOR)
    if role:
        await m.add_roles(role)

        embed_log = make_log_embed("⬆️ RANK-SENIOR — Staff Senior", 0x57f287, ctx.author, m, "Promotion")
        await send_log(embed_log)

        embed_dm = discord.Embed(
            title="🎉 Félicitations — Promotion",
            description=f"Vous êtes désormais **Staff Senior** sur **{ctx.guild.name}**.",
            color=0x57f287, timestamp=datetime.now()
        )
        embed_dm.set_footer(text=ctx.guild.name)
        await send_dm(m, embed_dm)

        await ctx.send(f"✅ {m.mention} est désormais **Staff Senior**.")

@bot.command()
@commands.has_permissions(administrator=True)
async def rank_admin(ctx, m: discord.Member):
    """Promeut un membre au rang Administrateur."""
    role = ctx.guild.get_role(R_ADMIN)
    if role:
        await m.add_roles(role)

        embed_log = make_log_embed("⬆️ RANK-ADMIN — Administrateur", 0x57f287, ctx.author, m, "Promotion")
        await send_log(embed_log)

        embed_dm = discord.Embed(
            title="🎉 Félicitations — Promotion",
            description=f"Vous êtes désormais **Administrateur** sur **{ctx.guild.name}**.",
            color=0x57f287, timestamp=datetime.now()
        )
        embed_dm.set_footer(text=ctx.guild.name)
        await send_dm(m, embed_dm)

        await ctx.send(f"✅ {m.mention} est désormais **Administrateur**.")

@bot.command()
@commands.has_permissions(administrator=True)
async def derank(ctx, m: discord.Member):
    """Retire tous les rôles staff d'un membre."""
    removed = []
    for r_id in ALL_STAFF_ROLES:
        role = ctx.guild.get_role(r_id)
        if role and role in m.roles:
            await m.remove_roles(role)
            removed.append(role.name)

    embed_log = make_log_embed(
        title="⬇️ DERANK — Dégradation",
        color=0xed4245,
        author=ctx.author,
        member=m,
        reason="Dégradation",
        extra_fields=[("🗑️ Rôles retirés", ", ".join(removed) if removed else "Aucun rôle staff détecté", False)]
    )
    await send_log(embed_log)

    embed_dm = discord.Embed(
        title="⬇️ Dégradation",
        description=f"Vous avez été dégradé sur **{ctx.guild.name}**.\nTous vos rôles staff ont été retirés.",
        color=0xed4245, timestamp=datetime.now()
    )
    embed_dm.set_footer(text=ctx.guild.name)
    await send_dm(m, embed_dm)

    await ctx.send(f"✅ {m.mention} a été dégradé avec succès.")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# COMMANDES — MODÉRATION (Staff)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@bot.command()
@commands.has_role(ROLE_STAFF)
async def ping(ctx):
    """Affiche la latence du bot."""
    await ctx.send(f"🏓 Pong ! Latence : **{round(bot.latency * 1000)}ms**")

@bot.command()
@commands.has_role(ROLE_STAFF)
async def warn(ctx, m: discord.Member, *, reason: str = "Aucune raison précisée"):
    """Avertit un membre."""
    if await check_protected(ctx, m):
        return

    if m.id not in sanctions_db:
        sanctions_db[m.id] = []
    sanctions_db[m.id].append(f"• **WARN** | {now_str()} | Raison : {reason}")

    embed_log = make_log_embed("⚠️ WARN — Avertissement", 0xfee75c, ctx.author, m, reason)
    await send_log(embed_log)

    embed_dm = discord.Embed(
        title="⚠️ Vous avez reçu un avertissement",
        description=f"**Raison :** {reason}\n**Serveur :** {ctx.guild.name}",
        color=0xfee75c, timestamp=datetime.now()
    )
    embed_dm.set_footer(text=ctx.guild.name)
    await send_dm(m, embed_dm)

    await ctx.send(f"⚠️ {m.mention} a reçu un avertissement.")

@bot.command()
@commands.has_role(ROLE_STAFF)
async def ban(ctx, m: discord.Member, *, reason: str = "Aucune raison précisée"):
    """Bannit un membre."""
    if await check_protected(ctx, m):
        return

    embed_dm = discord.Embed(
        title="🔨 Vous avez été banni",
        description=f"**Raison :** {reason}\n**Serveur :** {ctx.guild.name}",
        color=0xed4245, timestamp=datetime.now()
    )
    embed_dm.set_footer(text=ctx.guild.name)
    await send_dm(m, embed_dm)

    await m.ban(reason=reason)

    embed_log = make_log_embed("🔨 BAN — Bannissement", 0xed4245, ctx.author, m, reason)
    await send_log(embed_log)

    await ctx.send(f"✅ {m.mention} a été banni du serveur.")

@bot.command()
@commands.has_role(ROLE_STAFF)
async def kick(ctx, m: discord.Member, *, reason: str = "Aucune raison précisée"):
    """Expulse un membre du serveur."""
    if await check_protected(ctx, m):
        return

    embed_dm = discord.Embed(
        title="👢 Vous avez été expulsé",
        description=f"**Raison :** {reason}\n**Serveur :** {ctx.guild.name}",
        color=0xfaa61a, timestamp=datetime.now()
    )
    embed_dm.set_footer(text=ctx.guild.name)
    await send_dm(m, embed_dm)

    await m.kick(reason=reason)

    embed_log = make_log_embed("👢 KICK — Expulsion", 0xfaa61a, ctx.author, m, reason)
    await send_log(embed_log)

    await ctx.send(f"✅ {m.mention} a été expulsé du serveur.")

@bot.command()
@commands.has_role(ROLE_STAFF)
async def unban(ctx, user_id: int):
    """Débannit un utilisateur via son ID."""
    try:
        user = await bot.fetch_user(user_id)
        await ctx.guild.unban(user)

        embed_log = make_log_embed("✅ UNBAN — Débannissement", 0x57f287, ctx.author, user, "Débannissement manuel")
        await send_log(embed_log)

        embed_dm = discord.Embed(
            title="✅ Vous avez été débanni",
            description=f"Vous avez été débanni de **{ctx.guild.name}**.",
            color=0x57f287, timestamp=datetime.now()
        )
        embed_dm.set_footer(text=ctx.guild.name)
        await send_dm(user, embed_dm)

        await ctx.send(f"✅ L'utilisateur **{user.name}** a été débanni.")
    except discord.NotFound:
        await ctx.send("❌ Utilisateur introuvable ou non banni.")

@bot.command()
@commands.has_role(ROLE_STAFF)
async def mute(ctx, m: discord.Member, *, reason: str = "Aucune raison précisée"):
    """Mute un membre indéfiniment."""
    if await check_protected(ctx, m):
        return

    role = ctx.guild.get_role(ROLE_MUTED)
    if not role:
        await ctx.send("❌ Le rôle Muted est introuvable.")
        return

    await m.add_roles(role)

    embed_log = make_log_embed("🔇 MUTE — Mise en sourdine", 0xfaa61a, ctx.author, m, reason)
    await send_log(embed_log)

    embed_dm = discord.Embed(
        title="🔇 Vous avez été mis en sourdine",
        description=f"**Raison :** {reason}\n**Serveur :** {ctx.guild.name}\n\nContactez le staff pour plus d'informations.",
        color=0xfaa61a, timestamp=datetime.now()
    )
    embed_dm.set_footer(text=ctx.guild.name)
    await send_dm(m, embed_dm)

    await ctx.send(f"✅ {m.mention} a été mis en sourdine.")

@bot.command()
@commands.has_r
