# commands/free/channel_sync_command.py
"""
Channel sync command for Discord servers.

This module provides functionality to sync a channel's permissions with its category.
"""

import discord
import logging

log = logging.getLogger('MyBot.Commands.ChannelSync')

async def execute(interaction, bot, args):
    """
    Syncs a Discord channel's permissions with its category.

    Args:
        interaction (discord.Interaction): The interaction that triggered the command
        bot (commands.Bot): The bot instance
        args (dict): Command arguments
            - channel (str): Channel name or ID to sync
            - category (str, optional): Category name or ID to sync with (if different from current)
            - reason (str, optional): Reason for the audit log
    """
    if not interaction.guild:
        log.warning("Cannot sync channel: Not in a guild context")
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
    reason = args.get('reason', 'Channel sync command')

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

    if not target_channel.category and not category:
        await interaction.response.send_message(":warning: Channel is not in a category and no category was specified.", ephemeral=True)
        return False

    await interaction.response.defer(ephemeral=True)

    try:
        # If a category was specified, move the channel to that category first
        if category and target_channel.category != category:
            await target_channel.edit(category=category, reason=f"{reason} - Moving to category before sync")

        # Sync permissions with the category
        await target_channel.edit(sync_permissions=True, reason=reason)

        category_name = target_channel.category.name if target_channel.category else category.name
        await interaction.followup.send(f":white_check_mark: Channel {target_channel.mention} permissions synced with category `{category_name}`.", ephemeral=True)
        return True
    except discord.Forbidden:
        await interaction.followup.send(":x: I don't have permission to sync this channel's permissions.", ephemeral=True)
        return False
    except discord.HTTPException as e:
        await interaction.followup.send(f":x: Failed to sync channel permissions: {e}", ephemeral=True)
        return False
