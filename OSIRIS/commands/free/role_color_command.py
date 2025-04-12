# commands/free/role_color_command.py
"""
Role color command for Discord servers.

This module provides functionality to change a role's color.
"""

import discord
import logging

log = logging.getLogger('MyBot.Commands.RoleColor')

async def execute(interaction, bot, args):
    """
    Changes a Discord role's color.

    Args:
        interaction (discord.Interaction): The interaction that triggered the command
        bot (commands.Bot): The bot instance
        args (dict): Command arguments
            - role (str): Role name or ID to change color
            - color (str): New color for the role (hex code)
            - reason (str, optional): Reason for the audit log
    """
    if not interaction.guild:
        log.warning("Cannot change role color: Not in a guild context")
        await interaction.response.send_message(":warning: This command can only be used in a server.", ephemeral=True)
        return False

    # Check permissions
    if not interaction.guild.me.guild_permissions.manage_roles:
        log.warning(f"Bot lacks permission to manage roles in {interaction.guild.name}")
        await interaction.response.send_message(":warning: I don't have permission to manage roles in this server.", ephemeral=True)
        return False

    # Get parameters
    role_name_or_id = args.get('role', '')
    color_str = args.get('color', '')
    reason = args.get('reason', 'Role color change command')

    if not role_name_or_id:
        await interaction.response.send_message(":warning: Role name or ID is required.", ephemeral=True)
        return False

    if not color_str:
        await interaction.response.send_message(":warning: Color is required (hex code, e.g., #FF0000).", ephemeral=True)
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
        await interaction.response.send_message(":warning: I cannot change the color of a role that is higher than or equal to my highest role.", ephemeral=True)
        return False

    # Parse color
    try:
        # Remove # if present
        if color_str.startswith('#'):
            color_str = color_str[1:]
        # Convert hex to decimal
        color_int = int(color_str, 16)
        color = discord.Color(color_int)
    except ValueError:
        await interaction.response.send_message(f":warning: Invalid color: {color_str}. Must be a hex color code (e.g., #FF0000).", ephemeral=True)
        return False

    await interaction.response.defer(ephemeral=True)

    try:
        # Get the old color for display
        old_color = f"#{target_role.color.value:06x}" if target_role.color.value else "None"
        
        # Change the role color
        await target_role.edit(color=color, reason=reason)
        
        # Create an embed to show the color change
        embed = discord.Embed(
            title=f"Role Color Changed: {target_role.name}",
            description=f"Color changed from {old_color} to #{color.value:06x}",
            color=color
        )
        
        await interaction.followup.send(embed=embed, ephemeral=True)
        return True
    except discord.Forbidden:
        await interaction.followup.send(":x: I don't have permission to change this role's color.", ephemeral=True)
        return False
    except discord.HTTPException as e:
        await interaction.followup.send(f":x: Failed to change role color: {e}", ephemeral=True)
        return False
