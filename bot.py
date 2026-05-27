import discord
from discord.ext import commands
import asyncio
import os
from datetime import datetime

# --- CONFIGURATION ---
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="+", intents=intents)

TOKEN = os.getenv("DISCORD_TOKEN")

LOG_CH_ID = 1508595464168013965
GERANT_STAFF_ID = 1504792751777255545
ROLE_STAFF = 1504810257715822722
TICKET_CAT_ID = 1504792910892109935
R_T, R_C, R_PLUS, R_SENIOR, R_ADMIN = 1504792771977023591, 1504792768088903931, 1504792764448116776, 1504792759679057951, 1504792748098715660

# --- LOGS ---
async def send_log(action, ctx, target, reason="Aucune"):
    log_ch = bot.get_channel(LOG_CH_ID)
    if log_ch:
        e = discord.Embed(title=f"◈ LOG : {action} ◈", color=0x2f3136, timestamp=datetime.now())
        if target: e.set_thumbnail(url=target.display_avatar.url)
        e.add_field(name="Cible", value=target.mention if target else "N/A", inline=True)
        e.add_field(name="Staff", value=ctx.author.mention, inline=True)
        e.add_field(name="Détails", value=reason, inline=False)
        await log_ch.send(embed=e)

# --- TICKETS GESTION ---
class TicketPanel(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="Déposer une candidature", style=discord.ButtonStyle.primary, emoji="📝", custom_id="btn_candid")
    async def open_ticket(self, i: discord.Interaction, b):
        over = {i.guild.default_role: discord.PermissionOverwrite(view_channel=False), i.user: discord.PermissionOverwrite(view_channel=True, send_messages=True), i.guild.get_role(GERANT_STAFF_ID): discord.PermissionOverwrite(view_channel=True, send_messages=True)}
        ch = await i.guild.create_text_channel(name=f"📄-candid-{i.user.name}", category=i.guild.get_channel(TICKET_CAT_ID), overwrites=over)
        e = discord.Embed(title="◈ DOSSIER DE CANDIDATURE ◈", description=f"Bonjour {i.user.mention},\n\nMerci de bien vouloir **envoyer votre formulaire rempli** ici. L'équipe <@&{GERANT_STAFF_ID}> examinera votre profil.", color=0x5865f2)
        e.set_thumbnail(url=bot.user.display_avatar.url)
        await ch.send(content=f"{i.user.mention} | <@&{GERANT_STAFF_ID}>", embed=e)
        await i.response.send_message(f"✅ Dossier créé : {ch.mention}", ephemeral=True)

# --- COMMANDES TICKET ---
@bot.command()
@commands.has_role(GERANT_STAFF_ID)
async def add(ctx, m: discord.Member):
    await ctx.channel.set_permissions(m, view_channel=True, send_messages=True)
    await ctx.send(f"✅ {m.mention} ajouté au dossier.")

@bot.command()
@commands.has_role(GERANT_STAFF_ID)
async def remove(ctx, m: discord.Member):
    await ctx.channel.set_permissions(m, view_channel=False)
    await ctx.send(f"✅ {m.mention} retiré du dossier.")

@bot.command()
@commands.has_role(GERANT_STAFF_ID)
async def rename(ctx, *, nom: str):
    await ctx.channel.edit(name=nom)
    await ctx.send(f"✅ Salon renommé en : {nom}")

@bot.command()
@commands.has_role(GERANT_STAFF_ID)
async def close(ctx): await ctx.channel.delete()

# --- AUTRES COMMANDES ---
@bot.command()
@commands.has_permissions(administrator=True)
async def rank_t(ctx, m: discord.Member):
    await m.add_roles(ctx.guild.get_role(R_T), ctx.guild.get_role(ROLE_STAFF))
    await ctx.send(f"✅ {m.mention} est Staff Test."); await send_log("RANK-T", ctx, m)

@bot.command()
@commands.has_permissions(administrator=True)
async def derank(ctx, m: discord.Member):
    for r_id in [ROLE_STAFF, R_T, R_C, R_PLUS, R_SENIOR, R_ADMIN]:
        role = ctx.guild.get_role(r_id)
        if role: await m.remove_roles(role)
    await ctx.send(f"🐉 {m.mention} dégradé."); await send_log("DERANK", ctx, m)

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_ticket(ctx):
    e = discord.Embed(title="◈ CENTRE DE RECRUTEMENT ◈", description="Cliquez pour déposer votre candidature.", color=0x2f3136)
    e.set_thumbnail(url=bot.user.display_avatar.url)
    await ctx.send(embed=e, view=TicketPanel())

@bot.event
async def on_ready():
    bot.add_view(TicketPanel())
    print("✅ Bot opérationnel.")

bot.run(TOKEN)
        
