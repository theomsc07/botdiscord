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

# --- CONFIGURATION DES IDs ---
LOG_CH_ID = 1508595464168013965
GERANT_STAFF_ID = 1504792751777255545
ROLE_STAFF = 1504810257715822722
TICKET_CAT_ID = 1504792910892109935
R_T, R_C, R_PLUS, R_SENIOR, R_ADMIN = 1504792771977023591, 1504792768088903931, 1504792764448116776, 1504792759679057951, 1504792748098715660
PANEL_IMAGE_URL = "https://i.imgur.com/8N4N8f8.png"

# --- UTILITAIRES ---
async def send_log(action, ctx, target, reason="Aucune"):
    log_ch = bot.get_channel(LOG_CH_ID)
    if log_ch:
        e = discord.Embed(title=f"◈ LOG : {action} ◈", color=0x3498DB, timestamp=datetime.now())
        if target: e.set_thumbnail(url=target.display_avatar.url)
        e.add_field(name="Cible", value=target.mention if target else "N/A", inline=True)
        e.add_field(name="Staff", value=ctx.author.mention, inline=True)
        e.add_field(name="Détails", value=reason, inline=False)
        await log_ch.send(embed=e)

async def send_mod_embed(ctx, action, target, reason):
    e = discord.Embed(title=f"◈ SANCTION : {action} ◈", color=0xFF0000, timestamp=datetime.now())
    e.set_author(name=bot.user.name, icon_url=bot.user.display_avatar.url)
    e.set_thumbnail(url=target.display_avatar.url)
    e.add_field(name="Membre sanctionné", value=target.mention, inline=False)
    e.add_field(name="Staff", value=ctx.author.mention, inline=True)
    e.add_field(name="Raison", value=reason, inline=True)
    e.set_footer(text="Si vous pensez que c'est une erreur/abus, contactez le gérant staff : @theo_msc")
    return e

# --- TICKETS ---
class DecisionModal(discord.ui.Modal):
    def __init__(self, target, decision):
        super().__init__(title=f"Réponse à {target.name}")
        self.target = target; self.decision = decision
        self.msg = discord.ui.TextInput(label="Message personnalisé", style=discord.TextStyle.paragraph)
        self.add_item(self.msg)
    async def on_submit(self, i: discord.Interaction):
        try: await self.target.send(f"◈ **Candidature {self.decision}** ◈\n{self.msg.value}"); await i.response.send_message("✅", ephemeral=True)
        except: await i.response.send_message("❌ MP bloqué", ephemeral=True)

class TicketView(discord.ui.View):
    def __init__(self, member): super().__init__(timeout=None); self.member = member
    @discord.ui.button(label="Accepter", style=discord.ButtonStyle.green)
    async def acc(self, i, b): await i.response.send_modal(DecisionModal(self.member, "ACCEPTÉE"))
    @discord.ui.button(label="Refuser", style=discord.ButtonStyle.red)
    async def ref(self, i, b): await i.response.send_modal(DecisionModal(self.member, "REFUSÉE"))

class TicketPanel(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="Poser ma candidature", style=discord.ButtonStyle.primary, emoji="🛡️", custom_id="candid_btn")
    async def open_ticket(self, i: discord.Interaction, b):
        over = {i.guild.default_role: discord.PermissionOverwrite(view_channel=False), i.user: discord.PermissionOverwrite(view_channel=True, send_messages=True), i.guild.get_role(GERANT_STAFF_ID): discord.PermissionOverwrite(view_channel=True, send_messages=True)}
        ch = await i.guild.create_text_channel(name=f"recrut-{i.user.name}", category=i.guild.get_channel(TICKET_CAT_ID), overwrites=over)
        e = discord.Embed(title="◈ CANDIDATURE ◈", description=f"Bonjour {i.user.mention}, formulaire ici.", color=0x2C2F33)
        e.set_thumbnail(url=bot.user.display_avatar.url)
        await ch.send(content=f"{i.user.mention} | <@&{GERANT_STAFF_ID}>", embed=e, view=TicketView(i.user))
        await i.response.send_message(f"✅ Ticket : {ch.mention}", ephemeral=True)

# --- MODÉRATION ---
@bot.command()
@commands.has_permissions(kick_members=True)
async def warn(ctx, m: discord.Member, *, r="Aucune"): embed = await send_mod_embed(ctx, "WARN", m, r); try: await m.send(embed=embed) except: pass; await ctx.send(embed=embed); await send_log("WARN", ctx, m, r)

@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, m: discord.Member, *, r="Aucune"): embed = await send_mod_embed(ctx, "KICK", m, r); try: await m.send(embed=embed) except: pass; await m.kick(reason=r); await ctx.send(embed=embed); await send_log("KICK", ctx, m, r)

@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, m: discord.Member, *, r="Aucune"): embed = await send_mod_embed(ctx, "BAN", m, r); try: await m.send(embed=embed) except: pass; await m.ban(reason=r); await ctx.send(embed=embed); await send_log("BAN", ctx, m, r)

@bot.command()
@commands.has_permissions(manage_roles=True)
async def tempmute(ctx, m: discord.Member, s: int): embed = await send_mod_embed(ctx, "TEMPMUTE", m, f"{s}s"); try: await m.send(embed=embed) except: pass; [await ch.set_permissions(m, send_messages=False) for ch in ctx.guild.text_channels]; await ctx.send(embed=embed); await send_log("TEMPMUTE", ctx, m, f"{s}s"); await asyncio.sleep(s); [await ch.set_permissions(m, send_messages=None) for ch in ctx.guild.text_channels]; await ctx.send(f"✅ {m.mention} unmute.")

@bot.command()
@commands.has_permissions(manage_roles=True)
async def unmute(ctx, m: discord.Member): [await ch.set_permissions(m, send_messages=None) for ch in ctx.guild.text_channels]; await ctx.send(f"✅ {m.mention} est unmute."); await send_log("UNMUTE", ctx, m)

@bot.command()
@commands.has_permissions(ban_members=True)
async def unban(ctx, uid: int): u = await bot.fetch_user(uid); await ctx.guild.unban(u); await ctx.send(f"✅ {u.name} débanni."); await send_log("UNBAN", ctx, u)

@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, n: int): await ctx.channel.purge(limit=n+1); await send_log("CLEAR", ctx, None, f"{n} messages")

# --- GRADES ---
@bot.command()
@commands.has_permissions(administrator=True)
async def rank_t(ctx, m: discord.Member): r = ctx.guild.get_role(R_T); await m.add_roles(r, ctx.guild.get_role(ROLE_STAFF)); await ctx.send(f"✅ {m.mention} est désormais {r.mention} !"); await send_log("RANK-T", ctx, m)
@bot.command()
@commands.has_permissions(administrator=True)
async def rank_c(ctx, m: discord.Member): r_old, r_new = ctx.guild.get_role(R_T), ctx.guild.get_role(R_C); await m.remove_roles(r_old); await m.add_roles(r_new); await ctx.send(f"✅ {m.mention} est désormais {r_new.mention} !"); await send_log("RANK-C", ctx, m)
@bot.command()
@commands.has_permissions(administrator=True)
async def derank(ctx, m: discord.Member): [await m.remove_roles(ctx.guild.get_role(r)) for r in [ROLE_STAFF, R_T, R_C, R_PLUS, R_SENIOR, R_ADMIN]]; await ctx.send(f"🐉 {m.mention} est un simple mortel."); await send_log("DERANK", ctx, m)

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_ticket(ctx): e = discord.Embed(title="◈ RECRUTEMENT ◈", description="Cliquez ci-dessous.", color=0x000000); e.set_thumbnail(url=bot.user.display_avatar.url); e.set_image(url=PANEL_IMAGE_URL); await ctx.send(embed=e, view=TicketPanel())

@bot.event
async def on_ready(): bot.add_view(TicketPanel()); print("✅ Bot prêt.")
bot.run(TOKEN)
    
