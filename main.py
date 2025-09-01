# --- Imports ---
import discord
from discord.ext import commands, tasks
from discord import app_commands
from discord.ui import Button, View
from discord.utils import get
from datetime import timedelta, datetime
import os, asyncio, json, random
from dotenv import load_dotenv
from keep_alive import keep_alive
# --- Bot Setup ---
load_dotenv()
TOKEN = os.getenv("TOKEN")
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# --- Credit Storage Functions ---
def save_credits():
    with open("credits.json", "w") as f:
        json.dump(user_credits, f)

def load_credits():
    global user_credits
    try:
        with open("credits.json", "r") as f:
            user_credits = json.load(f)
            user_credits = {int(k): v for k, v in user_credits.items()}
    except (FileNotFoundError, json.JSONDecodeError):
        user_credits = {}

# -------- ON_READY --------
@bot.event
async def on_ready():
    global welcome_channel_id, leave_channel_id
    welcome_channel_id, leave_channel_id = load_channel_data()
    
    load_credits()  # ✅ Load credits from file

    try:
        bot.tree.add_command(ticketpanel)
        await bot.tree.sync()
        print(f"[✅] Synced slash commands for {bot.user}")
    except Exception as e:
        print(f"[❌] Slash command sync failed: {e}")

    print(f"✅ Logged in as {bot.user}")

# --- Globals ---
welcome_channel_id = None
leave_channel_id = None
ticket_category_id = None
welcome_image_url = "https://auto.creavite.co/api/out/xqzrBUqLQ6ilszt1c9_standard.gif"
UPI_QR_CODE_URL = "https://cdn.discordapp.com/attachments/1367192983740354672/1400094921590837258/my_cred_upi_qr.png?ex=68a47001&is=68a31e81&hm=d92f66426ca8e2c4c699a6b8f76f29026d349838763fde6cd1d82af697e14550"

voice_channel_start_times = {}
user_credits = {}

# --- Channel Config Storage ---
def load_channel_data():
    try:
        with open("channel_config.json", "r") as f:
            data = json.load(f)
            return data.get("welcome_channel"), data.get("leave_channel")
    except:
        return None, None

def save_channel_data(welcome_id, leave_id):
    with open("channel_config.json", "w") as f:
        json.dump({"welcome_channel": welcome_id, "leave_channel": leave_id}, f)

from discord.utils import get
import discord
from datetime import datetime

@bot.event
async def on_member_join(member):
    role = get(member.guild.roles, name="Brothers Army")
    if role:
        await member.add_roles(role)

    channel = bot.get_channel(welcome_channel_id)
    if channel:
        join_time = datetime.utcnow().strftime("%I:%M %p (UTC)")

        embed = discord.Embed(
            title="** WELCOME TO OUR SERVER **",
            description=(
                f"**https://discord.com/channels/1281988538841174026/1349250897456136202**\n"
                f"\u2800\n"
                f"**https://discord.com/channels/1281988538841174026/1349248257309675530**\n"
                f"\u2800\n"
                f"**https://discord.com/channels/1281988538841174026/1349253174766342214**\n"
                f"\u2800\n"
                f"**https://discord.com/channels/1281988538841174026/1349253276721352785**"
            ),
            color=discord.Color.red(),
            timestamp=datetime.utcnow()
        )

        # Avatar at top-right
        embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)

        # Footer with time
        embed.set_footer(text=f"Thanks for Joining! | Joined at {join_time}")

        # Add GIF image at bottom
        embed.set_image(url="https://auto.creavite.co/api/out/xqzrBUqLQ6ilszt1c9_standard.gif")

        await channel.send(f"**Hello** {member.mention} 👋")
        await channel.send(embed=embed)

@bot.event
async def on_member_remove(member):
    if leave_channel_id:
        channel = bot.get_channel(leave_channel_id)
        if channel:
            await channel.send(f"{member.mention} has left the server. 👋")
            embed = discord.Embed(
                title="👋 Member Left",
                description=f"Now there are **{member.guild.member_count}** members in the server.",
                color=discord.Color.red()
            )
            await channel.send(embed=embed)

# --- Slash Commands ---
@bot.tree.command(name="setwelcome", description="Set the welcome channel.")
@app_commands.describe(channel="Select the welcome channel.")
async def set_welcome(interaction: discord.Interaction, channel: discord.TextChannel):
    global welcome_channel_id
    welcome_channel_id = channel.id
    save_channel_data(welcome_channel_id, leave_channel_id)
    await interaction.response.send_message(f"✅ Welcome channel set to: {channel.mention}", ephemeral=True)

@bot.tree.command(name="setleave", description="Set the leave channel.")
@app_commands.describe(channel="Select the leave channel.")
async def set_leave(interaction: discord.Interaction, channel: discord.TextChannel):
    global leave_channel_id
    leave_channel_id = channel.id
    save_channel_data(welcome_channel_id, leave_channel_id)
    await interaction.response.send_message(f"✅ Leave channel set to: {channel.mention}", ephemeral=True)

@bot.tree.command(name="sendqr", description="Sends your UPI QR code.")
async def send_qr(interaction: discord.Interaction):
    embed = discord.Embed(description="Here is your UPI QR code:")
    embed.set_image(url=UPI_QR_CODE_URL)
    await interaction.response.send_message(embed=embed)

# =================== TICKET SYSTEM (FINAL FULL VERSION) ===================

# Global tracker for ticket creators
ticket_owners = {}  # {channel_id: user_object}
user_credits = {}  # Stores user credits
voice_channel_start_times = {}  # Tracks VC join time

@bot.tree.command(name="setticketcategory", description="Set the category for ticket channels.")
@app_commands.describe(category="Select the category for tickets.")
async def setticketcategory(interaction: discord.Interaction, category: discord.CategoryChannel):
    global ticket_category_id
    ticket_category_id = category.id
    await interaction.response.send_message(f"🎫 Ticket category set to: **{category.name}**", ephemeral=True)

@bot.tree.command(name="ticketpanel", description="Show the advanced ticket panel with categories.")
async def ticketpanel(interaction: discord.Interaction):
    view = CategoryView()
    embed = discord.Embed(
        title="🛒 Ticket Panel",
        description="Please select a category to begin:",
        color=discord.Color.blurple()
    )
    await interaction.response.send_message(embed=embed, view=view)

class CategoryView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(CategoryButton("🎯 Aimbot Products", "aimbot", row=0))
        self.add_item(CategoryButton("🎮 Streamer Tools", "streamer", row=1))
        self.add_item(CategoryButton("🧽 PC Optimization", "optimization", row=2))
        self.add_item(CategoryButton("🛠️ Support", "support", row=3))

class CategoryButton(discord.ui.Button):
    def __init__(self, label, custom_id, row=None):
        super().__init__(label=label, style=discord.ButtonStyle.primary, custom_id=custom_id, row=row)

    async def callback(self, interaction: discord.Interaction):
        category = self.custom_id

        if category == "aimbot":
            await interaction.response.edit_message(embed=discord.Embed(
                title="🎯 Aimbot Products",
                description="Select a product to create a ticket.",
                color=discord.Color.red()
            ), view=AimbotView())

        elif category == "streamer":
            await interaction.response.edit_message(embed=discord.Embed(
                title="🎮 Streamer Tools",
                description="Select a product to create a ticket.",
                color=discord.Color.green()
            ), view=StreamerView())

        elif category == "optimization":
            await interaction.response.edit_message(embed=discord.Embed(
                title="🧽 PC Optimization",
                description="Click below to create an optimization ticket.",
                color=discord.Color.orange()
            ), view=OptimizationView())

        elif category == "support":
            await interaction.response.edit_message(embed=discord.Embed(
                title="🛠️ Support",
                description="Click below to open a support ticket.",
                color=discord.Color.greyple()
            ), view=SupportView())

class AimbotView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(ProductButton("📦 Buy Brutal", "brutal", row=0))
        self.add_item(ProductButton("🧠 Buy Internal", "internal", row=1))
        self.add_item(ProductButton("🎯 Buy Silent-Aim", "silentaim", row=2))
        self.add_item(ProductButton("🎯 Buy Aim-Visible", "aimvisible", row=3))
        self.add_item(ProductButton("💀 Buy Ultimate", "ultimate", row=4))
        self.add_item(BackButton())

class StreamerView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(ProductButton("📺 Streamer External", "streamerexternal", row=0))
        self.add_item(ProductButton("🎮 Streamer Internal", "streamerinternal", row=1))
        self.add_item(ProductButton("🕹 Emulator Bypass", "emulatorbypass", row=2))
        self.add_item(BackButton())

class OptimizationView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(ProductButton("🧽 PC Optimization", "pcoptimization"))
        self.add_item(BackButton())

class SupportView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(ProductButton("🛠️ Support Ticket", "support"))
        self.add_item(BackButton())

class BackButton(discord.ui.Button):
    def __init__(self, row=None):
        super().__init__(label="🔙 Back", style=discord.ButtonStyle.secondary, row=row)

    async def callback(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🛒 Ticket Panel",
            description="Please select a category to begin:",
            color=discord.Color.blurple()
        )
        await interaction.response.edit_message(embed=embed, view=CategoryView())

class ProductButton(discord.ui.Button):
    def __init__(self, label, custom_id, row=None):
        super().__init__(label=label, style=discord.ButtonStyle.success, custom_id=custom_id, row=row)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        user = interaction.user
        product = self.custom_id
        ticket_name = f"ticket-{user.name.lower()}"

        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            interaction.guild.me: discord.PermissionOverwrite(read_messages=True),
            discord.utils.get(interaction.guild.roles, name="Staff"): discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }

        category = interaction.guild.get_channel(ticket_category_id) if ticket_category_id else None
        channel = await interaction.guild.create_text_channel(ticket_name, overwrites=overwrites, category=category)
        ticket_owners[channel.id] = user

        if product == "support":
            staff_role = discord.utils.get(interaction.guild.roles, name="Staff")
            embed = discord.Embed(
                title="🔧 Support Ticket Created",
                description=f"Hey {user.mention}, our support team will assist you shortly.\n\n{staff_role.mention}",
                color=discord.Color.red()
            )
            await channel.send(embed=embed, view=CloseTicketView())

        elif product == "pcoptimization":
            owner_role = discord.utils.get(interaction.guild.roles, name="Owner")
            embed = discord.Embed(
                title="🧽 PC Optimization Ticket",
                description=f"Hey {user.mention}, please describe your optimization needs below.\n\n{owner_role.mention}",
                color=discord.Color.orange()
            )
            await channel.send(embed=embed, view=CloseTicketView())

        else:
            embed = discord.Embed(
                title="🎛 Ticket Created",
                description=f"Hey {user.mention}, please select a plan below.",
                color=discord.Color.orange()
            )
            embed.set_thumbnail(url=user.avatar.url if user.avatar else user.default_avatar.url)
            view = PlanView(product, user)
            await channel.send(embed=embed, view=view)
            await channel.send(view=CloseTicketView())

        await interaction.followup.send(f"✅ Ticket created: {channel.mention}", ephemeral=True)

class PlanView(discord.ui.View):
    def __init__(self, product, user):
        super().__init__(timeout=None)
        self.add_item(PlanButton("🥐 Buy 1 Day", "1 Day", product, user, row=0))
        self.add_item(PlanButton("🗓 Buy 7 Days", "7 Days", product, user, row=1))
        self.add_item(PlanButton("🗒 Buy 30 Days", "30 Days", product, user, row=2))
        self.add_item(PlanButton("🛒 Buy Permanent", "Permanent", product, user, row=3))

class PlanButton(discord.ui.Button):
    def __init__(self, label, plan, product, user, row=None):
        super().__init__(label=label, style=discord.ButtonStyle.success, row=row)
        self.plan = plan
        self.product = product
        self.user = user

    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.user:
            await interaction.response.send_message("❌ Only the ticket creator can select a plan.", ephemeral=True)
            return

        embed = discord.Embed(
            title="✅ Plan Selected",
            description=f"**Product:** `{self.product}`\n**Plan:** `{self.plan}`\n**User:** {self.user.mention}\n\n📢 @Brothers will assist you shortly.",
            color=discord.Color.green()
        )
        await interaction.channel.send(embed=embed)
        await interaction.response.send_message(
            f"✅ You selected: **{self.plan}** for **{self.product}**.",
            ephemeral=True
        )

class CloseTicketButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="🔒 Close Ticket", style=discord.ButtonStyle.danger)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message("⏳ Closing ticket in 5 seconds...", ephemeral=True)
        await asyncio.sleep(5)
        await interaction.channel.delete()

class CloseTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(CloseTicketButton())

#======= TICKET REPLY NOTIFICATION ===================
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # Notify ticket owner on reply
    if message.channel.id in ticket_owners:
        owner = ticket_owners[message.channel.id]
        if message.author != owner:
            try:
                await owner.send(
                    f"📢 Someone replied in your ticket `{message.channel.name}`:\n>>> {message.content}"
                )
            except discord.Forbidden:
                pass

    # ✅ Credits system (add this block)
    uid = message.author.id
    user_credits[uid] = user_credits.get(uid, 0) + random.randint(1, 5)
    save_credits()

    await check_auto_roles(message.author)
    await bot.process_commands(message)

# =================== VOICE CREDITS ===================
@bot.event
async def on_voice_state_update(member, before, after):
    if member.bot:
        return

    if before.channel != after.channel:
        if before.channel and member.id in voice_channel_start_times:
            start_time = voice_channel_start_times.pop(member.id)
            time_spent = (datetime.utcnow() - start_time).total_seconds()
            credits_earned = int(time_spent // 60)

            if credits_earned > 0:
                user_credits[member.id] = user_credits.get(member.id, 0) + credits_earned
                save_credits()  # ✅ save yaha bhi kar le
                try:
                    await member.send(
                        f"🎉 You've earned **{credits_earned}** credits for spending **{int(time_spent // 60)} minutes** in a voice channel!"
                    )
                except discord.Forbidden:
                    pass

        if after.channel:
            voice_channel_start_times[member.id] = datetime.utcnow()   
# =================== CREDITS COMMAND ===================
@bot.command()
async def credits(ctx):
    uid = ctx.author.id
    credit_amount = user_credits.get(uid, 0)
    await ctx.send(f"💰 {ctx.author.mention}, you have **{credit_amount}** credits.")

@bot.command()
async def leaderboard(ctx):
    # Assuming user_credits is a dictionary where keys are user_ids and values are credits
    sorted_users = sorted(user_credits.items(), key=lambda x: x[1], reverse=True)

    # Get top 10 users
    top_10 = sorted_users[:10]

    # Build the leaderboard message
    leaderboard_message = "**Top 10 Users with the Most Credits:**\n\n"
    for idx, (user_id, credits) in enumerate(top_10, 1):
        user = ctx.guild.get_member(user_id)
        username = user.name if user else "Unknown"
        leaderboard_message += f"{idx}. {username} - {credits} credits\n"

    # Create the embed
    embed = discord.Embed(
        description=leaderboard_message,
        color=discord.Color.red(),
        timestamp=datetime.utcnow()
    )

    # Send the embed
    await ctx.send(embed=embed)
   
# =================== AUTO ROLE BASED ON CREDITS ===================
async def check_auto_roles(user):
    credits = user_credits.get(user.id, 0)
    thresholds = [
        (1000, "1000+ Credits"),
        (500, "500+ Credits"),
        (150, "150+ Credits"),
        (100, "100+ Credits"),
        (50, "50+ Credits")
    ]

    for threshold, role_name in thresholds:
        role = discord.utils.get(user.guild.roles, name=role_name)
        if role:
            if credits >= threshold and role not in user.roles:
                await user.add_roles(role)
                try:
                    await user.send(f"🎉 You've been given the '**{role_name}**' role for your activity!")
                except discord.Forbidden:
                    pass

# --- Start Bot ---
keep_alive()
bot.run(TOKEN)