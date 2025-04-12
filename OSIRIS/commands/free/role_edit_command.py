# commands/free/role_edit_command.py
"""
Role edit command for Discord servers.

This module provides functionality to edit a role's properties.
"""

import discord
import logging
import json

log = logging.getLogger('MyBot.Commands.RoleEdit')

async def execute(interaction, bot, args):
    """
    Edits a Discord role's properties.

    Args:
        interaction (discord.Interaction): The interaction that triggered the command
        bot (commands.Bot): The bot instance
        args (dict): Command arguments
            - role (str): Role name or ID to edit
            - name (str, optional): New name for the role
            - color (str, optional): New color for the role (hex code)
            - hoist (str, optional): Whether the role should be displayed separately (true/false)
            - mentionable (str, optional): Whether the role should be mentionable (true/false)
            - permissions (str, optional): JSON string of permission values
            - position (str, optional): New position for the role
            - reason (str, optional): Reason for the audit log
    """
    if not interaction.guild:
        log.warning("Cannot edit role: Not in a guild context")
        await interaction.response.send_message(":warning: This command can only be used in a server.", ephemeral=True)
        return False

    # Check permissions
    if not interaction.guild.me.guild_permissions.manage_roles:
        log.warning(f"Bot lacks permission to manage roles in {interaction.guild.name}")
        await interaction.response.send_message(":warning: I don't have permission to manage roles in this server.", ephemeral=True)
        return False

    # Get parameters
    role_name_or_id = args.get('role', '')
    new_name = args.get('name', '')
    color_str = args.get('color', '')
    hoist_str = args.get('hoist', '')
    mentionable_str = args.get('mentionable', '')
    permissions_str = args.get('permissions', '')
    position_str = args.get('position', '')
    reason = args.get('reason', 'Role edit command')

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
        await interaction.response.send_message(":warning: I cannot edit a role that is higher than or equal to my highest role.", ephemeral=True)
        return False

    # Parse color if specified
    color = None
    if color_str:
        try:
            # Remove # if present
            if color_str.startswith('#'):
                color_str = color_str[1:]
            # Convert hex to decimal
            color_int = int(color_str, 16)
            color = discord.Color(color_int)
        except ValueError:
            await interaction.response.send_message(f":warning: Invalid color: {color_str}. Must be a hex color code.", ephemeral=True)
            return False

    # Parse hoist if specified
    hoist = None
    if hoist_str:
        hoist_str = hoist_str.lower()
        if hoist_str in ('true', 'yes', '1'):
            hoist = True
        elif hoist_str in ('false', 'no', '0'):
            hoist = False
        else:
            await interaction.response.send_message(f":warning: Invalid hoist value: {hoist_str}. Must be true/false.", ephemeral=True)
            return False

    # Parse mentionable if specified
    mentionable = None
    if mentionable_str:
        mentionable_str = mentionable_str.lower()
        if mentionable_str in ('true', 'yes', '1'):
            mentionable = True
        elif mentionable_str in ('false', 'no', '0'):
            mentionable = False
        else:
            await interaction.response.send_message(f":warning: Invalid mentionable value: {mentionable_str}. Must be true/false.", ephemeral=True)
            return False

    # Parse position if specified
    position = None
    if position_str:
        try:
            position = int(position_str)
            if position < 0 or position >= len(interaction.guild.roles):
                await interaction.response.send_message(f":warning: Invalid position: {position}. Must be between 0 and {len(interaction.guild.roles) - 1}.", ephemeral=True)
                return False
        except ValueError:
            await interaction.response.send_message(f":warning: Invalid position: {position_str}. Must be a number.", ephemeral=True)
            return False

    # Parse permissions if specified
    permissions = None
    if permissions_str:
        try:
            permissions_data = json.loads(permissions_str)
            permissions = discord.Permissions()
            for perm_name, perm_value in permissions_data.items():
                if hasattr(permissions, perm_name):
                    setattr(permissions, perm_name, bool(perm_value))
                else:
                    await interaction.response.send_message(f":warning: Unknown permission: {perm_name}", ephemeral=True)
                    return False
        except json.JSONDecodeError:
            await interaction.response.send_message(f":warning: Invalid permissions format. Must be a valid JSON object.", ephemeral=True)
            return False
        except Exception as e:
            log.error(f"Error parsing permissions: {e}")
            await interaction.response.send_message(f":warning: Invalid permissions format: {e}", ephemeral=True)
            return False

    # Check if there's anything to edit
    if not new_name and color is None and hoist is None and mentionable is None and permissions is None and position is None:
        await interaction.response.send_message(":warning: No changes specified for editing.", ephemeral=True)
        return False

    await interaction.response.defer(ephemeral=True)

    try:
        # Prepare the edit parameters
        edit_params = {}
        if new_name:
            edit_params['name'] = new_name
        if color is not None:
            edit_params['color'] = color
        if hoist is not None:
            edit_params['hoist'] = hoist
        if mentionable is not None:
            edit_params['mentionable'] = mentionable
        if permissions is not None:
            edit_params['permissions'] = permissions
        if reason:
            edit_params['reason'] = reason

        # Edit the role
        await target_role.edit(**edit_params)

        # Handle position separately if specified
        if position is not None:
            await target_role.edit(position=position, reason=reason)

        # Prepare a message about what was changed
        changes = []
        if new_name:
            changes.append(f"name to `{new_name}`")
        if color is not None:
            changes.append(f"color to `{color}`")
        if hoist is not None:
            changes.append(f"hoist to `{hoist}`")
        if mentionable is not None:
            changes.append(f"mentionable to `{mentionable}`")
        if permissions is not None:
            changes.append("permissions")
        if position is not None:
            changes.append(f"position to `{position}`")

        changes_str = ", ".join(changes)
        await interaction.followup.send(f":white_check_mark: Role `{target_role.name}` updated: {changes_str}.", ephemeral=True)
        return True
    except discord.Forbidden:
        await interaction.followup.send(":x: I don't have permission to edit this role.", ephemeral=True)
        return False
    except discord.HTTPException as e:
        await interaction.followup.send(f":x: Failed to edit role: {e}", ephemeral=True)
        return False
