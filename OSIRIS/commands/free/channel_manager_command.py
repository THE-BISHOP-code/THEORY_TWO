# commands/free/channel_manager_command.py
"""
Channel management command for Discord servers.

This module provides comprehensive functionality to manage channels, including
creating, deleting, editing, moving, cloning, syncing, locking, unlocking, and
setting slowmode for channels.
"""

import discord
import logging
import asyncio
from typing import List, Optional, Union, Dict, Any

log = logging.getLogger('MyBot.Commands.ChannelManager')

async def execute(interaction, bot, args):
    """
    Comprehensive channel management command with multiple operations.

    Args:
        interaction (discord.Interaction): The interaction that triggered the command
        bot (commands.Bot): The bot instance
        args (dict): Command arguments
            - operation (str): The operation to perform (create, delete, edit, move, clone, sync, lock, unlock, slowmode)
            - channel (str, optional): Channel name or ID to operate on
            - category (str, optional): Category name or ID for the channel
            - name (str, optional): New name for the channel
            - topic (str, optional): New topic for the channel
            - position (str, optional): New position for the channel
            - permissions (str, optional): JSON string of permission overwrites
            - slowmode (str, optional): Slowmode delay in seconds
            - reason (str, optional): Reason for the audit log
    """
    if not interaction.guild:
        log.warning("Cannot manage channels: Not in a guild context")
        return False

    # Check permissions
    if not interaction.guild.me.guild_permissions.manage_channels:
        log.warning(f"Bot lacks permission to manage channels in {interaction.guild.name}")
        return False

    # Get parameters
    operation = args.get('operation', '').lower()
    channel_name_or_id = args.get('channel', '')
    category_name_or_id = args.get('category', '')
    new_name = args.get('name', '')
    topic = args.get('topic', '')
    position_str = args.get('position', '')
    permissions_str = args.get('permissions', '')
    slowmode_str = args.get('slowmode', '')
    reason = args.get('reason', 'Channel management command')

    # Find the target channel if specified
    target_channel = None
    if channel_name_or_id:
        try:
            channel_id = int(channel_name_or_id)
            target_channel = interaction.guild.get_channel(channel_id)
        except (ValueError, TypeError):
            # Not an ID, try to find by name
            target_channel = discord.utils.get(interaction.guild.channels, name=channel_name_or_id)

    # Find the category if specified
    category = None
    if category_name_or_id:
        try:
            category_id = int(category_name_or_id)
            category = interaction.guild.get_channel(category_id)
        except (ValueError, TypeError):
            # Not an ID, try to find by name
            category = discord.utils.get(interaction.guild.categories, name=category_name_or_id)

    # Parse position if specified
    position = None
    if position_str:
        try:
            position = int(position_str)
        except ValueError:
            await interaction.response.send_message(f":warning: Invalid position: {position_str}. Must be a number.", ephemeral=True)
            return False

    # Parse slowmode if specified
    slowmode = None
    if slowmode_str:
        try:
            slowmode = int(slowmode_str)
            if slowmode < 0 or slowmode > 21600:  # Discord's limit is 6 hours (21600 seconds)
                await interaction.response.send_message(":warning: Slowmode must be between 0 and 21600 seconds (6 hours).", ephemeral=True)
                return False
        except ValueError:
            await interaction.response.send_message(f":warning: Invalid slowmode: {slowmode_str}. Must be a number.", ephemeral=True)
            return False

    # Parse permissions if specified
    permission_overwrites = None
    if permissions_str:
        try:
            import json
            permissions_data = json.loads(permissions_str)

            # Convert the JSON data to discord.PermissionOverwrite objects
            permission_overwrites = {}
            for target_id_str, overwrite_data in permissions_data.items():
                # Find the target (role or member)
                target = None
                try:
                    target_id = int(target_id_str)
                    # Try to find a role first
                    target = interaction.guild.get_role(target_id)
                    if not target:
                        # If not a role, try to find a member
                        target = interaction.guild.get_member(target_id)
                except (ValueError, TypeError):
                    # Not an ID, skip
                    continue

                if not target:
                    continue

                # Create the permission overwrite
                overwrite = discord.PermissionOverwrite()
                for perm_name, perm_value in overwrite_data.items():
                    if perm_value is True:
                        setattr(overwrite, perm_name, True)
                    elif perm_value is False:
                        setattr(overwrite, perm_name, False)
                    # None (neutral) is the default

                permission_overwrites[target] = overwrite
        except Exception as e:
            log.error(f"Error parsing permissions: {e}")
            await interaction.response.send_message(f":warning: Invalid permissions format: {e}", ephemeral=True)
            return False

    # Execute the requested operation
    try:
        if operation == 'create':
            return await create_channel(interaction, category, new_name, topic, position, permission_overwrites, slowmode, reason)
        elif operation == 'delete':
            return await delete_channel(interaction, target_channel, reason)
        elif operation == 'edit':
            return await edit_channel(interaction, target_channel, new_name, topic, position, slowmode, reason)
        elif operation == 'move':
            return await move_channel(interaction, target_channel, category, position, reason)
        elif operation == 'clone':
            return await clone_channel(interaction, target_channel, new_name, reason)
        elif operation == 'sync':
            return await sync_channel(interaction, target_channel, category, reason)
        elif operation == 'lock':
            return await lock_channel(interaction, target_channel, reason)
        elif operation == 'unlock':
            return await unlock_channel(interaction, target_channel, reason)
        elif operation == 'slowmode':
            return await set_slowmode(interaction, target_channel, slowmode, reason)
        else:
            await interaction.response.send_message(f":warning: Unknown operation: {operation}", ephemeral=True)
            return False
    except Exception as e:
        log.error(f"Error executing channel operation {operation}: {e}", exc_info=True)
        await interaction.response.send_message(f":x: Error executing operation: {e}", ephemeral=True)
        return False

async def create_channel(interaction, category, name, topic, position, permission_overwrites, slowmode, reason):
    """Creates a new channel."""
    if not name:
        await interaction.response.send_message(":warning: Channel name is required for creation.", ephemeral=True)
        return False

    await interaction.response.defer(ephemeral=True)

    try:
        # Create the channel
        channel = await interaction.guild.create_text_channel(
            name=name,
            category=category,
            topic=topic if topic else None,
            position=position,
            overwrites=permission_overwrites,
            slowmode_delay=slowmode,
            reason=reason
        )

        await interaction.followup.send(f":white_check_mark: Channel {channel.mention} created successfully.", ephemeral=True)
        return True
    except discord.Forbidden:
        await interaction.followup.send(":x: I don't have permission to create channels.", ephemeral=True)
        return False
    except discord.HTTPException as e:
        await interaction.followup.send(f":x: Failed to create channel: {e}", ephemeral=True)
        return False

async def delete_channel(interaction, channel, reason):
    """Deletes a channel."""
    if not channel:
        await interaction.response.send_message(":warning: Channel not found.", ephemeral=True)
        return False

    await interaction.response.defer(ephemeral=True)

    try:
        channel_name = channel.name
        await channel.delete(reason=reason)
        await interaction.followup.send(f":white_check_mark: Channel `{channel_name}` deleted successfully.", ephemeral=True)
        return True
    except discord.Forbidden:
        await interaction.followup.send(":x: I don't have permission to delete this channel.", ephemeral=True)
        return False
    except discord.HTTPException as e:
        await interaction.followup.send(f":x: Failed to delete channel: {e}", ephemeral=True)
        return False

async def edit_channel(interaction, channel, name, topic, position, slowmode, reason):
    """Edits a channel's properties."""
    if not channel:
        await interaction.response.send_message(":warning: Channel not found.", ephemeral=True)
        return False

    # Check if there's anything to edit
    if not name and topic == '' and position is None and slowmode is None:
        await interaction.response.send_message(":warning: No changes specified for editing.", ephemeral=True)
        return False

    await interaction.response.defer(ephemeral=True)

    try:
        # Prepare the edit parameters
        edit_params = {}
        if name:
            edit_params['name'] = name
        if topic != '':  # Allow empty topic to clear it
            edit_params['topic'] = topic
        if position is not None:
            edit_params['position'] = position
        if slowmode is not None:
            edit_params['slowmode_delay'] = slowmode
        if reason:
            edit_params['reason'] = reason

        # Edit the channel
        await channel.edit(**edit_params)

        # Prepare a message about what was changed
        changes = []
        if name:
            changes.append(f"name to `{name}`")
        if topic != '':
            changes.append(f"topic to `{topic}`")
        if position is not None:
            changes.append(f"position to `{position}`")
        if slowmode is not None:
            changes.append(f"slowmode to `{slowmode}` seconds")

        changes_str = ", ".join(changes)
        await interaction.followup.send(f":white_check_mark: Channel {channel.mention} updated: {changes_str}.", ephemeral=True)
        return True
    except discord.Forbidden:
        await interaction.followup.send(":x: I don't have permission to edit this channel.", ephemeral=True)
        return False
    except discord.HTTPException as e:
        await interaction.followup.send(f":x: Failed to edit channel: {e}", ephemeral=True)
        return False

async def move_channel(interaction, channel, category, position, reason):
    """Moves a channel to a different category and/or position."""
    if not channel:
        await interaction.response.send_message(":warning: Channel not found.", ephemeral=True)
        return False

    if not category and position is None:
        await interaction.response.send_message(":warning: Either category or position must be specified for moving.", ephemeral=True)
        return False

    await interaction.response.defer(ephemeral=True)

    try:
        # Prepare the edit parameters
        edit_params = {}
        if category:
            edit_params['category'] = category
        if position is not None:
            edit_params['position'] = position
        if reason:
            edit_params['reason'] = reason

        # Move the channel
        await channel.edit(**edit_params)

        # Prepare a message about what was changed
        changes = []
        if category:
            changes.append(f"category to `{category.name}`")
        if position is not None:
            changes.append(f"position to `{position}`")

        changes_str = ", ".join(changes)
        await interaction.followup.send(f":white_check_mark: Channel {channel.mention} moved: {changes_str}.", ephemeral=True)
        return True
    except discord.Forbidden:
        await interaction.followup.send(":x: I don't have permission to move this channel.", ephemeral=True)
        return False
    except discord.HTTPException as e:
        await interaction.followup.send(f":x: Failed to move channel: {e}", ephemeral=True)
        return False

async def clone_channel(interaction, channel, name, reason):
    """Clones a channel."""
    if not channel:
        await interaction.response.send_message(":warning: Channel not found.", ephemeral=True)
        return False

    await interaction.response.defer(ephemeral=True)

    try:
        # Clone the channel
        clone = await channel.clone(name=name if name else None, reason=reason)

        await interaction.followup.send(f":white_check_mark: Channel {channel.mention} cloned to {clone.mention}.", ephemeral=True)
        return True
    except discord.Forbidden:
        await interaction.followup.send(":x: I don't have permission to clone this channel.", ephemeral=True)
        return False
    except discord.HTTPException as e:
        await interaction.followup.send(f":x: Failed to clone channel: {e}", ephemeral=True)
        return False

async def sync_channel(interaction, channel, category, reason):
    """Syncs a channel's permissions with its category."""
    if not channel:
        await interaction.response.send_message(":warning: Channel not found.", ephemeral=True)
        return False

    if not channel.category and not category:
        await interaction.response.send_message(":warning: Channel is not in a category and no category was specified.", ephemeral=True)
        return False

    await interaction.response.defer(ephemeral=True)

    try:
        # If a category was specified, move the channel to that category first
        if category and channel.category != category:
            await channel.edit(category=category, reason=f"{reason} - Moving to category before sync")

        # Sync permissions with the category
        await channel.edit(sync_permissions=True, reason=reason)

        category_name = channel.category.name if channel.category else category.name
        await interaction.followup.send(f":white_check_mark: Channel {channel.mention} permissions synced with category `{category_name}`.", ephemeral=True)
        return True
    except discord.Forbidden:
        await interaction.followup.send(":x: I don't have permission to sync this channel's permissions.", ephemeral=True)
        return False
    except discord.HTTPException as e:
        await interaction.followup.send(f":x: Failed to sync channel permissions: {e}", ephemeral=True)
        return False

async def lock_channel(interaction, channel, reason):
    """Locks a channel by denying @everyone send_messages permission."""
    if not channel:
        await interaction.response.send_message(":warning: Channel not found.", ephemeral=True)
        return False

    await interaction.response.defer(ephemeral=True)

    try:
        # Get the @everyone role
        everyone_role = interaction.guild.default_role

        # Create or update the permission overwrite
        overwrites = channel.overwrites
        if everyone_role in overwrites:
            overwrite = overwrites[everyone_role]
            overwrite.send_messages = False
        else:
            overwrite = discord.PermissionOverwrite(send_messages=False)

        await channel.set_permissions(everyone_role, overwrite=overwrite, reason=reason)

        await interaction.followup.send(f":lock: Channel {channel.mention} has been locked.", ephemeral=True)
        return True
    except discord.Forbidden:
        await interaction.followup.send(":x: I don't have permission to lock this channel.", ephemeral=True)
        return False
    except discord.HTTPException as e:
        await interaction.followup.send(f":x: Failed to lock channel: {e}", ephemeral=True)
        return False

async def unlock_channel(interaction, channel, reason):
    """Unlocks a channel by allowing @everyone send_messages permission."""
    if not channel:
        await interaction.response.send_message(":warning: Channel not found.", ephemeral=True)
        return False

    await interaction.response.defer(ephemeral=True)

    try:
        # Get the @everyone role
        everyone_role = interaction.guild.default_role

        # Create or update the permission overwrite
        overwrites = channel.overwrites
        if everyone_role in overwrites:
            overwrite = overwrites[everyone_role]
            overwrite.send_messages = None  # Reset to neutral (inherit)

            # If all permissions are neutral, remove the overwrite entirely
            if all(getattr(overwrite, perm) is None for perm in dir(overwrite) if not perm.startswith('_')):
                await channel.set_permissions(everyone_role, overwrite=None, reason=reason)
            else:
                await channel.set_permissions(everyone_role, overwrite=overwrite, reason=reason)

        await interaction.followup.send(f":unlock: Channel {channel.mention} has been unlocked.", ephemeral=True)
        return True
    except discord.Forbidden:
        await interaction.followup.send(":x: I don't have permission to unlock this channel.", ephemeral=True)
        return False
    except discord.HTTPException as e:
        await interaction.followup.send(f":x: Failed to unlock channel: {e}", ephemeral=True)
        return False

async def set_slowmode(interaction, channel, slowmode, reason):
    """Sets the slowmode delay for a channel."""
    if not channel:
        await interaction.response.send_message(":warning: Channel not found.", ephemeral=True)
        return False

    if slowmode is None:
        await interaction.response.send_message(":warning: Slowmode delay must be specified.", ephemeral=True)
        return False

    await interaction.response.defer(ephemeral=True)

    try:
        # Set the slowmode delay
        await channel.edit(slowmode_delay=slowmode, reason=reason)

        if slowmode == 0:
            await interaction.followup.send(f":white_check_mark: Slowmode disabled for {channel.mention}.", ephemeral=True)
        else:
            await interaction.followup.send(f":white_check_mark: Slowmode set to {slowmode} seconds for {channel.mention}.", ephemeral=True)
        return True
    except discord.Forbidden:
        await interaction.followup.send(":x: I don't have permission to set slowmode for this channel.", ephemeral=True)
        return False
    except discord.HTTPException as e:
        await interaction.followup.send(f":x: Failed to set slowmode: {e}", ephemeral=True)
        return False
