# commands/free/role_delete_command.py
"""
Role delete command for Discord servers.

This module provides functionality to delete a role.
"""

import discord
import logging

log = logging.getLogger('MyBot.Commands.RoleDelete')

async def execute(interaction, bot, args):
    """
    Deletes a Discord role.

    Args:
        interaction (discord.Interaction): The interaction that triggered the command
        bot (commands.Bot): The bot instance
        args (dict): Command arguments
            - role (str): Role name or ID to delete
            - reason (str, optional): Reason for the audit log
    """
    if not interaction.guild:
        log.warning("Cannot delete role: Not in a guild context")
        await interaction.response.send_message(":warning: This command can only be used in a server.", ephemeral=True)
        return False

    # Check permissions
    if not interaction.guild.me.guild_permissions.manage_roles:
        log.warning(f"Bot lacks permission to manage roles in {interaction.guild.name}")
        await interaction.response.send_message(":warning: I don't have permission to manage roles in this server.", ephemeral=True)
        return False

    # Get parameters
    role_name_or_id = args.get('role', '')
    reason = args.get('reason', 'Role deletion command')

    if not role_name_or_id:
        await interaction.response.send_message(":warning: Role name or ID is required.", ephemeral=True)
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
        await interaction.response.send_message(":warning: I cannot delete a role that is higher than or equal to my highest role.", ephemeral=True)
        return False

    await interaction.response.defer(ephemeral=True)

    try:
        role_name = target_role.name
        await target_role.delete(reason=reason)
        await interaction.followup.send(f":white_check_mark: Role `{role_name}` deleted successfully.", ephemeral=True)
        return True
    except discord.Forbidden:
        await interaction.followup.send(":x: I don't have permission to delete this role.", ephemeral=True)
        return False
    except discord.HTTPException as e:
        await interaction.followup.send(f":x: Failed to delete role: {e}", ephemeral=True)
        return False
