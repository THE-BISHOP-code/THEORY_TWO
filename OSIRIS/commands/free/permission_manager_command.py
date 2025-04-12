# commands/free/permission_manager_command.py
"""
Permission management command for Discord servers.

This module provides comprehensive functionality to manage permissions for roles and users
in channels, including viewing, setting, clearing, copying, and syncing permissions.
"""

import discord
import logging
import json
from typing import List, Dict, Any, Optional, Union

log = logging.getLogger('MyBot.Commands.PermissionManager')

# List of all Discord permissions
ALL_PERMISSIONS = [
    'add_reactions', 'administrator', 'attach_files', 'ban_members',
    'change_nickname', 'connect', 'create_instant_invite', 'deafen_members',
    'embed_links', 'external_emojis', 'kick_members', 'manage_channels',
    'manage_emojis', 'manage_guild', 'manage_messages', 'manage_nicknames',
    'manage_roles', 'manage_webhooks', 'mention_everyone', 'move_members',
    'mute_members', 'priority_speaker', 'read_message_history', 'read_messages',
    'send_messages', 'send_tts_messages', 'speak', 'stream', 'use_voice_activation',
    'view_audit_log', 'view_channel', 'view_guild_insights'
]

async def execute(interaction, bot, args):
    """
    Manages permissions for roles and users in channels.

    Args:
        interaction (discord.Interaction): The interaction that triggered the command
        bot (commands.Bot): The bot instance
        args (dict): Command arguments
            - operation (str): The operation to perform (view, set, clear, copy, sync)
            - channel (str): Channel name or ID to manage permissions for
            - target (str): Target role or user name/ID to manage permissions for
            - permissions (str, optional): JSON string of permission values to set
            - allow (str, optional): Comma-separated list of permissions to allow
            - deny (str, optional): Comma-separated list of permissions to deny
            - neutral (str, optional): Comma-separated list of permissions to set to neutral
            - source_channel (str, optional): Source channel to copy permissions from
            - reason (str, optional): Reason for the audit log
    """
    if not interaction.guild:
        log.warning("Cannot manage permissions: Not in a guild context")
        return False

    # Check permissions
    if not interaction.guild.me.guild_permissions.manage_roles:
        log.warning(f"Bot lacks permission to manage roles in {interaction.guild.name}")
        return False

    # Get parameters
    operation = args.get('operation', '').lower()
    channel_name_or_id = args.get('channel', '')
    target_name_or_id = args.get('target', '')
    permissions_str = args.get('permissions', '')
    allow_str = args.get('allow', '')
    deny_str = args.get('deny', '')
    neutral_str = args.get('neutral', '')
    source_channel_name_or_id = args.get('source_channel', '')
    reason = args.get('reason', 'Permission management command')

    # Find the target channel
    channel = None
    if channel_name_or_id:
        try:
            channel_id = int(channel_name_or_id)
            channel = interaction.guild.get_channel(channel_id)
        except (ValueError, TypeError):
            # Not an ID, try to find by name
            channel = discord.utils.get(interaction.guild.channels, name=channel_name_or_id)

    if not channel:
        await interaction.response.send_message(":warning: Channel not found.", ephemeral=True)
        return False

    # Find the source channel if specified
    source_channel = None
    if source_channel_name_or_id:
        try:
            source_channel_id = int(source_channel_name_or_id)
            source_channel = interaction.guild.get_channel(source_channel_id)
        except (ValueError, TypeError):
            # Not an ID, try to find by name
            source_channel = discord.utils.get(interaction.guild.channels, name=source_channel_name_or_id)

    # Find the target (role or user)
    target = None
    is_role = True

    if target_name_or_id:
        # Check if it's a mention
        if target_name_or_id.startswith('<@') and target_name_or_id.endswith('>'):
            # It's a user mention
            user_id_str = target_name_or_id.strip('<@!>')
            try:
                user_id = int(user_id_str)
                target = interaction.guild.get_member(user_id)
                is_role = False
            except (ValueError, TypeError):
                pass
        elif target_name_or_id.startswith('<@&') and target_name_or_id.endswith('>'):
            # It's a role mention
            role_id_str = target_name_or_id.strip('<@&>')
            try:
                role_id = int(role_id_str)
                target = interaction.guild.get_role(role_id)
            except (ValueError, TypeError):
                pass
        else:
            # Try to find by ID first
            try:
                target_id = int(target_name_or_id)
                # Try as role first
                target = interaction.guild.get_role(target_id)
                if not target:
                    # Try as user
                    target = interaction.guild.get_member(target_id)
                    if target:
                        is_role = False
            except (ValueError, TypeError):
                # Not an ID, try to find by name
                # Try as role first
                target = discord.utils.get(interaction.guild.roles, name=target_name_or_id)
                if not target:
                    # Try as user
                    target = discord.utils.get(interaction.guild.members, name=target_name_or_id)
                    if target:
                        is_role = False

    if not target and operation != 'view':
        await interaction.response.send_message(":warning: Target role or user not found.", ephemeral=True)
        return False

    # Parse permissions from JSON if provided
    permission_overwrite = None
    if permissions_str:
        try:
            permissions_data = json.loads(permissions_str)
            permission_overwrite = discord.PermissionOverwrite()

            for perm_name, perm_value in permissions_data.items():
                if perm_name in ALL_PERMISSIONS:
                    if perm_value is True:
                        setattr(permission_overwrite, perm_name, True)
                    elif perm_value is False:
                        setattr(permission_overwrite, perm_name, False)
                    else:
                        setattr(permission_overwrite, perm_name, None)
        except Exception as e:
            log.error(f"Error parsing permissions JSON: {e}")
            await interaction.response.send_message(f":warning: Invalid permissions format: {e}", ephemeral=True)
            return False

    # Parse allow, deny, and neutral permissions if provided
    if allow_str or deny_str or neutral_str:
        if not permission_overwrite:
            permission_overwrite = discord.PermissionOverwrite()

        # Process allow permissions
        if allow_str:
            allow_perms = [p.strip() for p in allow_str.split(',')]
            for perm in allow_perms:
                if perm in ALL_PERMISSIONS:
                    setattr(permission_overwrite, perm, True)

        # Process deny permissions
        if deny_str:
            deny_perms = [p.strip() for p in deny_str.split(',')]
            for perm in deny_perms:
                if perm in ALL_PERMISSIONS:
                    setattr(permission_overwrite, perm, False)

        # Process neutral permissions
        if neutral_str:
            neutral_perms = [p.strip() for p in neutral_str.split(',')]
            for perm in neutral_perms:
                if perm in ALL_PERMISSIONS:
                    setattr(permission_overwrite, perm, None)

    # Execute the requested operation
    try:
        if operation == 'view':
            return await view_permissions(interaction, channel, target)
        elif operation == 'set':
            return await set_permissions(interaction, channel, target, is_role, permission_overwrite, reason)
        elif operation == 'clear':
            return await clear_permissions(interaction, channel, target, is_role, reason)
        elif operation == 'copy':
            return await copy_permissions(interaction, channel, source_channel, target, is_role, reason)
        elif operation == 'sync':
            return await sync_permissions(interaction, channel, reason)
        else:
            await interaction.response.send_message(f":warning: Unknown operation: {operation}", ephemeral=True)
            return False
    except Exception as e:
        log.error(f"Error executing permission operation {operation}: {e}", exc_info=True)
        await interaction.response.send_message(f":x: Error executing operation: {e}", ephemeral=True)
        return False

async def view_permissions(interaction, channel, target=None):
    """Views permissions for a channel, optionally for a specific target."""
    await interaction.response.defer(ephemeral=True)

    if target:
        # View permissions for a specific target
        overwrite = channel.overwrites_for(target)

        # Create an embed with permission information
        embed = discord.Embed(
            title=f"Permissions for {target.name} in #{channel.name}",
            color=discord.Color.blue()
        )

        # Add permission fields
        allowed = []
        denied = []
        neutral = []

        for perm, value in overwrite:
            if value is True:
                allowed.append(perm)
            elif value is False:
                denied.append(perm)
            else:
                neutral.append(perm)

        if allowed:
            embed.add_field(name="✅ Allowed", value=", ".join(allowed) or "None", inline=False)

        if denied:
            embed.add_field(name="❌ Denied", value=", ".join(denied) or "None", inline=False)

        if neutral:
            embed.add_field(name="➖ Neutral (Inherited)", value=", ".join(neutral) or "None", inline=False)

        await interaction.followup.send(embed=embed, ephemeral=True)
    else:
        # View permissions for all targets
        overwrites = channel.overwrites

        if not overwrites:
            await interaction.followup.send(f":information_source: No permission overwrites set for #{channel.name}.", ephemeral=True)
            return True

        # Create an embed with permission information
        embed = discord.Embed(
            title=f"Permission Overwrites for #{channel.name}",
            description=f"Total: {len(overwrites)} overwrites",
            color=discord.Color.blue()
        )

        # Add each overwrite
        for target, overwrite in overwrites.items():
            # Count allowed and denied permissions
            allowed_count = 0
            denied_count = 0

            for perm, value in overwrite:
                if value is True:
                    allowed_count += 1
                elif value is False:
                    denied_count += 1

            # Add field for this target
            target_type = "Role" if isinstance(target, discord.Role) else "Member"
            embed.add_field(
                name=f"{target_type}: {target.name}",
                value=f"✅ {allowed_count} allowed, ❌ {denied_count} denied",
                inline=True
            )

        await interaction.followup.send(embed=embed, ephemeral=True)

    return True

async def set_permissions(interaction, channel, target, is_role, permission_overwrite, reason):
    """Sets permissions for a target in a channel."""
    if not permission_overwrite:
        await interaction.response.send_message(":warning: No permissions specified to set.", ephemeral=True)
        return False

    await interaction.response.defer(ephemeral=True)

    try:
        await channel.set_permissions(target, overwrite=permission_overwrite, reason=reason)

        target_type = "role" if is_role else "user"
        await interaction.followup.send(f":white_check_mark: Permissions updated for {target_type} {target.mention} in {channel.mention}.", ephemeral=True)
        return True
    except discord.Forbidden:
        await interaction.followup.send(":x: I don't have permission to set channel permissions.", ephemeral=True)
        return False
    except discord.HTTPException as e:
        await interaction.followup.send(f":x: Failed to set permissions: {e}", ephemeral=True)
        return False

async def clear_permissions(interaction, channel, target, is_role, reason):
    """Clears all permission overwrites for a target in a channel."""
    await interaction.response.defer(ephemeral=True)

    try:
        await channel.set_permissions(target, overwrite=None, reason=reason)

        target_type = "role" if is_role else "user"
        await interaction.followup.send(f":white_check_mark: Permissions cleared for {target_type} {target.mention} in {channel.mention}.", ephemeral=True)
        return True
    except discord.Forbidden:
        await interaction.followup.send(":x: I don't have permission to clear channel permissions.", ephemeral=True)
        return False
    except discord.HTTPException as e:
        await interaction.followup.send(f":x: Failed to clear permissions: {e}", ephemeral=True)
        return False

async def copy_permissions(interaction, channel, source_channel, target, is_role, reason):
    """Copies permissions for a target from one channel to another."""
    if not source_channel:
        await interaction.response.send_message(":warning: Source channel not found.", ephemeral=True)
        return False

    await interaction.response.defer(ephemeral=True)

    try:
        # Get the permission overwrite from the source channel
        source_overwrite = source_channel.overwrites_for(target)

        # Set the permissions in the target channel
        await channel.set_permissions(target, overwrite=source_overwrite, reason=reason)

        target_type = "role" if is_role else "user"
        await interaction.followup.send(
            f":white_check_mark: Permissions for {target_type} {target.mention} copied from {source_channel.mention} to {channel.mention}.",
            ephemeral=True
        )
        return True
    except discord.Forbidden:
        await interaction.followup.send(":x: I don't have permission to set channel permissions.", ephemeral=True)
        return False
    except discord.HTTPException as e:
        await interaction.followup.send(f":x: Failed to copy permissions: {e}", ephemeral=True)
        return False

async def sync_permissions(interaction, channel, reason):
    """Syncs permissions with the parent category."""
    if not channel.category:
        await interaction.response.send_message(":warning: Channel is not in a category.", ephemeral=True)
        return False

    await interaction.response.defer(ephemeral=True)

    try:
        # Sync permissions with the category
        await channel.edit(sync_permissions=True, reason=reason)

        await interaction.followup.send(
            f":white_check_mark: Permissions for {channel.mention} synced with category {channel.category.name}.",
            ephemeral=True
        )
        return True
    except discord.Forbidden:
        await interaction.followup.send(":x: I don't have permission to sync channel permissions.", ephemeral=True)
        return False
    except discord.HTTPException as e:
        await interaction.followup.send(f":x: Failed to sync permissions: {e}", ephemeral=True)
        return False
