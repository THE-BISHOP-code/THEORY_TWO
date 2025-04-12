# main.py

import discord
from discord.ext import commands
from discord import app_commands # Required for slash commands

# Suppress warnings
import warnings
warnings.filterwarnings("ignore", category=UserWarning, message="PyNaCl is not installed, voice will NOT be supported")
warnings.filterwarnings("ignore", message="Curlm already closed! quitting from process_data")
warnings.filterwarnings("ignore", category=UserWarning, module="curl_cffi")
import os
import dotenv
import psutil # For system stats
import asyncio
from asyncio import WindowsSelectorEventLoopPolicy
import datetime
import logging
from pathlib import Path
# import random  # Not used directly
import time # For uptime calculation
import aiosqlite # For potential DB init later if needed centrally
# import json  # Not used directly
import sys

# --- Constants ---
# Define file paths using pathlib for better OS compatibility
BASE_DIR = Path(__file__).parent
COGS_DIR = BASE_DIR / "cogs"
FILES_DIR = BASE_DIR # Assuming .txt files are in the base directory
CONFIG_PATH = BASE_DIR / "config.json"

# Add utils directory to path
sys.path.append(str(BASE_DIR))

# Import config manager
from utils.config_manager import config

# Load environment variables from .env file
dotenv.load_dotenv()

# Get environment variables with fallbacks from config
BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
OWNER_ID = int(os.getenv("BOT_OWNER_ID", "0")) # Ensure owner ID is an integer
REVIEW_CHANNEL_ID = int(os.getenv("REVIEW_CHANNEL_ID", "0"))
WEBSITE_URL = os.getenv("WEBSITE_URL", config.get("bot.website_url", "https://example.com"))
BUSINESS_EMAIL = os.getenv("BUSINESS_EMAIL", config.get("bot.business_email", ""))

# Add owner to config if not already there
if OWNER_ID != 0 and not config.is_owner(OWNER_ID):
    config.add_owner(OWNER_ID)
    config.save_config()

# --- Logging Setup ---
# Get logging configuration from config
logging_config = config.get_logging_config()
log_level = getattr(logging, logging_config.get("level", "INFO"))
log_format = logging_config.get("format", '%(asctime)s [%(levelname)s] %(name)s: %(message)s')

# Configure logging
log_formatter = logging.Formatter(log_format)

# Create logs directory if it doesn't exist
logs_dir = BASE_DIR / "logs"
logs_dir.mkdir(exist_ok=True)

# Add file handler if enabled
if logging_config.get("file_logging", True):
    log_file = logs_dir / "bishop.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(log_formatter)
    file_handler.setLevel(log_level)

# Add console handler if enabled
if logging_config.get("console_logging", True):
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    console_handler.setLevel(log_level)

# Configure discord.py logger
logger = logging.getLogger('discord')
logger.setLevel(log_level)
if logging_config.get("file_logging", True):
    logger.addHandler(file_handler)
if logging_config.get("console_logging", True):
    logger.addHandler(console_handler)

# Configure bot logger
bot_logger = logging.getLogger('MyBot')
bot_logger.setLevel(log_level)
if logging_config.get("file_logging", True):
    bot_logger.addHandler(file_handler)
if logging_config.get("console_logging", True):
    bot_logger.addHandler(console_handler)

# Configure error logger (separate file for errors even if bot continues running)
error_logger = logging.getLogger('MyBot.Errors')
error_logger.setLevel(logging.ERROR)

# Create error log file handler
error_log_file = logs_dir / "errors.log"
error_file_handler = logging.FileHandler(error_log_file)
error_file_handler.setFormatter(log_formatter)
error_file_handler.setLevel(logging.ERROR)
error_logger.addHandler(error_file_handler)

# Add console handler for errors if enabled
if logging_config.get("console_logging", True):
    error_logger.addHandler(console_handler)

# --- Bot Initialization ---
# Get intents configuration from config
intents_config = config.get("advanced.intents", {
    "message_content": True,
    "members": True,
    "presences": False,
    "guild_messages": True,
    "dm_messages": True,
    "reactions": True
})

# Define necessary intents
intents = discord.Intents.default()
intents.message_content = intents_config.get("message_content", True)
intents.members = intents_config.get("members", True)
intents.presences = intents_config.get("presences", False)
intents.members = True # Needed for user info, server info on review

# Keep track of the bot's startup time for uptime calculation
bot_start_time = time.time()

# Keep track of the last message sent by the bot for mention interactions
# Dictionary format: {channel_id: message_id}
last_mention_response = {}

class MyBot(commands.Bot):
    def __init__(self):
        # Disable voice support to avoid PyNaCl warning
        super().__init__(command_prefix="!", intents=intents, voice_client_class=None) # Prefix is fallback, main interaction is slash commands

    async def setup_hook(self):
        """Runs when the bot first connects. Loads cogs."""
        bot_logger.info("Starting setup hook...")
        # Create necessary directories if they don't exist
        required_dirs = [
            BASE_DIR / "temp",
            BASE_DIR / "saves",
            BASE_DIR / "market"
        ]
        for dir_path in required_dirs:
            dir_path.mkdir(exist_ok=True)
            # Create .gitkeep if directory is empty (useful for git)
            if not any(dir_path.iterdir()):
                (dir_path / ".gitkeep").touch()
                bot_logger.info(f"Created directory and .gitkeep: {dir_path}")

        # --- Database Initialization ---
        db_path = BASE_DIR / "market.db"
        async with aiosqlite.connect(db_path) as db:
            # Create market table if it doesn't exist
            await db.execute('''
                CREATE TABLE IF NOT EXISTS market_listings (
                    uid TEXT PRIMARY KEY,
                    owner_id INTEGER NOT NULL,
                    file_name TEXT NOT NULL,
                    description TEXT,
                    date_listed REAL NOT NULL,
                    saves_count INTEGER DEFAULT 0 NOT NULL,
                    stars_count INTEGER DEFAULT 0 NOT NULL
                )
            ''')
            # Create user saved market items table
            # Stores which users saved which market items
            await db.execute('''
                CREATE TABLE IF NOT EXISTS user_market_saves (
                    user_id INTEGER NOT NULL,
                    uid TEXT NOT NULL,
                    date_saved REAL NOT NULL,
                    PRIMARY KEY (user_id, uid),
                    FOREIGN KEY (uid) REFERENCES market_listings(uid) ON DELETE CASCADE
                )
            ''')
            # Create user awards table (to prevent multiple stars from same user)
            await db.execute('''
                 CREATE TABLE IF NOT EXISTS user_market_awards (
                    user_id INTEGER NOT NULL,
                    uid TEXT NOT NULL,
                    PRIMARY KEY (user_id, uid),
                    FOREIGN KEY (uid) REFERENCES market_listings(uid) ON DELETE CASCADE
                 )
            ''')
            await db.commit()
            bot_logger.info(f"Database '{db_path}' initialized and tables ensured.")


        # --- Load Cogs --- [cite: 16]
        bot_logger.info(f"Looking for cogs in: {COGS_DIR}")
        loaded_cogs = []
        failed_cogs = []
        for filename in os.listdir(COGS_DIR):
            # Ensure it's a python file and not __init__.py or other support files
            if filename.endswith(".py") and filename != "__init__.py":
                cog_name = f"cogs.{filename[:-3]}"
                try:
                    await self.load_extension(cog_name)
                    loaded_cogs.append(cog_name)
                    bot_logger.info(f"Successfully loaded cog: {cog_name}")
                except Exception as e:
                    failed_cogs.append(cog_name)
                    bot_logger.error(f"Failed to load cog {cog_name}: {e}", exc_info=True)
        bot_logger.info(f"Cog loading complete. Loaded: {len(loaded_cogs)}, Failed: {len(failed_cogs)}")
        if failed_cogs:
            bot_logger.warning(f"Failed cogs: {', '.join(failed_cogs)}")

        # Sync slash commands (globally - might take an hour for Discord to update)
        # For faster testing, sync to a specific guild:
        # await self.tree.sync(guild=discord.Object(id=YOUR_TEST_SERVER_ID))
        try:
            synced = await self.tree.sync()
            bot_logger.info(f"Synced {len(synced)} slash commands globally.")
        except Exception as e:
            bot_logger.error(f"Failed to sync slash commands: {e}")

    async def on_ready(self):
        """Event triggered when the bot is ready and logged in."""
        bot_logger.info(f'Logged in as {self.user.name} (ID: {self.user.id})')
        bot_logger.info(f'Discord.py version: {discord.__version__}')
        bot_logger.info('Bot is ready and online!')
        await self.change_presence(activity=discord.Game(name="with APIs")) # Set a status

    async def read_file_content(self, filename: str, directory: Path = FILES_DIR) -> str | None:
        """Helper to read text files asynchronously."""
        filepath = directory / filename
        try:
            # Define a function to read the file in a thread
            def read_file():
                return filepath.read_text(encoding='utf-8')

            # Use asyncio's thread to avoid blocking the event loop for file I/O
            content = await asyncio.to_thread(read_file)
            return content
        except FileNotFoundError:
            bot_logger.error(f"File not found: {filepath}")
            return f":warning: Error: `{filename}` not found. Please inform the bot owner."
        except Exception as e:
            bot_logger.error(f"Error reading file {filepath}: {e}")
            return f":x: Error reading `{filename}`."

# Instantiate the bot
bot = MyBot()

# --- Helper Functions & Checks ---

def is_owner():
    """Check if the command user is the bot owner."""
    async def predicate(interaction: discord.Interaction) -> bool:
        if interaction.user.id == OWNER_ID:
            return True
        await interaction.response.send_message("Sorry, this command can only be used by the bot owner.", ephemeral=True)
        return False
    return app_commands.check(predicate)

async def get_system_stats() -> str:
    """Retrieves formatted system statistics."""
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_used_gb = memory.used / (1024**3)
        memory_total_gb = memory.total / (1024**3)

        current_time = time.time()
        uptime_seconds = int(current_time - bot_start_time)
        uptime_str = str(datetime.timedelta(seconds=uptime_seconds)) # Format timedelta nicely

        stats = (
            f"**System Status**\n"
            f"```\n"
            f"CPU Usage : {cpu_percent}%\n"
            f"RAM Usage : {memory_percent}% ({memory_used_gb:.2f} GB / {memory_total_gb:.2f} GB)\n"
            f"Bot Uptime: {uptime_str}\n"
            f"```"
        )
        return stats
    except Exception as e:
        bot_logger.error(f"Error getting system stats: {e}")
        return ":warning: Could not retrieve system statistics."

# --- Cog Management Command Group --- [cite: 17]

cog_group = app_commands.Group(name="cog", description="Manage bot cogs (Owner Only)")
bot.tree.add_command(cog_group)

async def cog_autocomplete(
    interaction: discord.Interaction,
    current: str,
) -> list[app_commands.Choice[str]]:
    """Autocompletes available cog names."""
    choices = []
    for filename in os.listdir(COGS_DIR):
         if filename.endswith(".py") and filename != "__init__.py":
            cog_name = f"cogs.{filename[:-3]}"
            if current.lower() in cog_name.lower():
                 choices.append(app_commands.Choice(name=filename[:-3], value=cog_name))
    return choices[:25] # Discord limits choices to 25

@cog_group.command(name="load", description="Loads a specific cog (Owner Only)")
@is_owner()
@app_commands.autocomplete(cog_name=cog_autocomplete)
@app_commands.describe(cog_name="The name of the cog to load (e.g., cogs.spectre)")
async def cog_load(interaction: discord.Interaction, cog_name: str):
    """Loads a specified cog."""
    await interaction.response.defer(ephemeral=True)

    try:
        await bot.load_extension(cog_name)
        await interaction.followup.send(f":white_check_mark: Successfully loaded cog: `{cog_name}`")
        bot_logger.info(f"Cog loaded via command by {interaction.user}: {cog_name}")
    except commands.ExtensionAlreadyLoaded:
        await interaction.followup.send(f":warning: Cog `{cog_name}` is already loaded.")
    except commands.ExtensionNotFound:
        await interaction.followup.send(f":x: Cog `{cog_name}` not found.")
    except Exception as e:
        await interaction.followup.send(f":x: Failed to load cog `{cog_name}`.\n```py\n{e}\n```")
        bot_logger.error(f"Error loading cog {cog_name}: {e}", exc_info=True)

@cog_group.command(name="unload", description="Unloads a specific cog (Owner Only)")
@is_owner()
@app_commands.autocomplete(cog_name=cog_autocomplete)
@app_commands.describe(cog_name="The name of the cog to unload (e.g., cogs.spectre)")
async def cog_unload(interaction: discord.Interaction, cog_name: str):
    """Unloads a specified cog."""
    await interaction.response.defer(ephemeral=True)
    # Prevent unloading core components if needed (add checks here)
    if cog_name == "main": # Example: prevent unloading main logic if it were a cog
         await interaction.followup.send(":warning: Cannot unload core components.")
         return
    try:
        await bot.unload_extension(cog_name)
        await interaction.followup.send(f":white_check_mark: Successfully unloaded cog: `{cog_name}`")
        bot_logger.info(f"Cog unloaded via command by {interaction.user}: {cog_name}")
    except commands.ExtensionNotLoaded:
        await interaction.followup.send(f":warning: Cog `{cog_name}` is not currently loaded.")
    except commands.ExtensionNotFound:
         await interaction.followup.send(f":x: Cog `{cog_name}` not found.")
    except Exception as e:
        await interaction.followup.send(f":x: Failed to unload cog `{cog_name}`.\n```py\n{e}\n```")
        bot_logger.error(f"Error unloading cog {cog_name}: {e}", exc_info=True)

@cog_group.command(name="reload", description="Reloads a specific cog or all cogs (Owner Only)")
@is_owner()
@app_commands.autocomplete(cog_name=cog_autocomplete)
@app_commands.describe(cog_name="The cog name to reload, or type 'all' to reload all cogs")
async def cog_reload(interaction: discord.Interaction, cog_name: str):
    """Reloads specified cog(s)."""
    await interaction.response.defer(ephemeral=True)
    if cog_name.lower() == "all":
        # Reload all cogs found in the cogs directory
        reloaded_cogs = []
        failed_cogs = []
        bot_logger.info(f"Attempting to reload all cogs by {interaction.user}...")
        for filename in os.listdir(COGS_DIR):
            if filename.endswith(".py") and filename != "__init__.py":
                full_cog_name = f"cogs.{filename[:-3]}"
                try:
                    await bot.reload_extension(full_cog_name)
                    reloaded_cogs.append(full_cog_name)
                except Exception as e:
                    failed_cogs.append(full_cog_name)
                    bot_logger.error(f"Failed to reload cog {full_cog_name}: {e}", exc_info=True)

        msg = f"**Reload All Cogs Report:**\n"
        if reloaded_cogs:
            msg += f":white_check_mark: Reloaded successfully ({len(reloaded_cogs)}):\n```\n" + '\n'.join(reloaded_cogs) + "\n```\n"
        if failed_cogs:
             msg += f":x: Failed to reload ({len(failed_cogs)}):\n```\n" + '\n'.join(failed_cogs) + "\n```\n"
        await interaction.followup.send(msg)
        bot_logger.info(f"Reload all cogs finished. Success: {len(reloaded_cogs)}, Failed: {len(failed_cogs)}")

    else:
        # Reload a specific cog
        try:
            await bot.reload_extension(cog_name)
            await interaction.followup.send(f":white_check_mark: Successfully reloaded cog: `{cog_name}`")
            bot_logger.info(f"Cog reloaded via command by {interaction.user}: {cog_name}")
        except commands.ExtensionNotLoaded:
            await interaction.followup.send(f":warning: Cog `{cog_name}` was not loaded, attempting to load it instead...")
            try:
                await bot.load_extension(cog_name)
                await interaction.followup.send(f":white_check_mark: Successfully loaded cog: `{cog_name}`")
            except Exception as e:
                 await interaction.followup.send(f":x: Failed to load cog `{cog_name}` after reload attempt.\n```py\n{e}\n```")
        except commands.ExtensionNotFound:
             await interaction.followup.send(f":x: Cog `{cog_name}` not found.")
        except Exception as e:
            await interaction.followup.send(f":x: Failed to reload cog `{cog_name}`.\n```py\n{e}\n```")
            bot_logger.error(f"Error reloading cog {cog_name}: {e}", exc_info=True)


@cog_group.command(name="list", description="Lists all currently loaded cogs (Owner Only)")
@is_owner()
async def cog_list(interaction: discord.Interaction):
    """Lists loaded cogs."""
    loaded_extensions = bot.extensions
    if not loaded_extensions:
        await interaction.response.send_message("No cogs are currently loaded.", ephemeral=True)
        return

    embed = discord.Embed(title="Loaded Cogs", color=discord.Color.blue())
    embed.description = "```\n" + "\n".join(loaded_extensions.keys()) + "\n```"
    await interaction.response.send_message(embed=embed, ephemeral=True)

# --- Mention Response Logic --- [cite: 20]

class ReviewModal(discord.ui.Modal, title='Submit a Review'): # [cite: 25]
    review_text = discord.ui.TextInput(
        label='Your Review',
        style=discord.TextStyle.paragraph,
        placeholder='Please write your review here...',
        required=True,
        max_length=1000,
    )

    async def on_submit(self, interaction: discord.Interaction):
        """Handles submission of the review modal."""
        await interaction.response.defer(ephemeral=True, thinking=True) # Acknowledge interaction

        review_channel_id = REVIEW_CHANNEL_ID
        if not review_channel_id:
            await interaction.followup.send(":x: Review channel ID is not configured. Please contact the bot owner.", ephemeral=True)
            return

        review_channel = interaction.client.get_channel(review_channel_id)
        if not review_channel or not isinstance(review_channel, discord.TextChannel):
            await interaction.followup.send(f":x: Could not find the configured review channel (ID: {review_channel_id}). Please contact the bot owner.", ephemeral=True)
            return

        # --- Generate Invite Link --- [cite: 26]
        invite_link = "N/A"
        if interaction.guild and interaction.channel and isinstance(interaction.channel, discord.TextChannel):
            # Check bot permissions to create invites in the current channel
            perms = interaction.channel.permissions_for(interaction.guild.me)
            if perms.create_instant_invite:
                try:
                    # Create a never-expiring invite to the current channel
                    invite = await interaction.channel.create_invite(max_age=0, max_uses=0, temporary=False, unique=True, reason="Review submission")
                    invite_link = invite.url
                except discord.HTTPException as e:
                    bot_logger.warning(f"Failed to create invite for review in {interaction.guild.name} ({interaction.guild.id}): {e}")
                    invite_link = "Failed to create"
                except Exception as e:
                     bot_logger.error(f"Unexpected error creating invite: {e}", exc_info=True)
                     invite_link = "Error"
            else:
                invite_link = "Bot lacks permission"

        # --- Prepare Embed --- [cite: 26]
        embed = discord.Embed(
            title="New Review Submitted!",
            description=self.review_text.value,
            color=discord.Color.gold()
        )
        embed.set_author(name=f"{interaction.user.name} ({interaction.user.id})", icon_url=interaction.user.display_avatar.url)
        if interaction.guild:
            embed.add_field(name="Server", value=f"{interaction.guild.name} ({interaction.guild.id})", inline=False)
        if invite_link != "N/A":
             embed.add_field(name="Server Invite", value=invite_link, inline=False)
        embed.set_footer(text="Review submitted")
        embed.timestamp = discord.utils.utcnow()

        # --- Send to Review Channel ---
        try:
            await review_channel.send(embed=embed)
            await interaction.followup.send(":white_check_mark: Thank you! Your review has been submitted.", ephemeral=True)
            bot_logger.info(f"Review submitted by {interaction.user} from server {interaction.guild.name if interaction.guild else 'DM'}")
        except discord.Forbidden:
            await interaction.followup.send(":x: The bot doesn't have permission to send messages in the review channel. Please contact the bot owner.", ephemeral=True)
            bot_logger.error(f"Permission error sending review to channel {review_channel_id}")
        except Exception as e:
            await interaction.followup.send(":x: An error occurred while submitting your review. Please try again later.", ephemeral=True)
            bot_logger.error(f"Failed to send review to channel {review_channel_id}: {e}", exc_info=True)

    async def on_error(self, interaction: discord.Interaction, error: Exception):
        bot_logger.error(f"Error in ReviewModal: {error}", exc_info=True)
        if not interaction.response.is_done():
             await interaction.response.send_message(":x: An unexpected error occurred with the review form.", ephemeral=True)
        else:
            await interaction.followup.send(":x: An unexpected error occurred processing the review form.", ephemeral=True)


class MentionResponseView(discord.ui.View):
    def __init__(self, bot_instance: MyBot, timeout=180.0):
        super().__init__(timeout=timeout)
        self.bot_instance = bot_instance
        self.original_interaction_message = None # Store the message this view is attached to

        # Add the website button
        website_button = discord.ui.Button(label="Website", style=discord.ButtonStyle.link, url=WEBSITE_URL, emoji="🌐")
        self.add_item(website_button)

    async def handle_interaction(self, interaction: discord.Interaction, content: str):
        """Helper to send or edit the response, managing previous messages."""
        await interaction.response.defer(ephemeral=True) # Acknowledge the button click privately
        # Edit the original message if possible, otherwise send new [cite: 11]
        if self.original_interaction_message:
            try:
                await self.original_interaction_message.edit(content=content, view=self) # Keep the view active
                await interaction.followup.send("Updated information below.", ephemeral=True)
            except discord.NotFound:
                 # Original message deleted, send new one (ephemeral for button click ack won't interfere)
                 self.original_interaction_message = await interaction.channel.send(content=content, view=self)
                 await interaction.followup.send("Displayed information below.", ephemeral=True)
            except discord.HTTPException as e:
                 bot_logger.error(f"Failed to edit mention response message: {e}")
                 # Fallback to sending new if editing fails
                 self.original_interaction_message = await interaction.channel.send(content=content, view=self)
                 await interaction.followup.send("Could not update the previous message, showing information below.", ephemeral=True)
        else:
            # This case should ideally not happen if original_interaction_message is set correctly
            self.original_interaction_message = await interaction.channel.send(content=content, view=self)
            await interaction.followup.send("Displayed information below.", ephemeral=True)


    @discord.ui.button(label="System", style=discord.ButtonStyle.secondary, emoji="⚙️") # [cite: 21]
    async def system_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        stats_content = await get_system_stats()
        await self.handle_interaction(interaction, stats_content)

    @discord.ui.button(label="Credits", style=discord.ButtonStyle.secondary, emoji="📜") # [cite: 22]
    async def credits_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        credits_content = await self.bot_instance.read_file_content("credits.txt")
        await self.handle_interaction(interaction, credits_content)

    # Website button is added in __init__

    @discord.ui.button(label="About", style=discord.ButtonStyle.secondary, emoji="ℹ️") # [cite: 23]
    async def about_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        about_content = await self.bot_instance.read_file_content("about.txt")
        await self.handle_interaction(interaction, about_content)

    @discord.ui.button(label="Contact / Review", style=discord.ButtonStyle.primary, emoji="📧") # [cite: 23]
    async def contact_review_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Show a secondary view for Business/Review options
        view = ContactReviewChoiceView(timeout=60.0)
        await interaction.response.send_message("How would you like to proceed?", view=view, ephemeral=True)
        # We don't edit the main message here, just provide options


class ContactReviewChoiceView(discord.ui.View):
     def __init__(self, timeout=60.0):
        super().__init__(timeout=timeout)

     @discord.ui.button(label="Business Inquiry", style=discord.ButtonStyle.green, emoji="💼") # [cite: 24]
     async def business_button(self, interaction: discord.Interaction, button: discord.ui.Button):
         if BUSINESS_EMAIL:
             await interaction.response.send_message(f"For business inquiries, please contact: `{BUSINESS_EMAIL}`", ephemeral=True)
         else:
             await interaction.response.send_message("Business contact information is not configured.", ephemeral=True)
         # Stop the view after selection
         self.stop()


     @discord.ui.button(label="Leave a Review", style=discord.ButtonStyle.blurple, emoji="⭐") # [cite: 25]
     async def review_button(self, interaction: discord.Interaction, button: discord.ui.Button):
         # Open the review modal
         modal = ReviewModal()
         await interaction.response.send_modal(modal)
         # Stop the view after opening modal
         self.stop()

     async def on_timeout(self):
        # Optionally disable buttons on timeout
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                item.disabled = True
        # Need a message reference to edit, which we don't have here as it's ephemeral
        # await interaction.edit_original_response(view=self) # This won't work easily


@bot.event
async def on_message(message: discord.Message):
    """Event triggered when a message is sent in a channel the bot can see."""
    # Ignore messages sent by the bot itself to prevent loops
    if message.author == bot.user:
        return

    # Process commands first (if you have any legacy prefix commands)
    # await bot.process_commands(message) # Disabled if only using slash commands

    # Check if the bot was mentioned [cite: 20]
    if bot.user and bot.user.mentioned_in(message):
        bot_logger.info(f"Bot mentioned by {message.author} in {message.channel}")

        # --- Message Management --- [cite: 11]
        # Delete the previous response in this channel if one exists
        if message.channel.id in last_mention_response:
             try:
                 old_msg = await message.channel.fetch_message(last_mention_response[message.channel.id])
                 await old_msg.delete()
                 bot_logger.debug(f"Deleted previous mention response in channel {message.channel.id}")
             except discord.NotFound:
                 bot_logger.debug(f"Previous mention response message not found in channel {message.channel.id}.")
             except discord.Forbidden:
                 bot_logger.warning(f"Missing permissions to delete mention response in channel {message.channel.id}")
             except Exception as e:
                 bot_logger.error(f"Error deleting previous mention response msg: {e}", exc_info=True)
             # Remove from tracking even if deletion failed
             del last_mention_response[message.channel.id]

        # --- Send New Response ---
        # Read the base content from bot.txt
        mention_content = await bot.read_file_content("bot.txt")

        # Create the view with buttons
        view = MentionResponseView(bot_instance=bot, timeout=300.0) # Longer timeout for main view

        # Send the message and store its ID
        try:
            response_message = await message.channel.send(content=mention_content, view=view)
            last_mention_response[message.channel.id] = response_message.id
            view.original_interaction_message = response_message # Link the view to the message it's attached to
        except discord.Forbidden:
            bot_logger.error(f"Missing permissions to send mention response in channel {message.channel.id}")
            # Try sending to user DMs as a fallback? (Optional)
        except Exception as e:
             bot_logger.error(f"Error sending mention response: {e}", exc_info=True)

# --- Global Error Handler (Optional but Recommended) ---
# @bot.listen()
# async def on_command_error(ctx, error):
#     if isinstance(error, commands.CommandNotFound):
#         return # Ignore not found errors for prefix commands if only using slash
#     elif isinstance(error, commands.CheckFailure):
#         await ctx.send("You don't have permission to use this command.")
#     # Add more specific error handling as needed
#     else:
#         bot_logger.error(f"Unhandled command error: {error}", exc_info=True)
#         await ctx.send("An unexpected error occurred.")

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    """Global error handler for slash commands."""
    if isinstance(error, app_commands.CheckFailure):
         await interaction.response.send_message("You don't have the necessary permissions or conditions met to use this command.", ephemeral=True)
    elif isinstance(error, app_commands.CommandOnCooldown):
        await interaction.response.send_message(f"This command is on cooldown. Please try again in {error.retry_after:.2f} seconds.", ephemeral=True)
    # Add specific handling for your custom exceptions raised in cogs if needed
    # elif isinstance(error, MyCustomCogError):
    #    await interaction.response.send_message(f"Error: {error}", ephemeral=True)
    else:
        # Generic error message for unhandled exceptions
        bot_logger.error(f"Unhandled error in slash command '{interaction.command.name if interaction.command else 'N/A'}': {error}", exc_info=True)
        # Also log to the dedicated error log file
        error_logger.error(f"Unhandled error in slash command '{interaction.command.name if interaction.command else 'N/A'}': {error}", exc_info=True)
        error_message = ":x: An unexpected error occurred while executing this command. The developers have been notified."
        if interaction.response.is_done():
            await interaction.followup.send(error_message, ephemeral=True)
        else:
             # Use defer() then followup() if response hasn't been sent
            try:
                await interaction.response.defer(ephemeral=True)
                await interaction.followup.send(error_message)
            except discord.InteractionResponded:
                 # If somehow it got responded to between check and defer
                 await interaction.followup.send(error_message, ephemeral=True)
            except Exception as e:
                bot_logger.error(f"Further error trying to respond to interaction error: {e}")


# --- Global Exception Handler ---
def global_exception_handler(exctype, value, traceback):
    """Global exception handler to log unhandled exceptions."""
    # Log to both regular and error log
    error_logger.critical(f"Unhandled exception: {value}", exc_info=(exctype, value, traceback))
    # Also print to console in case logging fails
    print(f"CRITICAL ERROR: {value}")
    # Call the original exception handler
    sys.__excepthook__(exctype, value, traceback)

# Set the global exception handler
sys.excepthook = global_exception_handler

# --- Run the Bot ---
if __name__ == "__main__":
    # Set the event loop policy to WindowsSelectorEventLoopPolicy to avoid warnings with curl_cffi
    if sys.platform.startswith('win'):
        asyncio.set_event_loop_policy(WindowsSelectorEventLoopPolicy())
        bot_logger.info("Set event loop policy to WindowsSelectorEventLoopPolicy for Windows compatibility")

    if BOT_TOKEN is None:
        bot_logger.critical("FATAL ERROR: DISCORD_BOT_TOKEN environment variable not set.")
        error_logger.critical("FATAL ERROR: DISCORD_BOT_TOKEN environment variable not set.")
    else:
        try:
            bot.run(BOT_TOKEN, log_handler=None) # Use the logger configured above
        except discord.LoginFailure:
            bot_logger.critical("FATAL ERROR: Invalid Discord Token. Please check your .env file.")
            error_logger.critical("FATAL ERROR: Invalid Discord Token. Please check your .env file.")
        except Exception as e:
            bot_logger.critical(f"Bot crashed: {e}", exc_info=True)
            error_logger.critical(f"Bot crashed: {e}", exc_info=True)
            print(f"CRITICAL ERROR: Bot crashed: {e}")
            # Exit with error code
            sys.exit(1)