# commands/free/channel_edit_command.py
"""
Channel edit command for Discord servers.

This module provides functionality to edit a channel's properties.
"""

import discord
import logging

log = logging.getLogger('MyBot.Commands.ChannelEdit')

async def execute(interaction, bot, args):
    """
    Edits a Discord channel's properties.

    Args:
        interaction (discord.Interaction): The interaction that triggered the command
        bot (commands.Bot): The bot instance
        args (dict): Command arguments
            - channel (str): Channel name or ID to edit
            - name (str, optional): New name for the channel
            - topic (str, optional): New topic for the channel
            - position (str, optional): New position for the channel
            - slowmode (str, optional): Slowmode delay in seconds
            - reason (str, optional): Reason for the audit log
    """
    if not interaction.guild:
        log.warning("Cannot edit channel: Not in a guild context")
        await interaction.response.send_message(":warning: This command can only be used in a server.", ephemeral=True)
        return False

    # Check permissions
    if not interaction.guild.me.guild_permissions.manage_channels:
        log.warning(f"Bot lacks permission to manage channels in {interaction.guild.name}")
        await interaction.response.send_message(":warning: I don't have permission to manage channels in this server.", ephemeral=True)
        return False

    # Get parameters
    channel_name_or_id = args.get('channel', '')
    new_name = args.get('name', '')
    topic = args.get('topic', '')
    position_str = args.get('position', '')
    slowmode_str = args.get('slowmode', '')
    reason = args.get('reason', 'Channel edit command')

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

    # Check if there's anything to edit
    if not new_name and topic == '' and position is None and slowmode is None:
        await interaction.response.send_message(":warning: No changes specified for editing.", ephemeral=True)
        return False

    await interaction.response.defer(ephemeral=True)

    try:
        # Prepare the edit parameters
        edit_params = {}
        if new_name:
            edit_params['name'] = new_name
        if topic != '':  # Allow empty topic to clear it
            edit_params['topic'] = topic
        if position is not None:
            edit_params['position'] = position
        if slowmode is not None:
            edit_params['slowmode_delay'] = slowmode
        if reason:
            edit_params['reason'] = reason

        # Edit the channel
        await target_channel.edit(**edit_params)

        # Prepare a message about what was changed
        changes = []
        if new_name:
            changes.append(f"name to `{new_name}`")
        if topic != '':
            changes.append(f"topic to `{topic}`")
        if position is not None:
            changes.append(f"position to `{position}`")
        if slowmode is not None:
            changes.append(f"slowmode to `{slowmode}` seconds")

        changes_str = ", ".join(changes)
        await interaction.followup.send(f":white_check_mark: Channel {target_channel.mention} updated: {changes_str}.", ephemeral=True)
        return True
    except discord.Forbidden:
        await interaction.followup.send(":x: I don't have permission to edit this channel.", ephemeral=True)
        return False
    except discord.HTTPException as e:
        await interaction.followup.send(f":x: Failed to edit channel: {e}", ephemeral=True)
        return False
