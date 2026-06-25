import discord
from discord.ext import commands
import asyncio
from datetime import datetime
import os
import io
import json
import time

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="+", intents=intents)

TOKEN = os.getenv("DISCORD_TOKEN")
START_TIME = time.time()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CONFIGURATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

LOG_CH_ID          = 1508595464168013965
TICKET_CAT_ID      = 1504792910892109935
TICKET_PANEL_CH_ID = 1504792916772786298
TRANSCRIPT_CH_ID   = 1507694850282094683
ALERT_CH_ID        = 1507692397767954462

ROLE_STAFF  = 1504810257715822722
ROLE_MUTED  = 1509141375810011156
R_T         = 1504792771977023591
R_C         = 1504792768088903931
R_PLUS      = 1504792764448116776
R_SENIOR    = 1504792759679057951
R_ADMIN     = 1504792748098715660
ROLE_EXTRA1 = 1504823845981388860
ROLE_EXTRA2 = 1504792741811326986

GERANT_STAFF_ID = 968588191055642624
CO_FONDA_ID     = 1504792745170960516
FONDA_ID        = 1504792741811326986
OWNER_ID        = 968588191055642624

ALL_STAFF_ROLES = [ROLE_STAFF, R_T, R_C, R_PLUS, R_SENIOR, R_ADMIN, ROLE_EXTRA1, ROLE_EXTRA2]
STAFF_ROLES_IDS = [R_T, R_C, R_PLUS, R_SENIOR, R_ADMIN]

BLACKLIST_FILE  = "blacklist.json"
SANCTIONS_FILE  = "sanctions.json"
NOTES_FILE      = "notes.json"

sanctions_db = {}
notes_db     = {}
blacklist_db = {}

stats_db = {
    "warn": 0, "kick": 0, "ban": 0, "unban": 0,
    "mute": 0, "unmute": 0, "tempmute": 0, "tempban": 0,
    "derank": 0, "bl": 0
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PERSISTANCE JSON
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def load_data():
    global blacklist_db, sanctions_db, notes_db
    for fname, ref in [(BLACKLIST_FILE, "bl"), (SANCTIONS_FILE, "sc"), (NOTES_FILE, "no")]:
        if os.path.exists(fname):
            with open(fname, "r") as f:
                if ref == "bl":
                    blacklist_db = json.load(f)
                elif ref == "sc":
                    sanctions_db_raw = json.load(f)
                    sanctions_db.clear()
                    for k, v in sanctions_db_raw.items():
                        sanctions_db[int(k)] = v
                else:
                    notes_db_raw = json.load(f)
                    notes_db.clear()
                    for k, v in notes_db_raw.items():
                        notes_db[int(k)] = v

def save_blacklist():
    with open(BLACKLIST_FILE, "w") as f:
        json.dump(blacklist_db, f, indent=2)

def save_sanctions():
    out = {str(k): v for k, v in sanctions_db.items()}
    with open(SANCTIONS_FILE, "w") as f:
        json.dump(out, f, indent=2)

def save_notes():
    out = {str(k): v for k, v in notes_db.items()}
    with open(NOTES_FILE, "w") as f:
        json.dump(out, f, indent=2)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# UTILITAIRES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def now_str():
    return datetime.now().strftime("%d/%m/%Y a %H:%M")

def uptime_str():
    secs = int(time.time() - START_TIME)
    h, rem = divmod(secs, 3600)
    m, s = divmod(rem, 60)
    return str(h) + "h " + str(m) + "m " + str(s) + "s"

async def send_log(embed):
    ch = bot.get_channel(LOG_CH_ID)
    if ch:
        await ch.send(embed=embed)

async def send_dm(member, embed):
    try:
        await member.send(embed=embed)
    except Exception:
        pass

def make_embed(title, color, member=None, author=None, reason=None, extra_fields=None):
    e = discord.Embed(title=title, color=color, timestamp=datetime.now())
    if member:
        e.add_field(name="👤 Membre", value=member.mention, inline=True)
        e.set_thumbnail(url=member.display_avatar.url)
    if author:
        e.add_field(name="👮 Auteur", value=author.mention, inline=True)
    if reason:
        e.add_field(name="📜 Raison", value=reason, inline=False)
    if extra_fields:
        for fname, fvalue, finline in extra_fields:
            e.add_field(name=fname, value=fvalue, inline=finline)
    e.add_field(name="🕐 Date", value=now_str(), inline=False)
    if bot.user:
        e.set_footer(text="Systeme de Moderation", icon_url=bot.user.display_avatar.url)
    return e

def has_role_id(member, role_id):
    return any(r.id == role_id for r in member.roles)

def get_staff_level(member):
    for r_id in [R_ADMIN, R_SENIOR, R_PLUS, R_C, R_T]:
        if has_role_id(member, r_id):
            return r_id
    return None

def is_staff(member):
    return get_staff_level(member) is not None

async def auto_derank(guild, member):
    for r_id in ALL_STAFF_ROLES:
        role = guild.get_role(r_id)
        if role and role in member.roles:
            try:
                await member.remove_roles(role)
            except discord.Forbidden:
                pass

async def send_alert(ctx, target, extra=""):
    alert_ch = bot.get_channel(ALERT_CH_ID)
    if not alert_ch:
        return
    e = discord.Embed(title="🚨 TENTATIVE SUR UN MEMBRE PROTEGE", color=0xff0000, timestamp=datetime.now())
    e.add_field(name="👤 Auteur", value=ctx.author.mention + " (`" + str(ctx.author.id) + "`)", inline=False)
    e.add_field(name="🎯 Cible", value=target.mention + " (`" + str(target.id) + "`)", inline=False)
    e.add_field(name="⚙️ Commande", value="`+" + str(ctx.command.name) + "`", inline=True)
    e.add_field(name="📁 Salon", value=ctx.channel.mention, inline=True)
    e.add_field(name="🕐 Date", value=now_str(), inline=False)
    if extra:
        e.add_field(name="ℹ️ Info", value=extra, inline=False)
    e.add_field(name="⚡ Consequence", value="Derank automatique applique", inline=False)
    e.set_thumbnail(url=ctx.author.display_avatar.url)
    e.set_footer(text="Systeme de Protection", icon_url=bot.user.display_avatar.url)
    await alert_ch.send(
        content="<@" + str(OWNER_ID) + "> <@&" + str(CO_FONDA_ID) + "> <@&" + str(FONDA_ID) + ">",
        embed=e
    )

async def alert_staff_on_staff(ctx, target):
    alert_ch = bot.get_channel(ALERT_CH_ID)
    if not alert_ch:
        return
    e = discord.Embed(title="🚨 TENTATIVE DE SANCTION INTER-STAFF", color=0xff4400, timestamp=datetime.now())
    e.add_field(name="👤 Auteur", value=ctx.author.mention + " (`" + str(ctx.author.id) + "`)", inline=False)
    e.add_field(name="🎯 Cible (Staff)", value=target.mention + " (`" + str(target.id) + "`)", inline=False)
    e.add_field(name="⚙️ Commande", value="`+" + str(ctx.command.name) + "`", inline=True)
    e.add_field(name="📁 Salon", value=ctx.channel.mention, inline=True)
    e.add_field(name="🕐 Date", value=now_str(), inline=False)
    e.add_field(name="⚡ Consequence", value="Derank automatique applique a " + ctx.author.mention, inline=False)
    e.set_thumbnail(url=ctx.author.display_avatar.url)
    e.set_footer(text="Systeme de Protection Inter-Staff", icon_url=bot.user.display_avatar.url)
    await alert_ch.send(
        content="<@" + str(OWNER_ID) + "> <@&" + str(CO_FONDA_ID) + "> <@&" + str(FONDA_ID) + ">",
        embed=e
    )

async def check_protected(ctx, member):
    PROTECTED_IDS = (CO_FONDA_ID, FONDA_ID, OWNER_ID)
    if member.id not in PROTECTED_IDS:
        return False
    if ctx.author.id == OWNER_ID:
        await ctx.send("Cette personne est protegee.", delete_after=5)
        return True
    await send_alert(ctx, member)
    await auto_derank(ctx.guild, ctx.author)
    await send_log(make_embed("DERANK AUTO - Protection fondateur", 0xff0000, ctx.author, bot.user, "Tentative sur membre protege"))
    dm = discord.Embed(title="Vous avez ete degrade", description="Tentative sur membre protege (`+" + str(ctx.command.name) + "`).\nTous vos roles staff ont ete retires.", color=0xff0000, timestamp=datetime.now())
    dm.set_footer(text=ctx.guild.name)
    await send_dm(ctx.author, dm)
    await ctx.send("Action bloquee. Derank applique.", delete_after=8)
    return True

async def check_staff_on_staff(ctx, member):
    if member.id == ctx.author.id:
        await ctx.send("Vous ne pouvez pas vous sanctionner vous-meme.", delete_after=5)
        return True
    if is_staff(member):
        await alert_staff_on_staff(ctx, member)
        await auto_derank(ctx.guild, ctx.author)
        await send_log(make_embed("DERANK AUTO - Sanction inter-staff", 0xff4400, ctx.author, bot.user, "Tentative de +" + str(ctx.command.name) + " sur " + str(member.mention)))
        dm = discord.Embed(title="Vous avez ete degrade", description="Vous avez tente de sanctionner un autre membre du staff (`+" + str(ctx.command.name) + "`).\nTous vos roles ont ete retires.", color=0xff4400, timestamp=datetime.now())
        dm.set_footer(text=ctx.guild.name)
        await send_dm(ctx.author, dm)
        await ctx.send("Action bloquee. Vous ne pouvez pas sanctionner un autre staff. Derank applique.", delete_after=8)
        return True
    return False

def owner_only():
    async def predicate(ctx):
        if ctx.author.id != OWNER_ID:
            await auto_derank(ctx.guild, ctx.author)
            alert_ch = bot.get_channel(ALERT_CH_ID)
            if alert_ch:
                e = discord.Embed(title="🚨 COMMANDE RESERVEE AU OWNER", color=0xff0000, timestamp=datetime.now())
                e.add_field(name="👤 Auteur", value=ctx.author.mention + " (`" + str(ctx.author.id) + "`)", inline=False)
                e.add_field(name="⚙️ Commande tentee", value="`+" + str(ctx.command.name) + "`", inline=True)
                e.add_field(name="📁 Salon", value=ctx.channel.mention, inline=True)
                e.add_field(name="🕐 Date", value=now_str(), inline=False)
                e.add_field(name="⚡ Consequence", value="Derank automatique applique", inline=False)
                e.set_thumbnail(url=ctx.author.display_avatar.url)
                e.set_footer(text="Systeme de Protection", icon_url=bot.user.display_avatar.url)
                await alert_ch.send(
                    content="<@" + str(OWNER_ID) + "> <@&" + str(CO_FONDA_ID) + "> <@&" + str(FONDA_ID) + ">",
                    embed=e
                )
            dm = discord.Embed(title="Commande interdite", description="Vous avez tente d utiliser `+" + str(ctx.command.name) + "` qui est reservee au owner.\nTous vos roles staff ont ete retires.", color=0xff0000, timestamp=datetime.now())
            dm.set_footer(text=ctx.guild.name)
            await send_dm(ctx.author, dm)
            try:
                await ctx.message.delete()
            except Exception:
                pass
            return False
        return True
    return commands.check(predicate)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# EVENEMENTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@bot.event
async def on_ready():
    load_data()
    bot.add_view(TicketPanel())
    print("Bot connecte : " + str(bot.user))

@bot.event
async def on_member_join(member):
    uid = str(member.id)
    if uid in blacklist_db:
        entry = blacklist_db[uid]
        dm = discord.Embed(title="Vous etes blackliste", description="Vous etes blackliste de **" + member.guild.name + "** de facon permanente.\n**Raison :** " + entry.get("reason", "Aucune"), color=0xff0000, timestamp=datetime.now())
        dm.set_footer(text=member.guild.name)
        await send_dm(member, dm)
        await member.ban(reason="Blacklist permanente : " + entry.get("reason", "Aucune"))

@bot.event
async def on_command(ctx):
    if ctx.author.bot:
        return
    if not is_staff(ctx.author) and ctx.author.id != OWNER_ID:
        try:
            await ctx.message.delete()
        except Exception:
            pass
        raise commands.CheckFailure("no_perm")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        if "no_perm" in str(error):
            return
        return
    if isinstance(error, commands.MissingRole):
        await ctx.send("Vous n avez pas les permissions necessaires.", delete_after=6)
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("Vous n avez pas les permissions necessaires.", delete_after=6)
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send("Membre introuvable.", delete_after=6)
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Argument manquant.", delete_after=6)
    elif isinstance(error, commands.BadArgument):
        await ctx.send("Argument invalide.", delete_after=6)
    elif isinstance(error, commands.CommandOnCooldown):
        await ctx.send("Cooldown : reessayez dans " + str(round(error.retry_after, 1)) + "s.", delete_after=5)
    else:
        raise error

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TICKET PANEL
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TicketPanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Candidater", style=discord.ButtonStyle.primary, emoji="📩", custom_id="btn_candid")
    async def btn(self, interaction, button):
        guild = interaction.guild
        user = interaction.user
        existing = discord.utils.get(guild.text_channels, name="ticket-" + user.name.lower())
        if existing:
            await interaction.response.send_message("Vous avez deja un dossier ouvert : " + existing.mention, ephemeral=True)
            return
        category = guild.get_channel(TICKET_CAT_ID)
        gerant_role = guild.get_role(GERANT_STAFF_ID)
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
        }
        if gerant_role:
            overwrites[gerant_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)
        channel = await guild.create_text_channel(name="ticket-" + user.name.lower(), category=category, overwrites=overwrites)
        embed = discord.Embed(title="◈ DOSSIER DE CANDIDATURE ◈", description="Bonjour " + user.mention + ", bienvenue dans votre dossier.\n\nLe staff traitera votre demande dans les plus brefs delais.\nMerci de patienter.", color=0x5865f2, timestamp=datetime.now())
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        embed.set_footer(text=guild.name, icon_url=bot.user.display_avatar.url)
        ping = user.mention
        if gerant_role:
            ping = ping + " | " + gerant_role.mention
        await channel.send(content=ping, embed=embed, view=TicketActions())
        dm = discord.Embed(title="📩 Dossier ouvert", description="Votre dossier sur **" + guild.name + "** a ete cree.\nRendez-vous dans " + channel.mention + ".", color=0x5865f2, timestamp=datetime.now())
        dm.set_footer(text=guild.name)
        await send_dm(user, dm)
        e_log = discord.Embed(title="📩 TICKET OUVERT", color=0x5865f2, timestamp=datetime.now())
        e_log.add_field(name="👤 Candidat", value=user.mention, inline=True)
        e_log.add_field(name="📁 Salon", value=channel.mention, inline=True)
        e_log.add_field(name="🕐 Date", value=now_str(), inline=False)
        e_log.set_footer(text="Systeme de Tickets", icon_url=bot.user.display_avatar.url)
        await send_log(e_log)
        await interaction.response.send_message("Votre dossier a ete cree : " + channel.mention, ephemeral=True)

class TicketActions(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Accepter", style=discord.ButtonStyle.success, emoji="✅", custom_id="btn_accept")
    async def accept(self, interaction, button):
        if not is_staff(interaction.user):
            await interaction.response.send_message("Vous n avez pas la permission.", ephemeral=True)
            return
        candidate = None
        async for msg in interaction.channel.history(limit=100, oldest_first=True):
            if not msg.author.bot:
                candidate = msg.author
                break
        embed = discord.Embed(title="✅ Candidature Acceptee", description="Votre candidature a ete **acceptee** par " + interaction.user.mention + ".\nFelicitations et bienvenue dans l equipe !", color=0x57f287, timestamp=datetime.now())
        embed.set_footer(text=interaction.guild.name, icon_url=bot.user.display_avatar.url)
        await interaction.channel.send(embed=embed)
        if candidate:
            dm = discord.Embed(title="✅ Candidature Acceptee", description="Votre candidature sur **" + interaction.guild.name + "** a ete **acceptee** !\nFelicitations et bienvenue dans l equipe !", color=0x57f287, timestamp=datetime.now())
            dm.set_footer(text=interaction.guild.name)
            await send_dm(candidate, dm)
        e_log = discord.Embed(title="✅ CANDIDATURE ACCEPTEE", color=0x57f287, timestamp=datetime.now())
        e_log.add_field(name="👤 Candidat", value=candidate.mention if candidate else "Inconnu", inline=True)
        e_log.add_field(name="👮 Accepte par", value=interaction.user.mention, inline=True)
        e_log.add_field(name="🕐 Date", value=now_str(), inline=False)
        e_log.set_footer(text="Systeme de Tickets", icon_url=bot.user.display_avatar.url)
        await send_log(e_log)
        await interaction.response.send_message("Candidature acceptee.", ephemeral=True)
        self.stop()

    @discord.ui.button(label="Refuser", style=discord.ButtonStyle.danger, emoji="❌", custom_id="btn_refuse")
    async def refuse(self, interaction, button):
        if not is_staff(interaction.user):
            await interaction.response.send_message("Vous n avez pas la permission.", ephemeral=True)
            return
        candidate = None
        async for msg in interaction.channel.history(limit=100, oldest_first=True):
            if not msg.author.bot:
                candidate = msg.author
                break
        embed = discord.Embed(title="❌ Candidature Refusee", description="Votre candidature a ete **refusee** par " + interaction.user.mention + ".\nNous vous souhaitons bonne continuation.", color=0xed4245, timestamp=datetime.now())
        embed.set_footer(text=interaction.guild.name, icon_url=bot.user.display_avatar.url)
        await interaction.channel.send(embed=embed)
        if candidate:
            dm = discord.Embed(title="❌ Candidature Refusee", description="Votre candidature sur **" + interaction.guild.name + "** a ete **refusee**.\nNous vous souhaitons bonne continuation.", color=0xed4245, timestamp=datetime.now())
            dm.set_footer(text=interaction.guild.name)
            await send_dm(candidate, dm)
        e_log = discord.Embed(title="❌ CANDIDATURE REFUSEE", color=0xed4245, timestamp=datetime.now())
        e_log.add_field(name="👤 Candidat", value=candidate.mention if candidate else "Inconnu", inline=True)
        e_log.add_field(name="👮 Refuse par", value=interaction.user.mention, inline=True)
        e_log.add_field(name="🕐 Date", value=now_str(), inline=False)
        e_log.set_footer(text="Systeme de Tickets", icon_url=bot.user.display_avatar.url)
        await send_log(e_log)
        await interaction.response.send_message("Candidature refusee.", ephemeral=True)
        self.stop()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# COMMANDES OWNER UNIQUEMENT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@bot.command()
@owner_only()
@commands.cooldown(1, 3, commands.BucketType.user)
async def rank_t(ctx, *, member_str):
    m = await commands.MemberConverter().convert(ctx, member_str)
    role_t = ctx.guild.get_role(R_T)
    role_staff = ctx.guild.get_role(ROLE_STAFF)
    if role_t and role_staff:
        await m.add_roles(role_t, role_staff)
        await send_log(make_embed("⬆️ RANK-T — Moderateur Test", 0x57f287, m, ctx.author, "Promotion"))
        dm = discord.Embed(title="🎉 Promotion — Moderateur Test", description="Vous etes desormais **Moderateur Test** sur **" + ctx.guild.name + "**.\nBienvenue dans l equipe !", color=0x57f287, timestamp=datetime.now())
        dm.set_footer(text=ctx.guild.name)
        await send_dm(m, dm)
        await ctx.send(m.mention + " est desormais **Moderateur Test**.")

@bot.command()
@owner_only()
@commands.cooldown(1, 3, commands.BucketType.user)
async def rank_c(ctx, *, member_str):
    m = await commands.MemberConverter().convert(ctx, member_str)
    role = ctx.guild.get_role(R_C)
    if role:
        await m.add_roles(role)
        await send_log(make_embed("⬆️ RANK-C — Moderateur Confirme", 0x57f287, m, ctx.author, "Promotion"))
        dm = discord.Embed(title="🎉 Promotion — Moderateur Confirme", description="Vous etes desormais **Moderateur Confirme** sur **" + ctx.guild.name + "**.", color=0x57f287, timestamp=datetime.now())
        dm.set_footer(text=ctx.guild.name)
        await send_dm(m, dm)
        await ctx.send(m.mention + " est desormais **Moderateur Confirme**.")

@bot.command()
@owner_only()
@commands.cooldown(1, 3, commands.BucketType.user)
async def rank_plus(ctx, *, member_str):
    m = await commands.MemberConverter().convert(ctx, member_str)
    role = ctx.guild.get_role(R_PLUS)
    if role:
        await m.add_roles(role)
        await send_log(make_embed("⬆️ RANK-PLUS — Moderateur+", 0x57f287, m, ctx.author, "Promotion"))
        dm = discord.Embed(title="🎉 Promotion — Moderateur+", description="Vous etes desormais **Moderateur+** sur **" + ctx.guild.name + "**.", color=0x57f287, timestamp=datetime.now())
        dm.set_footer(text=ctx.guild.name)
        await send_dm(m, dm)
        await ctx.send(m.mention + " est desormais **Moderateur+**.")

@bot.command()
@owner_only()
@commands.cooldown(1, 3, commands.BucketType.user)
async def rank_s(ctx, *, member_str):
    m = await commands.MemberConverter().convert(ctx, member_str)
    role = ctx.guild.get_role(R_SENIOR)
    if role:
        await m.add_roles(role)
        await send_log(make_embed("⬆️ RANK-SENIOR — Staff Senior", 0x57f287, m, ctx.author, "Promotion"))
        dm = discord.Embed(title="🎉 Promotion — Staff Senior", description="Vous etes desormais **Staff Senior** sur **" + ctx.guild.name + "**.", color=0x57f287, timestamp=datetime.now())
        dm.set_footer(text=ctx.guild.name)
        await send_dm(m, dm)
        await ctx.send(m.mention + " est desormais **Staff Senior**.")

@bot.command()
@owner_only()
@commands.cooldown(1, 3, commands.BucketType.user)
async def rank_admin(ctx, *, member_str):
    m = await commands.MemberConverter().convert(ctx, member_str)
    role = ctx.guild.get_role(R_ADMIN)
    if role:
        await m.add_roles(role)
        await send_log(make_embed("⬆️ RANK-ADMIN — Administrateur", 0x57f287, m, ctx.author, "Promotion"))
        dm = discord.Embed(title="🎉 Promotion — Administrateur", description="Vous etes desormais **Administrateur** sur **" + ctx.guild.name + "**.", color=0x57f287, timestamp=datetime.now())
        dm.set_footer(text=ctx.guild.name)
        await send_dm(m, dm)
        await ctx.send(m.mention + " est desormais **Administrateur**.")

@bot.command()
@owner_only()
@commands.cooldown(1, 3, commands.BucketType.user)
async def derank(ctx, *, member_str):
    m = await commands.MemberConverter().convert(ctx, member_str)
    removed = []
    for r_id in ALL_STAFF_ROLES:
        role = ctx.guild.get_role(r_id)
        if role and role in m.roles:
            try:
                await m.remove_roles(role)
                removed.append(role.name)
            except discord.Forbidden:
                pass
    stats_db["derank"] += 1
    await send_log(make_embed("⬇️ DERANK — Degradation", 0xed4245, m, ctx.author, "Degradation", [("🗑️ Roles retires", ", ".join(removed) if removed else "Aucun", False)]))
    dm = discord.Embed(title="⬇️ Degradation", description="Vous avez ete degrade sur **" + ctx.guild.name + "**.\nTous vos roles staff ont ete retires.", color=0xed4245, timestamp=datetime.now())
    dm.set_footer(text=ctx.guild.name)
    await send_dm(m, dm)
    await ctx.send(m.mention + " a ete degrade avec succes.")

@bot.command()
@owner_only()
@commands.cooldown(1, 3, commands.BucketType.user)
async def unban(ctx, user_id_str):
    uid = str(user_id_str).strip("<@!>")
    if uid in blacklist_db:
        await ctx.send("Cet utilisateur est en blacklist permanente. Utilisez `+unbl` pour le retirer.", delete_after=8)
        return
    try:
        user = await bot.fetch_user(int(uid))
        await ctx.guild.unban(user)
        await send_log(make_embed("✅ UNBAN", 0x57f287, user, ctx.author, "Debannissement manuel"))
        dm = discord.Embed(title="✅ Vous avez ete debanni", description="Vous avez ete debanni de **" + ctx.guild.name + "**.", color=0x57f287, timestamp=datetime.now())
        dm.set_footer(text=ctx.guild.name)
        await send_dm(user, dm)
        await ctx.send("**" + user.name + "** a ete debanni.")
    except discord.NotFound:
        await ctx.send("Utilisateur introuvable ou non banni.")

@bot.command()
@owner_only()
@commands.cooldown(1, 3, commands.BucketType.user)
async def bl(ctx, member_str, *, reason="Aucune raison precisee"):
    try:
        m = await commands.MemberConverter().convert(ctx, member_str)
        user_id = m.id
        username = m.name
        dm = discord.Embed(title="🔒 Vous avez ete blackliste", description="Vous avez ete blackliste de **" + ctx.guild.name + "** de facon permanente.\n**Raison :** " + reason, color=0xff0000, timestamp=datetime.now())
        dm.set_footer(text=ctx.guild.name)
        await send_dm(m, dm)
        await m.ban(reason="Blacklist permanente : " + reason)
    except Exception:
        try:
            user = await bot.fetch_user(int(member_str))
            user_id = user.id
            username = user.name
            await ctx.guild.ban(user, reason="Blacklist permanente : " + reason)
        except Exception:
            await ctx.send("Membre introuvable.")
            return
    blacklist_db[str(user_id)] = {"name": username, "reason": reason, "date": now_str(), "by": str(ctx.author.id)}
    save_blacklist()
    stats_db["bl"] += 1
    e_log = discord.Embed(title="🔒 BLACKLIST — Ajout", color=0xff0000, timestamp=datetime.now())
    e_log.add_field(name="👤 Membre", value="<@" + str(user_id) + "> (`" + str(user_id) + "`)", inline=True)
    e_log.add_field(name="👮 Auteur", value=ctx.author.mention, inline=True)
    e_log.add_field(name="📜 Raison", value=reason, inline=False)
    e_log.add_field(name="🕐 Date", value=now_str(), inline=False)
    e_log.set_footer(text="Systeme Blacklist", icon_url=bot.user.display_avatar.url)
    await send_log(e_log)
    await ctx.send("<@" + str(user_id) + "> a ete blackliste de facon permanente.")

@bot.command()
@owner_only()
@commands.cooldown(1, 3, commands.BucketType.user)
async def unbl(ctx, user_id_str):
    uid = str(user_id_str).strip("<@!>")
    if uid not in blacklist_db:
        await ctx.send("Cet utilisateur n est pas dans la blacklist.")
        return
    try:
        user = await bot.fetch_user(int(uid))
        await ctx.guild.unban(user, reason="Retrait blacklist par owner")
        name = user.name
    except Exception:
        name = blacklist_db[uid].get("name", uid)
    del blacklist_db[uid]
    save_blacklist()
    e_log = discord.Embed(title="🔓 BLACKLIST — Retrait", color=0x57f287, timestamp=datetime.now())
    e_log.add_field(name="👤 Membre", value="<@" + uid + "> (`" + uid + "`)", inline=True)
    e_log.add_field(name="👮 Auteur", value=ctx.author.mention, inline=True)
    e_log.add_field(name="🕐 Date", value=now_str(), inline=False)
    e_log.set_footer(text="Systeme Blacklist", icon_url=bot.user.display_avatar.url)
    await send_log(e_log)
    await ctx.send("**" + name + "** a ete retire de la blacklist.")

@bot.command()
@owner_only()
@commands.cooldown(1, 5, commands.BucketType.user)
async def setup_ticket(ctx):
    e = discord.Embed(title="◈ RECRUTEMENT ◈", description="Vous souhaitez rejoindre notre equipe ?\n\nCliquez sur le bouton ci-dessous pour ouvrir votre dossier de candidature.\nLe staff prendra en charge votre demande dans les plus brefs delais.", color=0x5865f2)
    e.set_footer(text=ctx.guild.name, icon_url=bot.user.display_avatar.url)
    await ctx.send(embed=e, view=TicketPanel())

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# COMMANDES STAFF — MODO TEST+
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@bot.command()
@commands.has_role(ROLE_STAFF)
@commands.cooldown(1, 3, commands.BucketType.user)
async def ping(ctx):
    await ctx.send("🏓 Pong ! Latence : **" + str(round(bot.latency * 1000)) + "ms** | Uptime : **" + uptime_str() + "**")

@bot.command()
@commands.has_role(ROLE_STAFF)
@commands.cooldown(1, 3, commands.BucketType.user)
async def warn(ctx, member_str, *, reason="Aucune raison precisee"):
    m = await commands.MemberConverter().convert(ctx, member_str)
    if await check_protected(ctx, m):
        return
    if await check_staff_on_staff(ctx, m):
        return
    if m.id not in sanctions_db:
        sanctions_db[m.id] = []
    sanctions_db[m.id].append({"type": "WARN", "reason": reason, "by": str(ctx.author.id), "date": now_str()})
    save_sanctions()
    stats_db["warn"] += 1
    await send_log(make_embed("⚠️ WARN — Avertissement", 0xfee75c, m, ctx.author, reason))
    dm = discord.Embed(title="⚠️ Avertissement", description="**Raison :** " + reason + "\n**Serveur :** " + ctx.guild.name, color=0xfee75c, timestamp=datetime.now())
    dm.set_footer(text=ctx.guild.name)
    await send_dm(m, dm)
    await ctx.send(m.mention + " a recu un avertissement.")

@bot.command()
@commands.has_role(ROLE_STAFF)
@commands.cooldown(1, 3, commands.BucketType.user)
async def kick(ctx, member_str, *, reason="Aucune raison precisee"):
    m = await commands.MemberConverter().convert(ctx, member_str)
    if await check_protected(ctx, m):
        return
    if await check_staff_on_staff(ctx, m):
        return
    dm = discord.Embed(title="👢 Vous avez ete expulse", description="**Raison :** " + reason + "\n**Serveur :** " + ctx.guild.name, color=0xfaa61a, timestamp=datetime.now())
    dm.set_footer(text=ctx.guild.name)
    await send_dm(m, dm)
    await m.kick(reason=reason)
    stats_db["kick"] += 1
    await send_log(make_embed("👢 KICK — Expulsion", 0xfaa61a, m, ctx.author, reason))
    await ctx.send(m.mention + " a ete expulse du serveur.")

@bot.command()
@commands.has_role(ROLE_STAFF)
@commands.cooldown(1, 3, commands.BucketType.user)
async def mute(ctx, member_str, *, reason="Aucune raison precisee"):
    m = await commands.MemberConverter().convert(ctx, member_str)
    if await check_protected(ctx, m):
        return
    if await check_staff_on_staff(ctx, m):
        return
    role = ctx.guild.get_role(ROLE_MUTED)
    if not role:
        await ctx.send("Le role Muted est introuvable.")
        return
    await m.add_roles(role)
    stats_db["mute"] += 1
    await send_log(make_embed("🔇 MUTE", 0xfaa61a, m, ctx.author, reason))
    dm = discord.Embed(title="🔇 Mise en sourdine", description="**Raison :** " + reason + "\n**Serveur :** " + ctx.guild.name, color=0xfaa61a, timestamp=datetime.now())
    dm.set_footer(text=ctx.guild.name)
    await send_dm(m, dm)
    await ctx.send(m.mention + " a ete mis en sourdine.")

@bot.command()
@commands.has_role(ROLE_STAFF)
@commands.cooldown(1, 3, commands.BucketType.user)
async def unmute(ctx, member_str):
    m = await commands.MemberConverter().convert(ctx, member_str)
    if await check_protected(ctx, m):
        return
    role = ctx.guild.get_role(ROLE_MUTED)
    if not role:
        await ctx.send("Le role Muted est introuvable.")
        return
    await m.remove_roles(role)
    stats_db["unmute"] += 1
    await send_log(make_embed("🔊 UNMUTE", 0x57f287, m, ctx.author, "Retrait manuel"))
    dm = discord.Embed(title="🔊 Sourdine levee", description="Votre mise en sourdine sur **" + ctx.guild.name + "** a ete levee.", color=0x57f287, timestamp=datetime.now())
    dm.set_footer(text=ctx.guild.name)
    await send_dm(m, dm)
    await ctx.send(m.mention + " n est plus en sourdine.")

@bot.command()
@commands.has_role(ROLE_STAFF)
@commands.cooldown(1, 3, commands.BucketType.user)
async def tempmute(ctx, member_str, seconds, *, reason="Aucune raison precisee"):
    m = await commands.MemberConverter().convert(ctx, member_str)
    seconds = int(seconds)
    if await check_protected(ctx, m):
        return
    if await check_staff_on_staff(ctx, m):
        return
    role = ctx.guild.get_role(ROLE_MUTED)
    if not role:
        await ctx.send("Le role Muted est introuvable.")
        return
    await m.add_roles(role)
    stats_db["tempmute"] += 1
    await send_log(make_embed("🔇 TEMPMUTE", 0xfaa61a, m, ctx.author, reason, [("⏱️ Duree", str(seconds) + "s", True)]))
    dm = discord.Embed(title="🔇 Sourdine temporaire", description="**Duree :** " + str(seconds) + "s\n**Raison :** " + reason + "\n**Serveur :** " + ctx.guild.name, color=0xfaa61a, timestamp=datetime.now())
    dm.set_footer(text=ctx.guild.name)
    await send_dm(m, dm)
    await ctx.send(m.mention + " est en sourdine pour **" + str(seconds) + "s**.")
    await asyncio.sleep(seconds)
    try:
        mc = ctx.guild.get_member(m.id)
        if mc and role in mc.roles:
            await mc.remove_roles(role)
            await send_log(make_embed("🔊 FIN TEMPMUTE", 0x57f287, m, bot.user, "Fin automatique (" + str(seconds) + "s)"))
            dm2 = discord.Embed(title="🔊 Sourdine terminee", description="Votre sourdine de **" + str(seconds) + "s** sur **" + ctx.guild.name + "** est terminee.", color=0x57f287, timestamp=datetime.now())
            dm2.set_footer(text=ctx.guild.name)
            await send_dm(m, dm2)
    except Exception:
        pass

@bot.command()
@commands.has_role(ROLE_STAFF)
@commands.cooldown(1, 5, commands.BucketType.channel)
async def clear(ctx, n):
    n = int(n)
    if ctx.channel.id == LOG_CH_ID:
        await ctx.send("Impossible de purger le salon de logs.", delete_after=5)
        return
    await ctx.channel.purge(limit=n + 1)
    e = discord.Embed(title="🧹 CLEAR", color=0x99aab5, timestamp=datetime.now())
    e.add_field(name="👮 Auteur", value=ctx.author.mention, inline=True)
    e.add_field(name="📁 Salon", value=ctx.channel.mention, inline=True)
    e.add_field(name="🗑️ Messages", value=str(n), inline=True)
    e.add_field(name="🕐 Date", value=now_str(), inline=False)
    e.set_footer(text="Systeme de Moderation", icon_url=bot.user.display_avatar.url)
    await send_log(e)

@bot.command()
@commands.has_role(ROLE_STAFF)
@commands.cooldown(1, 5, commands.BucketType.user)
async def sanctions(ctx, member_str):
    m = await commands.MemberConverter().convert(ctx, member_str)
    entries = sanctions_db.get(m.id, [])
    if entries:
        desc = ""
        for entry in entries:
            desc = desc + "• **" + entry.get("type", "?") + "** — " + entry.get("reason", "?") + " — " + entry.get("date", "?") + "\n"
    else:
        desc = "Aucune sanction enregistree."
    e = discord.Embed(title="📋 Sanctions — " + m.display_name, description=desc, color=0xed4245, timestamp=datetime.now())
    e.set_thumbnail(url=m.display_avatar.url)
    e.set_footer(text="Total : " + str(len(entries)) + " sanction(s)")
    await ctx.send(embed=e)

@bot.command()
@commands.has_role(ROLE_STAFF)
@commands.cooldown(1, 3, commands.BucketType.user)
async def history(ctx, member_str):
    m = await commands.MemberConverter().convert(ctx, member_str)
    entries = sanctions_db.get(m.id, [])
    if entries:
        desc = ""
        for i, entry in enumerate(entries, 1):
            by = "<@" + entry.get("by", "?") + ">"
            desc = desc + "**" + str(i) + ".** " + entry.get("type", "?") + " par " + by + " le " + entry.get("date", "?") + "\n> " + entry.get("reason", "?") + "\n"
    else:
        desc = "Aucun historique."
    e = discord.Embed(title="📜 Historique — " + m.display_name, description=desc, color=0x5865f2, timestamp=datetime.now())
    e.set_thumbnail(url=m.display_avatar.url)
    e.set_footer(text="Total : " + str(len(entries)) + " entree(s)")
    await ctx.send(embed=e)

@bot.command()
@commands.has_role(ROLE_STAFF)
@commands.cooldown(1, 3, commands.BucketType.user)
async def clear_sanctions(ctx, member_str):
    m = await commands.MemberConverter().convert(ctx, member_str)
    if m.id in sanctions_db:
        del sanctions_db[m.id]
        save_sanctions()
    await send_log(make_embed("🧹 CLEAR SANCTIONS", 0x99aab5, m, ctx.author, "Effacement des sanctions"))
    await ctx.send("Les sanctions de " + m.mention + " ont ete effacees.")

@bot.command()
@commands.has_role(ROLE_STAFF)
@commands.cooldown(1, 5, commands.BucketType.user)
async def blacklist(ctx):
    if not blacklist_db:
        await ctx.send("La blacklist est vide.")
        return
    desc = ""
    for uid, data in blacklist_db.items():
        desc = desc + "<@" + uid + "> — " + data.get("reason", "?") + " — " + data.get("date", "?") + "\n"
    e = discord.Embed(title="🔒 BLACKLIST — " + str(len(blacklist_db)) + " personne(s)", description=desc, color=0xff0000, timestamp=datetime.now())
    e.set_footer(text="Systeme Blacklist", icon_url=bot.user.display_avatar.url)
    await ctx.send(embed=e)

@bot.command()
@commands.has_role(ROLE_STAFF)
@commands.cooldown(1, 5, commands.BucketType.user)
async def userinfo(ctx, member_str):
    m = await commands.MemberConverter().convert(ctx, member_str)
    roles = [r.mention for r in m.roles if r != ctx.guild.default_role]
    joined = m.joined_at.strftime("%d/%m/%Y") if m.joined_at else "Inconnu"
    created = m.created_at.strftime("%d/%m/%Y")
    entries = sanctions_db.get(m.id, [])
    bl = "Oui" if str(m.id) in blacklist_db else "Non"
    staff_lvl = get_staff_level(m)
    grade = "Aucun"
    grades = {R_T: "Moderateur Test", R_C: "Moderateur Confirme", R_PLUS: "Moderateur+", R_SENIOR: "Staff Senior", R_ADMIN: "Administrateur"}
    if staff_lvl:
        grade = grades.get(staff_lvl, "Staff")
    e = discord.Embed(title="👤 " + m.display_name, color=0x5865f2, timestamp=datetime.now())
    e.set_thumbnail(url=m.display_avatar.url)
    e.add_field(name="Nom", value=str(m), inline=True)
    e.add_field(name="ID", value=str(m.id), inline=True)
    e.add_field(name="Grade", value=grade, inline=True)
    e.add_field(name="Compte cree", value=created, inline=True)
    e.add_field(name="A rejoint", value=joined, inline=True)
    e.add_field(name="Sanctions", value=str(len(entries)), inline=True)
    e.add_field(name="Blackliste", value=bl, inline=True)
    e.add_field(name="Roles", value=", ".join(roles[:10]) if roles else "Aucun", inline=False)
    e.set_footer(text=ctx.guild.name, icon_url=bot.user.display_avatar.url)
    await ctx.send(embed=e)

@bot.command()
@commands.has_role(ROLE_STAFF)
@commands.cooldown(1, 10, commands.BucketType.user)
async def stafflist(ctx):
    grade_map = [(R_ADMIN, "👑 Administrateur"), (R_SENIOR, "⭐ Staff Senior"), (R_PLUS, "💠 Moderateur+"), (R_C, "✅ Moderateur Confirme"), (R_T, "🔰 Moderateur Test")]
    desc = ""
    for r_id, label in grade_map:
        role = ctx.guild.get_role(r_id)
        if role and role.members:
            desc = desc + "\n**" + label + "**\n"
            for member in role.members:
                desc = desc + "• " + member.mention + "\n"
    if not desc:
        desc = "Aucun membre staff trouve."
    e = discord.Embed(title="👥 Staff — " + ctx.guild.name, description=desc, color=0x5865f2, timestamp=datetime.now())
    e.set_footer(text=ctx.guild.name, icon_url=bot.user.display_avatar.url)
    await ctx.send(embed=e)

@bot.command()
@commands.has_role(ROLE_STAFF)
@commands.cooldown(1, 3, commands.BucketType.user)
async def note(ctx, member_str, *, text):
    m = await commands.MemberConverter().convert(ctx, member_str)
    if m.id not in notes_db:
        notes_db[m.id] = []
    notes_db[m.id].append({"text": text, "by": str(ctx.author.id), "date": now_str()})
    save_notes()
    await ctx.send("Note ajoutee pour " + m.mention + ".", delete_after=5)
    try:
        await ctx.message.delete()
    except Exception:
        pass

@bot.command()
@commands.has_role(ROLE_STAFF)
@commands.cooldown(1, 5, commands.BucketType.user)
async def notes(ctx, member_str):
    m = await commands.MemberConverter().convert(ctx, member_str)
    entries = notes_db.get(m.id, [])
    if entries:
        desc = ""
        for i, n in enumerate(entries, 1):
            desc = desc + "**" + str(i) + ".** <@" + n.get("by", "?") + "> — " + n.get("date", "?") + "\n> " + n.get("text", "") + "\n"
    else:
        desc = "Aucune note."
    e = discord.Embed(title="📝 Notes — " + m.display_name, description=desc, color=0xfee75c, timestamp=datetime.now())
    e.set_thumbnail(url=m.display_avatar.url)
    e.set_footer(text="Visible staff uniquement")
    await ctx.send(embed=e)

@bot.command()
@commands.has_role(ROLE_STAFF)
@commands.cooldown(1, 5, commands.BucketType.user)
async def stats(ctx):
    e = discord.Embed(title="📊 Statistiques du bot", color=0x5865f2, timestamp=datetime.now())
    e.add_field(name="⚠️ Warns", value=str(stats_db["warn"]), inline=True)
    e.add_field(name="👢 Kicks", value=str(stats_db["kick"]), inline=True)
    e.add_field(name="🔨 Bans", value=str(stats_db["ban"]), inline=True)
    e.add_field(name="✅ Unbans", value=str(stats_db["unban"]), inline=True)
    e.add_field(name="🔇 Mutes", value=str(stats_db["mute"]), inline=True)
    e.add_field(name="🔊 Unmutes", value=str(stats_db["unmute"]), inline=True)
    e.add_field(name="⏱️ Tempmutes", value=str(stats_db["tempmute"]), inline=True)
    e.add_field(name="⏳ Tempbans", value=str(stats_db["tempban"]), inline=True)
    e.add_field(name="⬇️ Deranks", value=str(stats_db["derank"]), inline=True)
    e.add_field(name="🔒 Blacklists", value=str(stats_db["bl"]), inline=True)
    e.add_field(name="🕐 Uptime", value=uptime_str(), inline=False)
    e.set_footer(text=ctx.guild.name, icon_url=bot.user.display_avatar.url)
    await ctx.send(embed=e)

@bot.command()
@commands.has_role(ROLE_STAFF)
@commands.cooldown(1, 3, commands.BucketType.user)
async def slowmode(ctx, seconds):
    seconds = int(seconds)
    if seconds < 0 or seconds > 21600:
        await ctx.send("Valeur invalide (0-21600).", delete_after=5)
        return
    await ctx.channel.edit(slowmode_delay=seconds)
    msg = "Slowmode desactive." if seconds == 0 else "Slowmode defini a **" + str(seconds) + "s**."
    await ctx.send(msg)
    e = discord.Embed(title="⏱️ SLOWMODE", color=0x5865f2, timestamp=datetime.now())
    e.add_field(name="👮 Auteur", value=ctx.author.mention, inline=True)
    e.add_field(name="📁 Salon", value=ctx.channel.mention, inline=True)
    e.add_field(name="Valeur", value=str(seconds) + "s", inline=True)
    e.add_field(name="🕐 Date", value=now_str(), inline=False)
    e.set_footer(text="Systeme de Moderation", icon_url=bot.user.display_avatar.url)
    await send_log(e)

@bot.command()
@commands.has_role(ROLE_STAFF)
@commands.cooldown(1, 3, commands.BucketType.user)
async def lock(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
    await ctx.send("🔒 Ce salon est desormais verrouille.")
    e = discord.Embed(title="🔒 LOCK", color=0xed4245, timestamp=datetime.now())
    e.add_field(name="👮 Auteur", value=ctx.author.mention, inline=True)
    e.add_field(name="📁 Salon", value=ctx.channel.mention, inline=True)
    e.add_field(name="🕐 Date", value=now_str(), inline=False)
    e.set_footer(text="Systeme de Moderation", icon_url=bot.user.display_avatar.url)
    await send_log(e)

@bot.command()
@commands.has_role(ROLE_STAFF)
@commands.cooldown(1, 3, commands.BucketType.user)
async def unlock(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=None)
    await ctx.send("🔓 Ce salon est desormais debloque.")
    e = discord.Embed(title="🔓 UNLOCK", color=0x57f287, timestamp=datetime.now())
    e.add_field(name="👮 Auteur", value=ctx.author.mention, inline=True)
    e.add_field(name="📁 Salon", value=ctx.channel.mention, inline=True)
    e.add_field(name="🕐 Date", value=now_str(), inline=False)
    e.set_footer(text="Systeme de Moderation", icon_url=bot.user.display_avatar.url)
    await send_log(e)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# COMMANDES MODO+ — BAN + TEMPBAN
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@bot.command()
@commands.cooldown(1, 3, commands.BucketType.user)
async def ban(ctx, member_str, *, reason="Aucune raison precisee"):
    if not has_role_id(ctx.author, R_PLUS) and not has_role_id(ctx.author, R_SENIOR) and not has_role_id(ctx.author, R_ADMIN) and ctx.author.id != OWNER_ID:
        await ctx.send("Cette commande est reservee aux Moderateurs+ et superieur.", delete_after=6)
        return
    m = await commands.MemberConverter().convert(ctx, member_str)
    if await check_protected(ctx, m):
        return
    if await check_staff_on_staff(ctx, m):
        return
    dm = discord.Embed(title="🔨 Vous avez ete banni", description="**Raison :** " + reason + "\n**Serveur :** " + ctx.guild.name, color=0xed4245, timestamp=datetime.now())
    dm.set_footer(text=ctx.guild.name)
    await send_dm(m, dm)
    await m.ban(reason=reason)
    stats_db["ban"] += 1
    await send_log(make_embed("🔨 BAN — Bannissement", 0xed4245, m, ctx.author, reason))
    await ctx.send(m.mention + " a ete banni du serveur.")

@bot.command()
@commands.cooldown(1, 3, commands.BucketType.user)
async def tempban(ctx, member_str, seconds, *, reason="Aucune raison precisee"):
    if not has_role_id(ctx.author, R_PLUS) and not has_role_id(ctx.author, R_SENIOR) and not has_role_id(ctx.author, R_ADMIN) and ctx.author.id != OWNER_ID:
        await ctx.send("Cette commande est reservee aux Moderateurs+ et superieur.", delete_after=6)
        return
    m = await commands.MemberConverter().convert(ctx, member_str)
    seconds = int(seconds)
    if await check_protected(ctx, m):
        return
    if await check_staff_on_staff(ctx, m):
        return
    dm = discord.Embed(title="⏳ Vous avez ete banni temporairement", description="**Duree :** " + str(seconds) + "s\n**Raison :** " + reason + "\n**Serveur :** " + ctx.guild.name, color=0xed4245, timestamp=datetime.now())
    dm.set_footer(text=ctx.guild.name)
    await send_dm(m, dm)
    await m.ban(reason="Tempban : " + reason)
    stats_db["tempban"] += 1
    await send_log(make_embed("⏳ TEMPBAN", 0xed4245, m, ctx.author, reason, [("⏱️ Duree", str(seconds) + "s", True)]))
    await ctx.send(m.mention + " a ete banni pour **" + str(seconds) + "s**.")
    await asyncio.sleep(seconds)
    try:
        await ctx.guild.unban(m, reason="Fin tempban automatique")
        await send_log(make_embed("✅ FIN TEMPBAN", 0x57f287, m, bot.user, "Fin automatique (" + str(seconds) + "s)"))
        dm2 = discord.Embed(title="✅ Ban temporaire termine", description="Votre ban temporaire de **" + str(seconds) + "s** sur **" + ctx.guild.name + "** est termine.", color=0x57f287, timestamp=datetime.now())
        dm2.set_footer(text=ctx.guild.name)
        await send_dm(m, dm2)
    except Exception:
        pass

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# COMMANDES TICKETS — STAFF
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@bot.command()
@commands.has_role(ROLE_STAFF)
async def add(ctx, member_str):
    m = await commands.MemberConverter().convert(ctx, member_str)
    await ctx.channel.set_permissions(m, view_channel=True, send_messages=True, read_message_history=True)
    e = discord.Embed(title="➕ ADD — Acces accorde", color=0x57f287, timestamp=datetime.now())
    e.add_field(name="👤 Membre", value=m.mention, inline=True)
    e.add_field(name="👮 Auteur", value=ctx.author.mention, inline=True)
    e.add_field(name="📁 Salon", value=ctx.channel.mention, inline=True)
    e.add_field(name="🕐 Date", value=now_str(), inline=False)
    e.set_footer(text="Systeme de Tickets", icon_url=bot.user.display_avatar.url)
    await send_log(e)
    await ctx.send(m.mention + " a ete ajoute au ticket.")

@bot.command(name="del")
@commands.has_role(ROLE_STAFF)
async def del_ticket(ctx, member_str):
    m = await commands.MemberConverter().convert(ctx, member_str)
    await ctx.channel.set_permissions(m, view_channel=False, send_messages=False)
    e = discord.Embed(title="➖ DEL — Acces retire", color=0xed4245, timestamp=datetime.now())
    e.add_field(name="👤 Membre", value=m.mention, inline=True)
    e.add_field(name="👮 Auteur", value=ctx.author.mention, inline=True)
    e.add_field(name="📁 Salon", value=ctx.channel.mention, inline=True)
    e.add_field(name="🕐 Date", value=now_str(), inline=False)
    e.set_footer(text="Systeme de Tickets", icon_url=bot.user.display_avatar.url)
    await send_log(e)
    await ctx.send(m.mention + " a ete retire du ticket.")

@bot.command()
@commands.has_role(ROLE_STAFF)
async def rename(ctx, *, name):
    old = ctx.channel.name
    await ctx.channel.edit(name=name)
    e = discord.Embed(title="✏️ RENAME", color=0x5865f2, timestamp=datetime.now())
    e.add_field(name="👮 Auteur", value=ctx.author.mention, inline=True)
    e.add_field(name="Ancien nom", value=old, inline=True)
    e.add_field(name="Nouveau nom", value=name, inline=True)
    e.add_field(name="🕐 Date", value=now_str(), inline=False)
    e.set_footer(text="Systeme de Tickets", icon_url=bot.user.display_avatar.url)
    await send_log(e)
    await ctx.send("Le salon a ete renomme en **" + name + "**.")

@bot.command()
@commands.has_role(ROLE_STAFF)
async def close(ctx):
    channel = ctx.channel
    messages = []
    async for msg in channel.history(limit=500, oldest_first=True):
        ts = msg.created_at.strftime("%d/%m/%Y %H:%M")
        content = msg.content or "[Embed/Fichier]"
        messages.append("[" + ts + "] " + msg.author.display_name + " : " + content)
    transcript_file = discord.File(fp=io.BytesIO("\n".join(messages).encode("utf-8")), filename="transcript-" + channel.name + ".txt")
    candidate = None
    async for msg in channel.history(limit=100, oldest_first=True):
        if not msg.author.bot:
            candidate = msg.author
            break
    transcript_ch = bot.get_channel(TRANSCRIPT_CH_ID)
    e_tr = discord.Embed(title="📄 TRANSCRIPT", color=0x5865f2, timestamp=datetime.now())
    e_tr.add_field(name="📁 Ticket", value=channel.name, inline=True)
    e_tr.add_field(name="👮 Ferme par", value=ctx.author.mention, inline=True)
    if candidate:
        e_tr.add_field(name="👤 Candidat", value=candidate.mention, inline=True)
    e_tr.add_field(name="🕐 Date", value=now_str(), inline=False)
    e_tr.set_footer(text="Systeme de Tickets", icon_url=bot.user.display_avatar.url)
    if transcript_ch:
        await transcript_ch.send(embed=e_tr, file=transcript_file)
    if candidate:
        dm_c = discord.Embed(title="📄 Dossier ferme", description="Votre dossier sur **" + ctx.guild.name + "** a ete ferme.\n**Ferme par :** " + ctx.author.display_name + "\n**Date :** " + now_str(), color=0x5865f2, timestamp=datetime.now())
        dm_c.set_footer(text=ctx.guild.name)
        await send_dm(candidate, dm_c)
    gerant_role = ctx.guild.get_role(GERANT_STAFF_ID)
    if gerant_role and gerant_role.members:
        dm_g = discord.Embed(title="📄 Ticket ferme", description="**Ticket :** " + channel.name + "\n**Candidat :** " + (candidate.mention if candidate else "Inconnu") + "\n**Ferme par :** " + ctx.author.mention + "\n**Date :** " + now_str(), color=0x5865f2, timestamp=datetime.now())
        dm_g.set_footer(text=ctx.guild.name)
        for gerant in gerant_role.members:
            await send_dm(gerant, dm_g)
    e_log = discord.Embed(title="🔒 TICKET FERME", color=0xed4245, timestamp=datetime.now())
    e_log.add_field(name="📁 Ticket", value=channel.name, inline=True)
    e_log.add_field(name="👮 Ferme par", value=ctx.author.mention, inline=True)
    if candidate:
        e_log.add_field(name="👤 Candidat", value=candidate.mention, inline=True)
    e_log.add_field(name="🕐 Date", value=now_str(), inline=False)
    e_log.set_footer(text="Systeme de Tickets", icon_url=bot.user.display_avatar.url)
    await send_log(e_log)
    await ctx.send("Fermeture en cours...", delete_after=3)
    await asyncio.sleep(3)
    await channel.delete()

bot.run(TOKEN)
