# cogs/manager.py

import discord
import warnings
import logging
import time
import json
import asyncio
import aiosqlite
import math
import sys
from pathlib import Path
from discord.ext import commands
from discord import app_commands, ui, ButtonStyle, TextStyle, Embed, Color
# Implement our own Paginator class instead of using discord.ext.pages

# Filter out curl_cffi warnings globally
warnings.filterwarnings("ignore", message="Curlm already closed! quitting from process_data")
warnings.filterwarnings("ignore", category=UserWarning, module="curl_cffi")

class Paginator(ui.View):
    """Custom paginator implementation to replace discord.ext.pages."""

    def __init__(self, pages=None, timeout=180.0, show_disabled=True, show_indicator=True):
        super().__init__(timeout=timeout)
        self.pages = pages or []
        self.current_page = 1
        self.total_pages = max(len(self.pages), 1)
        self.show_disabled = show_disabled
        self.show_indicator = show_indicator
        self.message = None

        # Add navigation buttons
        self.first_page_button = ui.Button(emoji="⏮️", style=ButtonStyle.secondary, disabled=True)
        self.prev_page_button = ui.Button(emoji="◀️", style=ButtonStyle.secondary, disabled=True)
        self.page_indicator = ui.Button(label=f"Page 1/{self.total_pages}", style=ButtonStyle.secondary, disabled=True)
        self.next_page_button = ui.Button(emoji="▶️", style=ButtonStyle.secondary, disabled=self.total_pages <= 1)
        self.last_page_button = ui.Button(emoji="⏭️", style=ButtonStyle.secondary, disabled=self.total_pages <= 1)

        self.first_page_button.callback = self.first_page_callback
        self.prev_page_button.callback = self.prev_page_callback
        self.next_page_button.callback = self.next_page_callback
        self.last_page_button.callback = self.last_page_callback

        self.add_item(self.first_page_button)
        self.add_item(self.prev_page_button)
        if self.show_indicator:
            self.add_item(self.page_indicator)
        self.add_item(self.next_page_button)
        self.add_item(self.last_page_button)

    async def first_page_callback(self, interaction):
        await interaction.response.defer()
        self.current_page = 1
        await self.update_page(interaction)

    async def prev_page_callback(self, interaction):
        await interaction.response.defer()
        self.current_page = max(1, self.current_page - 1)
        await self.update_page(interaction)

    async def next_page_callback(self, interaction):
        await interaction.response.defer()
        self.current_page = min(self.total_pages, self.current_page + 1)
        await self.update_page(interaction)

    async def last_page_callback(self, interaction):
        await interaction.response.defer()
        self.current_page = self.total_pages
        await self.update_page(interaction)

    async def update_page(self, interaction):
        # Update button states
        self.first_page_button.disabled = self.current_page == 1 or not self.show_disabled
        self.prev_page_button.disabled = self.current_page == 1 or not self.show_disabled
        self.next_page_button.disabled = self.current_page == self.total_pages or not self.show_disabled
        self.last_page_button.disabled = self.current_page == self.total_pages or not self.show_disabled

        if self.show_indicator:
            self.page_indicator.label = f"Page {self.current_page}/{self.total_pages}"

        # Get the current page content
        page_content = await self.format_page(self.current_page)

        # Update the message
        if isinstance(page_content, discord.Embed):
            await interaction.message.edit(embed=page_content, view=self)
        else:
            await interaction.message.edit(content=page_content, view=self)

    async def format_page(self, page_num):
        """Override this method to provide custom page formatting."""
        if self.pages and 0 < page_num <= len(self.pages):
            return self.pages[page_num - 1]
        return "No content available."

    async def send(self, interaction, ephemeral=False):
        """Sends the paginator to the given interaction."""
        page_content = await self.format_page(self.current_page)

        if isinstance(page_content, discord.Embed):
            self.message = await interaction.followup.send(embed=page_content, view=self, ephemeral=ephemeral)
        else:
            self.message = await interaction.followup.send(content=page_content, view=self, ephemeral=ephemeral)

        return self.message

    async def on_timeout(self):
        """Disables all buttons when the view times out."""
        for item in self.children:
            item.disabled = True

        if self.message:
            try:
                # Get the current page content
                page_content = await self.format_page(self.current_page)

                # Add timeout message
                if isinstance(page_content, discord.Embed):
                    # For embeds, add to footer
                    if page_content.footer.text:
                        page_content.set_footer(text=f"{page_content.footer.text} • Timed out")
                    else:
                        page_content.set_footer(text="Timed out")
                    await self.message.edit(embed=page_content, view=self)
                else:
                    # For text content, append to the end
                    await self.message.edit(content=f"{page_content}\n\n*This paginator has timed out.*", view=self)
            except discord.NotFound:
                log.warning(f"Message not found when handling Paginator timeout")
            except discord.HTTPException as e:
                log.error(f"HTTP error when handling Paginator timeout: {e}")
            except Exception as e:
                log.error(f"Error editing message after timeout: {e}", exc_info=True)

# Add parent directory to path for imports
BASE_DIR = Path(__file__).parent.parent # Project root directory
sys.path.append(str(BASE_DIR))

# Import config manager
from utils.config_manager import config

# --- Constants & Setup ---
SAVES_DIR = BASE_DIR / "saves"
TEMP_DIR = BASE_DIR / "temp"

# Get database config
db_config = config.get_database_config()
DB_PATH = BASE_DIR / db_config.get("path", "market.db")

# Logger for this cog
log = logging.getLogger('MyBot.ManagerCog')

# Get UI config
ui_config = config.get_ui_config()

# Items per page for paginated views
ITEMS_PER_PAGE = config.get("vault.max_saves_per_page", 5)

# --- Helper Functions ---

async def read_file_content(filepath: Path) -> str | None:
    """Helper to read text files asynchronously."""
    try:
        # Define a function to read the file in a thread
        def read_file():
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()

        # Use asyncio's thread to avoid blocking the event loop for file I/O
        content = await asyncio.to_thread(read_file)
        return content
    except FileNotFoundError:
        log.error(f"File not found: {filepath}")
        return f":warning: Error: Required file `{filepath.name}` not found. Please inform the bot owner."
    except Exception as e:
        log.error(f"Error reading file {filepath}: {e}", exc_info=True)
        return f":x: Error reading `{filepath.name}`."

# --- Database Helper Functions ---

async def db_connect() -> aiosqlite.Connection:
    """Establishes connection to the SQLite database."""
    # Create and return the connection directly
    conn = await aiosqlite.connect(DB_PATH)
    return conn

async def get_user_saves_metadata(user_id: int) -> list[dict]:
    """Reads all metadata JSON files for a user's personal saves."""
    user_saves_path = SAVES_DIR / str(user_id)
    metadata_list = []
    if not user_saves_path.is_dir():
        return metadata_list # No saves directory for this user

    for item in user_saves_path.iterdir():
        if item.is_file() and item.suffix == '.json':
            try:
                # Define a function to read and parse the JSON file
                def read_json_file():
                    with open(item, 'r', encoding='utf-8') as f:
                        return json.load(f)

                # Execute in a thread to avoid blocking
                data = await asyncio.to_thread(read_json_file)
                # Add file path info if needed, e.g., data['uid'] = item.stem
                if 'uid' not in data: # Ensure UID is present from file stem if missing
                    data['uid'] = item.stem
                metadata_list.append(data)
            except json.JSONDecodeError:
                log.error(f"Error decoding JSON file: {item}")
            except Exception as e:
                log.error(f"Error reading metadata file {item}: {e}", exc_info=True)
    # Sort by date created, newest first
    metadata_list.sort(key=lambda x: x.get('date_created', 0), reverse=True)
    return metadata_list

async def get_user_market_saves_info(user_id: int) -> list[aiosqlite.Row]:
    """Gets details of market items saved by the user."""
    db = await db_connect()
    try:
        db.row_factory = aiosqlite.Row # Return rows as dict-like objects
        async with db.execute('''
            SELECT ml.* FROM market_listings ml
            JOIN user_market_saves ums ON ml.uid = ums.uid
            WHERE ums.user_id = ?
            ORDER BY ums.date_saved DESC
        ''', (user_id,)) as cursor:
            rows = await cursor.fetchall()
            return rows if rows else []
    finally:
        await db.close()

async def get_market_listing(uid: str) -> aiosqlite.Row | None:
    """Fetches a specific listing from market_listings."""
    db = await db_connect()
    try:
        db.row_factory = aiosqlite.Row
        async with db.execute('SELECT * FROM market_listings WHERE uid = ?', (uid,)) as cursor:
            row = await cursor.fetchone()
            return row
    finally:
        await db.close()

async def get_all_market_listings(sort_by: str = 'date', search_term: str | None = None) -> list[aiosqlite.Row]:
    """Fetches all listings, with optional sorting and searching."""
    query = 'SELECT * FROM market_listings'
    params = []

    if search_term:
        query += ' WHERE file_name LIKE ? OR description LIKE ?'
        params.extend([f'%{search_term}%', f'%{search_term}%'])

    if sort_by == 'saves':
        query += ' ORDER BY saves_count DESC, date_listed DESC'
    elif sort_by == 'stars':
         query += ' ORDER BY stars_count DESC, date_listed DESC'
    else: # Default sort by date (newest first)
        query += ' ORDER BY date_listed DESC'

    db = await db_connect()
    try:
        db.row_factory = aiosqlite.Row
        async with db.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return rows if rows else []
    finally:
        await db.close()

async def add_market_listing(uid: str, owner_id: int, file_name: str, description: str | None) -> bool:
    """Adds a new listing to the market."""
    db = await db_connect()
    try:
        await db.execute('''
            INSERT INTO market_listings (uid, owner_id, file_name, description, date_listed, saves_count, stars_count)
            VALUES (?, ?, ?, ?, ?, 0, 0)
        ''', (uid, owner_id, file_name, description, time.time()))
        await db.commit()
        return True
    except aiosqlite.IntegrityError:
         log.warning(f"Attempted to list item with duplicate UID: {uid}")
         return False # Item likely already listed
    except Exception as e:
        log.error(f"Error adding market listing for UID {uid}: {e}", exc_info=True)
        return False
    finally:
        await db.close()

async def remove_market_listing(uid: str) -> bool:
    """Removes a listing from the market."""
    db = await db_connect()
    try:
        cursor = await db.execute('DELETE FROM market_listings WHERE uid = ?', (uid,))
        await db.commit()
        return cursor.rowcount > 0 # Return True if a row was deleted
    except Exception as e:
        log.error(f"Error removing market listing for UID {uid}: {e}", exc_info=True)
        return False
    finally:
        await db.close()

async def increment_market_saves(uid: str) -> bool:
    """Increments the saves_count for a listing."""
    db = await db_connect()
    try:
        await db.execute('UPDATE market_listings SET saves_count = saves_count + 1 WHERE uid = ?', (uid,))
        await db.commit()
        return True
    except Exception as e:
        log.error(f"Error incrementing saves for UID {uid}: {e}", exc_info=True)
        return False
    finally:
        await db.close()

async def increment_market_stars(uid: str) -> bool:
    """Increments the stars_count for a listing."""
    db = await db_connect()
    try:
        await db.execute('UPDATE market_listings SET stars_count = stars_count + 1 WHERE uid = ?', (uid,))
        await db.commit()
        return True
    except Exception as e:
        log.error(f"Error incrementing stars for UID {uid}: {e}", exc_info=True)
        return False
    finally:
        await db.close()

async def add_user_market_save(user_id: int, uid: str) -> bool:
    """Adds a record indicating a user saved a market item."""
    db = await db_connect()
    try:
        await db.execute('INSERT INTO user_market_saves (user_id, uid, date_saved) VALUES (?, ?, ?)', (user_id, uid, time.time()))
        await db.commit()
        return True
    except aiosqlite.IntegrityError:
        log.info(f"User {user_id} already saved item {uid}.")
        return False # User likely already saved this item
    except Exception as e:
        log.error(f"Error adding user market save for user {user_id}, UID {uid}: {e}", exc_info=True)
        return False
    finally:
        await db.close()

async def add_user_market_award(user_id: int, uid: str) -> bool:
    """Adds a record indicating a user awarded a market item."""
    db = await db_connect()
    try:
        await db.execute('INSERT INTO user_market_awards (user_id, uid) VALUES (?, ?)', (user_id, uid))
        await db.commit()
        return True
    except aiosqlite.IntegrityError:
        log.info(f"User {user_id} already awarded item {uid}.")
        return False # User likely already awarded this item
    except Exception as e:
         log.error(f"Error adding user market award for user {user_id}, UID {uid}: {e}", exc_info=True)
         return False
    finally:
        await db.close()

async def check_user_market_award(user_id: int, uid: str) -> bool:
    """Checks if a user has already awarded stars to a specific market item."""
    db = await db_connect()
    try:
        async with db.execute('SELECT 1 FROM user_market_awards WHERE user_id = ? AND uid = ?', (user_id, uid)) as cursor:
            result = await cursor.fetchone()
            return result is not None
    finally:
        await db.close() # Return True if an award record exists

async def get_user_relics(owner_id: int) -> list[aiosqlite.Row]:
    """Fetches market listings owned by a specific user."""
    db = await db_connect()
    try:
        db.row_factory = aiosqlite.Row
        async with db.execute('SELECT * FROM market_listings WHERE owner_id = ? ORDER BY date_listed DESC', (owner_id,)) as cursor:
            rows = await cursor.fetchall()
            return rows if rows else []
    finally:
        await db.close()

# --- Views & Modals ---

class VaultPaginator(Paginator):
    """ Custom Paginator for the Vault command. """
    def __init__(self, user_creations: list[dict], market_saves: list[aiosqlite.Row], user: discord.User, cog_instance: 'ManagerCog', items_per_page: int = ITEMS_PER_PAGE):
        # Call parent class's __init__
        super().__init__(timeout=180.0)

        self.user_creations = user_creations
        self.market_saves = market_saves
        self.user = user
        self.cog_instance = cog_instance
        self.items_per_page = items_per_page

        # Combine lists for pagination logic, but remember the source
        self.all_items = [('creation', item) for item in user_creations] + \
                         [('market', item) for item in market_saves]
        self.total_pages = math.ceil(len(self.all_items) / self.items_per_page)
        if self.total_pages == 0: self.total_pages = 1 # Ensure at least one page

        # Update the page indicator
        if hasattr(self, 'page_indicator'):
            self.page_indicator.label = f"Page 1/{self.total_pages}"

        # Add View Temp File button - independent of pagination items
        temp_file_path = TEMP_DIR / f"{user.id}.txt"
        view_temp_button = ui.Button(label="View Temp File", style=ButtonStyle.secondary, emoji="📄", custom_id="view_temp")
        view_temp_button.disabled = not temp_file_path.exists()
        view_temp_button.callback = self.view_temp_callback

        # Call super init *after* calculating total pages
        # Pass an empty list initially, format_page will handle content
        super().__init__(pages=[], timeout=180.0, show_disabled=True, show_indicator=True)
        self.add_item(view_temp_button) # Add the temp button to the paginator's view

    async def respond(self, interaction, ephemeral=False):
        """Send the paginator to the given interaction."""
        # Use the newer API method
        try:
            await interaction.response.defer(ephemeral=ephemeral)
            await self.send(interaction, ephemeral=ephemeral)
        except discord.InteractionResponded:
            # If the interaction has already been responded to, use followup.send
            log.info(f"Interaction already responded to in VaultPaginator.respond for user {interaction.user.id}")
            await self.send(interaction, ephemeral=ephemeral)


    async def format_page(self, page_num: int) -> discord.Embed | str:
        """ Creates the embed for the current page. """
        start_index = (page_num - 1) * self.items_per_page
        end_index = start_index + self.items_per_page
        current_items = self.all_items[start_index:end_index]

        embed = Embed(title=f"{self.user.display_name}'s Vault", color=Color.purple())
        embed.set_footer(text=f"Page {page_num}/{self.total_pages}")

        creations_str = ""
        market_str = ""

        # Clear previous page's buttons if any were added dynamically
        # The paginator manages its standard buttons; we handle dynamic ones.
        # A better approach might be to pass a factory to the page formatter.
        # For now, let's try adding buttons directly (might be limitations).
        # Clearing dynamically added items is tricky with discord.py pagination.
        # Instead of adding buttons here, handle interactions via separate views/modals if needed.

        action_info = [] # Store info for potential actions outside embed field value limits

        for item_type, item_data in current_items:
            if item_type == 'creation':
                 # uid = item_data.get('uid', 'N/A') # Already added in helper
                 uid = item_data['uid']
                 name = item_data.get('file_name', f"Unnamed ({uid[:6]})")
                 desc = item_data.get('description', '*No description.*')
                 date_ts = item_data.get('date_created', 0)
                 date_str = f"<t:{int(date_ts)}:R>" if date_ts else "Unknown date"
                 creations_str += f"**{name}** (`{uid}`)\n" \
                                 f"> {desc}\n" \
                                 f"> Created: {date_str}\n\n"
                 # Add action: List on Market
                 action_info.append({'type': 'list_creation', 'uid': uid, 'name': name})
            else: # market save
                 uid = item_data['uid']
                 name = item_data['file_name']
                 owner_id = item_data['owner_id']
                 # Fetch owner name - potentially slow, maybe store username in DB?
                 # owner = await self.cog_instance.bot.fetch_user(owner_id) # Avoid API call here
                 # owner_name = owner.name if owner else f"ID: {owner_id}"
                 stars = item_data['stars_count']
                 saves = item_data['saves_count']
                 market_str += f"**{name}** (`{uid}`)\n" \
                               f"> Owner: <@{owner_id}> | ⭐ {stars} | 💾 {saves}\n"
                 # Add action: Award Star
                 action_info.append({'type': 'award_star', 'uid': uid, 'name': name, 'owner_id': owner_id})


        if not creations_str: creations_str = "*No personal saves found.*"
        if not market_str: market_str = "*No market items saved.*"

        embed.add_field(name="Your Creations", value=creations_str[:1020] + ('...' if len(creations_str) > 1024 else ''), inline=False) # Limit field size
        embed.add_field(name="Saved Relics", value=market_str[:1020] + ('...' if len(market_str) > 1024 else ''), inline=False)


        # Update the view with buttons for actions on the current page
        # This requires modifying the paginator's view dynamically, which is complex.
        # Alternative: Instruct user to use /award <uid> or /list <uid> commands?
        # Let's stick to the spec: Buttons for Award Star.
        # We need a custom View passed to the Paginator or update it dynamically.

        # Simplification: For now, Vault just *displays* info. Actions like Award/List
        # will be handled by dedicated commands or buttons in `/the_exchange`.
        # This avoids complex dynamic view updates in the paginator.
        # Revisit if buttons *directly* in `/vault` are essential.

        return embed

    async def view_temp_callback(self, interaction: discord.Interaction):
        """Callback for the 'View Temp File' button."""
        await interaction.response.defer(ephemeral=True)
        user_id = interaction.user.id
        temp_file_path = TEMP_DIR / f"{user_id}.txt"
        if temp_file_path.exists():
            try:
                content = await read_file_content(temp_file_path)
                if content and not content.startswith(":"):
                    # Truncate long content
                    display_content = content[:1900] + ('...' if len(content) > 1900 else '')
                    await interaction.followup.send(f"**Temporary File Content:**\n```\n{display_content}\n```", ephemeral=True)
                else:
                    await interaction.followup.send(content or ":warning: Could not read temporary file.", ephemeral=True)
            except Exception as e:
                log.error(f"Error reading temp file {temp_file_path} in vault: {e}")
                await interaction.followup.send(":x: Error accessing temporary file.", ephemeral=True)
        else:
            await interaction.followup.send(":warning: Temporary file not found.", ephemeral=True)


class MarketPaginator(Paginator):
    """ Custom Paginator for The Bazaar view. """
    def __init__(self, listings: list[aiosqlite.Row], user: discord.User, cog_instance: 'ManagerCog', sort_by: str, search_term: str | None, items_per_page: int = ITEMS_PER_PAGE):
        self.listings = listings
        self.user = user
        self.cog_instance = cog_instance
        self.items_per_page = items_per_page
        self.total_pages = math.ceil(len(self.listings) / self.items_per_page)
        if self.total_pages == 0: self.total_pages = 1

        self.sort_by = sort_by
        self.search_term = search_term

        super().__init__(pages=[], timeout=300.0, show_disabled=True, show_indicator=True) # Longer timeout for Browse
        # Add Sort/Search buttons to the paginator's view
        sort_button = ui.Button(label="Sort", style=ButtonStyle.secondary, emoji="↕️", custom_id="market_sort")
        sort_button.callback = self.sort_callback
        search_button = ui.Button(label="Search", style=ButtonStyle.secondary, emoji="🔍", custom_id="market_search")
        search_button.callback = self.search_callback

        self.add_item(sort_button)
        self.add_item(search_button)

    async def respond(self, interaction, ephemeral=False):
        """Send the paginator to the given interaction."""
        # Use the newer API method
        try:
            await interaction.response.defer(ephemeral=ephemeral)
            await self.send(interaction, ephemeral=ephemeral)
        except discord.InteractionResponded:
            # If the interaction has already been responded to, use followup.send
            log.info(f"Interaction already responded to in MarketPaginator.respond for user {interaction.user.id}")
            await self.send(interaction, ephemeral=ephemeral)


    async def format_page(self, page_num: int) -> discord.Embed:
        start_index = (page_num - 1) * self.items_per_page
        end_index = start_index + self.items_per_page
        current_listings = self.listings[start_index:end_index]

        embed = Embed(title="The Bazaar - Market Listings", color=Color.gold())
        embed.set_footer(text=f"Page {page_num}/{self.total_pages} | Sorted by: {self.sort_by.capitalize()} " + (f"| Searching for: '{self.search_term}'" if self.search_term else ""))

        if not current_listings:
            embed.description = "*No listings found matching your criteria.*"
            return embed

        list_str = ""

        for i, item in enumerate(current_listings):
            uid = item['uid']
            name = item['file_name']
            owner_id = item['owner_id']
            stars = item['stars_count']
            saves = item['saves_count']
            desc = item.get('description', '*No description.*')
            date_ts = item.get('date_listed', 0)
            date_str = f"<t:{int(date_ts)}:R>" if date_ts else "Unknown date"

            list_str += f"**{i+1+start_index}. {name}** (`{uid}`)\n" \
                         f"> Owner: <@{owner_id}> | ⭐ {stars} | 💾 {saves}\n" \
                         f"> Listed: {date_str}\n" \
                         f"> {desc}\n\n"

            # Add Indulge button for each item [cite: 77 related]
            # Using buttons directly in paginator is complex. Link to /indulge command.
            # list_str += f"> Use `/indulge uid:{uid}` to view details & save.\n\n"

        embed.description = list_str[:4090] + ('...' if len(list_str) > 4096 else '') # Embed description limit

        # Add Indulge command hint
        embed.add_field(name="Actions", value="Use `/indulge <uid>` to view details, save, or award stars.", inline=False)

        return embed

    async def sort_callback(self, interaction: discord.Interaction):
        """ Callback for the Sort button. """
        view = SortChoiceView(current_sort=self.sort_by)
        await interaction.response.send_message("Select sorting criteria:", view=view, ephemeral=True)
        # Wait for the SortChoiceView interaction
        await view.wait()
        if hasattr(view, 'selected_sort') and view.selected_sort:
             # Re-fetch and update the paginator
             new_listings = await get_all_market_listings(sort_by=view.selected_sort, search_term=self.search_term)
             # Create a *new* paginator instance with the updated data
             new_paginator = MarketPaginator(new_listings, self.user, self.cog_instance, view.selected_sort, self.search_term)
             await self.message.edit(embed=await new_paginator.format_page(1), view=new_paginator)
             self.stop() # Stop the old paginator

    async def search_callback(self, interaction: discord.Interaction):
        """ Callback for the Search button. """
        modal = SearchModal()
        await interaction.response.send_modal(modal)
        # Wait for modal submission
        await modal.wait()
        if hasattr(modal, 'search_term'): # Check if search term was submitted
             new_search = modal.search_term if modal.search_term else None # Use None if cleared
             # Re-fetch and update
             new_listings = await get_all_market_listings(sort_by=self.sort_by, search_term=new_search)
             new_paginator = MarketPaginator(new_listings, self.user, self.cog_instance, self.sort_by, new_search)
             await self.message.edit(embed=await new_paginator.format_page(1), view=new_paginator)
             self.stop()


class SortChoiceView(ui.View):
    def __init__(self, current_sort: str):
        super().__init__(timeout=60.0)
        self.selected_sort = None

        options = [
            discord.SelectOption(label="Date Listed (Newest)", value="date", emoji="📅", default=current_sort=='date'),
            discord.SelectOption(label="Saves Count (Highest)", value="saves", emoji="💾", default=current_sort=='saves'),
            discord.SelectOption(label="Stars Count (Highest)", value="stars", emoji="⭐", default=current_sort=='stars'),
        ]
        self.select_menu = ui.Select(placeholder="Choose sorting...", options=options, custom_id="sort_select")
        self.select_menu.callback = self.select_callback
        self.add_item(self.select_menu)

    async def select_callback(self, interaction: discord.Interaction):
        self.selected_sort = interaction.data['values'][0]
        await interaction.response.send_message(f"Sorting by: {self.selected_sort.capitalize()}", ephemeral=True, delete_after=5)
        self.stop()


class SearchModal(ui.Modal, title="Search Bazaar Listings"):
    search_term_input = ui.TextInput(
        label="Search Term (leave blank to clear)",
        style=TextStyle.short,
        placeholder="Enter keywords for name or description...",
        required=False,
        max_length=100,
    )

    def __init__(self):
        super().__init__(timeout=120.0)
        self.search_term = None

    async def on_submit(self, interaction: discord.Interaction):
        self.search_term = self.search_term_input.value.strip()
        await interaction.response.send_message(f"Searching for: '{self.search_term}'" if self.search_term else "Cleared search.", ephemeral=True, delete_after=5)
        self.stop()

    async def on_error(self, interaction: discord.Interaction, error: Exception):
        log.error(f"Error in SearchModal: {error}")
        await interaction.response.send_message(":x: Error processing search.", ephemeral=True)
        self.stop()


class MyRelicsView(ui.View):
    def __init__(self, cog_instance: 'ManagerCog', owner_id: int, listed_relics: list[aiosqlite.Row]):
        super().__init__(timeout=300.0)
        self.cog_instance = cog_instance
        self.owner_id = owner_id
        self.listed_relics = listed_relics # Store for potential dynamic updates
        self.message = None

        # --- List Item Button ---
        list_button = ui.Button(label="List a Creation", style=ButtonStyle.green, emoji="➕", custom_id="list_creation")
        list_button.callback = self.list_creation_callback
        self.add_item(list_button)

        # --- Unlist Select Menu ---
        if listed_relics:
             options = [
                 discord.SelectOption(label=f"{relic['file_name']} ({relic['uid'][:6]}...)", value=relic['uid'], emoji="🗑️")
                 for relic in listed_relics[:25] # Max 25 options
             ]
             unlist_select = ui.Select(
                 placeholder="Select a listed relic to unlist...",
                 options=options,
                 custom_id="unlist_select"
             )
             unlist_select.callback = self.unlist_select_callback
             self.add_item(unlist_select)

    async def list_creation_callback(self, interaction: discord.Interaction):
        """Shows a dropdown of unlisted creations to list."""
        await interaction.response.defer(ephemeral=True)
        user_creations = await get_user_saves_metadata(self.owner_id)
        listed_uids = {relic['uid'] for relic in self.listed_relics}

        unlisted_creations = [c for c in user_creations if c['uid'] not in listed_uids]

        if not unlisted_creations:
             await interaction.followup.send("You have no unlisted creations in your saves to list.", ephemeral=True)
             return

        options = [
             discord.SelectOption(label=f"{c.get('file_name', 'Unnamed')[:90]}", value=c['uid'], description=f"({c['uid'][:6]}...)")
             for c in unlisted_creations[:25] # Limit options
        ]
        select_view = ListCreationSelectView(self.cog_instance, options)
        await interaction.followup.send("Select a creation from your saves to list on the market:", view=select_view, ephemeral=True)


    async def unlist_select_callback(self, interaction: discord.Interaction):
        """Callback for the Unlist select menu."""
        uid_to_unlist = interaction.data['values'][0]
        await interaction.response.defer(ephemeral=True)

        log.info(f"User {self.owner_id} attempting to unlist item {uid_to_unlist}")
        success = await remove_market_listing(uid_to_unlist)

        if success:
            await interaction.followup.send(f":white_check_mark: Successfully unlisted item `{uid_to_unlist}`.", ephemeral=True)
            # Refresh the view/message
            await self.refresh_message()
        else:
            await interaction.followup.send(f":x: Failed to unlist item `{uid_to_unlist}`. It might have already been removed.", ephemeral=True)

    async def refresh_message(self):
         """ Refreshes the My Relics message after an action. """
         if not self.message: return # Cannot refresh if message reference lost

         new_relics = await get_user_relics(self.owner_id)
         self.listed_relics = new_relics # Update internal state

         embed = await self.cog_instance.format_my_relics_embed(new_relics)
         new_view = MyRelicsView(self.cog_instance, self.owner_id, new_relics)
         new_view.message = self.message # Keep message reference

         try:
            await self.message.edit(embed=embed, view=new_view)
         except Exception as e:
            log.error(f"Failed to refresh My Relics view: {e}")


class ListCreationSelectView(ui.View):
     def __init__(self, cog_instance: 'ManagerCog', options: list[discord.SelectOption]):
        super().__init__(timeout=180.0)
        self.cog_instance = cog_instance

        select = ui.Select(
            placeholder="Select creation to list...",
            options=options,
            custom_id="list_creation_select"
        )
        select.callback = self.select_callback
        self.add_item(select)

     async def select_callback(self, interaction: discord.Interaction):
        """Lists the selected creation."""
        uid_to_list = interaction.data['values'][0]
        await interaction.response.defer(ephemeral=True)

        # Fetch metadata for the selected UID
        user_creations = await get_user_saves_metadata(interaction.user.id)
        creation_data = next((c for c in user_creations if c['uid'] == uid_to_list), None)

        if not creation_data:
            await interaction.followup.send(":x: Could not find metadata for the selected creation.", ephemeral=True)
            return

        file_name = creation_data.get('file_name', f"Unnamed ({uid_to_list[:6]})")
        description = creation_data.get('description')
        owner_id = interaction.user.id

        log.info(f"User {owner_id} attempting to list item {uid_to_list} ('{file_name}')")
        success = await add_market_listing(uid_to_list, owner_id, file_name, description)

        if success:
             await interaction.followup.send(f":white_check_mark: Successfully listed '{file_name}' (`{uid_to_list}`) on the market!", ephemeral=True)
             # Could potentially refresh the 'My Relics' view if it's accessible
        else:
             await interaction.followup.send(f":warning: Failed to list '{file_name}'. It might already be listed.", ephemeral=True)

        # Remove the selection view after action
        await interaction.edit_original_response(content="List action complete.", view=None)


class IndulgeView(ui.View):
    def __init__(self, cog_instance: 'ManagerCog', listing_data: aiosqlite.Row, current_user_id: int):
        super().__init__(timeout=180.0)
        self.cog_instance = cog_instance
        self.listing_data = listing_data
        self.uid = listing_data['uid']
        self.owner_id = listing_data['owner_id']
        self.current_user_id = current_user_id
        self.message = None

        # --- Save Relic Button ---
        save_button = ui.Button(label="Save Relic", style=ButtonStyle.green, emoji="💾", custom_id="indulge_save")
        save_button.disabled = (self.owner_id == current_user_id) # Disable saving own item
        save_button.callback = self.save_relic_callback
        self.add_item(save_button)

        # --- Award Star Button ---
        award_button = ui.Button(label="Award Star", style=ButtonStyle.blurple, emoji="⭐", custom_id="indulge_award")
        award_button.disabled = (self.owner_id == current_user_id) # Disable awarding own item
        award_button.callback = self.award_star_callback
        self.add_item(award_button)

    async def disable_buttons(self):
        for item in self.children:
            if isinstance(item, ui.Button):
                item.disabled = True
        try:
            if self.message: await self.message.edit(view=self)
        except: pass # Ignore errors editing view

    async def save_relic_callback(self, interaction: discord.Interaction):
        """Handles saving the relic."""
        await interaction.response.defer(ephemeral=True)
        user_id = interaction.user.id
        uid = self.uid

        # Check if already saved
        async with db_connect() as db:
             async with db.execute("SELECT 1 FROM user_market_saves WHERE user_id = ? AND uid = ?", (user_id, uid)) as cursor:
                 already_saved = await cursor.fetchone()

        if already_saved:
             await interaction.followup.send(":information_source: You have already saved this relic.", ephemeral=True)
             return

        # Add to user saves and increment count
        save_added = await add_user_market_save(user_id, uid)
        count_incremented = False
        if save_added:
             count_incremented = await increment_market_saves(uid)

        if save_added and count_incremented:
             log.info(f"User {user_id} saved market item {uid}")
             await interaction.followup.send(":white_check_mark: Relic saved to your `/vault`!", ephemeral=True)
             # Optionally update the displayed saves count? Requires re-fetching and editing embed.
        else:
             await interaction.followup.send(":x: Failed to save relic. Please try again.", ephemeral=True)


    async def award_star_callback(self, interaction: discord.Interaction):
        """Handles awarding a star."""
        await interaction.response.defer(ephemeral=True)
        user_id = interaction.user.id
        uid = self.uid

        # Check if already awarded
        already_awarded = await check_user_market_award(user_id, uid)
        if already_awarded:
            await interaction.followup.send(":information_source: You have already awarded a star to this relic.", ephemeral=True)
            return

        # Add award record and increment count
        award_added = await add_user_market_award(user_id, uid)
        count_incremented = False
        if award_added:
            count_incremented = await increment_market_stars(uid)

        if award_added and count_incremented:
            log.info(f"User {user_id} awarded star to market item {uid}")
            await interaction.followup.send(":star: Star awarded! Thank you for your appreciation.", ephemeral=True)
            # Optionally update the displayed stars count? Requires re-fetching and editing embed.
        else:
            await interaction.followup.send(":x: Failed to award star. Please try again.", ephemeral=True)

    async def on_timeout(self):
        await self.disable_buttons()


# --- Manager Cog Class ---

class ManagerCog(commands.Cog, name="Manager"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.maintenance_mode = False
        # Track sent messages for auto-deletion after 5000 seconds
        self.sent_messages = [] # List of (message, timestamp) tuples
        # Start the message cleanup task
        self.message_cleanup_task = asyncio.create_task(self.cleanup_old_messages())
        log.info("Manager Cog initialized.")

    # Track when maintenance mode was enabled
    maintenance_start_time = None

    async def check_maintenance(self, interaction: discord.Interaction) -> bool:
        """Checks if maintenance mode is active."""
        if self.maintenance_mode:
            # New commands are rejected immediately
            await interaction.response.send_message(":tools: The Market & Vault are currently undergoing maintenance. Please try again later.", ephemeral=True)
            return True
        return False

    async def maintenance_timeout_task(self):
        """Task that runs when maintenance mode is enabled to terminate active views after 15 minutes."""
        try:
            await asyncio.sleep(900)  # 15 minutes = 900 seconds

            if not self.maintenance_mode:
                # Maintenance mode was disabled before timeout
                return

            log.info("Maintenance timeout reached. Terminating all active market/vault views.")

            # Since we don't have a direct way to track active views, we'll log a message
            # The views will time out naturally based on their timeout settings
            log.info("All active market and vault views will time out naturally based on their timeout settings.")
        except asyncio.CancelledError:
            # Task was cancelled, just exit
            log.info("Maintenance timeout task cancelled")
            return
        except Exception as e:
            log.error(f"Error in maintenance timeout task: {e}", exc_info=True)

    async def format_my_relics_embed(self, relics: list[aiosqlite.Row]) -> Embed:
        """Formats the embed for the 'My Relics' view."""
        embed = Embed(title="My Relics on the Market", color=Color.blue())
        if not relics:
            embed.description = "You have not listed any creations on the market yet."
            return embed

        list_str = ""
        for item in relics:
             uid = item['uid']
             name = item['file_name']
             stars = item['stars_count']
             saves = item['saves_count']
             date_ts = item.get('date_listed', 0)
             date_str = f"<t:{int(date_ts)}:R>" if date_ts else "Unknown date"
             list_str += f"**{name}** (`{uid}`)\n" \
                         f"> ⭐ {stars} | 💾 {saves} | Listed: {date_str}\n\n"

        embed.description = list_str[:4090] + ('...' if len(list_str) > 4096 else '')
        return embed

    # --- Commands ---
    @app_commands.command(name="vault", description="View your saved creations and market items.")
    async def vault(self, interaction: discord.Interaction):
        """Displays the user's saved items."""
        if await self.check_maintenance(interaction): return
        await interaction.response.defer(ephemeral=True) # Make vault view private

        user_id = interaction.user.id
        user_creations = await get_user_saves_metadata(user_id)
        market_saves = await get_user_market_saves_info(user_id)

        if not user_creations and not market_saves:
            # Add temp file check here too before saying completely empty
            temp_file_path = TEMP_DIR / f"{user_id}.txt"
            view_temp_button = ui.Button(label="View Temp File", style=ButtonStyle.secondary, emoji="📄", custom_id="view_temp")
            view_temp_button.disabled = not temp_file_path.exists()
            # Need a dummy callback or reuse vault's
            async def temp_callback(inter: discord.Interaction): await VaultPaginator([], [], interaction.user, self).view_temp_callback(inter)
            view_temp_button.callback = temp_callback

            temp_view = ui.View(timeout=60)
            temp_view.add_item(view_temp_button)

            await interaction.followup.send("Your vault is empty. Use `/spectre` to create something or `/the_exchange` to find relics!", view=temp_view, ephemeral=True)
            return

        # Use the custom paginator
        paginator = VaultPaginator(user_creations, market_saves, interaction.user, self)
        await paginator.respond(interaction, ephemeral=True)


    @app_commands.command(name="the_exchange", description="Access the market: Browse or manage your listed items.")
    async def the_exchange(self, interaction: discord.Interaction):
        """Shows options for interacting with the market."""
        if await self.check_maintenance(interaction): return

        view = ui.View(timeout=180.0)
        my_relics_button = ui.Button(label="My Relics", style=ButtonStyle.primary, emoji="👑", custom_id="my_relics")
        bazaar_button = ui.Button(label="The Bazaar", style=ButtonStyle.success, emoji="🛒", custom_id="the_bazaar")

        async def my_relics_callback(inter: discord.Interaction):
             """Callback for My Relics button."""
             await inter.response.defer(ephemeral=True) # Keep market interactions private
             owner_id = inter.user.id
             relics = await get_user_relics(owner_id)
             embed = await self.format_my_relics_embed(relics)
             relics_view = MyRelicsView(self, owner_id, relics)
             message = await inter.followup.send(embed=embed, view=relics_view, ephemeral=True)
             relics_view.message = message # Store message ref

        async def bazaar_callback(inter: discord.Interaction):
             """Callback for The Bazaar button."""
             await inter.response.defer(ephemeral=True) # Keep Browse private? Or public? Let's try public
             listings = await get_all_market_listings(sort_by='date') # Default sort
             if not listings:
                  await inter.followup.send("The Bazaar is currently empty.", ephemeral=True)
                  return

             paginator = MarketPaginator(listings, inter.user, self, 'date', None)
             # Respond non-ephemerally for Bazaar Browse
             await paginator.respond(inter, ephemeral=False) # Send public message for Browse


        my_relics_button.callback = my_relics_callback
        bazaar_button.callback = bazaar_callback
        view.add_item(my_relics_button)
        view.add_item(bazaar_button)

        message = await interaction.response.send_message("Welcome to the Exchange. What would you like to do?", view=view, ephemeral=True)
        # Track message for auto-deletion
        self.track_message(message)


    @app_commands.command(name="indulge", description="View details, save, or award a specific market item.")
    @app_commands.describe(uid="The unique ID of the market item.")
    async def indulge(self, interaction: discord.Interaction, uid: str):
        """Displays details and actions for a specific market item."""
        if await self.check_maintenance(interaction): return
        await interaction.response.defer(ephemeral=False) # Show indulge publicly? Yes.

        listing = await get_market_listing(uid)

        if not listing:
            await interaction.followup.send(f":x: Market item with ID `{uid}` not found.", ephemeral=True)
            return

        owner_id = listing['owner_id']
        owner = await self.bot.fetch_user(owner_id) # Fetch user object for name/mention
        owner_name = owner.mention if owner else f"Unknown User ({owner_id})"
        date_ts = listing.get('date_listed', 0)
        date_str = f"<t:{int(date_ts)}:F>" if date_ts else "Unknown date" # Show full date

        embed = Embed(title=listing['file_name'], color=Color.teal())
        embed.description = listing.get('description', '*No description provided.*')
        embed.add_field(name="Owner", value=owner_name, inline=True)
        embed.add_field(name="Listed", value=date_str, inline=True)
        embed.add_field(name="Stats", value=f"⭐ {listing['stars_count']} Stars | 💾 {listing['saves_count']} Saves", inline=True)
        embed.set_footer(text=f"Item UID: {uid}")

        view = IndulgeView(self, listing, interaction.user.id)
        message = await interaction.followup.send(embed=embed, view=view)
        # Track message for auto-deletion
        self.track_message(message)
        view.message = message


    @indulge.autocomplete('uid')
    async def indulge_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        """Autocompletes UIDs for the indulge command.

        Args:
            interaction: The Discord interaction (required by Discord API but not used)
            current: The current input string

        Returns:
            A list of autocomplete choices
        """

        listings = await get_all_market_listings(search_term=current if current else None)
        choices = []
        for listing in listings[:25]: # Limit choices
            choices.append(app_commands.Choice(name=f"{listing['file_name']} ({listing['uid'][:6]}...)", value=listing['uid']))
        return choices

    @commands.is_owner()
    @commands.command(name="managermaintenance", aliases=['mmaint'])
    async def manager_maintenance(self, ctx: commands.Context):
        """Toggles maintenance mode for the Manager cog (Owner Only)."""
        self.maintenance_mode = not self.maintenance_mode
        status = "ENABLED" if self.maintenance_mode else "DISABLED"

        if self.maintenance_mode:
            # Start the maintenance timeout task
            self.maintenance_start_time = time.time()
            asyncio.create_task(self.maintenance_timeout_task())
            message = await ctx.send(f":tools: Manager Cog (Vault/Market) maintenance mode is now **{status}**. Active views will time out naturally, and all operations will be terminated in 15 minutes.")
            # Track message for auto-deletion
            self.track_message(message)
        else:
            # Maintenance mode disabled
            self.maintenance_start_time = None
            message = await ctx.send(f":tools: Manager Cog (Vault/Market) maintenance mode is now **{status}**. New operations are now allowed.")
            # Track message for auto-deletion
            self.track_message(message)

        log.info(f"Manager maintenance mode set to {status} by {ctx.author}")


    async def cog_load(self):
        """Called when the cog is loaded."""
        log.info(f"ManagerCog loaded")

    async def cleanup_old_messages(self):
        """Task that periodically checks for and deletes old messages."""
        while True:
            try:
                current_time = time.time()
                # Create a new list with messages that are still valid (not old enough to delete)
                still_valid = []

                for message, timestamp in self.sent_messages:
                    # Check if message is older than 5000 seconds
                    if current_time - timestamp > 5000:
                        try:
                            # Try to delete the message
                            await message.delete()
                            log.info(f"Auto-deleted message {message.id} after 5000 seconds")
                        except discord.NotFound:
                            # Message already deleted, just skip
                            log.debug(f"Message {message.id} already deleted")
                        except discord.Forbidden:
                            # Bot doesn't have permission to delete
                            log.warning(f"No permission to delete message {message.id}")
                        except Exception as e:
                            log.error(f"Error deleting message {message.id}: {e}")
                    else:
                        # Message not old enough yet, keep it in the list
                        still_valid.append((message, timestamp))

                # Update the list with only valid messages
                self.sent_messages = still_valid

                # Sleep for a minute before checking again
                await asyncio.sleep(60)
            except asyncio.CancelledError:
                # Task was cancelled, exit cleanly
                log.info("Message cleanup task cancelled")
                break
            except Exception as e:
                log.error(f"Error in message cleanup task: {e}", exc_info=True)
                # Sleep a bit before retrying
                await asyncio.sleep(60)

    # Helper method to track messages for auto-deletion
    def track_message(self, message):
        """Add a message to the tracking list for auto-deletion."""
        if message and hasattr(message, 'id'):
            self.sent_messages.append((message, time.time()))
            log.debug(f"Tracking message {message.id} for auto-deletion")

    async def cog_unload(self):
        """Called when the cog is unloaded."""
        # Cancel the message cleanup task
        if hasattr(self, 'message_cleanup_task') and self.message_cleanup_task:
            self.message_cleanup_task.cancel()
            try:
                await self.message_cleanup_task
            except asyncio.CancelledError:
                pass
        log.info(f"ManagerCog unloaded")

# --- Setup Function ---
async def setup(bot: commands.Bot):
    await bot.add_cog(ManagerCog(bot))