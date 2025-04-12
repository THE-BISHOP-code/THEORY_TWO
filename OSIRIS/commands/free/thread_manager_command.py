# commands/free/thread_manager_command.py
"""
Thread management command for Discord servers.

This module provides functionality to create, delete, edit, archive, unarchive,
and list threads, as well as manage thread settings and permissions.
"""

import discord
import logging
from typing import List, Dict, Any, Optional, Union
import datetime

log = logging.getLogger('MyBot.Commands.ThreadManager')

async def execute(interaction, bot, args):
    """
    Manages threads in text channels.
    
    Args:
        interaction (discord.Interaction): The interaction that triggered the command
        bot (commands.Bot): The bot instance
        args (dict): Command arguments
            - operation (str): The operation to perform (create, delete, edit, archive, unarchive, list, info, add, remove)
            - channel (str, optional): Channel name or ID where the thread is or will be created
            - thread (str, optional): Thread name or ID to operate on
            - name (str, optional): Name for the thread
            - type (str, optional): Type of thread to create (public, private, news, forum)
            - message (str, optional): Message ID to create a thread from
            - auto_archive (str, optional): Auto-archive duration in minutes (60, 1440, 4320, 10080)
            - slowmode (str, optional): Slowmode delay in seconds
            - locked (str, optional): Whether the thread should be locked (true/false)
            - invitable (str, optional): Whether non-moderators can add users to the thread (true/false)
            - user (str, optional): User ID or mention to add/remove from the thread
            - reason (str, optional): Reason for the audit log
    """
    if not interaction.guild:
        log.warning("Cannot manage threads: Not in a guild context")
        return False
    
    # Get parameters
    operation = args.get('operation', '').lower()
    channel_name_or_id = args.get('channel', '')
    thread_name_or_id = args.get('thread', '')
    name = args.get('name', '')
    thread_type = args.get('type', 'public').lower()
    message_id_str = args.get('message', '')
    auto_archive_str = args.get('auto_archive', '')
    slowmode_str = args.get('slowmode', '')
    locked_str = args.get('locked', '').lower()
    invitable_str = args.get('invitable', '').lower()
    user_id_or_mention = args.get('user', '')
    reason = args.get('reason', 'Thread management command')
    
    # Find the target channel
    target_channel = None
    if channel_name_or_id:
        try:
            channel_id = int(channel_name_or_id)
            target_channel = interaction.guild.get_channel(channel_id)
        except (ValueError, TypeError):
            # Not an ID, try to find by name
            target_channel = discord.utils.get(interaction.guild.text_channels, name=channel_name_or_id)
    
    # Find the target thread
    target_thread = None
    if thread_name_or_id:
        try:
            thread_id = int(thread_name_or_id)
            target_thread = interaction.guild.get_thread(thread_id)
        except (ValueError, TypeError):
            # Not an ID, try to find by name
            for thread in interaction.guild.threads:
                if thread.name == thread_name_or_id:
                    target_thread = thread
                    break
    
    # Find the target message if specified
    target_message = None
    if message_id_str and target_channel:
        try:
            message_id = int(message_id_str)
            try:
                target_message = await target_channel.fetch_message(message_id)
            except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                pass
        except ValueError:
            pass
    
    # Find the target user if specified
    target_user = None
    if user_id_or_mention:
        # Check if it's a mention
        if user_id_or_mention.startswith('<@') and user_id_or_mention.endswith('>'):
            user_id_str = user_id_or_mention.strip('<@!>')
            try:
                user_id = int(user_id_str)
                target_user = interaction.guild.get_member(user_id)
            except (ValueError, TypeError):
                pass
        else:
            # Try to find by ID first
            try:
                user_id = int(user_id_or_mention)
                target_user = interaction.guild.get_member(user_id)
            except (ValueError, TypeError):
                # Not an ID, try to find by name
                target_user = discord.utils.get(interaction.guild.members, name=user_id_or_mention)
                if not target_user:
                    # Try to find by display name
                    target_user = discord.utils.get(interaction.guild.members, display_name=user_id_or_mention)
    
    # Parse auto-archive duration
    auto_archive_duration = None
    if auto_archive_str:
        try:
            minutes = int(auto_archive_str)
            # Discord only allows specific values: 60 (1 hour), 1440 (1 day), 4320 (3 days), 10080 (1 week)
            valid_durations = [60, 1440, 4320, 10080]
            
            # Find the closest valid duration
            auto_archive_duration = min(valid_durations, key=lambda x: abs(x - minutes))
            
            if auto_archive_duration != minutes:
                log.warning(f"Auto-archive duration {minutes} minutes is not valid. Using {auto_archive_duration} minutes instead.")
        except ValueError:
            log.warning(f"Invalid auto-archive duration: {auto_archive_str}")
    
    # Parse slowmode delay
    slowmode = None
    if slowmode_str:
        try:
            slowmode = int(slowmode_str)
            if slowmode < 0:
                slowmode = 0
            elif slowmode > 21600:  # Discord's limit is 6 hours (21600 seconds)
                slowmode = 21600
        except ValueError:
            log.warning(f"Invalid slowmode delay: {slowmode_str}")
    
    # Parse boolean parameters
    locked = None
    if locked_str:
        locked = locked_str == 'true'
    
    invitable = None
    if invitable_str:
        invitable = invitable_str == 'true'
    
    # Execute the requested operation
    try:
        if operation == 'create':
            return await create_thread(interaction, target_channel, target_message, name, thread_type, auto_archive_duration, slowmode, invitable, reason)
        elif operation == 'delete':
            return await delete_thread(interaction, target_thread, reason)
        elif operation == 'edit':
            return await edit_thread(interaction, target_thread, name, auto_archive_duration, slowmode, locked, invitable, reason)
        elif operation == 'archive':
            return await archive_thread(interaction, target_thread, reason)
        elif operation == 'unarchive':
            return await unarchive_thread(interaction, target_thread, reason)
        elif operation == 'list':
            return await list_threads(interaction, target_channel)
        elif operation == 'info':
            return await thread_info(interaction, target_thread)
        elif operation == 'add':
            return await add_member(interaction, target_thread, target_user, reason)
        elif operation == 'remove':
            return await remove_member(interaction, target_thread, target_user, reason)
        else:
            await interaction.response.send_message(f":warning: Unknown operation: {operation}", ephemeral=True)
            return False
    except Exception as e:
        log.error(f"Error executing thread operation {operation}: {e}", exc_info=True)
        await interaction.response.send_message(f":x: Error executing operation: {e}", ephemeral=True)
        return False

async def create_thread(interaction, channel, message, name, thread_type, auto_archive_duration, slowmode, invitable, reason):
    """Creates a new thread in the specified channel."""
    if not channel:
        await interaction.response.send_message(":warning: Channel not found or not specified.", ephemeral=True)
        return False
    
    if not name:
        await interaction.response.send_message(":warning: Thread name is required.", ephemeral=True)
        return False
    
    # Check if the channel supports threads
    if not isinstance(channel, (discord.TextChannel, discord.ForumChannel)):
        await interaction.response.send_message(f":warning: Cannot create threads in {channel.mention}. Only text and forum channels support threads.", ephemeral=True)
        return False
    
    await interaction.response.defer(ephemeral=True)
    
    try:
        thread = None
        
        # Set default auto-archive duration if not specified
        if auto_archive_duration is None:
            auto_archive_duration = 1440  # 1 day
        
        # Create the thread based on the type
        if thread_type == 'private':
            # Create a private thread
            thread = await channel.create_thread(
                name=name,
                type=discord.ChannelType.private_thread,
                auto_archive_duration=auto_archive_duration,
                reason=reason,
                invitable=invitable if invitable is not None else True
            )
        elif thread_type == 'news' and isinstance(channel, discord.TextChannel) and channel.is_news():
            # Create a news thread (only in announcement channels)
            if message:
                thread = await message.create_thread(
                    name=name,
                    auto_archive_duration=auto_archive_duration,
                    reason=reason
                )
            else:
                # For news channels, we need a message to create a thread
                await interaction.followup.send(":warning: News threads can only be created from messages. Please provide a message ID.", ephemeral=True)
                return False
        elif thread_type == 'forum' and isinstance(channel, discord.ForumChannel):
            # Create a forum thread
            thread = await channel.create_thread(
                name=name,
                content="Thread created via command",
                auto_archive_duration=auto_archive_duration,
                reason=reason
            )
        else:
            # Create a public thread
            if message:
                # Create from a message
                thread = await message.create_thread(
                    name=name,
                    auto_archive_duration=auto_archive_duration,
                    reason=reason
                )
            else:
                # Create a standalone thread
                thread = await channel.create_thread(
                    name=name,
                    type=discord.ChannelType.public_thread,
                    auto_archive_duration=auto_archive_duration,
                    reason=reason
                )
        
        # Set slowmode if specified
        if thread and slowmode is not None:
            await thread.edit(slowmode_delay=slowmode)
        
        # Send success message
        await interaction.followup.send(f":white_check_mark: Thread {thread.mention} created successfully in {channel.mention}.", ephemeral=True)
        return True
    except discord.Forbidden:
        await interaction.followup.send(":x: I don't have permission to create threads in this channel.", ephemeral=True)
        return False
    except discord.HTTPException as e:
        await interaction.followup.send(f":x: Failed to create thread: {e}", ephemeral=True)
        return False

async def delete_thread(interaction, thread, reason):
    """Deletes a thread."""
    if not thread:
        await interaction.response.send_message(":warning: Thread not found or not specified.", ephemeral=True)
        return False
    
    await interaction.response.defer(ephemeral=True)
    
    try:
        # Store thread info before deletion
        thread_name = thread.name
        parent_channel = thread.parent
        
        # Delete the thread
        await thread.delete(reason=reason)
        
        # Send success message
        if parent_channel:
            await interaction.followup.send(f":white_check_mark: Thread **{thread_name}** deleted successfully from {parent_channel.mention}.", ephemeral=True)
        else:
            await interaction.followup.send(f":white_check_mark: Thread **{thread_name}** deleted successfully.", ephemeral=True)
        
        return True
    except discord.Forbidden:
        await interaction.followup.send(":x: I don't have permission to delete this thread.", ephemeral=True)
        return False
    except discord.HTTPException as e:
        await interaction.followup.send(f":x: Failed to delete thread: {e}", ephemeral=True)
        return False

async def edit_thread(interaction, thread, name, auto_archive_duration, slowmode, locked, invitable, reason):
    """Edits a thread's settings."""
    if not thread:
        await interaction.response.send_message(":warning: Thread not found or not specified.", ephemeral=True)
        return False
    
    # Check if there's anything to edit
    if not name and auto_archive_duration is None and slowmode is None and locked is None and invitable is None:
        await interaction.response.send_message(":warning: No changes specified for editing.", ephemeral=True)
        return False
    
    await interaction.response.defer(ephemeral=True)
    
    try:
        # Prepare the edit parameters
        edit_params = {'reason': reason}
        
        if name:
            edit_params['name'] = name
        
        if auto_archive_duration is not None:
            edit_params['auto_archive_duration'] = auto_archive_duration
        
        if slowmode is not None:
            edit_params['slowmode_delay'] = slowmode
        
        if locked is not None:
            edit_params['locked'] = locked
        
        if invitable is not None and thread.type == discord.ChannelType.private_thread:
            edit_params['invitable'] = invitable
        
        # Edit the thread
        await thread.edit(**edit_params)
        
        # Prepare a message about what was changed
        changes = []
        if name:
            changes.append(f"name to `{name}`")
        if auto_archive_duration is not None:
            duration_text = f"{auto_archive_duration // 60} hours" if auto_archive_duration >= 60 else f"{auto_archive_duration} minutes"
            changes.append(f"auto-archive duration to `{duration_text}`")
        if slowmode is not None:
            changes.append(f"slowmode to `{slowmode}` seconds")
        if locked is not None:
            changes.append(f"locked to `{locked}`")
        if invitable is not None and thread.type == discord.ChannelType.private_thread:
            changes.append(f"invitable to `{invitable}`")
        
        changes_str = ", ".join(changes)
        await interaction.followup.send(f":white_check_mark: Thread {thread.mention} updated: {changes_str}.", ephemeral=True)
        return True
    except discord.Forbidden:
        await interaction.followup.send(":x: I don't have permission to edit this thread.", ephemeral=True)
        return False
    except discord.HTTPException as e:
        await interaction.followup.send(f":x: Failed to edit thread: {e}", ephemeral=True)
        return False

async def archive_thread(interaction, thread, reason):
    """Archives a thread."""
    if not thread:
        await interaction.response.send_message(":warning: Thread not found or not specified.", ephemeral=True)
        return False
    
    if thread.archived:
        await interaction.response.send_message(f":information_source: Thread {thread.mention} is already archived.", ephemeral=True)
        return True
    
    await interaction.response.defer(ephemeral=True)
    
    try:
        # Archive the thread
        await thread.edit(archived=True, reason=reason)
        
        await interaction.followup.send(f":white_check_mark: Thread {thread.mention} archived successfully.", ephemeral=True)
        return True
    except discord.Forbidden:
        await interaction.followup.send(":x: I don't have permission to archive this thread.", ephemeral=True)
        return False
    except discord.HTTPException as e:
        await interaction.followup.send(f":x: Failed to archive thread: {e}", ephemeral=True)
        return False

async def unarchive_thread(interaction, thread, reason):
    """Unarchives a thread."""
    if not thread:
        await interaction.response.send_message(":warning: Thread not found or not specified.", ephemeral=True)
        return False
    
    if not thread.archived:
        await interaction.response.send_message(f":information_source: Thread {thread.mention} is not archived.", ephemeral=True)
        return True
    
    await interaction.response.defer(ephemeral=True)
    
    try:
        # Unarchive the thread
        await thread.edit(archived=False, reason=reason)
        
        await interaction.followup.send(f":white_check_mark: Thread {thread.mention} unarchived successfully.", ephemeral=True)
        return True
    except discord.Forbidden:
        await interaction.followup.send(":x: I don't have permission to unarchive this thread.", ephemeral=True)
        return False
    except discord.HTTPException as e:
        await interaction.followup.send(f":x: Failed to unarchive thread: {e}", ephemeral=True)
        return False

async def list_threads(interaction, channel):
    """Lists all threads in the server or a specific channel."""
    await interaction.response.defer(ephemeral=True)
    
    try:
        if channel:
            # List threads in the specified channel
            threads = [thread for thread in interaction.guild.threads if thread.parent_id == channel.id]
            
            if not threads:
                await interaction.followup.send(f":information_source: No threads found in {channel.mention}.", ephemeral=True)
                return True
            
            embed = discord.Embed(
                title=f"Threads in #{channel.name}",
                description=f"Found {len(threads)} thread{'s' if len(threads) != 1 else ''}",
                color=discord.Color.blue()
            )
        else:
            # List all threads in the server
            threads = interaction.guild.threads
            
            if not threads:
                await interaction.followup.send(f":information_source: No threads found in this server.", ephemeral=True)
                return True
            
            embed = discord.Embed(
                title=f"Threads in {interaction.guild.name}",
                description=f"Found {len(threads)} thread{'s' if len(threads) != 1 else ''}",
                color=discord.Color.blue()
            )
            
            # Group threads by parent channel
            threads_by_channel = {}
            for thread in threads:
                parent_id = thread.parent_id
                if parent_id not in threads_by_channel:
                    threads_by_channel[parent_id] = []
                threads_by_channel[parent_id].append(thread)
            
            # Add threads to the embed
            for parent_id, channel_threads in threads_by_channel.items():
                parent_channel = interaction.guild.get_channel(parent_id)
                channel_name = f"#{parent_channel.name}" if parent_channel else f"Unknown Channel ({parent_id})"
                
                thread_list = []
                for thread in channel_threads:
                    status = "🔒" if thread.locked else "🔓"
                    status += "📁" if thread.archived else "📂"
                    
                    if thread.type == discord.ChannelType.private_thread:
                        thread_type = "🔒 Private"
                    elif thread.parent and thread.parent.type == discord.ChannelType.news:
                        thread_type = "📢 News"
                    else:
                        thread_type = "💬 Public"
                    
                    thread_list.append(f"{status} {thread.mention} ({thread_type})")
                
                thread_list_str = "\n".join(thread_list)
                if thread_list_str:
                    embed.add_field(name=channel_name, value=thread_list_str, inline=False)
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            return True
    except discord.Forbidden:
        await interaction.followup.send(":x: I don't have permission to view threads.", ephemeral=True)
        return False
    except discord.HTTPException as e:
        await interaction.followup.send(f":x: Failed to list threads: {e}", ephemeral=True)
        return False

async def thread_info(interaction, thread):
    """Displays detailed information about a thread."""
    if not thread:
        await interaction.response.send_message(":warning: Thread not found or not specified.", ephemeral=True)
        return False
    
    await interaction.response.defer(ephemeral=True)
    
    try:
        # Create an embed with thread information
        embed = discord.Embed(
            title=f"Thread Information: {thread.name}",
            color=discord.Color.blue()
        )
        
        # Add basic information
        embed.add_field(name="ID", value=thread.id, inline=True)
        
        # Add thread type
        if thread.type == discord.ChannelType.private_thread:
            thread_type = "Private Thread"
        elif thread.parent and thread.parent.type == discord.ChannelType.news:
            thread_type = "News Thread"
        else:
            thread_type = "Public Thread"
        
        embed.add_field(name="Type", value=thread_type, inline=True)
        
        # Add parent channel
        if thread.parent:
            embed.add_field(name="Parent Channel", value=thread.parent.mention, inline=True)
        
        # Add creation time
        created_at = int(thread.created_at.timestamp())
        embed.add_field(name="Created", value=f"<t:{created_at}:R>", inline=True)
        
        # Add owner
        if thread.owner_id:
            owner = interaction.guild.get_member(thread.owner_id)
            if owner:
                embed.add_field(name="Owner", value=owner.mention, inline=True)
            else:
                embed.add_field(name="Owner ID", value=thread.owner_id, inline=True)
        
        # Add member count
        embed.add_field(name="Member Count", value=thread.member_count if hasattr(thread, 'member_count') else "Unknown", inline=True)
        
        # Add message count
        embed.add_field(name="Message Count", value=thread.message_count if hasattr(thread, 'message_count') else "Unknown", inline=True)
        
        # Add slowmode
        embed.add_field(name="Slowmode", value=f"{thread.slowmode_delay} seconds" if thread.slowmode_delay else "None", inline=True)
        
        # Add auto-archive duration
        if thread.auto_archive_duration:
            if thread.auto_archive_duration == 60:
                duration_text = "1 hour"
            elif thread.auto_archive_duration == 1440:
                duration_text = "1 day"
            elif thread.auto_archive_duration == 4320:
                duration_text = "3 days"
            elif thread.auto_archive_duration == 10080:
                duration_text = "1 week"
            else:
                duration_text = f"{thread.auto_archive_duration} minutes"
            
            embed.add_field(name="Auto-Archive", value=duration_text, inline=True)
        
        # Add archive status
        embed.add_field(name="Archived", value="Yes" if thread.archived else "No", inline=True)
        
        if thread.archived and thread.archive_timestamp:
            archive_timestamp = int(thread.archive_timestamp.timestamp())
            embed.add_field(name="Archived At", value=f"<t:{archive_timestamp}:R>", inline=True)
        
        # Add locked status
        embed.add_field(name="Locked", value="Yes" if thread.locked else "No", inline=True)
        
        # Add invitable status for private threads
        if thread.type == discord.ChannelType.private_thread:
            embed.add_field(name="Invitable", value="Yes" if thread.invitable else "No", inline=True)
        
        await interaction.followup.send(embed=embed, ephemeral=True)
        return True
    except discord.Forbidden:
        await interaction.followup.send(":x: I don't have permission to view this thread.", ephemeral=True)
        return False
    except discord.HTTPException as e:
        await interaction.followup.send(f":x: Failed to get thread information: {e}", ephemeral=True)
        return False

async def add_member(interaction, thread, user, reason):
    """Adds a user to a thread."""
    if not thread:
        await interaction.response.send_message(":warning: Thread not found or not specified.", ephemeral=True)
        return False
    
    if not user:
        await interaction.response.send_message(":warning: User not found or not specified.", ephemeral=True)
        return False
    
    await interaction.response.defer(ephemeral=True)
    
    try:
        # Check if the user is already in the thread
        try:
            await thread.fetch_member(user.id)
            await interaction.followup.send(f":information_source: {user.mention} is already in the thread {thread.mention}.", ephemeral=True)
            return True
        except discord.NotFound:
            # User is not in the thread, continue
            pass
        
        # Add the user to the thread
        await thread.add_user(user)
        
        await interaction.followup.send(f":white_check_mark: Added {user.mention} to thread {thread.mention}.", ephemeral=True)
        return True
    except discord.Forbidden:
        await interaction.followup.send(":x: I don't have permission to add users to this thread.", ephemeral=True)
        return False
    except discord.HTTPException as e:
        await interaction.followup.send(f":x: Failed to add user to thread: {e}", ephemeral=True)
        return False

async def remove_member(interaction, thread, user, reason):
    """Removes a user from a thread."""
    if not thread:
        await interaction.response.send_message(":warning: Thread not found or not specified.", ephemeral=True)
        return False
    
    if not user:
        await interaction.response.send_message(":warning: User not found or not specified.", ephemeral=True)
        return False
    
    await interaction.response.defer(ephemeral=True)
    
    try:
        # Check if the user is in the thread
        try:
            await thread.fetch_member(user.id)
        except discord.NotFound:
            await interaction.followup.send(f":information_source: {user.mention} is not in the thread {thread.mention}.", ephemeral=True)
            return True
        
        # Remove the user from the thread
        await thread.remove_user(user)
        
        await interaction.followup.send(f":white_check_mark: Removed {user.mention} from thread {thread.mention}.", ephemeral=True)
        return True
    except discord.Forbidden:
        await interaction.followup.send(":x: I don't have permission to remove users from this thread.", ephemeral=True)
        return False
    except discord.HTTPException as e:
        await interaction.followup.send(f":x: Failed to remove user from thread: {e}", ephemeral=True)
        return False
