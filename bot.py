import discord
from discord.ext import commands
import asyncio
import os
from datetime import datetime

# ==============================================================================
# CONFIGURATION
# ==============================================================================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="+", intents=intents)

TOKEN = os.getenv("DISCORD_TOKEN")

# IDs CONFIGURATION
LOG_CH_ID = 1508595464168013965
GERANT_STAFF_ID = 1504792751777255545
ROLE_STAFF = 1504810257715822722
TICKET_CAT_ID = 1504792910892109935

# RÔLES IDs
R_T = 1504792771977023591
R_C = 1504792768088903931
R_PLUS = 1504792764448116776
R_SENIOR = 1504792759679057951
R_ADMIN = 1504792748098715660

# URL de l'image pour le panel (tu peux changer le lien)
PANEL_IMAGE_URL = "https://i.imgur.com/8N4N8f8.png" 

# --- SYSTÈME DE LOGS ---
async def send_log(action, ctx, target, reason="Aucune"):
    log_ch = bot.get_channel(LOG_CH_ID)
    if log_ch:
        e = discord.Embed(title=f"◈ LOG : {action} ◈", color=0x3498DB, timestamp=datetime.now())
        e.add_field(name="Cible", value=f"{target.mention}" if target else "N/A", inline=True)
        e.add_field(name="Staff", value=ctx.author.mention, inline=True)
        e.add_field(name="Détails", value=reason, inline=False)
        e.set_thumbnail(url=bot.user.display_avatar.url)
        await log_ch.send(embed=e)

# --- TICKETS SYSTEM ---
class DecisionModal(discord.ui.Modal):
    def __init__(self, target, decision):
        super().__init__(title=f"Réponse à {target.name}")
        self.target = target
        self.decision = decision
        self.msg = discord.ui.TextInput(label="Message personnalisé", style=discord.TextStyle.paragraph)
        self.add_item(self.msg)
    async def on_submit(self, i: discord.Interaction):
        try:
            await self.target.send(f"◈ **Candidature {self.decision}** ◈\n{self.msg.value}")
            await i.response.send_message("✅ Réponse envoyée.", ephemeral=True)
        except:
            await i.response.send_message("❌ Impossible d'envoyer le MP.", ephemeral=True)

class TicketView(discord.ui.View):
    def __init__(self, member):
        super().__init__(timeout=None)
        self.member = member
    @discord.ui.button(label="Accepter", style=discord.ButtonStyle.green)
    async def acc(self, i, b): await i.response.send_modal(DecisionModal(self.member, "ACCEPTÉE"))
    @discord.ui.button(label="Refuser", style=discord.ButtonStyle.red)
    async def ref(self, i, b): await i.response.send_modal(DecisionModal(self.member, "REFUSÉE"))

class TicketPanel(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="Poser ma candidature", style=discord.ButtonStyle.primary, emoji="🛡️", custom_id="candid_btn")
    async def open_ticket(self, i: discord.Interaction, b):
        over = {
            i.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            i.user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            i.guild.get_role(GERANT_STAFF_ID): discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }
        ch = await i.guild.create_text_channel(name=f"recrut-{i.user.name}", category=i.guild.get_channel(TICKET_CAT_ID), overwrites=over)
        e = discord.Embed(title="◈ CANDIDATURE EN COURS ◈", description=f"Bonjour {i.user.mention},\nPosez votre candidature ci-dessous. Le Gérant Staff vous répondra via les boutons.", color=0x2B2D31)
        e.set_thumbnail(url=bot.user.display_avatar.url)
        await ch.send(content=f"{i.user.mention} | <@&{GERANT_STAFF_ID}>", embed=e, view=TicketView(i.user))
        await i.response.send_message(f"✅ Votre ticket : {ch.mention}", ephemeral=True)

# --- COMMANDES GESTION TICKET ---
@bot.command(name="close", aliases=['del'])
@commands.has_role(GERANT_STAFF_ID)
async def ticket_close(ctx): 
    await ctx.send("🚨 Fermeture du salon dans 3 secondes...")
    await asyncio.sleep(3)
    await ctx.channel.delete()

@bot.command(name="rename")
@commands.has_role(GERANT_STAFF_ID)
async def ticket_rename(ctx, *, new_name: str):
    await ctx.channel.edit(name=new_name)
    await ctx.send(f"✅ Salon renommé en : `{new_name}`")

@bot.command(name="add")
@commands.has_role(GERANT_STAFF_ID)
async def ticket_add(ctx, m: discord.Member):
    await ctx.channel.set_permissions(m, view_channel=True, send_messages=True)
    await ctx.send(f"✅ {m.mention} a été ajouté au ticket.")

@bot.command(name="remove")
@commands.has_role(GERANT_STAFF_ID)
async def ticket_remove(ctx, m: discord.Member):
    await ctx.channel.set_permissions(m, view_channel=False)
    await ctx.send(f"✅ {m.mention} a été retiré du ticket.")

# --- COMMANDES GRADES ---
@bot.command(name="rank-t")
@commands.has_permissions(administrator=True)
async def rank_t_cmd(ctx, m: discord.Member):
    await m.add_roles(ctx.guild.get_role(R_T), ctx.guild.get_role(ROLE_STAFF))
    await ctx.send(f"✅ {m.mention} est maintenant **Modo Test**.")
    await send_log("RANK-T", ctx, m)

@bot.command(name="rank-c")
@commands.has_permissions(administrator=True)
async def rank_c_cmd(ctx, m: discord.Member):
    await m.remove_roles(ctx.guild.get_role(R_T))
    await m.add_roles(ctx.guild.get_role(R_C))
    await ctx.send(f"✅ {m.mention} est maintenant **Modo Confirmé**.")
    await send_log("RANK-C", ctx, m)

@bot.command(name="rank-plus")
@commands.has_permissions(administrator=True)
async def rank_plus_cmd(ctx, m: discord.Member):
    await m.remove_roles(ctx.guild.get_role(R_C))
    await m.add_roles(ctx.guild.get_role(R_PLUS))
    await ctx.send(f"✅ {m.mention} est maintenant **Modo Plus**.")
    await send_log("RANK-PLUS", ctx, m)

@bot.command(name="rank-s")
@commands.has_permissions(administrator=True)
async def rank_s_cmd(ctx, m: discord.Member):
    await m.remove_roles(ctx.guild.get_role(R_PLUS))
    await m.add_roles(ctx.guild.get_role(R_SENIOR))
    await ctx.send(f"✅ {m.mention} est maintenant **Modo Senior**.")
    await send_log("RANK-SENIOR", ctx, m)

@bot.command(name="rank-admin")
@commands.has_permissions(administrator=True)
async def rank_admin_cmd(ctx, m: discord.Member):
    await m.add_roles(ctx.guild.get_role(R_ADMIN))
    await ctx.send(f"✅ {m.mention} est maintenant **Administrateur**.")
    await send_log("RANK-ADMIN", ctx, m)

@bot.command(name="derank")
@commands.has_permissions(administrator=True)
async def derank_cmd(ctx, m: discord.Member):
    roles_to_remove = [ROLE_STAFF, R_T, R_C, R_PLUS, R_SENIOR, R_ADMIN]
    for r_id in roles_to_remove:
        role = ctx.guild.get_role(r_id)
        if role: await m.remove_roles(role)
    await ctx.send(f"🐉 {m.mention} est maintenant un simple mortel.")
    await send_log("DERANK", ctx, m, "Destitution Staff")

# --- MODÉRATION ---
@bot.command(name="clear")
@commands.has_permissions(manage_messages=True)
async def clear_cmd(ctx, n: int):
    await ctx.channel.purge(limit=n+1)
    await ctx.send(f"✅ {n} messages supprimés.", delete_after=3)
    await send_log("CLEAR", ctx, None, f"{n} messages effacés")

@bot.command(name="setup_ticket")
@commands.has_permissions(administrator=True)
async def setup_ticket_cmd(ctx):
    e = discord.Embed(title="◈ RECRUTEMENT STAFF ◈", description="Vous souhaitez rejoindre l'équipe ? Cliquez sur le bouton ci-dessous pour ouvrir votre dossier.", color=0x000000)
    e.set_thumbnail(url=bot.user.display_avatar.url)
    e.set_image(url=PANEL_IMAGE_URL)
    await ctx.send(embed=e, view=TicketPanel())

@bot.event
async def on_ready():
    bot.add_view(TicketPanel())
    print(f"✅ Connecté en tant que {bot.user}")

bot.run(TOKEN)
                        
