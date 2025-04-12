# cogs/spectre.py

import discord
from discord.ext import commands
from discord import app_commands, ui, ButtonStyle, TextStyle
import asyncio
import random
import json
import uuid
import time
from pathlib import Path
import logging
import sys
import warnings

# Filter out curl_cffi warnings globally
warnings.filterwarnings("ignore", message="Curlm already closed! quitting from process_data")
warnings.filterwarnings("ignore", category=UserWarning, module="curl_cffi")

# Add parent directory to path for imports
BASE_DIR = Path(__file__).parent.parent # Project root directory
sys.path.append(str(BASE_DIR))

# Import config manager
from utils.config_manager import config

# Define paths
FILES_DIR = BASE_DIR
TEMP_DIR = BASE_DIR / "temp"
SAVES_DIR = BASE_DIR / "saves"

# Get file paths from config
RANDOM_TXT_PATH = FILES_DIR / config.get("spectre.loading_messages_file", "random.txt")

# Get tier limits from config
TIER_LIMITS = config.get_all_tiers()

# Logger for this cog
log = logging.getLogger('MyBot.SpectreCog')

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

def load_random_lines() -> list[str]:
    """Loads lines from random.txt."""
    try:
        with open(RANDOM_TXT_PATH, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip()]
        if not lines:
             log.warning(f"{RANDOM_TXT_PATH} is empty or contains only whitespace.")
             return ["Loading..."]
        return lines
    except FileNotFoundError:
        log.error(f"File not found: {RANDOM_TXT_PATH}. Using default loading message.")
        return ["Loading..."]
    except Exception as e:
        log.error(f"Error reading {RANDOM_TXT_PATH}: {e}")
        return ["Loading error..."]

def truncate_message(content: str, max_length: int = 1900) -> str:
    """Truncates a message to fit within Discord's character limit."""
    if len(content) <= max_length:
        return content

    # If we need to truncate, add an ellipsis to indicate truncation
    return content[:max_length] + "..."

def truncate_code_block(code: str, max_length: int = 1800) -> str:
    """Truncates code within a code block to fit within Discord's character limit."""
    if len(code) <= max_length:
        return f"```\n{code}\n```"

    # If we need to truncate, add an ellipsis to indicate truncation
    return f"```\n{code[:max_length]}...\n```"

async def safe_send_message(interaction: discord.Interaction, content: str, ephemeral: bool = True, delete_after: int = None):
    """Safely sends a message, handling the case where the interaction has expired."""
    try:
        # Try to use followup first
        await interaction.followup.send(content, ephemeral=ephemeral, delete_after=delete_after)
    except discord.errors.NotFound:
        # If the interaction has expired, try to send a message to the channel
        try:
            if interaction.channel:
                await interaction.channel.send(
                    f"{interaction.user.mention} {content}",
                    delete_after=30 if delete_after is None else delete_after
                )
        except Exception as e:
            log.error(f"Failed to send message after interaction expired: {e}")

# --- GPT Integration using g4f ---
from g4f.client import Client

class GPTInstance:
    """ Real GPT instance using g4f client. """
    def __init__(self, initial_prompt: str):
        self.client = Client()
        self.history = [{"role": "system", "content": initial_prompt}]
        self.timeout = config.get("spectre.timeout", 30)  # Default timeout of 30 seconds (reduced from 60)
        log.info(f"GPT initialized with prompt: {initial_prompt[:50]}...")

    async def close(self):
        """Close the GPT instance and clean up resources."""
        # Suppress any warnings during cleanup
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore")
            # Clear the history to help with garbage collection
            if hasattr(self, 'history'):
                self.history.clear()
            # Set client to None to help with garbage collection
            if hasattr(self, 'client'):
                self.client = None
        log.info("GPT instance closed")

    async def query(self, user_prompt: str) -> str:
        """ Sends a query to the GPT model. """
        log.info(f"GPT received query: {user_prompt[:50]}...")

        # Add user message to history
        self.history.append({"role": "user", "content": user_prompt})

        # Filter out curl_cffi warnings
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message="Curlm already closed! quitting from process_data")
            warnings.filterwarnings("ignore", category=UserWarning)

        # Create a task for the request that we can cancel if needed
        request_task = None

        try:
            # Make API call to g4f using the exact implementation provided
            async def _make_request():
                try:
                    # Use the existing client instance instead of creating a new one each time
                    # Note: g4f doesn't support parameters like temperature, tokens, etc.
                    # Only model and messages are passed, and even model might be ignored
                    response = self.client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=self.history
                    )
                    return response
                except Exception as e:
                    log.error(f"Error in _make_request: {e}")
                    raise

            # Create a task for the request
            request_task = asyncio.create_task(_make_request())

            # Execute with timeout
            response = await asyncio.wait_for(request_task, timeout=self.timeout)

            # Extract response content
            response_content = response.choices[0].message.content

            # Add assistant response to history
            self.history.append({"role": "assistant", "content": response_content})

            log.info(f"GPT generated response: {response_content[:50]}...")
            return response_content

        except asyncio.TimeoutError:
            # Cancel the task if it's still running
            if request_task and not request_task.done():
                request_task.cancel()
                log.warning(f"Cancelled stuck GPT request after {self.timeout} seconds")

            log.error(f"Timeout error in GPT query after {self.timeout} seconds")
            return f":x: The AI model took too long to respond. Please try again with a simpler query or try later."
        except Exception as e:
            # Cancel the task if it's still running
            if request_task and not request_task.done():
                request_task.cancel()
                log.warning("Cancelled GPT request due to error")

            log.error(f"Error in GPT query: {e}", exc_info=True)
            return f":x: Error communicating with the AI model: {str(e)}. Please try again later."

    # The close() method is already defined above

async def initialize_gpt_session(instructor_prompt: str) -> GPTInstance:
    """Initializes a GPT session using g4f."""
    return GPTInstance(initial_prompt=instructor_prompt)

async def query_gpt(gpt_instance: GPTInstance, prompt: str) -> str | None:
    """Sends a query to an existing GPT session with retry logic.

    Args:
        gpt_instance: The GPT instance to query
        prompt: The prompt to send to the GPT model

    Returns:
        The response from the GPT model, or an error message starting with ':x:'
    """
    if not gpt_instance:
        log.error("Attempted to query GPT with None instance")
        return ":x: Internal error: GPT instance not initialized."

    if not prompt or not prompt.strip():
        log.warning("Attempted to query GPT with empty prompt")
        return ":x: Cannot process empty prompt."

    max_retries = 2
    retry_count = 0
    backoff_time = 2  # Start with 2 seconds

    while retry_count <= max_retries:
        try:
            # Send the query to the GPT model
            response = await gpt_instance.query(prompt)

            # Check if response is empty or too short
            if not response or len(response.strip()) < 5:
                log.warning(f"GPT returned very short response: '{response}'")
                if retry_count < max_retries:
                    retry_count += 1
                    log.warning(f"Retrying due to short response (attempt {retry_count}/{max_retries})")
                    await asyncio.sleep(backoff_time)
                    backoff_time *= 2  # Exponential backoff
                    continue
                else:
                    return ":x: The AI model returned an unusually short response. Please try again."

            return response
        except asyncio.TimeoutError:
            retry_count += 1
            if retry_count <= max_retries:
                log.warning(f"Timeout querying GPT (attempt {retry_count}/{max_retries}). Retrying...")
                await asyncio.sleep(backoff_time)
                backoff_time *= 2  # Exponential backoff
            else:
                log.error(f"Timeout querying GPT after {max_retries} retries")
                return f":x: The AI model took too long to respond. Please try again with a simpler query or try later."
        except Exception as e:
            retry_count += 1
            if retry_count <= max_retries:
                log.warning(f"Error querying GPT (attempt {retry_count}/{max_retries}): {e}. Retrying...")
                await asyncio.sleep(backoff_time)
                backoff_time *= 2  # Exponential backoff
            else:
                log.error(f"Error querying GPT after {max_retries} retries: {e}", exc_info=True)
                return f":x: Error communicating with the AI model: {str(e)}. Please try again later."
# --- End Placeholder ---


# --- Views and Modals ---

class PromptModal(ui.Modal):
    def __init__(self, title: str, session_data: dict, interaction_view: 'InteractionView'):
        super().__init__(title=title, timeout=300.0) # 5 min timeout for modal input
        self.session_data = session_data
        self.interaction_view = interaction_view
        self.cog_instance = interaction_view.cog_instance # Get cog instance

        self.prompt_input = ui.TextInput(
            label="Your Prompt",
            style=TextStyle.paragraph,
            placeholder="Enter your instructions or follow-up here...",
            required=True,
            max_length=1500,
        )
        self.add_item(self.prompt_input)

    async def on_submit(self, interaction: discord.Interaction):
        """Process the submitted prompt."""
        # Store important information before deferring in case the interaction times out
        user_id = interaction.user.id
        prompt = self.prompt_input.value
        channel = interaction.channel
        user = interaction.user
        interaction_valid = True  # Default to valid interaction

        # Try to defer the response, but handle the case where the interaction has expired
        try:
            await interaction.response.defer(thinking=True, ephemeral=False) # Show loading state publicly
        except discord.errors.NotFound as e:
            # Interaction token has expired (error 10062: Unknown interaction)
            log.warning(f"Interaction expired for user {user_id} before deferring. Error: {e}")
            interaction_valid = False

        # --- Get Focused Server Structure Info ---
        server_info = ""
        if interaction.guild:
            guild = interaction.guild
            server_info = f"\n\n=== SERVER STRUCTURE ===\n"

            # Basic Server Information
            server_info += f"Server Name: {guild.name}\n"
            server_info += f"Total Members: {guild.member_count}\n"

            # Role Hierarchy (focused on position and permissions)
            server_info += f"\n--- ROLES ---\n"
            for role in sorted(guild.roles, key=lambda r: r.position, reverse=True):
                server_info += f"Role: {role.name} (Position: {role.position})\n"
                # Only include key permissions that affect channel access
                key_perms = []
                if role.permissions.administrator:
                    key_perms.append("administrator")
                if role.permissions.manage_channels:
                    key_perms.append("manage_channels")
                if role.permissions.manage_roles:
                    key_perms.append("manage_roles")
                if role.permissions.manage_guild:
                    key_perms.append("manage_guild")
                if role.permissions.view_channel:
                    key_perms.append("view_channel")
                if role.permissions.send_messages:
                    key_perms.append("send_messages")
                if role.permissions.connect:
                    key_perms.append("connect")
                if role.permissions.speak:
                    key_perms.append("speak")

                if key_perms:
                    server_info += f"  Key Permissions: {', '.join(key_perms)}\n"

            # Channel Structure (focused on hierarchy and permissions)
            server_info += f"\n--- CHANNEL STRUCTURE ---\n"

            # First list channels without categories
            no_category_channels = [c for c in guild.channels if not c.category]
            if no_category_channels:
                server_info += "Channels without category:\n"
                for channel in sorted(no_category_channels, key=lambda c: c.position):
                    server_info += f"Channel: {channel.name} (Type: {channel.type}, Position: {channel.position})\n"

                    # Only include permission overwrites for roles (not individual members)
                    if hasattr(channel, 'overwrites') and channel.overwrites:
                        role_overwrites = {target: overwrite for target, overwrite in channel.overwrites.items()
                                          if hasattr(target, "members")}
                        if role_overwrites:
                            server_info += f"  Role Access:\n"
                            for role, overwrite in role_overwrites.items():
                                # Focus on view/access permissions
                                access_info = []

                                # Check for view_channel permission
                                if any(perm[0] == 'view_channel' and perm[1] for perm in overwrite.allow):
                                    access_info.append("can view")
                                elif any(perm[0] == 'view_channel' and perm[1] for perm in overwrite.deny):
                                    access_info.append("cannot view")

                                # Check for send_messages permission for text channels
                                if hasattr(channel, 'type') and str(channel.type) == 'text':
                                    if any(perm[0] == 'send_messages' and perm[1] for perm in overwrite.allow):
                                        access_info.append("can send messages")
                                    elif any(perm[0] == 'send_messages' and perm[1] for perm in overwrite.deny):
                                        access_info.append("cannot send messages")

                                # Check for connect permission for voice channels
                                if hasattr(channel, 'type') and str(channel.type) == 'voice':
                                    if any(perm[0] == 'connect' and perm[1] for perm in overwrite.allow):
                                        access_info.append("can connect")
                                    elif any(perm[0] == 'connect' and perm[1] for perm in overwrite.deny):
                                        access_info.append("cannot connect")

                                if access_info:
                                    server_info += f"    {role.name}: {', '.join(access_info)}\n"

            # Now list categories and their channels
            categories = {cat: [] for cat in guild.categories}

            # Group channels by category
            for channel in guild.channels:
                if channel.category and channel.category in categories:
                    categories[channel.category].append(channel)

            # Add categorized channels with focused information
            for category, channels in categories.items():
                server_info += f"Category: {category.name} (Position: {category.position})\n"

                # Category role access
                if hasattr(category, 'overwrites') and category.overwrites:
                    role_overwrites = {target: overwrite for target, overwrite in category.overwrites.items()
                                      if hasattr(target, "members")}
                    if role_overwrites:
                        server_info += f"  Category Role Access:\n"
                        for role, overwrite in role_overwrites.items():
                            # Focus on view permission
                            if any(perm[0] == 'view_channel' and perm[1] for perm in overwrite.allow):
                                server_info += f"    {role.name}: can view all channels\n"
                            elif any(perm[0] == 'view_channel' and perm[1] for perm in overwrite.deny):
                                server_info += f"    {role.name}: cannot view channels\n"

                # Channels in this category
                for channel in sorted(channels, key=lambda c: c.position):
                    server_info += f"  Channel: {channel.name} (Type: {channel.type}, Position: {channel.position})\n"

                    # Only include permission overwrites that differ from category
                    if hasattr(channel, 'overwrites') and channel.overwrites:
                        role_overwrites = {target: overwrite for target, overwrite in channel.overwrites.items()
                                          if hasattr(target, "members")}
                        if role_overwrites:
                            server_info += f"    Channel-specific Role Access:\n"
                            for role, overwrite in role_overwrites.items():
                                # Focus on view/access permissions
                                access_info = []

                                # Check for view_channel permission
                                if any(perm[0] == 'view_channel' and perm[1] for perm in overwrite.allow):
                                    access_info.append("can view")
                                elif any(perm[0] == 'view_channel' and perm[1] for perm in overwrite.deny):
                                    access_info.append("cannot view")

                                # Check for send_messages permission for text channels
                                if hasattr(channel, 'type') and str(channel.type) == 'text':
                                    if any(perm[0] == 'send_messages' and perm[1] for perm in overwrite.allow):
                                        access_info.append("can send messages")
                                    elif any(perm[0] == 'send_messages' and perm[1] for perm in overwrite.deny):
                                        access_info.append("cannot send messages")

                                # Check for connect permission for voice channels
                                if hasattr(channel, 'type') and str(channel.type) == 'voice':
                                    if any(perm[0] == 'connect' and perm[1] for perm in overwrite.allow):
                                        access_info.append("can connect")
                                    elif any(perm[0] == 'connect' and perm[1] for perm in overwrite.deny):
                                        access_info.append("cannot connect")

                                if access_info:
                                    server_info += f"      {role.name}: {', '.join(access_info)}\n"

            # Current interaction context
            server_info += f"\n--- CURRENT CONTEXT ---\n"
            server_info += f"Current Channel: {interaction.channel.name} (Type: {interaction.channel.type})\n"

            # User's roles (just names, no details)
            if interaction.user and hasattr(interaction.user, 'roles'):
                member = interaction.user
                user_roles = [role.name for role in member.roles if role.name != '@everyone']
                if user_roles:
                    server_info += f"User Roles: {', '.join(user_roles)}\n"

        # --- Query GPT ---
        # Add server info to prompt if enabled in config
        include_server_info = config.get("spectre.include_server_info", True)  # Default to True now
        full_prompt = prompt + server_info if include_server_info else prompt
        gpt_response = await query_gpt(self.session_data['gpt_instance'], full_prompt)

        if not gpt_response or gpt_response.startswith(":x:"):
            error_message = gpt_response or ":x: Failed to get response from AI."

            if interaction_valid:
                # If the interaction is still valid, use followup
                await interaction.followup.send(error_message, ephemeral=True)
            else:
                # If interaction expired, send a new message mentioning the user
                try:
                    await channel.send(f"{user.mention} {error_message}", delete_after=30)
                except Exception as e:
                    log.error(f"Failed to send error message to channel for user {user_id}: {e}")
            # Don't end the session here, allow user to retry or retreat
            return

        # --- Update Session State ---
        self.session_data['last_gpt_reply'] = gpt_response
        if TIER_LIMITS[self.session_data['tier']]['replies'] != -1: # Check if not unlimited
            self.session_data['replies_left'] -= 1

        replies_left = self.session_data['replies_left']
        tier_limit = TIER_LIMITS[self.session_data['tier']]['replies']
        reply_info = f"Replies left: {replies_left}/{tier_limit}" if tier_limit != -1 else "Replies left: Unlimited"

        # --- Display Response & Buttons ---
        # Edit the original interaction message if possible, or send new one
        # Use the truncate_code_block function to ensure the response fits within Discord's character limit
        response_block = truncate_code_block(gpt_response, 1800)
        content = truncate_message(f"**AI Response:**\n{response_block}\n\n{reply_info}", 1900)

        # Re-enable Whisper button only if replies are left
        self.interaction_view.whisper_button.disabled = (replies_left == 0 and tier_limit != -1)

        # No need to create a new interaction view here, we already have it from initialization

        try:
            if interaction_valid:
                # If interaction is still valid, use the normal flow
                if self.interaction_view.message is None:
                    # If the message attribute is not set, send a new message
                    message = await interaction.followup.send(content=content, view=self.interaction_view)
                    self.interaction_view.message = message
                    # Update the session data with the new message
                    self.session_data['interaction_message'] = message
                    log.info(f"Created new message for InteractionView for user {user_id}")
                else:
                    # Edit the existing message
                    await self.interaction_view.message.edit(content=content, view=self.interaction_view)
                    # Send an empty followup to dismiss the "thinking" state from the modal submission
                    await interaction.followup.send("Response generated.", ephemeral=True)
                    await asyncio.sleep(2) # Give user time to read
                    await interaction.delete_original_response() # Delete the ephemeral confirmation
            else:
                # If interaction expired, send a new message to the channel
                message = await channel.send(content=f"{user.mention}\n{content}", view=self.interaction_view)
                self.interaction_view.message = message
                # Update the session data with the new message
                self.session_data['interaction_message'] = message
                log.info(f"Created new message for InteractionView for user {user_id} after interaction expired")

        except discord.NotFound:
             log.warning(f"Original interaction message not found for user {user_id}. Sending new message.")
             # Send a new message if the original was deleted
             self.interaction_view.message = await interaction.channel.send(content=content, view=self.interaction_view)
             await interaction.followup.send("Response generated below.", ephemeral=True)
        except Exception as e:
             log.error(f"Error updating interaction message for user {user_id}: {e}", exc_info=True)
             await interaction.followup.send(":warning: Error updating message display.", ephemeral=True)


    async def on_error(self, interaction: discord.Interaction, error: Exception):
        log.error(f"Error in PromptModal for user {interaction.user.id}: {error}", exc_info=True)

        # Try to send an error message, but handle the case where the interaction has expired
        try:
            # Try to use followup first
            await interaction.followup.send(":x: An error occurred processing your prompt.", ephemeral=True)
        except discord.errors.NotFound:
            # If the interaction has expired, try to send a message to the channel
            try:
                if interaction.channel:
                    await interaction.channel.send(
                        f"{interaction.user.mention} :x: An error occurred processing your prompt. Please try again.",
                        delete_after=30
                    )
            except Exception as e:
                log.error(f"Failed to send error message after interaction expired: {e}")


class MetadataModal(ui.Modal, title="Save File Metadata"):
    def __init__(self, cog_instance: 'SpectreCog', user_id: int, uid: str, gpt_response: str, tier: str):
        super().__init__(timeout=300.0)
        self.cog_instance = cog_instance
        self.user_id = user_id
        self.uid = uid
        self.gpt_response = gpt_response # Final GPT response for the file content
        self.tier = tier

        self.file_name_input = ui.TextInput(
            label="File Name",
            placeholder="Enter a short, descriptive name for this save",
            required=True,
            max_length=50,
            style=TextStyle.short,
        )
        self.description_input = ui.TextInput(
            label="Description",
            placeholder="Describe the purpose or content of this file (optional)",
            required=False,
            max_length=200,
            style=TextStyle.paragraph,
        )
        self.add_item(self.file_name_input)
        self.add_item(self.description_input)

    async def on_submit(self, interaction: discord.Interaction):
        """Saves metadata and file content."""
        # Store important information before deferring in case the interaction times out
        file_name = self.file_name_input.value
        description = self.description_input.value
        user_saves_dir = SAVES_DIR / str(self.user_id)
        user_saves_dir.mkdir(parents=True, exist_ok=True) # Ensure directory exists

        # Try to defer the response, but handle the case where the interaction has expired
        try:
            await interaction.response.defer(thinking=True, ephemeral=True) # Private thinking
        except discord.errors.NotFound as e:
            # Interaction token has expired (error 10062: Unknown interaction)
            log.warning(f"Interaction expired for user {self.user_id} before deferring in MetadataModal. Error: {e}")
            # Continue with the save process even if the interaction expired
            # We'll handle the response differently at the end

        # --- Refinement Step with forever1.txt ---
        log.info(f"Starting refinement step for UID {self.uid} (User: {self.user_id})")
        refinement_gpt_instance = None
        final_content = self.gpt_response # Start with the already refined content
        try:
            forever1_prompt = await read_file_content(FILES_DIR / "forever1.txt")
            if forever1_prompt and not forever1_prompt.startswith(":"): # Check for read errors
                # Initialize a *new* GPT instance for this step
                refinement_gpt_instance = await initialize_gpt_session(forever1_prompt)
                # Send the content refined by 'forever.txt' to this new instance
                refined_content_step2 = await query_gpt(refinement_gpt_instance, self.gpt_response)

                if refined_content_step2 and not refined_content_step2.startswith(":x:"):
                    final_content = refined_content_step2 # Use the doubly refined content
                    log.info(f"Successfully refined content with forever1.txt for UID {self.uid}")
                else:
                     log.warning(f"Failed to get refinement from forever1.txt for UID {self.uid}. Using previous version.")
            else:
                 log.warning(f"Could not read or invalid content in forever1.txt. Skipping final refinement.")

        except Exception as e:
            log.error(f"Error during forever1.txt refinement for UID {self.uid}: {e}", exc_info=True)
            # Use the content refined by forever.txt as fallback
        finally:
            if refinement_gpt_instance:
                 # Ensure cleanup of the temporary GPT instance
                 await refinement_gpt_instance.close()

        # --- Save Final Content ---
        file_path = user_saves_dir / f"{self.uid}.txt"
        try:
            # Define a regular (non-async) function to write the file in a thread
            def write_file():
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(final_content)

            # Execute file writing in a thread to avoid blocking
            await asyncio.to_thread(write_file)
            log.info(f"Saved final content to {file_path}")
        except Exception as e:
            log.error(f"Failed to save final content to {file_path}: {e}", exc_info=True)
            await interaction.followup.send(f":x: Critical error saving file content for `{file_name}`.", ephemeral=True)
            # Don't proceed with metadata if file save failed
            await self.cog_instance.cleanup_session(self.user_id)
            return

        # --- Save Metadata ---
        metadata_path = user_saves_dir / f"{self.uid}.json"
        metadata = {
            "file_name": file_name,
            "description": description,
            "saves": 0, # Start count at 0 as clarified
            "tier_used": self.tier,
            "date_created": time.time(), # Store as Unix timestamp
            "uid": self.uid # Include UID for easier reference
        }
        try:
            # Define a regular (non-async) function to write the metadata file in a thread
            def write_metadata():
                with open(metadata_path, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, indent=4)

            # Execute metadata writing in a thread to avoid blocking
            await asyncio.to_thread(write_metadata)
            log.info(f"Saved metadata to {metadata_path}")
        except Exception as e:
            log.error(f"Failed to save metadata to {metadata_path}: {e}", exc_info=True)
            await interaction.followup.send(f":x: Error saving metadata for `{file_name}`, but content was saved.", ephemeral=True)
            # Content saved, but metadata failed. Still cleanup.
            await self.cog_instance.cleanup_session(self.user_id)
            return

        # --- Decrement Save Count & Finalize ---
        # Decrement save count in the main session data
        if TIER_LIMITS[self.tier]['saves'] != -1:
            self.cog_instance.active_sessions[self.user_id]['saves_left'] -= 1

        await interaction.followup.send(
            f":white_check_mark: Successfully saved '{file_name}' (`{self.uid}`).\n"
            f"You can access it later using `/vault` or `/commit`.",
            ephemeral=True
        )
        log.info(f"User {self.user_id} permanently saved file {self.uid} ('{file_name}') using tier {self.tier}")

        # Apply cooldown and cleanup session
        await self.cog_instance.apply_cooldown(interaction)
        await self.cog_instance.cleanup_session(self.user_id, interaction) # Pass interaction to edit original message

    async def on_error(self, interaction: discord.Interaction, error: Exception):
        log.error(f"Error in MetadataModal for user {interaction.user.id}: {error}", exc_info=True)

        # Try to send an error message, but handle the case where the interaction has expired
        try:
            # Try to use followup first
            await interaction.followup.send(":x: An error occurred saving the file metadata.", ephemeral=True)
        except discord.errors.NotFound:
            # If the interaction has expired, try to send a message to the channel
            try:
                if interaction.channel:
                    await interaction.channel.send(
                        f"{interaction.user.mention} :x: An error occurred saving the file metadata. Please try again.",
                        delete_after=30
                    )
            except Exception as e:
                log.error(f"Failed to send error message after interaction expired: {e}")


class SubmitChoiceView(ui.View):
    def __init__(self, cog_instance: 'SpectreCog', session_data: dict, user_id: int, gpt_response: str = None):
        super().__init__(timeout=180.0) # 3 min timeout for choice
        self.cog_instance = cog_instance
        self.session_data = session_data
        self.user_id = user_id
        self.gpt_response = gpt_response
        self.message = None # Will be set after sending

    async def disable_buttons(self):
        """Disables all buttons on this view."""
        for item in self.children:
            if isinstance(item, ui.Button):
                item.disabled = True
        try:
            if self.message:
                await self.message.edit(view=self)
        except discord.NotFound:
            pass # Ignore if message was deleted
        except Exception as e:
             log.error(f"Error disabling buttons on SubmitChoiceView: {e}")

    @ui.button(label="Temporary", style=ButtonStyle.secondary, emoji="⏳")
    async def temporary_button(self, interaction: discord.Interaction, button: ui.Button):
        """Handles temporary save."""
        user_id = interaction.user.id

        # Disable the button to prevent multiple clicks
        button.disabled = True

        try:
            await interaction.response.defer(thinking=True, ephemeral=True) # Private thinking
        except discord.InteractionResponded:
            # If the interaction has already been responded to, just continue
            log.warning(f"Interaction already responded to for user {user_id} in temporary_button")
        except Exception as e:
            log.error(f"Error deferring interaction for user {user_id}: {e}", exc_info=True)

        await self.disable_buttons() # Disable buttons after click

        gpt_instance = self.session_data['gpt_instance']
        last_reply = self.session_data.get('last_gpt_reply', None)

        if not last_reply:
            try:
                await interaction.followup.send(":x: No AI response found to save.", ephemeral=True)
            except Exception as e:
                log.error(f"Error sending followup message for user {user_id}: {e}", exc_info=True)
            await self.cog_instance.cleanup_session(user_id) # Cleanup needed
            return

        log.info(f"User {user_id} chose temporary save.")

        # --- Refine with temp.txt ---
        final_content = last_reply # Start with last reply
        try:
            temp_prompt = await read_file_content(FILES_DIR / "temp.txt")
            if temp_prompt and not temp_prompt.startswith(":"):
                refined_content = await query_gpt(gpt_instance, temp_prompt)
                if refined_content and not refined_content.startswith(":x:"):
                    final_content = refined_content
                    log.info(f"Refined temporary content for user {user_id} using temp.txt")
                else:
                    log.warning(f"Failed to refine temporary content for user {user_id}. Using last reply.")
            else:
                 log.warning(f"Could not read or invalid content in temp.txt for user {user_id}.")
        except Exception as e:
             log.error(f"Error during temp.txt refinement for user {user_id}: {e}", exc_info=True)

        # --- Save to temp file ---
        temp_file_path = TEMP_DIR / f"{user_id}.txt"
        try:
            TEMP_DIR.mkdir(exist_ok=True) # Ensure temp dir exists
            # Define a regular (non-async) function to write the file in a thread
            def write_temp_file():
                with open(temp_file_path, 'w', encoding='utf-8') as f:
                    f.write(final_content)

            # Execute file writing in a thread to avoid blocking
            await asyncio.to_thread(write_temp_file)
            log.info(f"Saved temporary file for user {user_id} to {temp_file_path}")
            await interaction.followup.send(
                f":white_check_mark: Saved output temporarily. You can execute it using `/commit` (select Temporary File).",
                ephemeral=True
            ) #
        except Exception as e:
            log.error(f"Failed to save temporary file {temp_file_path}: {e}", exc_info=True)
            await interaction.followup.send(":x: Failed to save temporary file.", ephemeral=True)

        # --- Finalize ---
        await self.cog_instance.apply_cooldown(interaction)
        await self.cog_instance.cleanup_session(user_id, interaction) # Edit original message here

    @ui.button(label="Forever", style=ButtonStyle.primary, emoji="💾")
    async def forever_button(self, interaction: discord.Interaction, button: ui.Button):
        """Handles permanent save."""
        user_id = interaction.user.id

        # Disable the button to prevent multiple clicks
        button.disabled = True

        try:
            await interaction.response.defer(thinking=True, ephemeral=True) # Private thinking
        except discord.InteractionResponded:
            # If the interaction has already been responded to, just continue
            log.warning(f"Interaction already responded to for user {user_id} in forever_button")
        except Exception as e:
            log.error(f"Error deferring interaction for user {user_id}: {e}", exc_info=True)

        await self.disable_buttons() # Disable all buttons after click

        tier = self.session_data['tier']
        saves_left = self.session_data['saves_left']

        # --- Check Save Limit ---
        if TIER_LIMITS[tier]['saves'] != -1 and saves_left <= 0:
            await interaction.followup.send(f":x: You have reached your save limit ({TIER_LIMITS[tier]['saves']}) for this session/tier.", ephemeral=True)
            # Don't clean up session here, let user Retreat or Whisper if possible
            # Re-enable the original InteractionView buttons maybe? Or just leave disabled. Leaving disabled for now.
            return
        else:
             log.info(f"User {user_id} chose permanent save. Saves left: {saves_left}/{TIER_LIMITS[tier]['saves']}")


        gpt_instance = self.session_data['gpt_instance']
        last_reply = self.session_data.get('last_gpt_reply', None)

        if not last_reply:
            await interaction.followup.send(":x: No AI response found to save.", ephemeral=True)
            await self.cog_instance.cleanup_session(user_id)
            return

        # --- Refine with forever.txt ---
        refined_content = last_reply # Start with the last AI reply
        try:
            forever_prompt = await read_file_content(FILES_DIR / "forever.txt")
            if forever_prompt and not forever_prompt.startswith(":"):
                refined_content_step1 = await query_gpt(gpt_instance, forever_prompt)
                if refined_content_step1 and not refined_content_step1.startswith(":x:"):
                    refined_content = refined_content_step1
                    log.info(f"Refined permanent content for user {user_id} using forever.txt")
                else:
                    log.warning(f"Failed to refine permanent content for user {user_id}. Using last reply.")
            else:
                 log.warning(f"Could not read or invalid content in forever.txt for user {user_id}.")

        except Exception as e:
             log.error(f"Error during forever.txt refinement for user {user_id}: {e}", exc_info=True)


        # --- Save Initial Content & Get Metadata ---
        # We need to save the *first* refined content temporarily before the second refinement
        # The second refinement happens *after* metadata modal submission

        uid = str(uuid.uuid4())
        user_saves_dir = SAVES_DIR / str(user_id)
        user_saves_dir.mkdir(parents=True, exist_ok=True)
        initial_save_path = user_saves_dir / f"{uid}.txt"

        try:
             # Define a regular (non-async) function to write the file in a thread
             def write_file():
                 with open(initial_save_path, 'w', encoding='utf-8') as f:
                     f.write(refined_content)

             # Execute file writing in a thread to avoid blocking
             await asyncio.to_thread(write_file)
             log.info(f"Saved initial permanent content for UID {uid} to {initial_save_path}")

             # Create a new interaction for the modal since we already deferred this one
             # We need to inform the user about what's happening
             await interaction.followup.send("Preparing permanent save. Please provide file details in the popup window.", ephemeral=True)

             # Create the metadata modal
             modal = MetadataModal(self.cog_instance, user_id, uid, refined_content, tier)

             # We can't use send_modal on a deferred interaction, so we'll create a new button for the user to click
             # that will open the modal
             metadata_view = ui.View(timeout=60)
             metadata_button = ui.Button(label="Enter File Details", style=ButtonStyle.primary, emoji="📝")

             async def metadata_button_callback(btn_interaction):
                 await btn_interaction.response.send_modal(modal)

             metadata_button.callback = metadata_button_callback
             metadata_view.add_item(metadata_button)

             # Send the button that will open the modal
             await interaction.followup.send("Click the button below to enter file details:", view=metadata_view, ephemeral=True)

        except Exception as e:
            log.error(f"Error processing forever save for user {user_id}, UID {uid}: {e}", exc_info=True)
            await interaction.followup.send(":x: An error occurred while preparing the permanent save.", ephemeral=True)
            # Cleanup if something failed before modal
            await self.cog_instance.cleanup_session(user_id)

    async def on_timeout(self):
        log.warning(f"SubmitChoiceView timed out for message {self.message.id if self.message else 'Unknown'}")
        await self.disable_buttons()
        # Maybe inform the user?
        # await self.message.channel.send("Save choice timed out.", delete_after=10) # Risky if channel context lost

class InteractionView(ui.View):
    def __init__(self, cog_instance: 'SpectreCog', session_data: dict):
        super().__init__(timeout=300.0) # 5 min timeout for interaction choices
        self.cog_instance = cog_instance
        self.session_data = session_data
        self.message = None # This will be set after sending the message

        # Add buttons dynamically based on session state if needed
        # For now, add all and disable Whisper if replies are 0

        tier = session_data['tier']
        replies_left = session_data['replies_left']
        self.whisper_button = ui.Button(label="Whisper", style=ButtonStyle.primary, emoji="🗣️", custom_id="whisper")
        self.whisper_button.disabled = (replies_left == 0 and TIER_LIMITS[tier]['replies'] != -1)
        self.whisper_button.callback = self.whisper_callback # Assign callback

        self.submit_button = ui.Button(label="Submit", style=ButtonStyle.success, emoji="✅", custom_id="submit")
        self.submit_button.callback = self.submit_callback

        self.retreat_button = ui.Button(label="Retreat", style=ButtonStyle.danger, emoji="🚪", custom_id="retreat")
        self.retreat_button.callback = self.retreat_callback

        self.add_item(self.whisper_button)
        self.add_item(self.submit_button)
        self.add_item(self.retreat_button)


    async def disable_all_buttons(self):
        for item in self.children:
            if isinstance(item, ui.Button):
                item.disabled = True
        try:
            if self.message:
                await self.message.edit(view=self)
        except discord.NotFound:
             pass
        except Exception as e:
            log.error(f"Error disabling buttons on InteractionView: {e}")

    async def whisper_callback(self, interaction: discord.Interaction):
        """Handles the Whisper button click."""
        user_id = interaction.user.id
        # Double-check reply limits
        tier = self.session_data['tier']
        replies_left = self.session_data['replies_left']
        if TIER_LIMITS[tier]['replies'] != -1 and replies_left <= 0:
             await interaction.response.send_message(":x: You have no replies left in this session.", ephemeral=True)
             self.whisper_button.disabled = True # Ensure button is disabled
             await self.message.edit(view=self)
             return

        log.info(f"User {user_id} chose Whisper. Replies left: {replies_left}")
        # Open the prompt modal again for follow-up
        modal = PromptModal(title="Whisper to the Void", session_data=self.session_data, interaction_view=self)
        await interaction.response.send_modal(modal)

    async def submit_callback(self, interaction: discord.Interaction):
        """Handles the Submit button click."""
        user_id = interaction.user.id
        log.info(f"User {user_id} chose Submit.")
        # Disable buttons on this view
        await self.disable_all_buttons()
        # Show the Temporary/Forever choice view
        choice_view = SubmitChoiceView(self.cog_instance, self.session_data, user_id, self.session_data.get('last_gpt_reply'))
        # Edit the existing message to show the new choice view
        try:
            if self.message:
                 choice_view.message = self.message # Link choice view to the message
                 await self.message.edit(content="Choose how to save the output:", view=choice_view)

                 # Try to acknowledge the interaction, but handle the case where it's already been responded to
                 try:
                     await interaction.response.send_message("Please choose a save option below.", ephemeral=True) # Ack interaction
                 except discord.InteractionResponded:
                     # If the interaction has already been responded to, use followup instead
                     await interaction.followup.send("Please choose a save option below.", ephemeral=True)
                 except Exception as e:
                     log.error(f"Error acknowledging interaction for user {user_id}: {e}", exc_info=True)
            else:
                 # Fallback if message ref lost
                 try:
                     await interaction.response.send_message("Choose how to save the output:", view=choice_view, ephemeral=False) # Send new if needed
                 except discord.InteractionResponded:
                     # If the interaction has already been responded to, use followup instead
                     await interaction.followup.send("Choose how to save the output:", view=choice_view, ephemeral=False)
                 except Exception as e:
                     log.error(f"Error sending message for user {user_id}: {e}", exc_info=True)
                 # This might cause issues with view referencing later. Best to ensure self.message is solid.
        except Exception as e:
            log.error(f"Error showing SubmitChoiceView for user {user_id}: {e}", exc_info=True)
            try:
                await interaction.response.send_message(":x: Error preparing save options.", ephemeral=True)
            except discord.InteractionResponded:
                await interaction.followup.send(":x: Error preparing save options.", ephemeral=True)
            except Exception as inner_e:
                log.error(f"Failed to send error message to user {user_id}: {inner_e}", exc_info=True)


    async def retreat_callback(self, interaction: discord.Interaction):
        """Handles the Retreat button click."""
        user_id = interaction.user.id
        log.info(f"User {user_id} chose Retreat.")

        try:
            await interaction.response.defer(ephemeral=True) # Ack privately
        except discord.InteractionResponded:
            # If the interaction has already been responded to, just continue
            log.warning(f"Interaction already responded to for user {user_id} in retreat_callback")
        except Exception as e:
            log.error(f"Error deferring interaction for user {user_id}: {e}", exc_info=True)

        await self.disable_all_buttons() # Disable buttons
        await self.cog_instance.apply_cooldown(interaction) # Apply cooldown on retreat
        await self.cog_instance.cleanup_session(user_id, interaction, retreated=True) # Cleanup session, edit message

        try:
            await interaction.followup.send("You have retreated from the void. Session ended.", ephemeral=True)
        except Exception as e:
            log.error(f"Error sending followup message for user {user_id}: {e}", exc_info=True)

    async def on_timeout(self):
        user_id = self.session_data.get('user_id', 'Unknown') # Get user ID if stored
        log.warning(f"InteractionView timed out for user {user_id}, message {self.message.id if self.message else 'Unknown'}")
        await self.disable_all_buttons()
        # Auto-cleanup session on timeout? Yes.
        await self.cog_instance.cleanup_session(user_id)


class EmbraceView(ui.View):
     def __init__(self, cog_instance: 'SpectreCog', session_data: dict):
        super().__init__(timeout=180.0) # 3 min timeout to click Embrace
        self.cog_instance = cog_instance
        self.session_data = session_data
        self.message = None # Will be set after sending

     @ui.button(label="Embrace the Void", style=ButtonStyle.blurple, emoji="✨", custom_id="embrace")
     async def embrace_button(self, interaction: discord.Interaction, button: ui.Button):
         """Opens the prompt modal."""
         user_id = interaction.user.id
         log.info(f"User {user_id} clicked Embrace.")
         # Disable this button after click
         button.disabled = True
         await interaction.message.edit(view=self) # Update message to show disabled button

         # Create the next view ready (InteractionView) but don't show it yet
         interaction_view = InteractionView(self.cog_instance, self.session_data)

         # Open the modal
         modal = PromptModal(title="Commune with the Void", session_data=self.session_data, interaction_view=interaction_view)
         await interaction.response.send_modal(modal)
         # The modal's on_submit will handle displaying the InteractionView

     async def on_timeout(self):
        user_id = self.session_data.get('user_id', 'Unknown')
        log.warning(f"EmbraceView timed out for user {user_id}, message {self.message.id if self.message else 'Unknown'}")
        # Disable button
        for item in self.children:
            if isinstance(item, ui.Button):
                item.disabled = True
        try:
            if self.message:
                 await self.message.edit(content=f"{self.message.content}\n\n*This interaction has timed out.*", view=self)
        except discord.NotFound:
            log.warning(f"Message not found when timing out EmbraceView for user {user_id}")
        except Exception as e:
             log.error(f"Error editing message on EmbraceView timeout: {e}")
        # Cleanup session on timeout
        try:
            await self.cog_instance.cleanup_session(user_id)
        except Exception as e:
            log.error(f"Error cleaning up session on EmbraceView timeout for user {user_id}: {e}")


class TierSelectView(ui.View):
    def __init__(self, cog_instance: 'SpectreCog'):
        super().__init__(timeout=180.0) # 3 min timeout for tier selection
        self.cog_instance = cog_instance
        self.message = None # Will be set after sending

    async def start_gpt_init_task(self, interaction: discord.Interaction, tier: str):
        """Initiates the background GPT setup."""
        user_id = interaction.user.id

        # Show loading state - Edit the original message
        loading_lines = self.cog_instance.random_loading_lines
        random_line = random.choice(loading_lines)
        loading_msg = f":hourglass: Initializing **{tier}** session... \n\n```{random_line}```"
        await interaction.response.edit_message(content=loading_msg, view=None) # Remove tier buttons

        log.info(f"Starting GPT initialization for User {user_id}, Tier {tier}")
        # Run GPT initialization in the background
        asyncio.create_task(self.cog_instance.initialize_user_session(interaction, user_id, tier))

    # Define buttons for each tier
    @ui.button(label="Drifter", style=ButtonStyle.secondary, custom_id="drifter")
    async def drifter_button(self, interaction: discord.Interaction, button: ui.Button):
        try:
            # Disable the button to prevent multiple clicks
            button.disabled = True
            await self.message.edit(view=self)
            await self.start_gpt_init_task(interaction, "Drifter")
        except discord.InteractionResponded:
            log.warning(f"Interaction already responded to for user {interaction.user.id} in drifter_button")
        except Exception as e:
            log.error(f"Error in drifter_button for user {interaction.user.id}: {e}", exc_info=True)

    @ui.button(label="Seeker", style=ButtonStyle.primary, custom_id="seeker")
    async def seeker_button(self, interaction: discord.Interaction, button: ui.Button):
        try:
            # Disable the button to prevent multiple clicks
            button.disabled = True
            await self.message.edit(view=self)
            await self.start_gpt_init_task(interaction, "Seeker")
        except discord.InteractionResponded:
            log.warning(f"Interaction already responded to for user {interaction.user.id} in seeker_button")
        except Exception as e:
            log.error(f"Error in seeker_button for user {interaction.user.id}: {e}", exc_info=True)

    @ui.button(label="Abysswalker", style=ButtonStyle.danger, custom_id="abysswalker")
    async def abysswalker_button(self, interaction: discord.Interaction, button: ui.Button):
        try:
            # Disable the button to prevent multiple clicks
            button.disabled = True
            await self.message.edit(view=self)
            await self.start_gpt_init_task(interaction, "Abysswalker")
        except discord.InteractionResponded:
            log.warning(f"Interaction already responded to for user {interaction.user.id} in abysswalker_button")
        except Exception as e:
            log.error(f"Error in abysswalker_button for user {interaction.user.id}: {e}", exc_info=True)

    async def on_timeout(self):
        message_id = self.message.id if self.message else 'Unknown'
        log.info(f"TierSelectView timed out for message {message_id}")
        # Disable buttons
        for item in self.children:
            item.disabled = True
        try:
            if self.message:
                await self.message.edit(content=f"{self.message.content}\n\n*Tier selection timed out.*", view=self)
        except discord.NotFound:
            log.info(f"Message {message_id} not found when handling TierSelectView timeout")
        except discord.HTTPException as e:
            log.info(f"HTTP error when handling TierSelectView timeout for message {message_id}: {e}")
        except Exception as e:
            log.error(f"Error editing message on TierSelectView timeout: {e}")


# --- Spectre Cog Class ---

class SpectreCog(commands.Cog, name="Spectre"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.active_sessions = {} # user_id: {gpt_instance, tier, replies_left, saves_left, last_gpt_reply, interaction_message}
        self.maintenance_mode = False
        self.random_loading_lines = load_random_lines()
        # Track Drifter tier usage for custom cooldown
        self.drifter_usage = {}
        # Track sent messages for auto-deletion after 5000 seconds
        self.sent_messages = [] # List of (message, timestamp) tuples
        # Start the message cleanup task
        self.message_cleanup_task = asyncio.create_task(self.cleanup_old_messages())
        # Cooldown mapping: 1 use per X seconds per user
        self.cooldown_mapping = commands.CooldownMapping.from_cooldown(1, 10, commands.BucketType.user) # Default 10s, override per tier

        log.info("Spectre Cog initialized.")
        log.info(f"Loaded {len(self.random_loading_lines)} random loading lines.")


    # Track when maintenance mode was enabled
    maintenance_start_time = None

    async def check_maintenance(self, interaction: discord.Interaction) -> bool:
        """Checks if maintenance mode is active."""
        if self.maintenance_mode:
            # New commands are rejected immediately
            await interaction.response.send_message(":tools: The Spectre module is currently undergoing maintenance. Please try again later.", ephemeral=True)
            return True
        return False

    async def maintenance_timeout_task(self):
        """Task that runs when maintenance mode is enabled to terminate sessions after 15 minutes."""
        try:
            await asyncio.sleep(900)  # 15 minutes = 900 seconds

            if not self.maintenance_mode:
                # Maintenance mode was disabled before timeout
                return

            log.info("Maintenance timeout reached. Terminating all active Spectre sessions.")
        except asyncio.CancelledError:
            # Task was cancelled, just exit
            log.info("Maintenance timeout task cancelled")
            return
        except Exception as e:
            log.error(f"Error in maintenance timeout task: {e}", exc_info=True)

        # Get a copy of active session user IDs to avoid modification during iteration
        active_users = list(self.active_sessions.keys())

        for user_id in active_users:
            if user_id in self.active_sessions:
                try:
                    # Get the interaction message if it exists
                    message = self.active_sessions[user_id].get('interaction_message')
                    if message:
                        try:
                            await message.edit(content=":tools: This session has been terminated due to scheduled maintenance.", view=None)
                        except Exception as e:
                            log.error(f"Error notifying user {user_id} about maintenance termination: {e}")

                    # Clean up the session
                    del self.active_sessions[user_id]
                    log.info(f"Terminated session for user {user_id} due to maintenance timeout")
                except Exception as e:
                    log.error(f"Error terminating session for user {user_id}: {e}")

    # Store usage timestamps for Drifter tier cooldown tracking
    drifter_usage = {} # user_id: [timestamp1, timestamp2, ...]

    async def apply_cooldown(self, interaction: discord.Interaction):
        """Applies the appropriate cooldown based on the user's session tier."""
        user_id = interaction.user.id
        if user_id in self.active_sessions:
            tier = self.active_sessions[user_id]['tier']

            # Special handling for Drifter tier (10-minute cooldown after 3 uses in 5 minutes)
            if tier == "Drifter":
                current_time = time.time()

                # Initialize user's usage tracking if not exists
                if user_id not in self.drifter_usage:
                    self.drifter_usage[user_id] = []

                # Add current usage timestamp
                self.drifter_usage[user_id].append(current_time)

                # Keep only timestamps from the last 5 minutes
                five_minutes_ago = current_time - 300  # 300 seconds = 5 minutes
                self.drifter_usage[user_id] = [ts for ts in self.drifter_usage[user_id] if ts > five_minutes_ago]

                # Check if this is the 3rd or more usage in 5 minutes
                if len(self.drifter_usage[user_id]) >= 3:
                    # Apply 10-minute cooldown
                    cooldown_duration = TIER_LIMITS[tier]['cooldown']
                    # Create a custom message-like object for cooldown tracking
                    class DummyMessage:
                        def __init__(self, author):
                            self.author = author

                    # Create a dummy message with the user as author
                    dummy_message = DummyMessage(interaction.user)

                    try:
                        bucket = self.cooldown_mapping.get_bucket(dummy_message)
                        bucket.update_rate_limit()
                        log.info(f"Applied {cooldown_duration}s cooldown for Drifter user {user_id} (3+ uses in 5 minutes)")
                    except Exception as e:
                        log.error(f"Error applying cooldown for user {user_id}: {e}", exc_info=True)

            # Standard cooldown for other tiers
            elif TIER_LIMITS[tier]['cooldown'] > 0:
                cooldown_duration = TIER_LIMITS[tier]['cooldown']
                # Create a custom message-like object for cooldown tracking
                class DummyMessage:
                    def __init__(self, author):
                        self.author = author

                # Create a dummy message with the user as author
                dummy_message = DummyMessage(interaction.user)

                try:
                    bucket = self.cooldown_mapping.get_bucket(dummy_message)
                    bucket.update_rate_limit()
                    log.info(f"Applied {cooldown_duration}s cooldown for user {user_id} (Tier: {tier})")
                except Exception as e:
                    log.error(f"Error applying cooldown for user {user_id}: {e}", exc_info=True)

    async def cleanup_session(self, user_id: int, interaction: discord.Interaction | None = None, retreated: bool = False):
         """Cleans up a user's active session data and optionally edits the interaction message."""
         if user_id in self.active_sessions:
             log.info(f"Cleaning up session for user {user_id}")
             session = self.active_sessions.pop(user_id)
             gpt_instance = session.get('gpt_instance')
             if gpt_instance:
                 try:
                     await gpt_instance.close() # Close GPT session if applicable
                     log.info(f"Closed GPT instance for user {user_id}")
                 except Exception as e:
                     log.error(f"Error closing GPT instance for user {user_id}: {e}", exc_info=True)

             # Edit the original interaction message to indicate session end
             if interaction and session.get('interaction_message'):
                 try:
                    message_to_edit = session['interaction_message']
                    end_reason = "Session ended." if not retreated else "Retreated from the void."
                    # Get last reply to show it if available
                    last_reply = session.get('last_gpt_reply', '')

                    # Truncate the last reply if it's too long to fit in a Discord message
                    if last_reply and len(last_reply) > 1800:  # Leave room for formatting
                        last_reply = last_reply[:1800] + "..."

                    final_content = f"**AI Response:**\n```\n{last_reply}\n```\n\n*{end_reason}*" if last_reply else f"*{end_reason}*"

                    await message_to_edit.edit(content=final_content, view=None) # Remove buttons
                    log.info(f"Edited final message for user {user_id}")
                 except discord.NotFound:
                     log.warning(f"Could not find message to edit for user {user_id} session cleanup.")
                 except Exception as e:
                     log.error(f"Error editing message during session cleanup for user {user_id}: {e}", exc_info=True)
         else:
            log.warning(f"Attempted to cleanup session for user {user_id}, but no active session found.")


    async def initialize_user_session(self, interaction: discord.Interaction, user_id: int, tier: str):
        """Reads instructions, initializes GPT, and presents the Embrace button."""
        # Read user instructor file
        user_instructor_content = await read_file_content(FILES_DIR / "user_instructor.txt")
        if not user_instructor_content or user_instructor_content.startswith(":"):
            await interaction.followup.send(user_instructor_content or ":x: Failed to load instructions.", ephemeral=True)
            await self.cleanup_session(user_id) # Cleanup needed if files missing
            return

        # Initialize GPT
        gpt_instructor_prompt = await read_file_content(FILES_DIR / "gpt_instructor.txt")
        if not gpt_instructor_prompt or gpt_instructor_prompt.startswith(":"):
            await interaction.followup.send(gpt_instructor_prompt or ":x: Failed to load AI configuration.", ephemeral=True)
            await self.cleanup_session(user_id)
            return

        gpt_instance = await initialize_gpt_session(gpt_instructor_prompt)
        if not gpt_instance: # Handle potential init failure
             await interaction.followup.send(":x: Failed to initialize AI session. Please try again later.", ephemeral=True)
             await self.cleanup_session(user_id)
             return

        # Store session data
        self.active_sessions[user_id] = {
            "user_id": user_id, # Store user_id in session data as well
            "gpt_instance": gpt_instance,
            "tier": tier,
            "replies_left": TIER_LIMITS[tier]['replies'],
            "saves_left": TIER_LIMITS[tier]['saves'],
            "last_gpt_reply": None,
            "interaction_message": interaction.message # Store the message being edited
        }
        log.info(f"User session initialized for {user_id} (Tier: {tier}). Replies: {self.active_sessions[user_id]['replies_left']}, Saves: {self.active_sessions[user_id]['saves_left']}")

        # Show user instructions and Embrace button
        embrace_view = EmbraceView(self, self.active_sessions[user_id])
        content = f"**Instructions ({tier} Tier):**\n{user_instructor_content}"
        try:
             # Edit the message originally sent by TierSelectView button callback
             await interaction.edit_original_response(content=content, view=embrace_view)
             # Get the message object after editing to store it
             message = await interaction.original_response()
             embrace_view.message = message # Link view to the message
             self.active_sessions[user_id]['interaction_message'] = message # Update session message reference
             log.info(f"Presented Embrace view to user {user_id}")
        except discord.NotFound:
            log.error(f"Failed to edit original response for EmbraceView (User: {user_id}). Message likely deleted.")
            await interaction.followup.send(":warning: Original interaction message lost. Please start again.", ephemeral=True)
            await self.cleanup_session(user_id)
        except Exception as e:
            log.error(f"Error presenting Embrace view for user {user_id}: {e}", exc_info=True)
            await interaction.followup.send(":x: Error displaying next step.", ephemeral=True)
            await self.cleanup_session(user_id)


    # --- Commands ---
    # Custom cooldown function for the spectre command
    def get_spectre_cooldown(self, interaction):
        # Custom cooldown check for Drifter tier (3 uses in 5 minutes, then 10 min cooldown)
        user_id = interaction.user.id

        # Get user's tier - default to Drifter if not in active sessions
        tier = self.active_sessions.get(user_id, {}).get('tier', 'Drifter')

        if tier == "Drifter":
            # Check if user has usage history
            if hasattr(self, 'drifter_usage') and user_id in self.drifter_usage:
                current_time = time.time()
                five_minutes_ago = current_time - 300  # 5 minutes

                # Filter to only include uses in the last 5 minutes
                recent_uses = [ts for ts in self.drifter_usage[user_id] if ts > five_minutes_ago]

                # If 3+ uses in last 5 minutes, apply 10-minute cooldown
                if len(recent_uses) >= 3:
                    oldest_use = min(recent_uses)
                    ten_minutes = 600  # 10 minutes in seconds
                    cooldown_end = oldest_use + ten_minutes

                    # If cooldown period hasn't expired
                    if current_time < cooldown_end:
                        retry_after = cooldown_end - current_time
                        return commands.Cooldown(1, retry_after)

        # For other tiers, use standard cooldown
        cooldown_seconds = TIER_LIMITS.get(tier, TIER_LIMITS['Drifter'])['cooldown']
        return commands.Cooldown(1, cooldown_seconds)

    @app_commands.command(name="spectre", description="Initiate a session with the AI.")
    @app_commands.checks.cooldown(1, 10, key=lambda i: i.user.id)
    async def spectre(self, interaction: discord.Interaction):
        """Starts the Spectre interaction flow."""
        if await self.check_maintenance(interaction):
            return

        user_id = interaction.user.id
        # Check if user already has an active session
        if user_id in self.active_sessions:
             await interaction.response.send_message(":warning: You already have an active Spectre session. Please finish or `/spectre retreat` that one first.", ephemeral=True)
             return

        # Check cooldown based on *potential* tier (assume lowest for initial check or track last used tier?)
        # For simplicity, we apply cooldown *after* a session ends (Retreat/Submit).
        # Check initial cooldown using the default mapping
        # Create a custom message-like object for cooldown tracking
        class DummyMessage:
            def __init__(self, author):
                self.author = author

        # Create a dummy message with the user as author
        dummy_message = DummyMessage(interaction.user)

        try:
            bucket = self.cooldown_mapping.get_bucket(dummy_message)
            retry_after = bucket.update_rate_limit()
        except Exception as e:
            log.error(f"Error checking cooldown for user {interaction.user.id}: {e}", exc_info=True)
            # Default to no cooldown if there's an error
            retry_after = 0
        if retry_after:
             await interaction.response.send_message(f":hourglass: You are on cooldown. Please wait {retry_after:.2f} seconds.", ephemeral=True)
             return

        log.info(f"'/spectre' command invoked by user {user_id}")

        # Track usage for Drifter tier cooldown
        if user_id not in self.drifter_usage:
            self.drifter_usage[user_id] = []
        self.drifter_usage[user_id].append(time.time())
        # Read spectre.txt
        spectre_intro = await read_file_content(FILES_DIR / "spectre.txt")
        if not spectre_intro or spectre_intro.startswith(":"):
             await interaction.response.send_message(spectre_intro or ":x: Bot configuration error.", ephemeral=True)
             return

        # Show intro and tier selection
        view = TierSelectView(self)
        await interaction.response.send_message(spectre_intro, view=view, ephemeral=False) # Send publicly
        message = await interaction.original_response()
        view.message = message # Link the view to the message it's attached to
        # Track message for auto-deletion
        self.track_message(message)

    @commands.command(name="spectreretreat") # Prefix command as fallback/alternative
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def spectre_retreat_prefix(self, ctx: commands.Context):
        """Fallback command to end an active session."""
        user_id = ctx.author.id
        if user_id in self.active_sessions:
             await self.cleanup_session(user_id, None, retreated=True) # No interaction obj here
             message = await ctx.send("Session ended via retreat command.")
             # Track message for auto-deletion
             self.track_message(message)
             log.info(f"User {user_id} ended session via prefix retreat command.")
        else:
            message = await ctx.send("You don't have an active Spectre session.")
            # Track message for auto-deletion
            self.track_message(message)


    @commands.is_owner()
    @commands.command(name="spectremaintenance", aliases=['smaint'])
    async def spectre_maintenance(self, ctx: commands.Context):
        """Toggles maintenance mode for the Spectre cog (Owner Only)."""
        self.maintenance_mode = not self.maintenance_mode
        status = "ENABLED" if self.maintenance_mode else "DISABLED"

        if self.maintenance_mode:
            # Start the maintenance timeout task
            self.maintenance_start_time = time.time()
            asyncio.create_task(self.maintenance_timeout_task())
            active_sessions = len(self.active_sessions)
            message = await ctx.send(f":tools: Spectre Cog maintenance mode is now **{status}**. {active_sessions} active sessions will be terminated in 15 minutes.")
            # Track message for auto-deletion
            self.track_message(message)
        else:
            # Maintenance mode disabled
            self.maintenance_start_time = None
            message = await ctx.send(f":tools: Spectre Cog maintenance mode is now **{status}**. New sessions are now allowed.")
            # Track message for auto-deletion
            self.track_message(message)

        log.info(f"Spectre maintenance mode set to {status} by {ctx.author}")

    async def cog_load(self):
        """Called when the cog is loaded."""
        log.info(f"SpectreCog loaded")

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
        log.info(f"SpectreCog unloaded")


# --- Setup Function ---
async def setup(bot: commands.Bot):
    await bot.add_cog(SpectreCog(bot))