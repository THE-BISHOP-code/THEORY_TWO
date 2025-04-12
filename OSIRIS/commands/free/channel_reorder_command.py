# commands/free/channel_reorder_command.py
"""
Channel reordering command for Discord servers.

This module provides functionality to reorder channels within a category or the entire server,
allowing for alphabetical sorting, custom ordering, and position adjustments.
"""

import discord
import logging
from typing import List, Optional, Union

log = logging.getLogger('MyBot.Commands.ChannelReorder')

async def execute(interaction, bot, args):
    """
    Reorders channels in a category or the entire server.

    Args:
        interaction (discord.Interaction): The interaction that triggered the command
        bot (commands.Bot): The bot instance
        args (dict): Command arguments
            - channels (str): Comma-separated list of channel names or IDs in desired order
            - category (str, optional): Category name or ID to reorder channels within
            - alphabetical (str, optional): If "true", sorts channels alphabetically
            - reverse (str, optional): If "true", reverses the order
    """
    if not interaction.guild:
        log.warning("Cannot reorder channels: Not in a guild context")
        return False

    # Check permissions
    if not interaction.guild.me.guild_permissions.manage_channels:
        log.warning(f"Bot lacks permission to manage channels in {interaction.guild.name}")
        return False

    # Get parameters
    channels_str = args.get('channels', '')
    category_name_or_id = args.get('category', '')
    alphabetical = args.get('alphabetical', 'false').lower() == 'true'
    reverse = args.get('reverse', 'false').lower() == 'true'

    # Get the category if specified
    category = None
    if category_name_or_id:
        try:
            category_id = int(category_name_or_id)
            category = interaction.guild.get_channel(category_id)
        except (ValueError, TypeError):
            # Not an ID, try to find by name
            category = discord.utils.get(interaction.guild.categories, name=category_name_or_id)

        if not category:
            log.error(f"Category '{category_name_or_id}' not found")
            return False

    # Get the channels to reorder
    channels_to_reorder = []

    if category:
        # Get all channels in the category
        channels_to_reorder = category.channels
    else:
        # Get all channels in the guild
        channels_to_reorder = [ch for ch in interaction.guild.channels if not isinstance(ch, discord.CategoryChannel)]

    # Sort channels if alphabetical is specified
    if alphabetical:
        channels_to_reorder = sorted(channels_to_reorder, key=lambda ch: ch.name)
        if reverse:
            channels_to_reorder.reverse()
    # Otherwise, use the specified order if provided
    elif channels_str:
        channel_names_or_ids = [name.strip() for name in channels_str.split(',')]

        # Create a new list for the ordered channels
        ordered_channels = []

        for name_or_id in channel_names_or_ids:
            # Try to find the channel by ID first
            channel = None
            try:
                channel_id = int(name_or_id)
                channel = interaction.guild.get_channel(channel_id)
            except (ValueError, TypeError):
                # Not an ID, try to find by name
                channel = discord.utils.get(channels_to_reorder, name=name_or_id)

            if channel and channel in channels_to_reorder:
                ordered_channels.append(channel)

        # Only use the ordered list if we found all channels
        if ordered_channels:
            channels_to_reorder = ordered_channels
            if reverse:
                channels_to_reorder.reverse()
    elif reverse:
        # Just reverse the current order
        channels_to_reorder.reverse()

    # Reorder the channels
    try:
        for i, channel in enumerate(channels_to_reorder):
            await channel.edit(position=i)

        log.info(f"Reordered {len(channels_to_reorder)} channels in {category.name if category else interaction.guild.name}")
        return True
    except discord.Forbidden:
        log.error(f"Forbidden: Bot lacks permission to reorder channels")
        return False
    except discord.HTTPException as e:
        log.error(f"HTTP error reordering channels: {e}")
        return False
    except Exception as e:
        log.error(f"Error reordering channels: {e}", exc_info=True)
        return False
