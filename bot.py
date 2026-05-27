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

# --- IDs CONFIG ---
LOG_CH_ID = 1508595464168013965
GERANT_STAFF_ID = 1504792751777255545
ROLE_STAFF = 1504810257715822722
TICKET_CAT_ID = 1504792910892109935
R_T, R_C, R_PLUS, R_SENIOR, R_ADMIN = 1504792771977023591, 1504792768088903931, 1504792764448116776, 1504792759679057951, 1504792748098715660

# --- UTILS ---
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
    e.set_thumbnail(url=target.display_avatar.url)
    e.add_field(name="Membre", value=target.mention, inline=False)
    e.add_field(name="Staff", value=ctx.author.mention, inline=True)
    e.add_field(name="Raison", value=reason, inline=True)
    return e

# --- TICKETS ---
class DecisionModal(discord.ui.Modal):
    def __init__(self, target, decision):
        super().__init__(title=f"Réponse à {target.name}")
        self.target = target; self.decision = decision
        self.msg = discord.ui.TextInput(label="Message", style=discord.TextStyle.paragraph)
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
        e = discord.Embed(title="◈ CANDIDATURE ◈", description="Merci d'envoyer votre candidature ici !", color=0x2C2F33)
        await ch.send(content=f"{i.user.mention} | <@&{GERANT_STAFF_ID}>", embed=e, view=TicketView(i.user)); await i.response.send_message("✅ Ouvert", ephemeral=True)

# --- MODERATION & GRADES ---
@bot.command()
@commands.has_permissions(kick_members=True)
async def warn(ctx, m: discord.Member, *, r="Aucune"): e = await send_mod_embed(ctx, "WARN", m, r); try: await m.send(embed=e) except: pass; await ctx.send(embed=e); await send_log("WARN", ctx, m, r)
@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, m: discord.Member, *, r="Aucune"): e = await send_mod_embed(ctx, "KICK", m, r); try: await m.send(embed=e) except: pass; await m.kick(reason=r); await ctx.send(embed=e); await send_log("KICK", ctx, m, r)
@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, m: discord.Member, *, r="Aucune"): e = await send_mod_embed(ctx, "BAN", m, r); try: await m.send(embed=e) except: pass; await m.ban(reason=r); await ctx.send(embed=e); await send_log("BAN", ctx, m, r)
@bot.command()
@commands.has_permissions(manage_roles=True)
async def tempmute(ctx, m: discord.Member, s: int): e = await send_mod_embed(ctx, "MUTE", m, f"{s}s"); try: await m.send(embed=e) except: pass; [await ch.set_permissions(m, send_messages=False) for ch in ctx.guild.text_channels]; await ctx.send(embed=e); await send_log("MUTE", ctx, m, f"{s}s"); await asyncio.sleep(s); [await ch.set_permissions(m, send_messages=None) for ch in ctx.guild.text_channels]
@bot.command()
@commands.has_permissions(administrator=True)
async def rank_t(ctx, m: discord.Member): r = ctx.guild.get_role(R_T); await m.add_roles(r, ctx.guild.get_role(ROLE_STAFF)); await ctx.send(f"✅ {m.mention} est {r.mention} !"); await send_log("RANK-T", ctx, m)
@bot.command()
@commands.has_permissions(administrator=True)
async def derank(ctx, m: discord.Member): [await m.remove_roles(ctx.guild.get_role(r)) for r in [ROLE_STAFF, R_T, R_C, R_PLUS, R_SENIOR, R_ADMIN]]; await ctx.send(f"🐉 {m.mention} est redevenu un simple mortel."); await send_log("DERANK", ctx, m)

# --- TICKETS ADMIN ---
@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, n: int): await ctx.message.delete(); deleted = await ctx.channel.purge(limit=n); await ctx.send(f"🧹 {len(deleted)} msg supprimés.", delete_after=3)
@bot.command()
@commands.has_role(GERANT_STAFF_ID)
async def del(ctx): await ctx.channel.delete()
@bot.command()
@commands.has_role(GERANT_STAFF_ID)
async def add(ctx, m: discord.Member): await ctx.channel.set_permissions(m, view_channel=True, send_messages=True); await ctx.send(f"✅ Ajouté.")
@bot.command()
@commands.has_role(GERANT_STAFF_ID)
async def remove(ctx, m: discord.Member): await ctx.channel.set_permissions(m, view_channel=False); await ctx.send(f"✅ Retiré.")
@bot.command()
@commands.has_role(GERANT_STAFF_ID)
async def rename(ctx, *, nom: str): await ctx.channel.edit(name=nom); await ctx.send(f"✅ Renommé.")
@bot.command()
@commands.has_permissions(administrator=True)
async def setup_ticket(ctx): e = discord.Embed(title="◈ RECRUTEMENT ◈", description="Cliquez pour candidater !", color=0x000000); e.set_thumbnail(url=bot.user.display_avatar.url); await ctx.send(embed=e, view=TicketPanel())

@bot.event
async def on_ready(): bot.add_view(TicketPanel()); print("✅ Bot actif.")
bot.run(TOKEN)
