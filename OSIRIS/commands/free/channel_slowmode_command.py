# commands/free/channel_slowmode_command.py
"""
Channel slowmode command for Discord servers.

This module provides functionality to set the slowmode delay for a channel.
"""

import discord
import logging

log = logging.getLogger('MyBot.Commands.ChannelSlowmode')

async def execute(interaction, bot, args):
    """
    Sets the slowmode delay for a Discord channel.

    Args:
        interaction (discord.Interaction): The interaction that triggered the command
        bot (commands.Bot): The bot instance
        args (dict): Command arguments
            - channel (str): Channel name or ID to set slowmode for
            - slowmode (str): Slowmode delay in seconds (0 to disable)
            - reason (str, optional): Reason for the audit log
    """
    if not interaction.guild:
        log.warning("Cannot set slowmode: Not in a guild context")
        await interaction.response.send_message(":warning: This command can only be used in a server.", ephemeral=True)
        return False

    # Check permissions
    if not interaction.guild.me.guild_permissions.manage_channels:
        log.warning(f"Bot lacks permission to manage channels in {interaction.guild.name}")
        await interaction.response.send_message(":warning: I don't have permission to manage channels in this server.", ephemeral=True)
        return False

    # Get parameters
    channel_name_or_id = args.get('channel', '')
    slowmode_str = args.get('slowmode', '')
    reason = args.get('reason', 'Channel slowmode command')

    if not channel_name_or_id:
        await interaction.response.send_message(":warning: Channel name or ID is required.", ephemeral=True)
        return False

    if not slowmode_str:
        await interaction.response.send_message(":warning: Slowmode delay must be specified.", ephemeral=True)
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

    # Parse slowmode
    try:
        slowmode = int(slowmode_str)
        if slowmode < 0 or slowmode > 21600:  # Discord's limit is 6 hours (21600 seconds)
            await interaction.response.send_message(":warning: Slowmode must be between 0 and 21600 seconds (6 hours).", ephemeral=True)
            return False
    except ValueError:
        await interaction.response.send_message(f":warning: Invalid slowmode: {slowmode_str}. Must be a number.", ephemeral=True)
        return False

    await interaction.response.defer(ephemeral=True)

    try:
        # Set the slowmode delay
        await target_channel.edit(slowmode_delay=slowmode, reason=reason)

        if slowmode == 0:
            await interaction.followup.send(f":white_check_mark: Slowmode disabled for {target_channel.mention}.", ephemeral=True)
        else:
            await interaction.followup.send(f":white_check_mark: Slowmode set to {slowmode} seconds for {target_channel.mention}.", ephemeral=True)
        return True
    except discord.Forbidden:
        await interaction.followup.send(":x: I don't have permission to set slowmode for this channel.", ephemeral=True)
        return False
    except discord.HTTPException as e:
        await interaction.followup.send(f":x: Failed to set slowmode: {e}", ephemeral=True)
        return False
