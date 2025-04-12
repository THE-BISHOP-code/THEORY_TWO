# cogs/executor.py

import discord
from discord.ext import commands
from discord import app_commands, ui, ButtonStyle, Embed, Color
# import os  # Not used directly
import asyncio
import importlib
import time
from pathlib import Path
import logging
import shlex # For robust command line parsing
import traceback
import json
import random
import sys
import warnings

# Filter out curl_cffi warnings globally
warnings.filterwarnings("ignore", message="Curlm already closed! quitting from process_data")
warnings.filterwarnings("ignore", category=UserWarning, module="curl_cffi")

# Add parent directory to path for imports
BASE_DIR = Path(__file__).parent.parent
sys.path.append(str(BASE_DIR))

# Import config manager
from utils.config_manager import config

# --- Constants & Setup ---
TEMP_DIR = BASE_DIR / "temp"
SAVES_DIR = BASE_DIR / "saves"
COMMANDS_DIR = BASE_DIR / "commands"
FREE_COMMANDS_DIR = COMMANDS_DIR / "free"
PREMIUM_COMMANDS_DIR = COMMANDS_DIR / "premium"
FILES_DIR = BASE_DIR # For undo.txt etc.

# Get file paths from config
RANDOM_TXT_PATH = FILES_DIR / config.get("spectre.loading_messages_file", "random.txt")
UNDO_FILE = FILES_DIR / config.get("spectre.undo_file", "undo.txt")

# Logger for this cog
log = logging.getLogger('MyBot.ExecutorCog')

# --- GPT Integration using g4f ---
from g4f.client import Client

class GPTInstanceExecutor:
    """ Real GPT instance for executor using g4f client. """
    def __init__(self, initial_prompt: str):
        self.client = Client()
        self.history = [{"role": "system", "content": initial_prompt}]
        log.info(f"Executor GPT initialized with prompt: {initial_prompt[:50]}...")

    async def query(self, user_prompt: str) -> str:
        """ Sends a query to the GPT model. """
        log.info(f"Executor GPT received query: {user_prompt[:50]}...")

        # Add user message to history
        self.history.append({"role": "user", "content": user_prompt})

        try:
            # Make API call to g4f using the exact implementation provided
            # Use the existing client instance instead of creating a new one each time
            # Note: g4f doesn't support parameters like temperature, tokens, etc.
            # Only model and messages are passed, and even model might be ignored
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=self.history
            )

            # Extract response content
            response_content = response.choices[0].message.content

            # Add assistant response to history
            self.history.append({"role": "assistant", "content": response_content})

            log.info(f"Executor GPT generated response: {response_content[:50]}...")
            return response_content

        except Exception as e:
            log.error(f"Error in Executor GPT query: {e}", exc_info=True)
            return f":x: Error communicating with the AI model: {str(e)}"

    async def close(self):
        """Close the GPT instance and clean up resources."""
        # No actual cleanup needed for g4f client, but method provided for interface consistency
        log.info("Executor GPT instance closed")

async def initialize_gpt_session_executor(instructor_prompt: str) -> GPTInstanceExecutor:
    """Initializes a GPT session using g4f for the executor."""
    return GPTInstanceExecutor(initial_prompt=instructor_prompt)

async def query_gpt_executor(gpt_instance: GPTInstanceExecutor, prompt: str) -> str | None:
    """Sends a query to an existing GPT session."""
    try:
        response = await gpt_instance.query(prompt)
        return response
    except Exception as e:
        log.error(f"Error querying Executor GPT: {e}", exc_info=True)
        return ":x: Error communicating with the AI model for undo."
# --- End GPT Integration ---


# --- Helper Functions ---

async def read_file_content(filepath: Path) -> str | None:
    """Helper to read text files asynchronously.

    Args:
        filepath: Path to the file to read

    Returns:
        The file content as a string, None if file not found, or an error message string starting with ':x:'
    """
    if not filepath:
        log.error(f"Invalid file path: {filepath}")
        return ":x: Invalid file path."

    try:
        # Define a function to read the file in a thread
        def read_file():
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()

        # Use asyncio's thread to avoid blocking the event loop for file I/O
        content = await asyncio.to_thread(read_file)

        # Check if content is empty
        if not content or content.strip() == "":
            log.warning(f"File is empty: {filepath}")
            return ":x: File is empty."

        return content
    except FileNotFoundError:
        log.warning(f"File not found: {filepath}")
        return None # Return None specifically for file not found
    except PermissionError:
        log.error(f"Permission denied when reading file {filepath}")
        return f":x: Permission denied when reading file `{filepath.name}`."
    except UnicodeDecodeError:
        log.error(f"Unicode decode error when reading file {filepath}. File may not be text.")
        return f":x: File `{filepath.name}` appears to be binary or not valid UTF-8 text."
    except Exception as e:
        log.error(f"Error reading file {filepath}: {e}", exc_info=True)
        return f":x: Error reading file `{filepath.name}`: {str(e)}"

async def get_user_saves_metadata(user_id: int) -> list[dict]:
    """Reads all metadata JSON files for a user's personal saves.

    Args:
        user_id: The Discord user ID

    Returns:
        A list of metadata dictionaries for the user's saves, sorted by date created (newest first)
    """
    user_saves_path = SAVES_DIR / str(user_id)
    metadata_list = []

    # Ensure the saves directory exists
    if not SAVES_DIR.exists():
        try:
            SAVES_DIR.mkdir(parents=True, exist_ok=True)
            log.info(f"Created saves directory: {SAVES_DIR}")
        except Exception as e:
            log.error(f"Failed to create saves directory: {e}", exc_info=True)
            return metadata_list

    # Ensure the user's saves directory exists
    if not user_saves_path.exists():
        try:
            user_saves_path.mkdir(parents=True, exist_ok=True)
            log.info(f"Created user saves directory for user {user_id}: {user_saves_path}")
            return metadata_list  # Return empty list for newly created directory
        except Exception as e:
            log.error(f"Failed to create user saves directory for user {user_id}: {e}", exc_info=True)
            return metadata_list
    elif not user_saves_path.is_dir():
        log.error(f"User saves path exists but is not a directory: {user_saves_path}")
        return metadata_list

    try:
        for item in user_saves_path.iterdir():
            if item.is_file() and item.suffix == '.json':
                try:
                    # Define a function to read and parse the JSON file
                    def read_json_file():
                        with open(item, 'r', encoding='utf-8') as f:
                            return json.load(f)

                    # Execute in a thread to avoid blocking
                    data = await asyncio.to_thread(read_json_file)

                    # Validate the metadata has required fields
                    if not all(key in data for key in ['file_name', 'date_created']):
                        log.warning(f"Metadata file {item} is missing required fields")
                        # Try to repair if possible
                        if 'file_name' not in data:
                            data['file_name'] = item.stem
                        if 'date_created' not in data:
                            data['date_created'] = time.time()

                    # Add file path info if needed, e.g., data['uid'] = item.stem
                    if 'uid' not in data: # Ensure UID is present from file stem if missing
                        data['uid'] = item.stem

                    metadata_list.append(data)
                except json.JSONDecodeError:
                    log.error(f"Error decoding JSON file: {item}")
                except Exception as e:
                    log.error(f"Error reading metadata file {item}: {e}", exc_info=True)
    except Exception as e:
        log.error(f"Error listing files in user saves directory for user {user_id}: {e}", exc_info=True)

    # Sort by date created, newest first
    metadata_list.sort(key=lambda x: x.get('date_created', 0), reverse=True)
    return metadata_list

def load_random_lines() -> list[str]:
    """Loads lines from random.txt for use as loading messages.

    Returns:
        A list of strings to use as loading messages, or a default if the file can't be read
    """
    # This duplicates logic from spectre. Consider putting in a central helper module.
    default_lines = ["Executing...", "Processing commands...", "Working on it...", "Almost there..."]

    if not RANDOM_TXT_PATH.exists():
        log.warning(f"Random text file not found: {RANDOM_TXT_PATH}. Using default loading messages.")
        return default_lines

    try:
        with open(RANDOM_TXT_PATH, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip()]

        if not lines:
            log.warning(f"Random text file is empty: {RANDOM_TXT_PATH}. Using default loading messages.")
            return default_lines

        log.info(f"Loaded {len(lines)} random loading messages from {RANDOM_TXT_PATH}")
        return lines
    except Exception as e:
        log.error(f"Error reading random text file {RANDOM_TXT_PATH}: {e}", exc_info=True)
        return default_lines

async def get_user_tier(user_id: int, uid: str | None = None) -> str:
    """Determines the applicable tier for execution.

    Args:
        user_id: The Discord user ID
        uid: Optional UID of a saved file to check for tier information

    Returns:
        The user's tier as a string, defaulting to 'Drifter' if not determinable
    """
    # TODO: In the future, this could check a database or Discord roles for the user's tier

    # First check if we have a UID to look up metadata
    if uid:
        metadata_path = SAVES_DIR / str(user_id) / f"{uid}.json"
        if metadata_path.exists():
            try:
                # Define a function to read and parse the JSON file
                def read_json_file():
                    with open(metadata_path, 'r', encoding='utf-8') as f:
                        return json.load(f)

                # Execute in a thread to avoid blocking
                metadata = await asyncio.to_thread(read_json_file)

                # Get tier from metadata with validation
                tier = metadata.get('tier_used', 'Drifter')

                # Validate tier is one of the allowed values
                valid_tiers = ['Drifter', 'Abysswalker', 'Voidborn']
                if tier not in valid_tiers:
                    log.warning(f"Invalid tier '{tier}' in metadata for user {user_id}, UID {uid}. Defaulting to 'Drifter'.")
                    tier = 'Drifter'

                log.debug(f"Using tier '{tier}' from metadata file {uid}.json for user {user_id}")
                return tier
            except json.JSONDecodeError as e:
                log.error(f"Invalid JSON in metadata file {metadata_path}: {e}")
                return 'Drifter' # Default on JSON error
            except Exception as e:
                log.error(f"Error reading metadata {metadata_path} for tier: {e}", exc_info=True)
                return 'Drifter' # Default on error reading metadata

    # If we get here, either no UID was provided or we couldn't get tier from metadata
    log.debug(f"Using default tier 'Drifter' for user {user_id} (temp file or no metadata)")
    return 'Drifter' # Default tier for temp files or if metadata fails

async def get_command_module(command_name: str) -> tuple[object | None, str | None]:
    """Finds and imports the command logic module.

    Args:
        command_name: The name of the command to find

    Returns:
        A tuple containing (module_object, tier) if found, or (None, None) if not found or error
    """
    if not command_name:
        log.error("Attempted to get command module with empty command name")
        return None, None

    # Normalize command name to lowercase and remove any special characters
    normalized_name = ''.join(c for c in command_name.lower() if c.isalnum() or c == '_')
    if normalized_name != command_name.lower():
        log.warning(f"Command name '{command_name}' was normalized to '{normalized_name}'")

    # Check if command directories exist
    if not FREE_COMMANDS_DIR.exists():
        try:
            FREE_COMMANDS_DIR.mkdir(parents=True, exist_ok=True)
            log.info(f"Created free commands directory: {FREE_COMMANDS_DIR}")
        except Exception as e:
            log.error(f"Failed to create free commands directory: {e}", exc_info=True)
            return None, None

    if not PREMIUM_COMMANDS_DIR.exists():
        try:
            PREMIUM_COMMANDS_DIR.mkdir(parents=True, exist_ok=True)
            log.info(f"Created premium commands directory: {PREMIUM_COMMANDS_DIR}")
        except Exception as e:
            log.error(f"Failed to create premium commands directory: {e}", exc_info=True)
            return None, None

    # Prioritize premium, then free? Or check free first? Let's check free first.
    for directory, tier in [(FREE_COMMANDS_DIR, 'free'), (PREMIUM_COMMANDS_DIR, 'premium')]:
        module_filename = f"{normalized_name}_command.py"
        module_path = directory / module_filename

        if module_path.is_file():
            module_name_import = f"commands.{tier}.{normalized_name}_command"
            try:
                # Use importlib to load the module dynamically
                module = importlib.import_module(module_name_import)
                # Reload module in case it was updated since bot start (useful for development)
                module = importlib.reload(module)
                log.debug(f"Loaded command module '{module_name_import}' for command '{command_name}'")
                return module, tier
            except ModuleNotFoundError:
                 log.error(f"Found command file {module_path}, but failed to import module '{module_name_import}'")
            except ImportError as e:
                 log.error(f"Import error for command module {module_name_import}: {e}", exc_info=True)
            except Exception as e:
                 log.error(f"Error importing command module {module_name_import}: {e}", exc_info=True)
            # Only return None if we found the file but failed to import it
            return None, None # Import error

    log.warning(f"Command logic file not found for command: {command_name}")
    return None, None # Command not found in either directory

def parse_command_line(line: str) -> tuple[str | None, dict | None, str | None]:
    """Parses a command line into name and args dict using shlex.

    Args:
        line: The command line to parse

    Returns:
        A tuple containing (command_name, args_dict, error_message)
        If parsing fails, command_name and args_dict will be None, and error_message will contain the error
        If the line is empty or a comment, all three values will be None
    """
    if not line:
        return None, None, None

    # Ignore comments (lines starting with #)
    if line.strip().startswith('#'):
        return None, None, None

    try:
        # Handle NOTICE:"..." separately first
        if line.upper().startswith("NOTICE:"):
            notice_content = line[len("NOTICE:"):].strip()
            # Handle quoted and unquoted notice content
            if notice_content.startswith('"') and notice_content.endswith('"'):
                notice_content = notice_content[1:-1] # Remove surrounding quotes
            elif notice_content.startswith("'") and notice_content.endswith("'"):
                notice_content = notice_content[1:-1] # Remove surrounding single quotes

            # Validate notice content is not empty
            if not notice_content.strip():
                return None, None, "Empty NOTICE content"

            return "NOTICE", {"message": notice_content}, None

        # Special handling for JSON content
        # Check if this is a JSON object (starts with { and ends with })
        stripped_line = line.strip()
        if stripped_line.startswith('{') and stripped_line.endswith('}'):
            try:
                # Try to parse as JSON to validate
                json_obj = json.loads(stripped_line)
                if isinstance(json_obj, dict) and 'command' in json_obj:
                    # Extract the command and arguments from the JSON
                    command_name = json_obj.pop('command')
                    # Remove '_command' suffix if present
                    if command_name.endswith('_command'):
                        command_name = command_name[:-8]

                    # Convert remaining JSON properties to command arguments
                    args_dict = {}
                    for key, value in json_obj.items():
                        args_dict[key.lower()] = str(value)

                    log.info(f"Converted JSON to command: {command_name} with args {args_dict}")
                    return command_name, args_dict, None
            except json.JSONDecodeError:
                # Not valid JSON, continue with normal parsing
                pass

        # Ignore lines with ```json or ``` markers - these are handled in execute_file
        if line.strip() == '```' or line.strip().startswith('```'):
            return None, None, None

        # Special handling for lines containing "json" as a word
        # Only treat as notice if it's not part of a valid command format
        if "json" in line.lower() and not any('=' in part for part in line.split()):
            # Check if this is likely just a description mentioning JSON
            if not line.strip().startswith('{') and not line.strip().endswith('}'):
                log.info(f"Treating line with 'json' as a notice: '{line}'")
                return "NOTICE", {"message": f"Note: {line}"}, None

        # Use shlex for robust parsing of args with spaces/quotes
        parts = shlex.split(line)
        if not parts:
            return None, None, None

        command_name = parts[0]
        args_dict = {}
        for part in parts[1:]:
            if '=' in part:
                key, value = part.split('=', 1)
                args_dict[key.lower()] = value # Store keys as lowercase
            else:
                 # Handle positional args? Or require key=value?
                 # For simplicity, require key=value for now.
                 log.warning(f"Ignoring arg without '=' in line '{line}': {part}")

        return command_name, args_dict, None
    except Exception as e:
        log.error(f"Error parsing command line '{line}': {e}")
        return None, None, f"Parsing error: {e}"

# --- Views & Modals ---

class UndoConfirmView(ui.View):
    def __init__(self, cog_instance: 'ExecutorCog', undone_commands: str, target_file_path: Path, uid: str | None):
        super().__init__(timeout=300.0) # 5 min to confirm undo commit
        self.cog_instance = cog_instance
        self.undone_commands = undone_commands
        self.target_file_path = target_file_path
        self.uid = uid
        self.message = None

        commit_button = ui.Button(label="Commit Undo", style=ButtonStyle.danger, emoji="↩️", custom_id="commit_undo")
        commit_button.callback = self.commit_undo_callback
        self.add_item(commit_button)

    async def disable_buttons(self):
        for item in self.children: item.disabled = True
        try:
            if self.message: await self.message.edit(view=self)
        except: pass

    async def commit_undo_callback(self, interaction: discord.Interaction):
        """Replaces file content and re-executes."""
        await self.disable_buttons()
        await interaction.response.defer(thinking=True, ephemeral=False) # Show public thinking for undo execution
        log.info(f"User {interaction.user.id} confirmed commit for undo of file {self.target_file_path.name}")

        # Replace file content
        try:
             # Define a function to write the file in a thread
             async def write_file():
                 with open(self.target_file_path, 'w', encoding='utf-8') as f:
                     f.write(self.undone_commands)

             # Execute file writing in a thread to avoid blocking
             await asyncio.to_thread(write_file)
             log.info(f"Replaced content of {self.target_file_path.name} with undone commands.")
        except Exception as e:
            log.error(f"Failed to write undone commands to {self.target_file_path.name}: {e}", exc_info=True)
            await interaction.followup.send(":x: Failed to save undone commands to file. Cannot proceed.", ephemeral=True)
            return

        # Determine tier again
        user_id = interaction.user.id
        tier = await get_user_tier(user_id, self.uid)

        # Start new execution task for the undone commands
        await self.cog_instance.execute_command_file(interaction, self.target_file_path, tier, self.uid, is_undo=True)

    async def on_timeout(self):
        await self.disable_buttons()
        log.warning(f"UndoConfirmView timed out for file {self.target_file_path.name}")
        # Edit the message
        if self.message:
             try:
                 await self.message.edit(content=f"{self.message.content}\n\n*Undo confirmation timed out.*", view=None)
             except discord.NotFound:
                 log.warning(f"Message not found when timing out UndoConfirmView for {self.target_file_path.name}")
             except Exception as e:
                 log.error(f"Error editing message on UndoConfirmView timeout: {e}")


class CommitResultView(ui.View):
    def __init__(self, cog_instance: 'ExecutorCog', target_file_path: Path, original_content: str, uid: str | None):
        super().__init__(timeout=300.0) # 5 min timeout for undo button
        self.cog_instance = cog_instance
        self.target_file_path = target_file_path
        self.original_content = original_content
        self.uid = uid
        self.message = None

        undo_button = ui.Button(label="Undo", style=ButtonStyle.danger, emoji="↩️", custom_id="undo_execution")
        undo_button.callback = self.undo_callback
        self.add_item(undo_button)

    async def disable_buttons(self):
        for item in self.children: item.disabled = True
        try:
            if self.message: await self.message.edit(view=self)
        except: pass

    async def undo_callback(self, interaction: discord.Interaction):
        """Starts the GPT-based undo process."""
        await self.disable_buttons()
        await interaction.response.defer(thinking=True, ephemeral=True) # Private thinking for GPT part
        log.info(f"User {interaction.user.id} initiated Undo for file {self.target_file_path.name}")

        gpt_instance = None
        try:
            # 1. Init GPT with undo.txt
            undo_prompt = await read_file_content(FILES_DIR / "undo.txt")
            if not undo_prompt or undo_prompt.startswith(":x:"):
                await interaction.followup.send(undo_prompt or ":x: Failed to load undo instructions.", ephemeral=True)
                return

            gpt_instance = await initialize_gpt_session_executor(undo_prompt)

            # 2. Send original file content
            undone_commands = await query_gpt_executor(gpt_instance, self.original_content)

            if not undone_commands or undone_commands.startswith(":x:"):
                await interaction.followup.send(undone_commands or ":x: Failed to generate undo commands from AI.", ephemeral=True)
                return

            log.info(f"Received potential undone commands for {self.target_file_path.name}: {undone_commands[:100]}...")

            # 3. Show proposed commands and Commit Undo button
            # Truncate for display
            display_commands = undone_commands[:1900] + ('...' if len(undone_commands) > 1900 else '')
            content = f"**Proposed Undo Commands:**\n```\n{display_commands}\n```\nClick 'Commit Undo' to replace the file and execute these commands."
            confirm_view = UndoConfirmView(self.cog_instance, undone_commands, self.target_file_path, self.uid)

            # Send new message for confirmation (ephemeral or public?) - let's keep it ephemeral
            msg = await interaction.followup.send(content=content, view=confirm_view, ephemeral=True)
            confirm_view.message = msg # Link view to message

        except Exception as e:
             log.error(f"Error during Undo process for {self.target_file_path.name}: {e}", exc_info=True)
             await interaction.followup.send(":x: An unexpected error occurred during the Undo process.", ephemeral=True)
        finally:
             # Ensure GPT instance is closed
             if gpt_instance: await gpt_instance.close()

    async def on_timeout(self):
        await self.disable_buttons()
        log.warning(f"CommitResultView timed out for file {self.target_file_path.name}")
        if self.message:
            try: await self.message.edit(view=None) # Remove buttons
            except: pass


class CommitSavedSelectView(ui.View):
     def __init__(self, cog_instance: 'ExecutorCog', saved_files_metadata: list[dict]):
        super().__init__(timeout=180.0)
        self.cog_instance = cog_instance
        self.message = None

        if not saved_files_metadata:
            # This should be checked before creating the view, but handle anyway
            self.add_item(ui.Button(label="No saved files found", style=ButtonStyle.secondary, disabled=True))
            return

        options = [
             discord.SelectOption(
                 label=f"{meta.get('file_name', 'Unnamed')[:90]}",
                 value=meta['uid'], # Value is the UID
                 description=f"({meta['uid'][:6]}...) Tier: {meta.get('tier_used', '?')}"
             ) for meta in saved_files_metadata[:25] # Limit options
        ]
        select_menu = ui.Select(
            placeholder="Select a saved file to execute...",
            options=options,
            custom_id="commit_saved_select"
        )
        select_menu.callback = self.select_callback
        self.add_item(select_menu)

     async def select_callback(self, interaction: discord.Interaction):
        """Starts execution for the selected saved file."""
        uid = interaction.data['values'][0]
        user_id = interaction.user.id
        target_file_path = SAVES_DIR / str(user_id) / f"{uid}.txt"

        log.info(f"User {user_id} selected saved file {uid} for commit.")

        # Defer the select interaction before starting long task
        await interaction.response.defer(thinking=True, ephemeral=False) # Public thinking state

        # Get tier from metadata
        tier = await get_user_tier(user_id, uid)

        if not target_file_path.exists():
            log.error(f"Selected file {target_file_path} does not exist despite metadata existing.")
            await interaction.followup.send(f":x: Error: Could not find the content file for `{uid}`.", ephemeral=True)
            return

        # Start execution task
        await self.cog_instance.execute_command_file(interaction, target_file_path, tier, uid)

        # Disable the select menu after starting
        try:
             # We responded with defer, now edit the original message holding the view
             self.children[0].disabled = True # Assuming select is the first child
             await interaction.edit_original_response(view=self)
        except Exception as e:
             log.warning(f"Could not disable CommitSavedSelectView after selection: {e}")

     async def on_timeout(self):
         log.warning(f"CommitSavedSelectView timed out.")
         if self.message:
            for item in self.children: item.disabled = True
            try: await self.message.edit(content="File selection timed out.", view=self)
            except: pass


class CommitSourceView(ui.View):
    def __init__(self, cog_instance: 'ExecutorCog'):
        super().__init__(timeout=180.0)
        self.cog_instance = cog_instance
        self.message = None

        temp_button = ui.Button(label="Temporary File", style=ButtonStyle.secondary, emoji="⏳", custom_id="commit_temp")
        saved_button = ui.Button(label="Saved File", style=ButtonStyle.primary, emoji="💾", custom_id="commit_saved")

        temp_button.callback = self.temp_callback
        saved_button.callback = self.saved_callback

        self.add_item(temp_button)
        self.add_item(saved_button)

    async def disable_buttons(self):
         for item in self.children: item.disabled = True
         try:
             if self.message: await self.message.edit(view=self)
         except: pass

    async def temp_callback(self, interaction: discord.Interaction):
        """Handles commit for the temporary file."""
        await self.disable_buttons()
        user_id = interaction.user.id
        target_file_path = TEMP_DIR / f"{user_id}.txt"
        log.info(f"User {user_id} selected temporary file for commit.")

        await interaction.response.defer(thinking=True, ephemeral=False) # Public thinking state

        if not target_file_path.exists():
            await interaction.followup.send(":warning: No temporary file found to execute.", ephemeral=True)
            return

        # Temp files use default tier
        tier = await get_user_tier(user_id, uid=None) # Should return 'Drifter'

        # Start execution task
        await self.cog_instance.execute_command_file(interaction, target_file_path, tier, uid=None)

    async def saved_callback(self, interaction: discord.Interaction):
        """Handles commit for saved files."""
        await self.disable_buttons()
        user_id = interaction.user.id
        log.info(f"User {user_id} selected saved file option for commit.")
        await interaction.response.defer(ephemeral=True) # Defer ephemerally before showing select

        saved_files_metadata = await get_user_saves_metadata(user_id)

        if not saved_files_metadata:
             await interaction.followup.send("You have no saved files to choose from. Use `/spectre` to create and save one.", ephemeral=True)
             return

        select_view = CommitSavedSelectView(self.cog_instance, saved_files_metadata)
        msg = await interaction.followup.send("Select the saved file you want to execute:", view=select_view, ephemeral=True)
        select_view.message = msg # Link view to message

    async def on_timeout(self):
        log.warning(f"CommitSourceView timed out.")
        await self.disable_buttons()
        if self.message:
             try:
                 await self.message.edit(content="Commit choice timed out.", view=None)
             except discord.NotFound:
                 log.warning("Message not found when timing out CommitSourceView")
             except Exception as e:
                 log.error(f"Error editing message on CommitSourceView timeout: {e}")


# --- Executor Cog Class ---

class ExecutorCog(commands.Cog, name="Executor"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.maintenance_mode = False
        self.random_loading_lines = load_random_lines()
        # Store active execution message IDs maybe? For dynamic updates. user_id: message_id
        self.active_executions = {} # user_id: discord.Message
        # Track sent messages for auto-deletion
        self.sent_messages = [] # List of (message, timestamp) tuples
        # Start the message cleanup task
        self.message_cleanup_task = asyncio.create_task(self.cleanup_old_messages())
        log.info("Executor Cog initialized.")

    # Track when maintenance mode was enabled
    maintenance_start_time = None

    async def check_maintenance(self, interaction: discord.Interaction) -> bool:
        """Checks if maintenance mode is active."""
        if self.maintenance_mode:
            # New commands are rejected immediately
            await interaction.response.send_message(":tools: The Executor module is currently undergoing maintenance. Please try again later.", ephemeral=True)
            return True
        return False

    async def maintenance_timeout_task(self):
        """Task that runs when maintenance mode is enabled to terminate executions after 15 minutes."""
        try:
            await asyncio.sleep(900)  # 15 minutes = 900 seconds

            if not self.maintenance_mode:
                # Maintenance mode was disabled before timeout
                return

            log.info("Maintenance timeout reached. Terminating all active command executions.")
        except asyncio.CancelledError:
            # Task was cancelled, just exit
            log.info("Maintenance timeout task cancelled")
            return
        except Exception as e:
            log.error(f"Error in maintenance timeout task: {e}", exc_info=True)

        # Get a copy of active execution user IDs to avoid modification during iteration
        active_users = list(self.active_executions.keys())

        for user_id in active_users:
            if user_id in self.active_executions:
                try:
                    # Get the message if it exists
                    message = self.active_executions[user_id]
                    if message:
                        try:
                            await message.edit(embed=Embed(
                                title="Execution Terminated",
                                description=":tools: This command execution has been terminated due to scheduled maintenance.",
                                color=Color.red()
                            ), view=None)
                        except Exception as e:
                            log.error(f"Error notifying user {user_id} about maintenance termination: {e}")

                    # Clean up the execution
                    del self.active_executions[user_id]
                    log.info(f"Terminated execution for user {user_id} due to maintenance timeout")
                except Exception as e:
                    log.error(f"Error terminating execution for user {user_id}: {e}")

    async def update_progress(self, message: discord.Message, statuses: dict):
         """Dynamically updates the execution status message."""
         total = statuses['total']
         done = statuses['success'] + statuses['failed'] + statuses['skipped']
         progress = int((done / total) * 10) if total > 0 else 0
         progress_bar = f"[{'#' * progress}{'.' * (10 - progress)}]"

         # symbols = {'success': '✅', 'failed': '❌', 'skipped': '⚠️', 'notice': 'ℹ️'}
         status_line = f"✅ {statuses['success']} | ❌ {statuses['failed']} | ⚠️ {statuses['skipped']}"
         notices = "\n".join([f"> ℹ️ {n}" for n in statuses['notices']])

         loading_line = random.choice(self.random_loading_lines)

         embed = Embed(title="Executing Commands...", color=Color.orange())
         embed.description = f"Processing file: `{statuses['filename']}`\n" \
                             f"Progress: {progress_bar} ({done}/{total})\n" \
                             f"{status_line}\n\n" \
                             f"{notices}\n\n" \
                             f"```{loading_line}```"

         try:
            await message.edit(embed=embed)
         except discord.HTTPException as e:
            if e.code == 50035: # Invalid Form Body (often happens if editing too fast)
                 log.warning("Rate limit or edit conflict likely hit during progress update. Skipping update.")
                 await asyncio.sleep(1) # Short pause
            elif e.code == 10008: # Message not found
                 log.warning(f"Message {message.id} not found during progress update. User may have deleted it.")
                 # No need to continue trying to update this message
                 return False
            else:
                 log.error(f"HTTP error updating progress message: {e.code} - {e.text}")
         except discord.NotFound:
            log.warning(f"Message {message.id} not found during progress update. It may have been deleted.")
            return False
         except Exception as e:
            log.error(f"Error updating progress message: {e}", exc_info=True)

         return True # Successfully updated or recoverable error


    async def execute_command_file(self, interaction: discord.Interaction, target_file_path: Path, tier: str, uid: str | None, is_undo: bool = False):
        """Parses and executes commands from a specified file."""
        user_id = interaction.user.id
        start_time = time.time()
        log.info(f"Starting execution of {'undo' if is_undo else 'commit'} for {target_file_path} by user {user_id} (Tier: {tier})")

        # Send initial status message
        initial_embed = Embed(title="Preparing Execution...", description=f"Reading `{target_file_path.name}`...", color=Color.greyple())
        # Use followup if interaction was deferred, else send new response (should always be deferred)
        status_message = await interaction.followup.send(embed=initial_embed, wait=True) # Send publicly, wait for message object
        self.active_executions[user_id] = status_message # Store message for updates
        # Track message for auto-deletion
        self.track_message(status_message)

        original_content = await read_file_content(target_file_path)
        if original_content is None:
             await status_message.edit(embed=Embed(title="Execution Failed", description=f":x: File not found: `{target_file_path.name}`", color=Color.red()), view=None)
             del self.active_executions[user_id]
             return
        if original_content.startswith(":x:"): # Handle read error
            await status_message.edit(embed=Embed(title="Execution Failed", description=original_content, color=Color.red()), view=None)
            del self.active_executions[user_id]
            return

        # Process the content to handle code blocks with JSON content
        processed_content = []
        in_code_block = False
        code_block_content = []

        # Split by lines to handle code blocks
        for line in original_content.splitlines():
            line = line.strip()
            if not line:
                continue

            # Check for code block start/end (ignore the 'json' word in ```json)
            if line.startswith('```'):
                if in_code_block:
                    # End of code block
                    in_code_block = False

                    # Process the collected code block content
                    block_content = '\n'.join(code_block_content).strip()
                    if block_content:
                        # Just add the content directly as a command
                        processed_content.append(block_content)
                        log.info(f"Processed code block content: {block_content[:50]}...")
                else:
                    # Start of code block - ignore any language marker
                    in_code_block = True
                    code_block_content = []
                continue

            # Collect content if in code block
            if in_code_block:
                code_block_content.append(line)
                continue

            # Handle normal command lines (split by semicolons)
            for cmd in line.split(';'):
                cmd = cmd.strip()
                if cmd:
                    processed_content.append(cmd)

        # Handle any unclosed code block
        if in_code_block and code_block_content:
            block_content = '\n'.join(code_block_content).strip()
            if block_content:
                processed_content.append(block_content)
                log.info(f"Processed unclosed code block: {block_content[:50]}...")

        commands_to_run = processed_content
        if not commands_to_run:
            await status_message.edit(embed=Embed(title="Execution Finished", description=f"File `{target_file_path.name}` is empty or contains no valid commands.", color=Color.green()), view=None)
            del self.active_executions[user_id]
            return

        # Initialize statuses
        statuses = {'total': len(commands_to_run), 'success': 0, 'failed': 0, 'skipped': 0, 'notices': [], 'filename': target_file_path.name}
        last_update_time = time.time()

        # Execution loop
        for i, line in enumerate(commands_to_run):
             command_name, args, parse_error = parse_command_line(line)

             # Update progress before processing
             current_time = time.time()
             if current_time - last_update_time > 1.0 or command_name == "NOTICE": # Update every second or on notice
                 update_success = await self.update_progress(status_message, statuses)
                 if not update_success:
                     # Message was deleted or otherwise can't be updated
                     log.warning(f"Stopping execution for user {user_id} as status message can't be updated")
                     del self.active_executions[user_id]
                     return
                 last_update_time = current_time

             if parse_error:
                 log.warning(f"Parse error on line {i+1} of {target_file_path.name}: {parse_error}")
                 statuses['failed'] += 1
                 statuses['notices'].append(f"Line {i+1}: Parse Error - {parse_error}")
                 continue # Skip to next command

             if not command_name: # Skip empty/comment lines if parser returns None
                 continue

             # Handle NOTICE directly
             if command_name == "NOTICE":
                 notice_msg = args.get("message", "")
                 log.info(f"NOTICE from file {target_file_path.name}: {notice_msg}")
                 statuses['notices'].append(notice_msg)
                 # Update progress immediately after notice is added
                 update_success = await self.update_progress(status_message, statuses)
                 if not update_success:
                     # Message was deleted or otherwise can't be updated
                     log.warning(f"Stopping execution for user {user_id} as status message can't be updated")
                     del self.active_executions[user_id]
                     return
                 last_update_time = time.time()
                 continue # NOTICE isn't counted as success/fail/skip

             # Find command module
             module, command_tier = await get_command_module(command_name)

             if not module:
                 log.warning(f"Command '{command_name}' not found (Line {i+1}, File {target_file_path.name})")
                 statuses['failed'] += 1
                 statuses['notices'].append(f"Line {i+1}: Command '{command_name}' not found.")
                 continue

             # Check tier permission
             if command_tier == 'premium' and tier == 'Drifter':
                 log.warning(f"Skipping premium command '{command_name}' for Drifter tier user {user_id} (Line {i+1}, File {target_file_path.name})")
                 statuses['skipped'] += 1
                 statuses['notices'].append(f"Line {i+1}: Skipped premium command '{command_name}' (Requires Seeker/Abysswalker).")
                 continue

             # Execute command
             try:
                 if hasattr(module, 'execute') and asyncio.iscoroutinefunction(module.execute):
                     # Pass interaction, bot, and args
                     log.info(f"Executing command '{command_name}' with args {args} (Line {i+1}, File {target_file_path.name})")
                     await module.execute(interaction=interaction, bot=self.bot, args=args)
                     statuses['success'] += 1
                     # Add success notice? Maybe too verbose.
                     # statuses['notices'].append(f"Line {i+1}: ✅ {command_name}")
                 else:
                     log.error(f"Command module {module.__name__} does not have a valid async 'execute' function.")
                     statuses['failed'] += 1
                     statuses['notices'].append(f"Line {i+1}: Execution error for '{command_name}' (Invalid command file).")

             except Exception as e:
                 log.error(f"Error executing command '{command_name}' (Line {i+1}, File {target_file_path.name}): {e}", exc_info=True)
                 statuses['failed'] += 1
                 # Get traceback string
                 tb_str = traceback.format_exc().splitlines()[-1] # Get last line of traceback
                 statuses['notices'].append(f"Line {i+1}: ❌ {command_name} failed - {tb_str}")


        # --- Final Status Update ---
        end_time = time.time()
        duration = end_time - start_time
        final_title = f"Execution {'Undo ' if is_undo else ''}Finished"
        final_color = Color.green() if statuses['failed'] == 0 and statuses['skipped'] == 0 else (Color.orange() if statuses['failed'] == 0 else Color.red())

        final_embed = Embed(title=final_title, color=final_color)
        final_status_line = f"✅ {statuses['success']} Succeeded | ❌ {statuses['failed']} Failed | ⚠️ {statuses['skipped']} Skipped"
        final_notices = "\n".join([f"> {('ℹ️' if 'Skipped' not in n and 'failed' not in n else '')} {n}" for n in statuses['notices']])
        final_embed.description = f"File: `{target_file_path.name}`\n" \
                                  f"Took {duration:.2f} seconds.\n\n" \
                                  f"**Summary:** {final_status_line}\n\n" \
                                  f"**Log:**\n{final_notices if final_notices else '*No notices*'}"

        # Add Undo button if it wasn't an undo execution already
        result_view = None
        if not is_undo:
             result_view = CommitResultView(self, target_file_path, original_content, uid)

        await status_message.edit(embed=final_embed, view=result_view)
        if result_view: result_view.message = status_message # Link view to message

        if user_id in self.active_executions:
            del self.active_executions[user_id] # Remove from active tracking
        log.info(f"Execution finished for {target_file_path.name}. Success: {statuses['success']}, Failed: {statuses['failed']}, Skipped: {statuses['skipped']}. Took {duration:.2f}s")


    # --- Commands ---
    @app_commands.command(name="commit", description="Execute a sequence of commands from a temporary or saved file.")
    async def commit(self, interaction: discord.Interaction):
        """Starts the commit process by asking for the file source."""
        if await self.check_maintenance(interaction): return

        # Check if user already has an execution running (prevent parallel commits for same user)
        if interaction.user.id in self.active_executions:
             try:
                 # Check if message still exists
                 await self.active_executions[interaction.user.id].channel.fetch_message(self.active_executions[interaction.user.id].id)
                 await interaction.response.send_message(":warning: You already have a command execution in progress. Please wait for it to complete.", ephemeral=True)
                 return
             except (discord.NotFound, discord.HTTPException):
                 # Message doesn't exist, clear stale entry
                 del self.active_executions[interaction.user.id]
             except Exception as e:
                 log.error(f"Error checking active execution for user {interaction.user.id}: {e}")
                 # Allow proceeding if check fails, but log it


        view = CommitSourceView(self)

        try:
            # Try to respond to the interaction
            message = await interaction.response.send_message("Execute commands from which file?", view=view, ephemeral=True) # Ask privately
            view.message = message # Link view to message
        except discord.NotFound:
            # Interaction has expired/timed out
            log.warning(f"Interaction expired for /commit command from user {interaction.user.id}")
            # We can't respond to this interaction anymore, so we'll just log it
            return
        except Exception as e:
            # Log any other errors
            log.error(f"Error responding to /commit command from user {interaction.user.id}: {e}")
            return


    @commands.is_owner()
    @commands.command(name="executormaintenance", aliases=['emaint'])
    async def executor_maintenance(self, ctx: commands.Context):
        """Toggles maintenance mode for the Executor cog (Owner Only)."""
        self.maintenance_mode = not self.maintenance_mode
        status = "ENABLED" if self.maintenance_mode else "DISABLED"

        if self.maintenance_mode:
            # Start the maintenance timeout task
            self.maintenance_start_time = time.time()
            asyncio.create_task(self.maintenance_timeout_task())
            active_executions = len(self.active_executions)
            message = await ctx.send(f":tools: Executor Cog maintenance mode is now **{status}**. {active_executions} active executions will be terminated in 15 minutes.")
            # Track message for auto-deletion
            self.track_message(message)
        else:
            # Maintenance mode disabled
            self.maintenance_start_time = None
            message = await ctx.send(f":tools: Executor Cog maintenance mode is now **{status}**. New command executions are now allowed.")
            # Track message for auto-deletion
            self.track_message(message)

        log.info(f"Executor maintenance mode set to {status} by {ctx.author}")

    async def cog_load(self):
        """Called when the cog is loaded."""
        log.info(f"ExecutorCog loaded")

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
        log.info(f"ExecutorCog unloaded")

# --- Setup Function ---
async def setup(bot: commands.Bot):
    # Ensure command directories exist
    FREE_COMMANDS_DIR.mkdir(parents=True, exist_ok=True)
    PREMIUM_COMMANDS_DIR.mkdir(parents=True, exist_ok=True)
    # Create dummy command files if they don't exist for testing
    if not (FREE_COMMANDS_DIR / "notice_command.py").exists():
        # Create the notice_command.py file directly without using asyncio.to_thread
        with open(FREE_COMMANDS_DIR / "notice_command.py", 'w') as f:
            f.write("# commands/free/notice_command.py\nasync def execute(interaction, bot, args):\n  pass # Handled in main loop")
    if not (PREMIUM_COMMANDS_DIR / "channel_create_command.py").exists():
        # Create the channel_create_command.py file directly without using asyncio.to_thread
        with open(PREMIUM_COMMANDS_DIR / "channel_create_command.py", 'w') as f:
            f.write("# commands/premium/channel_create_command.py\nimport discord\nasync def execute(interaction, bot, args):\n  name=args.get('name','new-channel')\n  print(f'Simulating channel create: {name}')\n  # await interaction.guild.create_text_channel(name=name)\n")

    await bot.add_cog(ExecutorCog(bot))