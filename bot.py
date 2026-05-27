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

# --- LOGS & EMBEDS ---
async def send_log(action, ctx, target, reason="Aucune"):
    log_ch = bot.get_channel(LOG_CH_ID)
    if log_ch:
        e = discord.Embed(title=f"◈ LOG : {action} ◈", color=0x3498DB, timestamp=datetime.now())
        if target:
            e.set_thumbnail(url=target.display_avatar.url)
        e.add_field(name="Cible", value=target.mention if target else "N/A", inline=True)
        e.add_field(name="Staff", value=ctx.author.mention, inline=True)
        e.add_field(name="Détails", value=reason, inline=False)
        await log_ch.send(embed=e)

# --- TICKETS ---
class DecisionModal(discord.ui.Modal):
    def __init__(self, target, decision):
        super().__init__(title=f"Réponse à {target.name}")
        self.target = target
        self.decision = decision
        self.msg = discord.ui.TextInput(label="Message", style=discord.TextStyle.paragraph)
        self.add_item(self.msg)
    async def on_submit(self, i: discord.Interaction):
        try:
            await self.target.send(f"◈ **Candidature {self.decision}** ◈\n{self.msg.value}")
            await i.response.send_message("✅ Réponse envoyée", ephemeral=True)
        except:
            await i.response.send_message("❌ MP bloqué", ephemeral=True)

class TicketView(discord.ui.View):
    def __init__(self, member):
        super().__init__(timeout=None)
        self.member = member
    @discord.ui.button(label="Accepter", style=discord.ButtonStyle.green)
    async def acc(self, i, b):
        await i.response.send_modal(DecisionModal(self.member, "ACCEPTÉE"))
    @discord.ui.button(label="Refuser", style=discord.ButtonStyle.red)
    async def ref(self, i, b):
        await i.response.send_modal(DecisionModal(self.member, "REFUSÉE"))

class TicketPanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="Poser ma candidature", style=discord.ButtonStyle.primary, emoji="🛡️", custom_id="candid_btn")
    async def open_ticket(self, i: discord.Interaction, b):
        over = {
            i.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            i.user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            i.guild.get_role(GERANT_STAFF_ID): discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }
        ch = await i.guild.create_text_channel(name=f"recrut-{i.user.name}", category=i.guild.get_channel(TICKET_CAT_ID), overwrites=over)
        e = discord.Embed(title="◈ CANDIDATURE ◈", description="Merci d'envoyer votre candidature ici !", color=0x2C2F33)
        await ch.send(content=f"{i.user.mention} | <@&{GERANT_STAFF_ID}>", embed=e, view=TicketView(i.user))
        await i.response.send_message("✅ Ticket ouvert.", ephemeral=True)

# --- COMMANDES ---
@bot.command()
@commands.has_permissions(ban_members=True)
async def unban(ctx, user_id: int):
    user = await bot.fetch_user(user_id)
    await ctx.guild.unban(user)
    await ctx.send(f"✅ {user.name} débanni.")
    await send_log("UNBAN", ctx, user)

@bot.command()
@commands.has_permissions(manage_roles=True)
async def unmute(ctx, m: discord.Member):
    for ch in ctx.guild.text_channels:
        await ch.set_permissions(m, send_messages=None)
    await ctx.send(f"✅ {m.mention} unmute.")
    await send_log("UNMUTE", ctx, m)

@bot.command()
@commands.has_permissions(administrator=True)
async def rank_t(ctx, m: discord.Member):
    await m.add_roles(ctx.guild.get_role(R_T), ctx.guild.get_role(ROLE_STAFF))
    await ctx.send("✅ Rôle T attribué."); await send_log("RANK-T", ctx, m)

@bot.command()
@commands.has_permissions(administrator=True)
async def rank_c(ctx, m: discord.Member):
    await m.add_roles(ctx.guild.get_role(R_C))
    await ctx.send("✅ Rôle C attribué."); await send_log("RANK-C", ctx, m)

@bot.command()
@commands.has_permissions(administrator=True)
async def derank(ctx, m: discord.Member):
    for r_id in [ROLE_STAFF, R_T, R_C, R_PLUS, R_SENIOR, R_ADMIN]:
        role = ctx.guild.get_role(r_id)
        if role: await m.remove_roles(role)
    await ctx.send("🐉 Dégradé."); await send_log("DERANK", ctx, m)

@bot.command()
@commands.has_role(GERANT_STAFF_ID)
async def close(ctx):
    await ctx.channel.delete()

@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, n: int):
    await ctx.message.delete()
    await ctx.channel.purge(limit=n)

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_ticket(ctx):
    e = discord.Embed(title="◈ RECRUTEMENT ◈", description="Cliquez pour candidater.", color=0x000000)
    await ctx.send(embed=e, view=TicketPanel())

@bot.event
async def on_ready():
    bot.add_view(TicketPanel())
    print("✅ Bot actif.")

bot.run(TOKEN)
        
