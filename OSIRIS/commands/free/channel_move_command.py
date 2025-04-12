# commands/free/channel_move_command.py
"""
Channel move command for Discord servers.

This module provides functionality to move a channel to a different category and/or position.
"""

import discord
import logging

log = logging.getLogger('MyBot.Commands.ChannelMove')

async def execute(interaction, bot, args):
    """
    Moves a Discord channel to a different category and/or position.

    Args:
        interaction (discord.Interaction): The interaction that triggered the command
        bot (commands.Bot): The bot instance
        args (dict): Command arguments
            - channel (str): Channel name or ID to move
            - category (str, optional): Category name or ID to move the channel to
            - position (str, optional): New position for the channel
            - reason (str, optional): Reason for the audit log
    """
    if not interaction.guild:
        log.warning("Cannot move channel: Not in a guild context")
        await interaction.response.send_message(":warning: This command can only be used in a server.", ephemeral=True)
        return False

    # Check permissions
    if not interaction.guild.me.guild_permissions.manage_channels:
        log.warning(f"Bot lacks permission to manage channels in {interaction.guild.name}")
        await interaction.response.send_message(":warning: I don't have permission to manage channels in this server.", ephemeral=True)
        return False

    # Get parameters
    channel_name_or_id = args.get('channel', '')
    category_name_or_id = args.get('category', '')
    position_str = args.get('position', '')
    reason = args.get('reason', 'Channel move command')

    if not channel_name_or_id:
        await interaction.response.send_message(":warning: Channel name or ID is required.", ephemeral=True)
        return False

    # Find the target channel
    target_channel = None
    try:
        channel_id = int(channel_name_or_id)
        target_channel = interaction.guild.get_channel(channel_id)
    except (ValueError, TypeError):
        # Not an ID, try to find by name
        target_channel = discord.utils.get(interaction.guild.channels, name=channel_name_or_id)

    if not target_channel:
        await interaction.response.send_message(f":warning: Channel '{channel_name_or_id}' not found.", ephemeral=True)
        return False

    # Find the category if specified
    category = None
    if category_name_or_id:
        try:
            category_id = int(category_name_or_id)
            category = interaction.guild.get_channel(category_id)
        except (ValueError, TypeError):
            # Not an ID, try to find by name
            category = discord.utils.get(interaction.guild.categories, name=category_name_or_id)

        if not category:
            await interaction.response.send_message(f":warning: Category '{category_name_or_id}' not found.", ephemeral=True)
            return False

    # Parse position if specified
    position = None
    if position_str:
        try:
            position = int(position_str)
        except ValueError:
            await interaction.response.send_message(f":warning: Invalid position: {position_str}. Must be a number.", ephemeral=True)
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
        await target_channel.edit(**edit_params)

        # Prepare a message about what was changed
        changes = []
        if category:
            changes.append(f"category to `{category.name}`")
        if position is not None:
            changes.append(f"position to `{position}`")

        changes_str = ", ".join(changes)
        await interaction.followup.send(f":white_check_mark: Channel {target_channel.mention} moved: {changes_str}.", ephemeral=True)
        return True
    except discord.Forbidden:
        await interaction.followup.send(":x: I don't have permission to move this channel.", ephemeral=True)
        return False
    except discord.HTTPException as e:
        await interaction.followup.send(f":x: Failed to move channel: {e}", ephemeral=True)
        return False
