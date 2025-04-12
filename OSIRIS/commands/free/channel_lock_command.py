# commands/free/channel_lock_command.py
"""
Channel lock command for Discord servers.

This module provides functionality to lock a channel by denying @everyone send_messages permission.
"""

import discord
import logging

log = logging.getLogger('MyBot.Commands.ChannelLock')

async def execute(interaction, bot, args):
    """
    Locks a Discord channel by denying @everyone send_messages permission.

    Args:
        interaction (discord.Interaction): The interaction that triggered the command
        bot (commands.Bot): The bot instance
        args (dict): Command arguments
            - channel (str): Channel name or ID to lock
            - reason (str, optional): Reason for the audit log
    """
    if not interaction.guild:
        log.warning("Cannot lock channel: Not in a guild context")
        await interaction.response.send_message(":warning: This command can only be used in a server.", ephemeral=True)
        return False

    # Check permissions
    if not interaction.guild.me.guild_permissions.manage_channels:
        log.warning(f"Bot lacks permission to manage channels in {interaction.guild.name}")
        await interaction.response.send_message(":warning: I don't have permission to manage channels in this server.", ephemeral=True)
        return False

    # Get parameters
    channel_name_or_id = args.get('channel', '')
    reason = args.get('reason', 'Channel lock command')

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
        # Get the @everyone role
        everyone_role = interaction.guild.default_role

        # Create or update the permission overwrite
        overwrites = target_channel.overwrites
        if everyone_role in overwrites:
            overwrite = overwrites[everyone_role]
            overwrite.send_messages = False
        else:
            overwrite = discord.PermissionOverwrite(send_messages=False)

        await target_channel.set_permissions(everyone_role, overwrite=overwrite, reason=reason)

        await interaction.followup.send(f":lock: Channel {target_channel.mention} has been locked.", ephemeral=True)
        return True
    except discord.Forbidden:
        await interaction.followup.send(":x: I don't have permission to lock this channel.", ephemeral=True)
        return False
    except discord.HTTPException as e:
        await interaction.followup.send(f":x: Failed to lock channel: {e}", ephemeral=True)
        return False
