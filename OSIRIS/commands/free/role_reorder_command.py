# commands/free/role_reorder_command.py
"""
Role reordering command for Discord servers.

This module provides functionality to reorder roles in the server, allowing for
alphabetical sorting, custom ordering, and position adjustments.
"""

import discord
import logging
from typing import List, Optional

log = logging.getLogger('MyBot.Commands.RoleReorder')

async def execute(interaction, bot, args):
    """
    Reorders roles in the server.

    Args:
        interaction (discord.Interaction): The interaction that triggered the command
        bot (commands.Bot): The bot instance
        args (dict): Command arguments
            - roles (str): Comma-separated list of role names or IDs in desired order
            - alphabetical (str, optional): If "true", sorts roles alphabetically
            - reverse (str, optional): If "true", reverses the order
            - above (str, optional): Role name or ID to place roles above
            - below (str, optional): Role name or ID to place roles below
    """
    if not interaction.guild:
        log.warning("Cannot reorder roles: Not in a guild context")
        return False

    # Check permissions
    if not interaction.guild.me.guild_permissions.manage_roles:
        log.warning(f"Bot lacks permission to manage roles in {interaction.guild.name}")
        return False

    # Get parameters
    roles_str = args.get('roles', '')
    alphabetical = args.get('alphabetical', 'false').lower() == 'true'
    reverse = args.get('reverse', 'false').lower() == 'true'
    above_role_name_or_id = args.get('above', '')
    below_role_name_or_id = args.get('below', '')

    # Get the reference roles for positioning
    above_role = None
    if above_role_name_or_id:
        try:
            role_id = int(above_role_name_or_id)
            above_role = interaction.guild.get_role(role_id)
        except (ValueError, TypeError):
            # Not an ID, try to find by name
            above_role = discord.utils.get(interaction.guild.roles, name=above_role_name_or_id)

    below_role = None
    if below_role_name_or_id:
        try:
            role_id = int(below_role_name_or_id)
            below_role = interaction.guild.get_role(role_id)
        except (ValueError, TypeError):
            # Not an ID, try to find by name
            below_role = discord.utils.get(interaction.guild.roles, name=below_role_name_or_id)

    # Get all roles except @everyone
    roles_to_reorder = [role for role in interaction.guild.roles if role.name != "@everyone"]

    # Sort roles if alphabetical is specified
    if alphabetical:
        roles_to_reorder = sorted(roles_to_reorder, key=lambda r: r.name)
        if reverse:
            roles_to_reorder.reverse()
    # Otherwise, use the specified order if provided
    elif roles_str:
        role_names_or_ids = [name.strip() for name in roles_str.split(',')]

        # Create a new list for the ordered roles
        ordered_roles = []

        for name_or_id in role_names_or_ids:
            # Try to find the role by ID first
            role = None
            try:
                role_id = int(name_or_id)
                role = interaction.guild.get_role(role_id)
            except (ValueError, TypeError):
                # Not an ID, try to find by name
                role = discord.utils.get(roles_to_reorder, name=name_or_id)

            if role and role in roles_to_reorder:
                ordered_roles.append(role)

        # Only use the ordered list if we found roles
        if ordered_roles:
            roles_to_reorder = ordered_roles
            if reverse:
                roles_to_reorder.reverse()
    elif reverse:
        # Just reverse the current order
        roles_to_reorder.reverse()

    # Determine the position to start placing roles
    start_position = 1  # Default to just above @everyone

    if above_role:
        start_position = above_role.position
    elif below_role:
        start_position = below_role.position - len(roles_to_reorder)

    # Ensure start_position is at least 1 (above @everyone)
    start_position = max(1, start_position)

    # Reorder the roles
    try:
        # Create a list of (role, position) tuples
        role_positions = []
        for i, role in enumerate(roles_to_reorder):
            # Skip roles that are higher than the bot's highest role
            if role.position >= interaction.guild.me.top_role.position:
                continue
            role_positions.append((role, start_position + i))

        # Update all roles at once
        if role_positions:
            await interaction.guild.edit_role_positions(positions=role_positions)

        log.info(f"Reordered {len(role_positions)} roles in {interaction.guild.name}")
        return True
    except discord.Forbidden:
        log.error(f"Forbidden: Bot lacks permission to reorder roles")
        return False
    except discord.HTTPException as e:
        log.error(f"HTTP error reordering roles: {e}")
        return False
    except Exception as e:
        log.error(f"Error reordering roles: {e}", exc_info=True)
        return False
