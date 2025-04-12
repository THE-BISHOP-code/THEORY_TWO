# commands/free/role_hoist_command.py
"""
Role hoist command for Discord servers.

This module provides functionality to toggle whether a role is displayed separately in the member list.
"""

import discord
import logging

log = logging.getLogger('MyBot.Commands.RoleHoist')

async def execute(interaction, bot, args):
    """
    Toggles whether a Discord role is displayed separately in the member list.

    Args:
        interaction (discord.Interaction): The interaction that triggered the command
        bot (commands.Bot): The bot instance
        args (dict): Command arguments
            - role (str): Role name or ID to modify
            - hoist (str): Whether the role should be displayed separately (true/false)
            - reason (str, optional): Reason for the audit log
    """
    if not interaction.guild:
        log.warning("Cannot change role hoist: Not in a guild context")
        await interaction.response.send_message(":warning: This command can only be used in a server.", ephemeral=True)
        return False

    # Check permissions
    if not interaction.guild.me.guild_permissions.manage_roles:
        log.warning(f"Bot lacks permission to manage roles in {interaction.guild.name}")
        await interaction.response.send_message(":warning: I don't have permission to manage roles in this server.", ephemeral=True)
        return False

    # Get parameters
    role_name_or_id = args.get('role', '')
    hoist_str = args.get('hoist', '')
    reason = args.get('reason', 'Role hoist change command')

    if not role_name_or_id:
        await interaction.response.send_message(":warning: Role name or ID is required.", ephemeral=True)
        return False

    if not hoist_str:
        await interaction.response.send_message(":warning: Hoist value is required (true/false).", ephemeral=True)
        return False

    # Find the target role
    target_role = None
    try:
        role_id = int(role_name_or_id)
        target_role = interaction.guild.get_role(role_id)
    except (ValueError, TypeError):
        # Not an ID, try to find by name
        target_role = discord.utils.get(interaction.guild.roles, name=role_name_or_id)

    if not target_role:
        await interaction.response.send_message(f":warning: Role '{role_name_or_id}' not found.", ephemeral=True)
        return False

    # Check if the bot can manage this role (role hierarchy)
    if target_role >= interaction.guild.me.top_role:
        await interaction.response.send_message(":warning: I cannot modify a role that is higher than or equal to my highest role.", ephemeral=True)
        return False

    # Parse hoist value
    hoist_str = hoist_str.lower()
    if hoist_str in ('true', 'yes', '1'):
        hoist = True
    elif hoist_str in ('false', 'no', '0'):
        hoist = False
    else:
        await interaction.response.send_message(f":warning: Invalid hoist value: {hoist_str}. Must be true/false.", ephemeral=True)
        return False

    await interaction.response.defer(ephemeral=True)

    try:
        # Check if the role's hoist status is already set to the requested value
        if target_role.hoist == hoist:
            status = "displayed separately" if hoist else "not displayed separately"
            await interaction.followup.send(f":information_source: Role `{target_role.name}` is already {status} in the member list.", ephemeral=True)
            return True

        # Change the role's hoist status
        await target_role.edit(hoist=hoist, reason=reason)
        
        status = "will now be displayed separately" if hoist else "will no longer be displayed separately"
        await interaction.followup.send(f":white_check_mark: Role `{target_role.name}` {status} in the member list.", ephemeral=True)
        return True
    except discord.Forbidden:
        await interaction.followup.send(":x: I don't have permission to modify this role.", ephemeral=True)
        return False
    except discord.HTTPException as e:
        await interaction.followup.send(f":x: Failed to change role hoist status: {e}", ephemeral=True)
        return False
