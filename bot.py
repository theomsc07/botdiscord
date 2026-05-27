import discord
from discord.ext import commands
import asyncio
import os
from datetime import datetime

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="+", intents=intents)

TOKEN = os.getenv("DISCORD_TOKEN")

# IDs CONFIG
LOG_CH_ID = 1508595464168013965
GERANT_STAFF_ID = 1504792751777255545
ROLE_STAFF = 1504810257715822722
TICKET_CAT_ID = 1504792910892109935
R_T, R_C, R_PLUS, R_SENIOR, R_ADMIN = 1504792771977023591, 1504792768088903931, 1504792764448116776, 1504792759679057951, 1504792748098715660

# LOGS
async def send_log(action, ctx, target, reason="Aucune"):
    log_ch = bot.get_channel(LOG_CH_ID)
    if log_ch:
        e = discord.Embed(title=f"◈ LOG : {action} ◈", color=0x3498DB, timestamp=datetime.now())
        if target: e.set_thumbnail(url=target.display_avatar.url)
        e.add_field(name="Cible", value=target.mention if target else "N/A", inline=True)
        e.add_field(name="Staff", value=ctx.author.mention, inline=True)
        e.add_field(name="Détails", value=reason, inline=False)
        await log_ch.send(embed=e)

# TICKETS
class TicketPanel(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="Poser ma candidature", style=discord.ButtonStyle.primary, emoji="🛡️", custom_id="candid_btn")
    async def open_ticket(self, i: discord.Interaction, b):
        over = {i.guild.default_role: discord.PermissionOverwrite(view_channel=False), i.user: discord.PermissionOverwrite(view_channel=True, send_messages=True), i.guild.get_role(GERANT_STAFF_ID): discord.PermissionOverwrite(view_channel=True, send_messages=True)}
        ch = await i.guild.create_text_channel(name=f"recrut-{i.user.name}", category=i.guild.get_channel(TICKET_CAT_ID), overwrites=over)
        e = discord.Embed(title="◈ CANDIDATURE ◈", description=f"Bonjour {i.user.mention}, le staff arrive.", color=0x2C2F33)
        e.set_thumbnail(url=bot.user.display_avatar.url)
        await ch.send(content=f"{i.user.mention} | <@&{GERANT_STAFF_ID}>", embed=e)
        await i.response.send_message("✅ Ticket ouvert.", ephemeral=True)

# COMMANDES GRADES
@bot.command()
@commands.has_permissions(administrator=True)
async def rank_t(ctx, m: discord.Member):
    await m.add_roles(ctx.guild.get_role(R_T), ctx.guild.get_role(ROLE_STAFF))
    await ctx.send("✅ Rôle T attribué."); await send_log("RANK-T", ctx, m)

@bot.command()
@commands.has_permissions(administrator=True)
async def derank(ctx, m: discord.Member):
    for r_id in [ROLE_STAFF, R_T, R_C, R_PLUS, R_SENIOR, R_ADMIN]:
        role = ctx.guild.get_role(r_id)
        if role: await m.remove_roles(role)
    await ctx.send("🐉 Membre dégradé."); await send_log("DERANK", ctx, m)

# DIVERS
@bot.command()
@commands.has_role(GERANT_STAFF_ID)
async def close(ctx): await ctx.channel.delete()

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_ticket(ctx):
    e = discord.Embed(title="◈ RECRUTEMENT ◈", description="Cliquez pour candidater.", color=0x000000)
    e.set_thumbnail(url=bot.user.display_avatar.url)
    await ctx.send(embed=e, view=TicketPanel())

@bot.event
async def on_ready(): bot.add_view(TicketPanel()); print("✅ Bot en ligne.")

bot.run(TOKEN)
        
