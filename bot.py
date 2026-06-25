import discord
from discord.ext import commands
import asyncio
from datetime import datetime
import os
import io

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="+", intents=intents)

TOKEN = os.getenv("DISCORD_TOKEN")

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

ALL_STAFF_ROLES = [ROLE_STAFF, R_T, R_C, R_PLUS, R_SENIOR, R_ADMIN, ROLE_EXTRA1, ROLE_EXTRA2]

sanctions_db = {}


def now_str():
    return datetime.now().strftime("%d/%m/%Y a %H:%M")


async def send_log(embed):
    ch = bot.get_channel(LOG_CH_ID)
    if ch:
        await ch.send(embed=embed)


async def send_dm(member, embed):
    try:
        await member.send(embed=embed)
    except Exception:
        pass


def make_log_embed(title, color, author, member, reason=None, extra_fields=None):
    e = discord.Embed(title=title, color=color, timestamp=datetime.now())
    e.add_field(name="Membre concerne", value=member.mention, inline=True)
    e.add_field(name="Auteur de l action", value=author.mention, inline=True)
    if reason:
        e.add_field(name="Raison", value=reason, inline=False)
    if extra_fields:
        for fname, fvalue, finline in extra_fields:
            e.add_field(name=fname, value=fvalue, inline=finline)
    e.add_field(name="Date", value=now_str(), inline=False)
    e.set_thumbnail(url=member.display_avatar.url)
    e.set_footer(text="Systeme de Moderation", icon_url=bot.user.display_avatar.url)
    return e


async def check_protected(ctx, member):
    if member.id not in (CO_FONDA_ID, FONDA_ID):
        return False

    guild = ctx.guild

    if ctx.author.id == guild.owner_id:
        await ctx.send("Cette personne est protegee et ne peut pas etre sanctionnee.", delete_after=5)
        return True

    alert_ch = bot.get_channel(ALERT_CH_ID)
    if alert_ch:
        embed_alert = discord.Embed(
            title="TENTATIVE DE SANCTION SUR UN FONDATEUR",
            description=(
                str(ctx.author.mention) + " a tente d utiliser +" + str(ctx.command.name) +
                " sur " + str(member.mention) + ", qui est un membre fondateur protege.\n\n"
                "Un derank automatique a ete applique."
            ),
            color=0xff0000,
            timestamp=datetime.now()
        )
        embed_alert.add_field(name="Date", value=now_str(), inline=False)
        embed_alert.set_footer(text="Systeme de Protection", icon_url=bot.user.display_avatar.url)
        await alert_ch.send(
            content="<@&" + str(CO_FONDA_ID) + "> <@&" + str(FONDA_ID) + ">",
            embed=embed_alert
        )

    for r_id in ALL_STAFF_ROLES:
        role = guild.get_role(r_id)
        if role and role in ctx.author.roles:
            try:
                await ctx.author.remove_roles(role)
            except discord.Forbidden:
                pass

    embed_log = make_log_embed(
        "DERANK AUTOMATIQUE - Protection Fondateur",
        0xff0000,
        bot.user,
        ctx.author,
        "Tentative de sanction sur un membre protege"
    )
    await send_log(embed_log)

    embed_dm = discord.Embed(
        title="Vous avez ete degrade automatiquement",
        description="Vous avez tente d effectuer une action sur un fondateur protege. Tous vos roles staff ont ete retires.",
        color=0xff0000,
        timestamp=datetime.now()
    )
    embed_dm.set_footer(text=guild.name)
    await send_dm(ctx.author, embed_dm)

    await ctx.send("Action bloquee. Cette personne est protegee. Derank automatique applique.", delete_after=8)
    return True


class TicketPanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Candidater",
        style=discord.ButtonStyle.primary,
        emoji="📩",
        custom_id="btn_candid"
    )
    async def btn(self, interaction, button):
        guild = interaction.guild
        user = interaction.user

        existing = discord.utils.get(guild.text_channels, name="ticket-" + user.name.lower())
        if existing:
            await interaction.response.send_message(
                "Vous avez deja un dossier ouvert : " + existing.mention,
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
            overwrites[gerant_role] = discord.PermissionOverwrite(
                view_channel=True, send_messages=True, read_message_history=True
            )

        channel = await guild.create_text_channel(
            name="ticket-" + user.name.lower(),
            category=category,
            overwrites=overwrites
        )

        embed = discord.Embed(
            title="DOSSIER DE CANDIDATURE",
            description=(
                "Bonjour " + user.mention + ", bienvenue dans votre dossier de candidature.\n\n"
                "Le staff prendra en charge votre demande dans les plus brefs delais.\n"
                "Merci de patienter."
            ),
            color=0x5865f2,
            timestamp=datetime.now()
        )
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        embed.set_footer(text=guild.name, icon_url=bot.user.display_avatar.url)

        ping_content = user.mention
        if gerant_role:
            ping_content = ping_content + " | " + gerant_role.mention

        await channel.send(content=ping_content, embed=embed)

        embed_dm = discord.Embed(
            title="Dossier de candidature ouvert",
            description=(
                "Votre dossier de candidature sur **" + guild.name + "** a bien ete cree.\n"
                "Rendez-vous dans " + channel.mention + " pour suivre votre candidature."
            ),
            color=0x5865f2,
            timestamp=datetime.now()
        )
        embed_dm.set_footer(text=guild.name)
        await send_dm(user, embed_dm)

        embed_log = discord.Embed(title="TICKET OUVERT", color=0x5865f2, timestamp=datetime.now())
        embed_log.add_field(name="Candidat", value=user.mention, inline=True)
        embed_log.add_field(name="Salon", value=channel.mention, inline=True)
        embed_log.add_field(name="Date", value=now_str(), inline=False)
        embed_log.set_footer(text="Systeme de Tickets", icon_url=bot.user.display_avatar.url)
        await send_log(embed_log)

        await interaction.response.send_message(
            "Votre dossier a ete cree : " + channel.mention,
            ephemeral=True
        )


@bot.event
async def on_ready():
    bot.add_view(TicketPanel())
    print("Bot connecte : " + str(bot.user))


@bot.event
async def on_command_error(ctx, error):
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
    else:
        raise error


@bot.command()
@commands.has_permissions(administrator=True)
async def rank_t(ctx, *, member_str):
    m = await commands.MemberConverter().convert(ctx, member_str)
    role_t = ctx.guild.get_role(R_T)
    role_staff = ctx.guild.get_role(ROLE_STAFF)
    if role_t and role_staff:
        await m.add_roles(role_t, role_staff)
        await send_log(make_log_embed("RANK-T - Moderateur Test", 0x57f287, ctx.author, m, "Promotion"))
        dm = discord.Embed(title="Felicitations - Promotion", description="Vous etes desormais **Moderateur Test** sur **" + ctx.guild.name + "**.", color=0x57f287, timestamp=datetime.now())
        dm.set_footer(text=ctx.guild.name)
        await send_dm(m, dm)
        await ctx.send(m.mention + " est desormais **Moderateur Test**.")


@bot.command()
@commands.has_permissions(administrator=True)
async def rank_c(ctx, *, member_str):
    m = await commands.MemberConverter().convert(ctx, member_str)
    role = ctx.guild.get_role(R_C)
    if role:
        await m.add_roles(role)
        await send_log(make_log_embed("RANK-C - Moderateur Confirme", 0x57f287, ctx.author, m, "Promotion"))
        dm = discord.Embed(title="Felicitations - Promotion", description="Vous etes desormais **Moderateur Confirme** sur **" + ctx.guild.name + "**.", color=0x57f287, timestamp=datetime.now())
        dm.set_footer(text=ctx.guild.name)
        await send_dm(m, dm)
        await ctx.send(m.mention + " est desormais **Moderateur Confirme**.")


@bot.command()
@commands.has_permissions(administrator=True)
async def rank_plus(ctx, *, member_str):
    m = await commands.MemberConverter().convert(ctx, member_str)
    role = ctx.guild.get_role(R_PLUS)
    if role:
        await m.add_roles(role)
        await send_log(make_log_embed("RANK-PLUS - Moderateur+", 0x57f287, ctx.author, m, "Promotion"))
        dm = discord.Embed(title="Felicitations - Promotion", description="Vous etes desormais **Moderateur+** sur **" + ctx.guild.name + "**.", color=0x57f287, timestamp=datetime.now())
        dm.set_footer(text=ctx.guild.name)
        await send_dm(m, dm)
        await ctx.send(m.mention + " est desormais **Moderateur+**.")


@bot.command()
@commands.has_permissions(administrator=True)
async def rank_s(ctx, *, member_str):
    m = await commands.MemberConverter().convert(ctx, member_str)
    role = ctx.guild.get_role(R_SENIOR)
    if role:
        await m.add_roles(role)
        await send_log(make_log_embed("RANK-SENIOR - Staff Senior", 0x57f287, ctx.author, m, "Promotion"))
        dm = discord.Embed(title="Felicitations - Promotion", description="Vous etes desormais **Staff Senior** sur **" + ctx.guild.name + "**.", color=0x57f287, timestamp=datetime.now())
        dm.set_footer(text=ctx.guild.name)
        await send_dm(m, dm)
        await ctx.send(m.mention + " est desormais **Staff Senior**.")


@bot.command()
@commands.has_permissions(administrator=True)
async def rank_admin(ctx, *, member_str):
    m = await commands.MemberConverter().convert(ctx, member_str)
    role = ctx.guild.get_role(R_ADMIN)
    if role:
        await m.add_roles(role)
        await send_log(make_log_embed("RANK-ADMIN - Administrateur", 0x57f287, ctx.author, m, "Promotion"))
        dm = discord.Embed(title="Felicitations - Promotion", description="Vous etes desormais **Administrateur** sur **" + ctx.guild.name + "**.", color=0x57f287, timestamp=datetime.now())
        dm.set_footer(text=ctx.guild.name)
        await send_dm(m, dm)
        await ctx.send(m.mention + " est desormais **Administrateur**.")


@bot.command()
@commands.has_permissions(administrator=True)
async def derank(ctx, *, member_str):
    m = await commands.MemberConverter().convert(ctx, member_str)
    removed = []
    for r_id in ALL_STAFF_ROLES:
        role = ctx.guild.get_role(r_id)
        if role and role in m.roles:
            await m.remove_roles(role)
            removed.append(role.name)
    await send_log(make_log_embed("DERANK - Degradation", 0xed4245, ctx.author, m, "Degradation", [("Roles retires", ", ".join(removed) if removed else "Aucun", False)]))
    dm = discord.Embed(title="Degradation", description="Vous avez ete degrade sur **" + ctx.guild.name + "**. Tous vos roles staff ont ete retires.", color=0xed4245, timestamp=datetime.now())
    dm.set_footer(text=ctx.guild.name)
    await send_dm(m, dm)
    await ctx.send(m.mention + " a ete degrade avec succes.")


@bot.command()
@commands.has_role(ROLE_STAFF)
async def ping(ctx):
    await ctx.send("Pong ! Latence : **" + str(round(bot.latency * 1000)) + "ms**")


@bot.command()
@commands.has_role(ROLE_STAFF)
async def warn(ctx, member_str, *, reason="Aucune raison precisee"):
    m = await commands.MemberConverter().convert(ctx, member_str)
    if await check_protected(ctx, m):
        return
    if m.id not in sanctions_db:
        sanctions_db[m.id] = []
    sanctions_db[m.id].append("WARN | " + now_str() + " | " + reason)
    await send_log(make_log_embed("WARN - Avertissement", 0xfee75c, ctx.author, m, reason))
    dm = discord.Embed(title="Vous avez recu un avertissement", description="**Raison :** " + reason + "\n**Serveur :** " + ctx.guild.name, color=0xfee75c, timestamp=datetime.now())
    dm.set_footer(text=ctx.guild.name)
    await send_dm(m, dm)
    await ctx.send(m.mention + " a recu un avertissement.")


@bot.command()
@commands.has_role(ROLE_STAFF)
async def kick(ctx, member_str, *, reason="Aucune raison precisee"):
    m = await commands.MemberConverter().convert(ctx, member_str)
    if await check_protected(ctx, m):
        return
    dm = discord.Embed(title="Vous avez ete expulse", description="**Raison :** " + reason + "\n**Serveur :** " + ctx.guild.name, color=0xfaa61a, timestamp=datetime.now())
    dm.set_footer(text=ctx.guild.name)
    await send_dm(m, dm)
    await m.kick(reason=reason)
    await send_log(make_log_embed("KICK - Expulsion", 0xfaa61a, ctx.author, m, reason))
    await ctx.send(m.mention + " a ete expulse du serveur.")


@bot.command()
@commands.has_role(ROLE_STAFF)
async def ban(ctx, member_str, *, reason="Aucune raison precisee"):
    m = await commands.MemberConverter().convert(ctx, member_str)
    if await check_protected(ctx, m):
        return
    dm = discord.Embed(title="Vous avez ete banni", description="**Raison :** " + reason + "\n**Serveur :** " + ctx.guild.name, color=0xed4245, timestamp=datetime.now())
    dm.set_footer(text=ctx.guild.name)
    await send_dm(m, dm)
    await m.ban(reason=reason)
    await send_log(make_log_embed("BAN - Bannissement", 0xed4245, ctx.author, m, reason))
    await ctx.send(m.mention + " a ete banni du serveur.")


@bot.command()
@commands.has_role(ROLE_STAFF)
async def unban(ctx, user_id):
    try:
        user = await bot.fetch_user(int(user_id))
        await ctx.guild.unban(user)
        await send_log(make_log_embed("UNBAN - Debannissement", 0x57f287, ctx.author, user, "Debannissement manuel"))
        dm = discord.Embed(title="Vous avez ete debanni", description="Vous avez ete debanni de **" + ctx.guild.name + "**.", color=0x57f287, timestamp=datetime.now())
        dm.set_footer(text=ctx.guild.name)
        await send_dm(user, dm)
        await ctx.send("**" + user.name + "** a ete debanni.")
    except discord.NotFound:
        await ctx.send("Utilisateur introuvable ou non banni.")


@bot.command()
@commands.has_role(ROLE_STAFF)
async def mute(ctx, member_str, *, reason="Aucune raison precisee"):
    m = await commands.MemberConverter().convert(ctx, member_str)
    if await check_protected(ctx, m):
        return
    role = ctx.guild.get_role(ROLE_MUTED)
    if not role:
        await ctx.send("Le role Muted est introuvable.")
        return
    await m.add_roles(role)
    await send_log(make_log_embed("MUTE - Mise en sourdine", 0xfaa61a, ctx.author, m, reason))
    dm = discord.Embed(title="Vous avez ete mis en sourdine", description="**Raison :** " + reason + "\n**Serveur :** " + ctx.guild.name, color=0xfaa61a, timestamp=datetime.now())
    dm.set_footer(text=ctx.guild.name)
    await send_dm(m, dm)
    await ctx.send(m.mention + " a ete mis en sourdine.")


@bot.command()
@commands.has_role(ROLE_STAFF)
async def unmute(ctx, member_str):
    m = await commands.MemberConverter().convert(ctx, member_str)
    if await check_protected(ctx, m):
        return
    role = ctx.guild.get_role(ROLE_MUTED)
    if not role:
        await ctx.send("Le role Muted est introuvable.")
        return
    await m.remove_roles(role)
    await send_log(make_log_embed("UNMUTE - Retrait de sourdine", 0x57f287, ctx.author, m, "Retrait manuel"))
    dm = discord.Embed(title="Votre sourdine a ete levee", description="Votre mise en sourdine sur **" + ctx.guild.name + "** a ete levee.", color=0x57f287, timestamp=datetime.now())
    dm.set_footer(text=ctx.guild.name)
    await send_dm(m, dm)
    await ctx.send(m.mention + " n est plus en sourdine.")


@bot.command()
@commands.has_role(ROLE_STAFF)
async def tempmute(ctx, member_str, seconds, *, reason="Aucune raison precisee"):
    m = await commands.MemberConverter().convert(ctx, member_str)
    seconds = int(seconds)
    if await check_protected(ctx, m):
        return
    role = ctx.guild.get_role(ROLE_MUTED)
    if not role:
        await ctx.send("Le role Muted est introuvable.")
        return
    await m.add_roles(role)
    await send_log(make_log_embed("TEMPMUTE - Sourdine temporaire", 0xfaa61a, ctx.author, m, reason, [("Duree", str(seconds) + "s", True)]))
    dm = discord.Embed(title="Vous avez ete mis en sourdine temporairement", description="**Duree :** " + str(seconds) + " secondes\n**Raison :** " + reason + "\n**Serveur :** " + ctx.guild.name, color=0xfaa61a, timestamp=datetime.now())
    dm.set_footer(text=ctx.guild.name)
    await send_dm(m, dm)
    await ctx.send(m.mention + " a ete mis en sourdine pour **" + str(seconds) + " secondes**.")
    await asyncio.sleep(seconds)
    try:
        mc = ctx.guild.get_member(m.id)
        if mc and role in mc.roles:
            await mc.remove_roles(role)
            await send_log(make_log_embed("FIN TEMPMUTE - Sourdine levee", 0x57f287, bot.user, m, "Fin du tempmute (" + str(seconds) + "s)"))
            dm2 = discord.Embed(title="Votre sourdine temporaire est terminee", description="Votre sourdine de **" + str(seconds) + "s** sur **" + ctx.guild.name + "** est terminee.", color=0x57f287, timestamp=datetime.now())
            dm2.set_footer(text=ctx.guild.name)
            await send_dm(m, dm2)
    except Exception:
        pass


@bot.command()
@commands.has_role(ROLE_STAFF)
async def sanctions(ctx, member_str):
    m = await commands.MemberConverter().convert(ctx, member_str)
    entries = sanctions_db.get(m.id, [])
    desc = "\n".join(entries) if entries else "Aucune sanction enregistree."
    e = discord.Embed(title="Sanctions - " + m.display_name, description=desc, color=0xed4245, timestamp=datetime.now())
    e.set_thumbnail(url=m.display_avatar.url)
    e.set_footer(text="Total : " + str(len(entries)) + " sanction(s)")
    await ctx.send(embed=e)


@bot.command()
@commands.has_role(ROLE_STAFF)
async def clear_sanctions(ctx, member_str):
    m = await commands.MemberConverter().convert(ctx, member_str)
    if m.id in sanctions_db:
        del sanctions_db[m.id]
    await send_log(make_log_embed("CLEAR SANCTIONS", 0x99aab5, ctx.author, m, "Effacement des sanctions"))
    await ctx.send("Les sanctions de " + m.mention + " ont ete effacees.")


@bot.command()
@commands.has_role(ROLE_STAFF)
async def clear(ctx, n):
    n = int(n)
    await ctx.channel.purge(limit=n + 1)
    e = discord.Embed(title="CLEAR - Suppression de messages", color=0x99aab5, timestamp=datetime.now())
    e.add_field(name="Auteur", value=ctx.author.mention, inline=True)
    e.add_field(name="Salon", value=ctx.channel.mention, inline=True)
    e.add_field(name="Messages supprimes", value=str(n), inline=True)
    e.add_field(name="Date", value=now_str(), inline=False)
    e.set_footer(text="Systeme de Moderation", icon_url=bot.user.display_avatar.url)
    await send_log(e)


@bot.command()
@commands.has_role(ROLE_STAFF)
async def add(ctx, member_str):
    m = await commands.MemberConverter().convert(ctx, member_str)
    await ctx.channel.set_permissions(m, view_channel=True, send_messages=True, read_message_history=True)
    e = discord.Embed(title="ADD - Acces ticket accorde", color=0x57f287, timestamp=datetime.now())
    e.add_field(name="Membre ajoute", value=m.mention, inline=True)
    e.add_field(name="Auteur", value=ctx.author.mention, inline=True)
    e.add_field(name="Salon", value=ctx.channel.mention, inline=True)
    e.add_field(name="Date", value=now_str(), inline=False)
    e.set_footer(text="Systeme de Tickets", icon_url=bot.user.display_avatar.url)
    await send_log(e)
    await ctx.send(m.mention + " a ete ajoute au ticket.")


@bot.command(name="del")
@commands.has_role(ROLE_STAFF)
async def del_ticket(ctx, member_str):
    m = await commands.MemberConverter().convert(ctx, member_str)
    await ctx.channel.set_permissions(m, view_channel=False, send_messages=False)
    e = discord.Embed(title="DEL - Acces ticket retire", color=0xed4245, timestamp=datetime.now())
    e.add_field(name="Membre retire", value=m.mention, inline=True)
    e.add_field(name="Auteur", value=ctx.author.mention, inline=True)
    e.add_field(name="Salon", value=ctx.channel.mention, inline=True)
    e.add_field(name="Date", value=now_str(), inline=False)
    e.set_footer(text="Systeme de Tickets", icon_url=bot.user.display_avatar.url)
    await send_log(e)
    await ctx.send(m.mention + " a ete retire du ticket.")


@bot.command()
@commands.has_role(ROLE_STAFF)
async def rename(ctx, *, name):
    old_name = ctx.channel.name
    await ctx.channel.edit(name=name)
    e = discord.Embed(title="RENAME - Renommage de salon", color=0x5865f2, timestamp=datetime.now())
    e.add_field(name="Auteur", value=ctx.author.mention, inline=True)
    e.add_field(name="Ancien nom", value=old_name, inline=True)
    e.add_field(name="Nouveau nom", value=name, inline=True)
    e.add_field(name="Date", value=now_str(), inline=False)
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

    transcript_file = discord.File(
        fp=io.BytesIO("\n".join(messages).encode("utf-8")),
        filename="transcript-" + channel.name + ".txt"
    )

    candidate = None
    async for msg in channel.history(limit=100, oldest_first=True):
        if not msg.author.bot:
            candidate = msg.author
            break

    transcript_ch = bot.get_channel(TRANSCRIPT_CH_ID)
    e_tr = discord.Embed(title="TRANSCRIPT - Fermeture de ticket", color=0x5865f2, timestamp=datetime.now())
    e_tr.add_field(name="Ticket", value=channel.name, inline=True)
    e_tr.add_field(name="Ferme par", value=ctx.author.mention, inline=True)
    if candidate:
        e_tr.add_field(name="Candidat", value=candidate.mention, inline=True)
    e_tr.add_field(name="Date", value=now_str(), inline=False)
    e_tr.set_footer(text="Systeme de Tickets", icon_url=bot.user.display_avatar.url)
    if transcript_ch:
        await transcript_ch.send(embed=e_tr, file=transcript_file)

    if candidate:
        dm_c = discord.Embed(
            title="Votre dossier a ete ferme",
            description="Votre dossier sur **" + ctx.guild.name + "** a ete ferme.\n**Ferme par :** " + ctx.author.display_name + "\n**Date :** " + now_str(),
            color=0x5865f2, timestamp=datetime.now()
        )
        dm_c.set_footer(text=ctx.guild.name)
        await send_dm(candidate, dm_c)

    gerant_role = ctx.guild.get_role(GERANT_STAFF_ID)
    if gerant_role and gerant_role.members:
        dm_g = discord.Embed(
            title="Ticket ferme - Notification Gerant Staff",
            description="**Ticket :** " + channel.name + "\n**Candidat :** " + (candidate.mention if candidate else "Inconnu") + "\n**Ferme par :** " + ctx.author.mention + "\n**Date :** " + now_str(),
            color=0x5865f2, timestamp=datetime.now()
        )
        dm_g.set_footer(text=ctx.guild.name)
        for gerant in gerant_role.members:
            await send_dm(gerant, dm_g)

    e_log = discord.Embed(title="TICKET FERME", color=0xed4245, timestamp=datetime.now())
    e_log.add_field(name="Ticket", value=channel.name, inline=True)
    e_log.add_field(name="Ferme par", value=ctx.author.mention, inline=True)
    if candidate:
        e_log.add_field(name="Candidat", value=candidate.mention, inline=True)
    e_log.add_field(name="Date", value=now_str(), inline=False)
    e_log.set_footer(text="Systeme de Tickets", icon_url=bot.user.display_avatar.url)
    await send_log(e_log)

    await ctx.send("Fermeture du ticket en cours...", delete_after=3)
    await asyncio.sleep(3)
    await channel.delete()


@bot.command()
@commands.has_permissions(administrator=True)
async def setup_ticket(ctx):
    e = discord.Embed(
        title="RECRUTEMENT",
        description="Vous souhaitez rejoindre notre equipe ?\n\nCliquez sur le bouton ci-dessous pour ouvrir votre dossier de candidature.\nLe staff prendra en charge votre demande dans les plus brefs delais.",
        color=0x5865f2
    )
    e.set_footer(text=ctx.guild.name, icon_url=bot.user.display_avatar.url)
    await ctx.send(embed=e, view=TicketPanel())


bot.run(TOKEN)
