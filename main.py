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
GUILD_ID = 1281988538841174026  # <<-- Change this to your test server ID

@bot.event
async def on_ready():
    global welcome_channel_id, leave_channel_id
    welcome_channel_id, leave_channel_id = load_channel_data()
    
    load_credits()  # ✅ Load credits from file

    try:
        await bot.tree.sync(guild=discord.Object(id=GUILD_ID))  # ✅ Sync all commands for guild
        print(f"[✅] Synced slash commands for {bot.user} in test guild")
    except Exception as e:
        print(f"[❌] Slash command sync failed: {e}")

    print(f"✅ Logged in as {bot.user}")

# --- Globals ---
welcome_channel_id = None
leave_channel_id = None
ticket_category_id = None
welcome_image_url = "."
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

        embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
        embed.set_footer(text=f"Thanks for Joining! | Joined at {join_time}")
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


# =================== TICKET SYSTEM ===================

ticket_owners = {}
user_credits = {}
voice_channel_start_times = {}

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

# =================== TICKET VIEWS ===================

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

# =================== BACK BUTTON ===================

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

# =================== PRODUCT BUTTON ===================

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

# =================== PLAN VIEW & BUTTON ===================

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
            description=f"**Product:** {self.product}\n**Plan:** {self.plan}\n**User:** {self.user.mention}\n\n📢 @Brothers will assist you shortly.",
            color=discord.Color.green()
        )
        await interaction.channel.send(embed=embed)
        await interaction.response.send_message(f"✅ You selected: **{self.plan}** for **{self.product}**.", ephemeral=True)

# =================== CLOSE TICKET BUTTON & VIEW ===================

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
        
# =================== TICKET REPLY NOTIFICATION ===================
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.channel.id in ticket_owners:
        owner = ticket_owners[message.channel.id]
        if message.author != owner:
            try:
                await owner.send(
                    f"📢 Someone replied in your ticket `{message.channel.name}`:\n>>> {message.content}"
                )
            except discord.Forbidden:
                pass

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
                save_credits()
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
    sorted_users = sorted(user_credits.items(), key=lambda x: x[1], reverse=True)
    top_10 = sorted_users[:10]
    leaderboard_message = "**Top 10 Users with the Most Credits:**\n\n"
    for idx, (user_id, credits) in enumerate(top_10, 1):
        user = ctx.guild.get_member(user_id)
        username = user.name if user else "Unknown"
        leaderboard_message += f"{idx}. {username} - {credits} credits\n"
    embed = discord.Embed(
        description=leaderboard_message,
        color=discord.Color.red(),
        timestamp=datetime.utcnow()
    )
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

# =================== REQUIREMENTS PANEL (DROPDOWN STYLE) ===================
@bot.tree.command(name="requirements", description="Open the system requirements panel.")
@app_commands.guilds(discord.Object(id=GUILD_ID))
async def requirements(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📋 Requirements Panel",
        description="Select the requirement you want to download from the dropdown below.",
        color=discord.Color.blurple()
    )
    embed.set_footer(text="Brothers Army | Requirements Center")
    view = RequirementsDropdownView()
    await interaction.response.send_message(embed=embed, view=view, ephemeral=False)

class RequirementsDropdownView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(RequirementsDropdown())

class RequirementsDropdown(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label="🧩 DirectX & Visual C++",
                description="Required for Free Fire panel to work properly.",
                value="directx"
            ),
            discord.SelectOption(
                label="💻 .NET Framework 4.8 / 8",
                description="Required for Free Fire panel to work properly.",
                value="dotnet"
            ),
            discord.SelectOption(
                label="🧠 Disable Hyper-V",
                description="Required for Free Fire panel to work properly.",
                value="hyperv"
            ),
            discord.SelectOption(
                label="🛡 Windows Defender Fix",
                description="Required for Free Fire panel to work properly.",
                value="defender"
            )
        ]
        super().__init__(
            placeholder="📋 Choose a requirement to download...",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        selection = self.values[0]
        links = {
            "directx": "https://cdn.discordapp.com/attachments/1304025484769628170/1305560640802521158/Requerimientos_1.rar?ex=68f1bd58&is=68f06bd8&hm=79149732caadc4b49ceb1120687f1fda05c54a0125b41c0eda2b63627b20a4d3",
            "dotnet": "https://example.com/dotnet-placeholder",
            "hyperv": "https://cdn.discordapp.com/attachments/1304025484769628170/1427414446979940372/HD-DisableHyperV_native_v2.exe?ex=68f2128c&is=68f0c10c&hm=f66d9466590c74f66bac6cc66d4487852d4b23aa75ac7c2eab724d3326f21e92",
            "defender": "https://cdn.discordapp.com/attachments/1258024547878441071/1262949258953228328/Antivirus_Fix.zip?ex=68f1a0a7&is=68f04f27&hm=ebbe6f1ef8f21677ac108a3f7acf4073ccc5961a8a30871f04f3"
        }

        titles = {
            "directx": "🧩 DirectX & Visual C++",
            "dotnet": "💻 .NET Framework 4.8 / 8",
            "hyperv": "🧠 Disable Hyper-V",
            "defender": "🛡 Windows Defender Fix"
        }

        title = titles.get(selection, "Requirement")
        link = links.get(selection, "Link not available")

        embed = discord.Embed(
            title=title,
            description=f"This is required for Free Fire panel to work properly.\n\nClick the button below to download:",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        embed.set_footer(text="Brothers Army | Requirements Downloader")
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="Click Here to Download", url=link, style=discord.ButtonStyle.link))
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

# =================== NEW FREE FIRE APK PANEL ===================
@bot.tree.command(name="freefireapk", description="Download Free Fire APKs from the dropdown.")
@app_commands.guilds(discord.Object(id=GUILD_ID))
async def freefireapk(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📥 Free Fire APK Panel",
        description="Choose which Free Fire APK you want to download from the dropdown below.",
        color=discord.Color.blurple()
    )
    embed.set_footer(text="Brothers Army | Free Fire APK Downloader")
    view = FreeFireDropdownView()
    await interaction.response.send_message(embed=embed, view=view, ephemeral=False)

class FreeFireDropdownView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(FreeFireDropdown())

class FreeFireDropdown(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label="🔥 Free Fire Amazon APK",
                description="Download the Free Fire Amazon APK.",
                value="amazon"
            ),
            discord.SelectOption(
                label="🎯 Free Fire Combo APK",
                description="Download the Free Fire Combo APK.",
                value="combo"
            ),
            discord.SelectOption(
                label="🌍 Free Fire Global APK",
                description="Download the Free Fire Global APK.",
                value="global"
            )
        ]
        super().__init__(
            placeholder="📋 Choose the Free Fire APK...",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        selection = self.values[0]
        links = {
            "amazon": "https://cdn.discordapp.com/attachments/1370143048062734336/1428346041006166167/FF_OB50.xapk?ex=68f22a69&is=68f0d8e9&hm=17616561db1d01eaf29d17c583d51820a757c7b8caf9e4de47ca20da3495e68b&", 
            "combo": "https://cdn.discordapp.com/attachments/1392480174104383623/1400092321520816200/Garena_Free_Fire_1.114.1_apkcombo.com.xapk?ex=68f18d55&is=68f03bd5&hm=a374f1a86daa54fc37568a46db15d2b80066df05d5dba7cf8e436f880676e522",
            "global": "https://cdn.discordapp.com/attachments/1370143048062734336/1428344985962418196/FreeFireGlobalApk.zip?ex=68f2296e&is=68f0d7ee&hm=dfa1d69015b9da2f095faac79d65f453f1621114a6dc665c507fc4dc23bf14fc&" 
        }

        titles = {
            "amazon": "🔥 Free Fire Amazon APK",
            "combo": "🎯 Free Fire Combo APK",
            "global": "🌍 Free Fire Global APK"
        }

        title = titles.get(selection, "Free Fire APK")
        link = links.get(selection, "Link not available")

        embed = discord.Embed(
            title=title,
            description=f"Click the button below to download your selected Free Fire APK:",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        embed.set_footer(text="Brothers Army | Free Fire Downloader")
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="Click Here to Download", url=link, style=discord.ButtonStyle.link))
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        
# =================== EMULATOR PANEL ===================
@bot.tree.command(name="emulators", description="Open the emulator download panel.")
@app_commands.guilds(discord.Object(id=GUILD_ID))
async def emulators(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🖥 Emulator Panel",
        description="Select the emulator you want to download:",
        color=discord.Color.blurple()
    )
    view = EmulatorChoiceView()
    await interaction.response.send_message(embed=embed, view=view, ephemeral=False)

# -------- Page 1 Buttons --------
class EmulatorChoiceView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(EmulatorButton("Bluestacks", "bluestacks"))
        self.add_item(EmulatorButton("MSI", "msi"))

class EmulatorButton(discord.ui.Button):
    def __init__(self, label, custom_id):
        super().__init__(label=label, style=discord.ButtonStyle.primary, custom_id=custom_id)

    async def callback(self, interaction: discord.Interaction):
        emulator = self.custom_id
        if emulator == "bluestacks":
            await interaction.response.edit_message(
                embed=discord.Embed(
                    title="📋 Bluestacks Versions",
                    description="Choose which Bluestacks version you want to download:",
                    color=discord.Color.green()
                ),
                view=BluestacksDropdownView()
            )
        elif emulator == "msi":
            await interaction.response.edit_message(
                embed=discord.Embed(
                    title="📋 MSI Versions",
                    description="Choose which MSI emulator version you want to download:",
                    color=discord.Color.green()
                ),
                view=MSIDropdownView()
            )

# -------- Back Button --------
class BackToEmulatorChoiceButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="🔙 Back", style=discord.ButtonStyle.secondary)

    async def callback(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🖥 Emulator Panel",
            description="Select the emulator you want to download:",
            color=discord.Color.blurple()
        )
        await interaction.response.edit_message(embed=embed, view=EmulatorChoiceView())

# -------- Bluestacks Dropdown --------
class BluestacksDropdownView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(BluestacksDropdown())
        self.add_item(BackToEmulatorChoiceButton())

class BluestacksDropdown(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Bluestacks 5.22", description="Download Bluestacks 5.22 installer", value="bs522"),
            discord.SelectOption(label="Bluestacks 5.14", description="Download Bluestacks 5.14 installer", value="bs514"),
            discord.SelectOption(label="Bluestacks 5.12", description="Download Bluestacks 5.12 installer", value="bs512"),
            discord.SelectOption(label="Bluestacks 5.9", description="Download Bluestacks 5.9 installer", value="bs59"),
            discord.SelectOption(label="Bluestacks 4", description="Download Bluestacks 4 installer", value="bs4")
        ]
        super().__init__(placeholder="📋 Choose Bluestacks version...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        links = {
            "bs522": "https://cdn.discordapp.com/attachments/1370143048062734336/1428348113621356655/BlueStacksInstaller_5.22.125.1001_native_f7ab1781dac28810aa6baa4242803436_MzsxNQ.exe?ex=68f22c57&is=68f0dad7&hm=2ed23cf11ca7a918318ae4fdae0fb98e2238daa180b24e132ad79b95f9846476&",
            "bs514": "https://cdn.discordapp.com/attachments/1370143048062734336/1428349404732981269/BlueStacks_App_Player_v5.14.10.exe?ex=68f22d8b&is=68f0dc0b&hm=07b17131d2301aae7da3a7bec9f1d6f8ea41e25906a445399301c87bad70962c&",
            "bs512": "https://cdn.discordapp.com/attachments/1370143048062734336/1428349519749316618/BlueStacks_App_Player_v5.12.115.exe?ex=68f22da6&is=68f0dc26&hm=38d90695fa8381ee736c589790b4edfff307bf65217189cc69bb68e862b46772&",
            "bs59": "https://cdn.discordapp.com/attachments/1370143048062734336/1428349624103473252/BlueStacks_App_Player_v5.9.0.exe?ex=68f22dbf&is=68f0dc3f&hm=6af6900e480abd392341331eeb041413878578291def259cf419268a5fa3a306&",
            "bs4": "https://cdn.discordapp.com/attachments/1370143048062734336/1428349679195918346/BlueStacksMicroInstaller_4.280.1.1002_native_c7e2d110d374cecd4f763f9844041184.exe?ex=68f22dcc&is=68f0dc4c&hm=47c210f6a46290ac76d5b773dd8035bc671882b68c41bd0e51064010ed6eac7b&"
        }
        selection = self.values[0]
        link = links.get(selection, "Link not available")
        embed = discord.Embed(
            title=f"💻 {selection} Download",
            description="Click the button below to download the emulator.",
            color=discord.Color.green()
        )
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="Click Here to Download", url=link, style=discord.ButtonStyle.link))
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

# -------- MSI Dropdown --------
class MSIDropdownView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(MSIDropdown())
        self.add_item(BackToEmulatorChoiceButton())

class MSIDropdown(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="MSI 5.22", description="Download MSI 5.22 installer", value="msi522"),
            discord.SelectOption(label="MSI 5.12", description="Download MSI 5.12 installer", value="msi512"),
            discord.SelectOption(label="MSI 5.9", description="Download MSI 5.9 installer", value="msi59"),
            discord.SelectOption(label="MSI 4", description="Download MSI 4 installer", value="msi4")
        ]
        super().__init__(placeholder="📋 Choose MSI version...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        links = {
            "msi522": "https://cdn.discordapp.com/attachments/1370143048062734336/1428350293254340649/BlueStacksMicroInstaller_5.22.75.6322_native.exe?ex=68f22e5f&is=68f0dcdf&hm=1406c20dd6f1f2bbd61644b004d1144e494f238fb879b48feff8359681974020&",
            "msi512": "https://cdn.discordapp.com/attachments/1391076756051460208/1406340422594465975/MSI_5.12.exe?ex=68f1ded5&is=68f08d55&hm=952a42e48b3455805ac0e50a5c22caefc020501b906da24c229519a9ee137f32&",
            "msi59": "https://cdn.discordapp.com/attachments/1370143048062734336/1428351932904243402/msi-app-player-5.9.300.6315-installer.exe?ex=68f22fe6&is=68f0de66&hm=002c3d943e468020932d96c014cf8ab42da57636d3e2ce93005713707a2b9db5&",
            "msi4": "https://cdn.discordapp.com/attachments/1370143048062734336/1428352085044363354/MSI_APP_Player.exe?ex=68f2300a&is=68f0de8a&hm=438247d09429483927c42c0247e8d4e58af595ee5e538aae353da8275c065273&"
        }
        selection = self.values[0]
        link = links.get(selection, "Link not available")
        embed = discord.Embed(
            title=f"💻 {selection} Download",
            description="Click the button below to download the emulator.",
            color=discord.Color.green()
        )
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="Click Here to Download", url=link, style=discord.ButtonStyle.link))
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

# --- Start Bot ---
bot.run(TOKEN)
