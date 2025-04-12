# commands/free/channel_delete_command.py
"""
Channel delete command for Discord servers.

This module provides functionality to delete a channel.
"""

import discord
import logging

log = logging.getLogger('MyBot.Commands.ChannelDelete')

async def execute(interaction, bot, args):
    """
    Deletes a Discord channel.

    Args:
        interaction (discord.Interaction): The interaction that triggered the command
        bot (commands.Bot): The bot instance
        args (dict): Command arguments
            - channel (str): Channel name or ID to delete
            - reason (str, optional): Reason for the audit log
    """
    if not interaction.guild:
        log.warning("Cannot delete channel: Not in a guild context")
        await interaction.response.send_message(":warning: This command can only be used in a server.", ephemeral=True)
        return False

    # Check permissions
    if not interaction.guild.me.guild_permissions.manage_channels:
        log.warning(f"Bot lacks permission to manage channels in {interaction.guild.name}")
        await interaction.response.send_message(":warning: I don't have permission to manage channels in this server.", ephemeral=True)
        return False

    # Get parameters
    channel_name_or_id = args.get('channel', '')
    reason = args.get('reason', 'Channel deletion command')

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

    await interaction.response.defer(ephemeral=True)

    try:
        channel_name = target_channel.name
        await target_channel.delete(reason=reason)
        await interaction.followup.send(f":white_check_mark: Channel `{channel_name}` deleted successfully.", ephemeral=True)
        return True
    except discord.Forbidden:
        await interaction.followup.send(":x: I don't have permission to delete this channel.", ephemeral=True)
        return False
    except discord.HTTPException as e:
        await interaction.followup.send(f":x: Failed to delete channel: {e}", ephemeral=True)
        return False
