# commands/free/category_manager_command.py
"""
Category management command for Discord servers.

This module provides functionality to create, delete, rename, move, and list categories,
as well as view detailed information about a specific category.
"""

import discord
import logging
import json
from typing import List, Dict, Any, Optional, Union

log = logging.getLogger('MyBot.Commands.CategoryManager')

async def execute(interaction, bot, args):
    """
    Manages categories in the server.

    Args:
        interaction (discord.Interaction): The interaction that triggered the command
        bot (commands.Bot): The bot instance
        args (dict): Command arguments
            - operation (str): The operation to perform (create, delete, rename, move, list, info)
            - category (str, optional): Category name or ID to operate on
            - name (str, optional): New name for the category
            - position (str, optional): New position for the category
            - permissions (str, optional): JSON string of permission overwrites
            - reason (str, optional): Reason for the audit log
    """
    if not interaction.guild:
        log.warning("Cannot manage categories: Not in a guild context")
        return False

    # Check permissions
    if not interaction.guild.me.guild_permissions.manage_channels:
        log.warning(f"Bot lacks permission to manage channels in {interaction.guild.name}")
        return False

    # Get parameters
    operation = args.get('operation', '').lower()
    category_name_or_id = args.get('category', '')
    new_name = args.get('name', '')
    position_str = args.get('position', '')
    permissions_str = args.get('permissions', '')
    reason = args.get('reason', 'Category management command')

    # Find the target category if specified
    target_category = None
    if category_name_or_id and operation != 'create' and operation != 'list':
        try:
            category_id = int(category_name_or_id)
            target_category = interaction.guild.get_channel(category_id)
        except (ValueError, TypeError):
            # Not an ID, try to find by name
            target_category = discord.utils.get(interaction.guild.categories, name=category_name_or_id)

        if not target_category or not isinstance(target_category, discord.CategoryChannel):
            await interaction.response.send_message(f":warning: Category not found: {category_name_or_id}", ephemeral=True)
            return False

    # Parse position if specified
    position = None
    if position_str:
        try:
            position = int(position_str)
        except ValueError:
            await interaction.response.send_message(f":warning: Invalid position: {position_str}. Must be a number.", ephemeral=True)
            return False

    # Parse permissions if specified
    permission_overwrites = None
    if permissions_str:
        try:
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
            return await create_category(interaction, new_name, position, permission_overwrites, reason)
        elif operation == 'delete':
            return await delete_category(interaction, target_category, reason)
        elif operation == 'rename':
            return await rename_category(interaction, target_category, new_name, reason)
        elif operation == 'move':
            return await move_category(interaction, target_category, position, reason)
        elif operation == 'list':
            return await list_categories(interaction)
        elif operation == 'info':
            return await category_info(interaction, target_category)
        else:
            await interaction.response.send_message(f":warning: Unknown operation: {operation}", ephemeral=True)
            return False
    except Exception as e:
        log.error(f"Error executing category operation {operation}: {e}", exc_info=True)
        await interaction.response.send_message(f":x: Error executing operation: {e}", ephemeral=True)
        return False

async def create_category(interaction, name, position, permission_overwrites, reason):
    """Creates a new category."""
    if not name:
        await interaction.response.send_message(":warning: Category name is required for creation.", ephemeral=True)
        return False

    await interaction.response.defer(ephemeral=True)

    try:
        # Create the category
        category = await interaction.guild.create_category(
            name=name,
            overwrites=permission_overwrites,
            reason=reason,
            position=position
        )

        await interaction.followup.send(f":white_check_mark: Category `{category.name}` created successfully.", ephemeral=True)
        return True
    except discord.Forbidden:
        await interaction.followup.send(":x: I don't have permission to create categories.", ephemeral=True)
        return False
    except discord.HTTPException as e:
        await interaction.followup.send(f":x: Failed to create category: {e}", ephemeral=True)
        return False

async def delete_category(interaction, category, reason):
    """Deletes a category."""
    await interaction.response.defer(ephemeral=True)

    try:
        # Get the category name before deletion
        category_name = category.name

        # Check if the category has channels
        channels = category.channels
        if channels:
            # Ask for confirmation
            await interaction.followup.send(
                f":warning: Category `{category_name}` has {len(channels)} channels. "
                f"These channels will also be deleted. Are you sure you want to proceed?",
                ephemeral=True
            )
            return False

        # Delete the category
        await category.delete(reason=reason)

        await interaction.followup.send(f":white_check_mark: Category `{category_name}` deleted successfully.", ephemeral=True)
        return True
    except discord.Forbidden:
        await interaction.followup.send(":x: I don't have permission to delete this category.", ephemeral=True)
        return False
    except discord.HTTPException as e:
        await interaction.followup.send(f":x: Failed to delete category: {e}", ephemeral=True)
        return False

async def rename_category(interaction, category, name, reason):
    """Renames a category."""
    if not name:
        await interaction.response.send_message(":warning: New category name is required.", ephemeral=True)
        return False

    await interaction.response.defer(ephemeral=True)

    try:
        # Get the old name
        old_name = category.name

        # Rename the category
        await category.edit(name=name, reason=reason)

        await interaction.followup.send(f":white_check_mark: Category renamed from `{old_name}` to `{name}`.", ephemeral=True)
        return True
    except discord.Forbidden:
        await interaction.followup.send(":x: I don't have permission to rename this category.", ephemeral=True)
        return False
    except discord.HTTPException as e:
        await interaction.followup.send(f":x: Failed to rename category: {e}", ephemeral=True)
        return False

async def move_category(interaction, category, position, reason):
    """Moves a category to a new position."""
    if position is None:
        await interaction.response.send_message(":warning: New position is required.", ephemeral=True)
        return False

    await interaction.response.defer(ephemeral=True)

    try:
        # Get the old position
        old_position = category.position

        # Move the category
        await category.edit(position=position, reason=reason)

        await interaction.followup.send(f":white_check_mark: Category `{category.name}` moved from position {old_position} to {position}.", ephemeral=True)
        return True
    except discord.Forbidden:
        await interaction.followup.send(":x: I don't have permission to move this category.", ephemeral=True)
        return False
    except discord.HTTPException as e:
        await interaction.followup.send(f":x: Failed to move category: {e}", ephemeral=True)
        return False

async def list_categories(interaction):
    """Lists all categories in the server."""
    await interaction.response.defer(ephemeral=True)

    # Get all categories
    categories = interaction.guild.categories

    if not categories:
        await interaction.followup.send(":information_source: No categories found in this server.", ephemeral=True)
        return True

    # Create an embed with category information
    embed = discord.Embed(
        title=f"Categories in {interaction.guild.name}",
        description=f"Total: {len(categories)} categories",
        color=discord.Color.blue()
    )

    # Add categories to the embed
    for category in categories:
        channel_count = len(category.channels)
        text_channels = len([c for c in category.channels if isinstance(c, discord.TextChannel)])
        voice_channels = len([c for c in category.channels if isinstance(c, discord.VoiceChannel)])

        embed.add_field(
            name=f"{category.name} (ID: {category.id})",
            value=f"Position: {category.position}\nChannels: {channel_count} ({text_channels} text, {voice_channels} voice)",
            inline=False
        )

    await interaction.followup.send(embed=embed, ephemeral=True)
    return True

async def category_info(interaction, category):
    """Displays detailed information about a category."""
    await interaction.response.defer(ephemeral=True)

    # Create an embed with category information
    embed = discord.Embed(
        title=f"Category Information: {category.name}",
        color=discord.Color.blue()
    )

    # Add basic information
    embed.add_field(name="ID", value=category.id, inline=True)
    embed.add_field(name="Position", value=category.position, inline=True)
    embed.add_field(name="Created", value=f"<t:{int(category.created_at.timestamp())}:R>", inline=True)

    # Add channel information
    channel_count = len(category.channels)
    text_channels = [c for c in category.channels if isinstance(c, discord.TextChannel)]
    voice_channels = [c for c in category.channels if isinstance(c, discord.VoiceChannel)]

    embed.add_field(name="Total Channels", value=channel_count, inline=True)
    embed.add_field(name="Text Channels", value=len(text_channels), inline=True)
    embed.add_field(name="Voice Channels", value=len(voice_channels), inline=True)

    # Add text channels
    if text_channels:
        text_channels_str = "\n".join([f"{channel.mention} (ID: {channel.id})" for channel in text_channels[:10]])
        if len(text_channels) > 10:
            text_channels_str += f"\n... and {len(text_channels) - 10} more"

        embed.add_field(name="Text Channels", value=text_channels_str, inline=False)

    # Add voice channels
    if voice_channels:
        voice_channels_str = "\n".join([f"{channel.name} (ID: {channel.id})" for channel in voice_channels[:10]])
        if len(voice_channels) > 10:
            voice_channels_str += f"\n... and {len(voice_channels) - 10} more"

        embed.add_field(name="Voice Channels", value=voice_channels_str, inline=False)

    # Add permission overwrites
    if category.overwrites:
        overwrites_str = ""
        for target, overwrite in category.overwrites.items():
            target_type = "Role" if isinstance(target, discord.Role) else "Member"
            target_name = target.name if isinstance(target, discord.Role) else f"{target.name}#{target.discriminator}"

            # Count allowed and denied permissions
            allowed = [perm for perm, value in overwrite if value is True]
            denied = [perm for perm, value in overwrite if value is False]

            overwrites_str += f"**{target_type}: {target_name}**\n"
            if allowed:
                overwrites_str += f"✅ Allowed: {', '.join(allowed[:5])}"
                if len(allowed) > 5:
                    overwrites_str += f" and {len(allowed) - 5} more"
                overwrites_str += "\n"

            if denied:
                overwrites_str += f"❌ Denied: {', '.join(denied[:5])}"
                if len(denied) > 5:
                    overwrites_str += f" and {len(denied) - 5} more"
                overwrites_str += "\n"

            overwrites_str += "\n"

        if len(overwrites_str) > 1024:
            overwrites_str = overwrites_str[:1021] + "..."

        embed.add_field(name="Permission Overwrites", value=overwrites_str or "None", inline=False)

    await interaction.followup.send(embed=embed, ephemeral=True)
    return True
