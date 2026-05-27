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
        except: await i.response.send_message("❌ MP bloqué", ephemeral=True)

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
        over = {i.guild.default_role: discord.PermissionOverwrite(view_channel=False), i.user: discord.PermissionOverwrite(view_channel=True, send_messages=True), i.guild.get_role(GERANT_STAFF_ID): discord.PermissionOverwrite(view_channel=True, send_messages=True)}
        ch = await i.guild.create_text_channel(name=f"recrut-{i.user.name}", category=i.guild.get_channel(TICKET_CAT_ID), overwrites=over)
        e = discord.Embed(title="◈ CANDIDATURE ◈", description="Merci d'envoyer votre candidature ici, le gérant staff va s'occuper !", color=0x2C2F33)
        e.set_thumbnail(url=bot.user.display_avatar.url)
        await ch.send(content=f"{i.user.mention} | <@&{GERANT_STAFF_ID}>", embed=e, view=TicketView(i.user))
        await i.response.send_message(f"✅ Ticket ouvert.", ephemeral=True)

# --- COMMANDES ---
@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, n: int):
    await ctx.message.delete()
    deleted = await ctx.channel.purge(limit=n)
    await ctx.send(f"🧹 {len(deleted)} messages supprimés.", delete_after=3)

@bot.command()
@commands.has_role(GERANT_STAFF_ID)
async def del(ctx):
    await ctx.send("⏳ Suppression du salon dans 2 secondes...")
    await asyncio.sleep(2)
    await ctx.channel.delete()

@bot.command()
@commands.has_role(GERANT_STAFF_ID)
async def add(ctx, m: discord.Member): await ctx.channel.set_permissions(m, view_channel=True, send_messages=True); await ctx.send(f"✅ {m.mention} ajouté.")

@bot.command()
@commands.has_role(GERANT_STAFF_ID)
async def remove(ctx, m: discord.Member): await ctx.channel.set_permissions(m, view_channel=False); await ctx.send(f"✅ {m.mention} retiré.")

@bot.command()
@commands.has_role(GERANT_STAFF_ID)
async def rename(ctx, *, nom: str): await ctx.channel.edit(name=nom); await ctx.send(f"✅ Renommé en : {nom}")

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_ticket(ctx):
    e = discord.Embed(title="◈ RECRUTEMENT ◈", description="Bonjour, tu veux tenter ta chance pour devenir staff ? Je te laisse appuyer sur le bouton pour envoyer ta candidature !", color=0x000000)
    e.set_thumbnail(url=bot.user.display_avatar.url)
    await ctx.send(embed=e, view=TicketPanel())

@bot.event
async def on_ready():
    bot.add_view(TicketPanel())
    print("✅ Bot opérationnel.")

bot.run(TOKEN)
                                                                         
