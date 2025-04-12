# commands/free/role_manager_command.py
"""
Role management command for Discord servers.

This module provides comprehensive functionality to manage roles, including creating,
deleting, editing, assigning, removing, and viewing information about roles.
"""

import discord
import logging
import asyncio
from typing import List, Optional, Union, Dict, Any
import json

log = logging.getLogger('MyBot.Commands.RoleManager')

async def execute(interaction, bot, args):
    """
    Comprehensive role management command with multiple operations.

    Args:
        interaction (discord.Interaction): The interaction that triggered the command
        bot (commands.Bot): The bot instance
        args (dict): Command arguments
            - operation (str): The operation to perform (create, delete, edit, assign, remove, info, list, color, hoist, mentionable)
            - role (str, optional): Role name or ID to operate on
            - name (str, optional): New name for the role
            - color (str, optional): New color for the role (hex code)
            - hoist (str, optional): Whether the role should be displayed separately (true/false)
            - mentionable (str, optional): Whether the role should be mentionable (true/false)
            - permissions (str, optional): JSON string of permission values
            - position (str, optional): New position for the role
            - user (str, optional): User ID or mention to assign/remove role from
            - reason (str, optional): Reason for the audit log
    """
    if not interaction.guild:
        log.warning("Cannot manage roles: Not in a guild context")
        return False

    # Check permissions
    if not interaction.guild.me.guild_permissions.manage_roles:
        log.warning(f"Bot lacks permission to manage roles in {interaction.guild.name}")
        return False

    # Get parameters
    operation = args.get('operation', '').lower()
    role_name_or_id = args.get('role', '')
    new_name = args.get('name', '')
    color_str = args.get('color', '')
    hoist_str = args.get('hoist', '')
    mentionable_str = args.get('mentionable', '')
    permissions_str = args.get('permissions', '')
    position_str = args.get('position', '')
    user_id_or_mention = args.get('user', '')
    reason = args.get('reason', 'Role management command')

    # Find the target role if specified
    target_role = None
    if role_name_or_id:
        try:
            role_id = int(role_name_or_id)
            target_role = interaction.guild.get_role(role_id)
        except (ValueError, TypeError):
            # Not an ID, try to find by name
            target_role = discord.utils.get(interaction.guild.roles, name=role_name_or_id)

    # Find the target user if specified
    target_user = None
    if user_id_or_mention:
        # Extract user ID from mention if necessary
        if user_id_or_mention.startswith('<@') and user_id_or_mention.endswith('>'):
            user_id_str = user_id_or_mention.strip('<@!>')
            try:
                user_id = int(user_id_str)
                target_user = interaction.guild.get_member(user_id)
            except (ValueError, TypeError):
                pass
        else:
            try:
                user_id = int(user_id_or_mention)
                target_user = interaction.guild.get_member(user_id)
            except (ValueError, TypeError):
                # Not an ID, try to find by name
                target_user = discord.utils.get(interaction.guild.members, name=user_id_or_mention)

    # Parse color if specified
    color = None
    if color_str:
        try:
            if color_str.startswith('#'):
                color_str = color_str[1:]
            color = discord.Color(int(color_str, 16))
        except ValueError:
            await interaction.response.send_message(f":warning: Invalid color: {color_str}. Must be a hex color code (e.g., #FF0000).", ephemeral=True)
            return False

    # Parse boolean parameters
    hoist = None
    if hoist_str:
        hoist = hoist_str.lower() == 'true'

    mentionable = None
    if mentionable_str:
        mentionable = mentionable_str.lower() == 'true'

    # Parse position if specified
    position = None
    if position_str:
        try:
            position = int(position_str)
        except ValueError:
            await interaction.response.send_message(f":warning: Invalid position: {position_str}. Must be a number.", ephemeral=True)
            return False

    # Parse permissions if specified
    permissions = None
    if permissions_str:
        try:
            permissions_data = json.loads(permissions_str)

            # Create a new permissions object
            permissions = discord.Permissions()

            # Set each permission
            for perm_name, perm_value in permissions_data.items():
                if hasattr(permissions, perm_name):
                    setattr(permissions, perm_name, bool(perm_value))
        except Exception as e:
            log.error(f"Error parsing permissions: {e}")
            await interaction.response.send_message(f":warning: Invalid permissions format: {e}", ephemeral=True)
            return False

    # Execute the requested operation
    try:
        if operation == 'create':
            return await create_role(interaction, new_name, color, hoist, mentionable, permissions, position, reason)
        elif operation == 'delete':
            return await delete_role(interaction, target_role, reason)
        elif operation == 'edit':
            return await edit_role(interaction, target_role, new_name, color, hoist, mentionable, permissions, position, reason)
        elif operation == 'assign':
            return await assign_role(interaction, target_role, target_user, reason)
        elif operation == 'remove':
            return await remove_role(interaction, target_role, target_user, reason)
        elif operation == 'info':
            return await role_info(interaction, target_role)
        elif operation == 'list':
            return await list_roles(interaction)
        elif operation == 'color':
            return await set_role_color(interaction, target_role, color, reason)
        elif operation == 'hoist':
            return await set_role_hoist(interaction, target_role, hoist, reason)
        elif operation == 'mentionable':
            return await set_role_mentionable(interaction, target_role, mentionable, reason)
        else:
            await interaction.response.send_message(f":warning: Unknown operation: {operation}", ephemeral=True)
            return False
    except Exception as e:
        log.error(f"Error executing role operation {operation}: {e}", exc_info=True)
        await interaction.response.send_message(f":x: Error executing operation: {e}", ephemeral=True)
        return False

async def create_role(interaction, name, color, hoist, mentionable, permissions, position, reason):
    """Creates a new role."""
    if not name:
        await interaction.response.send_message(":warning: Role name is required for creation.", ephemeral=True)
        return False

    await interaction.response.defer(ephemeral=True)

    try:
        # Create the role
        role_params = {
            'name': name,
            'reason': reason
        }

        if color is not None:
            role_params['color'] = color
        if hoist is not None:
            role_params['hoist'] = hoist
        if mentionable is not None:
            role_params['mentionable'] = mentionable
        if permissions is not None:
            role_params['permissions'] = permissions

        role = await interaction.guild.create_role(**role_params)

        # Set position if specified
        if position is not None:
            try:
                await role.edit(position=position)
            except discord.HTTPException as e:
                log.warning(f"Failed to set role position: {e}")

        await interaction.followup.send(f":white_check_mark: Role {role.mention} created successfully.", ephemeral=True)
        return True
    except discord.Forbidden:
        await interaction.followup.send(":x: I don't have permission to create roles.", ephemeral=True)
        return False
    except discord.HTTPException as e:
        await interaction.followup.send(f":x: Failed to create role: {e}", ephemeral=True)
        return False

async def delete_role(interaction, role, reason):
    """Deletes a role."""
    if not role:
        await interaction.response.send_message(":warning: Role not found.", ephemeral=True)
        return False

    # Check if the bot can manage this role
    if role.position >= interaction.guild.me.top_role.position:
        await interaction.response.send_message(":warning: I cannot delete a role that is higher than or equal to my highest role.", ephemeral=True)
        return False

    await interaction.response.defer(ephemeral=True)

    try:
        role_name = role.name
        await role.delete(reason=reason)
        await interaction.followup.send(f":white_check_mark: Role `{role_name}` deleted successfully.", ephemeral=True)
        return True
    except discord.Forbidden:
        await interaction.followup.send(":x: I don't have permission to delete this role.", ephemeral=True)
        return False
    except discord.HTTPException as e:
        await interaction.followup.send(f":x: Failed to delete role: {e}", ephemeral=True)
        return False

async def edit_role(interaction, role, name, color, hoist, mentionable, permissions, position, reason):
    """Edits a role's properties."""
    if not role:
        await interaction.response.send_message(":warning: Role not found.", ephemeral=True)
        return False

    # Check if the bot can manage this role
    if role.position >= interaction.guild.me.top_role.position:
        await interaction.response.send_message(":warning: I cannot edit a role that is higher than or equal to my highest role.", ephemeral=True)
        return False

    # Check if there's anything to edit
    if not name and color is None and hoist is None and mentionable is None and permissions is None and position is None:
        await interaction.response.send_message(":warning: No changes specified for editing.", ephemeral=True)
        return False

    await interaction.response.defer(ephemeral=True)

    try:
        # Prepare the edit parameters
        edit_params = {'reason': reason}
        if name:
            edit_params['name'] = name
        if color is not None:
            edit_params['color'] = color
        if hoist is not None:
            edit_params['hoist'] = hoist
        if mentionable is not None:
            edit_params['mentionable'] = mentionable
        if permissions is not None:
            edit_params['permissions'] = permissions

        # Edit the role
        await role.edit(**edit_params)

        # Set position if specified (needs to be done separately)
        if position is not None:
            try:
                await role.edit(position=position)
            except discord.HTTPException as e:
                log.warning(f"Failed to set role position: {e}")

        # Prepare a message about what was changed
        changes = []
        if name:
            changes.append(f"name to `{name}`")
        if color is not None:
            changes.append(f"color to `{color}`")
        if hoist is not None:
            changes.append(f"hoist to `{hoist}`")
        if mentionable is not None:
            changes.append(f"mentionable to `{mentionable}`")
        if permissions is not None:
            changes.append("permissions updated")
        if position is not None:
            changes.append(f"position to `{position}`")

        changes_str = ", ".join(changes)
        await interaction.followup.send(f":white_check_mark: Role {role.mention} updated: {changes_str}.", ephemeral=True)
        return True
    except discord.Forbidden:
        await interaction.followup.send(":x: I don't have permission to edit this role.", ephemeral=True)
        return False
    except discord.HTTPException as e:
        await interaction.followup.send(f":x: Failed to edit role: {e}", ephemeral=True)
        return False

async def assign_role(interaction, role, user, reason):
    """Assigns a role to a user."""
    if not role:
        await interaction.response.send_message(":warning: Role not found.", ephemeral=True)
        return False

    if not user:
        await interaction.response.send_message(":warning: User not found.", ephemeral=True)
        return False

    # Check if the bot can manage this role
    if role.position >= interaction.guild.me.top_role.position:
        await interaction.response.send_message(":warning: I cannot assign a role that is higher than or equal to my highest role.", ephemeral=True)
        return False

    # Check if the user already has the role
    if role in user.roles:
        await interaction.response.send_message(f":information_source: {user.mention} already has the {role.mention} role.", ephemeral=True)
        return True

    await interaction.response.defer(ephemeral=True)

    try:
        await user.add_roles(role, reason=reason)
        await interaction.followup.send(f":white_check_mark: Role {role.mention} assigned to {user.mention}.", ephemeral=True)
        return True
    except discord.Forbidden:
        await interaction.followup.send(":x: I don't have permission to assign roles to this user.", ephemeral=True)
        return False
    except discord.HTTPException as e:
        await interaction.followup.send(f":x: Failed to assign role: {e}", ephemeral=True)
        return False

async def remove_role(interaction, role, user, reason):
    """Removes a role from a user."""
    if not role:
        await interaction.response.send_message(":warning: Role not found.", ephemeral=True)
        return False

    if not user:
        await interaction.response.send_message(":warning: User not found.", ephemeral=True)
        return False

    # Check if the bot can manage this role
    if role.position >= interaction.guild.me.top_role.position:
        await interaction.response.send_message(":warning: I cannot remove a role that is higher than or equal to my highest role.", ephemeral=True)
        return False

    # Check if the user has the role
    if role not in user.roles:
        await interaction.response.send_message(f":information_source: {user.mention} doesn't have the {role.mention} role.", ephemeral=True)
        return True

    await interaction.response.defer(ephemeral=True)

    try:
        await user.remove_roles(role, reason=reason)
        await interaction.followup.send(f":white_check_mark: Role {role.mention} removed from {user.mention}.", ephemeral=True)
        return True
    except discord.Forbidden:
        await interaction.followup.send(":x: I don't have permission to remove roles from this user.", ephemeral=True)
        return False
    except discord.HTTPException as e:
        await interaction.followup.send(f":x: Failed to remove role: {e}", ephemeral=True)
        return False

async def role_info(interaction, role):
    """Displays information about a role."""
    if not role:
        await interaction.response.send_message(":warning: Role not found.", ephemeral=True)
        return False

    # Create an embed with role information
    embed = discord.Embed(
        title=f"Role Information: {role.name}",
        color=role.color
    )

    # Add basic information
    embed.add_field(name="ID", value=role.id, inline=True)
    embed.add_field(name="Color", value=f"#{role.color.value:06x}", inline=True)
    embed.add_field(name="Position", value=role.position, inline=True)

    embed.add_field(name="Hoisted", value="Yes" if role.hoist else "No", inline=True)
    embed.add_field(name="Mentionable", value="Yes" if role.mentionable else "No", inline=True)
    embed.add_field(name="Created", value=f"<t:{int(role.created_at.timestamp())}:R>", inline=True)

    # Add member count
    member_count = len(role.members)
    embed.add_field(name="Members", value=member_count, inline=True)

    # Add key permissions
    key_permissions = []
    if role.permissions.administrator:
        key_permissions.append("Administrator")
    if role.permissions.ban_members:
        key_permissions.append("Ban Members")
    if role.permissions.kick_members:
        key_permissions.append("Kick Members")
    if role.permissions.manage_guild:
        key_permissions.append("Manage Server")
    if role.permissions.manage_channels:
        key_permissions.append("Manage Channels")
    if role.permissions.manage_roles:
        key_permissions.append("Manage Roles")
    if role.permissions.manage_messages:
        key_permissions.append("Manage Messages")
    if role.permissions.mention_everyone:
        key_permissions.append("Mention Everyone")

    if key_permissions:
        embed.add_field(name="Key Permissions", value=", ".join(key_permissions), inline=False)

    await interaction.response.send_message(embed=embed, ephemeral=True)
    return True

async def list_roles(interaction):
    """Lists all roles in the server."""
    # Get all roles except @everyone
    roles = sorted([role for role in interaction.guild.roles if role.name != "@everyone"], key=lambda r: r.position, reverse=True)

    if not roles:
        await interaction.response.send_message(":information_source: No roles found in this server (except @everyone).", ephemeral=True)
        return True

    # Create an embed with role information
    embed = discord.Embed(
        title=f"Roles in {interaction.guild.name}",
        description=f"Total: {len(roles)} roles",
        color=discord.Color.blue()
    )

    # Add roles to the embed
    role_chunks = [roles[i:i+20] for i in range(0, len(roles), 20)]

    for i, chunk in enumerate(role_chunks):
        role_list = "\n".join([f"{role.mention} - {len(role.members)} members" for role in chunk])
        embed.add_field(name=f"Roles {i*20+1}-{i*20+len(chunk)}", value=role_list, inline=False)

    await interaction.response.send_message(embed=embed, ephemeral=True)
    return True

async def set_role_color(interaction, role, color, reason):
    """Sets the color of a role."""
    if not role:
        await interaction.response.send_message(":warning: Role not found.", ephemeral=True)
        return False

    if color is None:
        await interaction.response.send_message(":warning: Color must be specified.", ephemeral=True)
        return False

    # Check if the bot can manage this role
    if role.position >= interaction.guild.me.top_role.position:
        await interaction.response.send_message(":warning: I cannot edit a role that is higher than or equal to my highest role.", ephemeral=True)
        return False

    await interaction.response.defer(ephemeral=True)

    try:
        await role.edit(color=color, reason=reason)
        await interaction.followup.send(f":white_check_mark: Role {role.mention} color set to `#{color.value:06x}`.", ephemeral=True)
        return True
    except discord.Forbidden:
        await interaction.followup.send(":x: I don't have permission to edit this role.", ephemeral=True)
        return False
    except discord.HTTPException as e:
        await interaction.followup.send(f":x: Failed to set role color: {e}", ephemeral=True)
        return False

async def set_role_hoist(interaction, role, hoist, reason):
    """Sets whether a role is hoisted (displayed separately)."""
    if not role:
        await interaction.response.send_message(":warning: Role not found.", ephemeral=True)
        return False

    if hoist is None:
        await interaction.response.send_message(":warning: Hoist value must be specified.", ephemeral=True)
        return False

    # Check if the bot can manage this role
    if role.position >= interaction.guild.me.top_role.position:
        await interaction.response.send_message(":warning: I cannot edit a role that is higher than or equal to my highest role.", ephemeral=True)
        return False

    await interaction.response.defer(ephemeral=True)

    try:
        await role.edit(hoist=hoist, reason=reason)
        status = "displayed separately" if hoist else "not displayed separately"
        await interaction.followup.send(f":white_check_mark: Role {role.mention} is now {status}.", ephemeral=True)
        return True
    except discord.Forbidden:
        await interaction.followup.send(":x: I don't have permission to edit this role.", ephemeral=True)
        return False
    except discord.HTTPException as e:
        await interaction.followup.send(f":x: Failed to set role hoist: {e}", ephemeral=True)
        return False

async def set_role_mentionable(interaction, role, mentionable, reason):
    """Sets whether a role is mentionable."""
    if not role:
        await interaction.response.send_message(":warning: Role not found.", ephemeral=True)
        return False

    if mentionable is None:
        await interaction.response.send_message(":warning: Mentionable value must be specified.", ephemeral=True)
        return False

    # Check if the bot can manage this role
    if role.position >= interaction.guild.me.top_role.position:
        await interaction.response.send_message(":warning: I cannot edit a role that is higher than or equal to my highest role.", ephemeral=True)
        return False

    await interaction.response.defer(ephemeral=True)

    try:
        await role.edit(mentionable=mentionable, reason=reason)
        status = "mentionable" if mentionable else "not mentionable"
        await interaction.followup.send(f":white_check_mark: Role {role.mention} is now {status}.", ephemeral=True)
        return True
    except discord.Forbidden:
        await interaction.followup.send(":x: I don't have permission to edit this role.", ephemeral=True)
        return False
    except discord.HTTPException as e:
        await interaction.followup.send(f":x: Failed to set role mentionable: {e}", ephemeral=True)
        return False
