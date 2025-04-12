# commands/free/role_create_command.py
"""
Role creation command for Discord servers.

This module provides functionality to create new roles with customizable permissions,
colors, and other settings.
"""

import discord
import logging
import re

log = logging.getLogger('MyBot.Commands.RoleCreate')

async def execute(interaction, bot, args):
    """
    Creates a new role in the Discord server.

    Args:
        interaction (discord.Interaction): The interaction that triggered the command
        bot (commands.Bot): The bot instance
        args (dict): Command arguments
            - name (str): The name of the role to create
            - color (str, optional): The color of the role in hex format (#RRGGBB)
            - hoist (bool, optional): Whether the role should be displayed separately in the member list
            - mentionable (bool, optional): Whether the role should be mentionable by everyone
            - position (int, optional): The position of the role in the hierarchy
    """
    if not interaction.guild:
        log.warning("Cannot create role: Not in a guild context")
        return False

    # Check permissions
    if not interaction.guild.me.guild_permissions.manage_roles:
        log.warning(f"Bot lacks permission to create roles in {interaction.guild.name}")
        return False

    # Get parameters
    name = args.get('name')
    if not name:
        log.error("Cannot create role: No name provided")
        return False

    # Parse color if provided
    color = discord.Color.default()
    color_str = args.get('color')
    if color_str:
        # Handle hex color format (#RRGGBB)
        if color_str.startswith('#'):
            try:
                # Remove # and convert to integer
                color_int = int(color_str[1:], 16)
                color = discord.Color(color_int)
            except ValueError:
                log.warning(f"Invalid color format: {color_str}. Using default color.")
        # Handle named colors
        elif hasattr(discord.Color, color_str.lower()):
            color = getattr(discord.Color, color_str.lower())()

    # Parse boolean parameters
    hoist = args.get('hoist', 'false').lower() == 'true'
    mentionable = args.get('mentionable', 'false').lower() == 'true'

    # Parse position if provided
    position = None
    position_str = args.get('position')
    if position_str:
        try:
            position = int(position_str)
        except ValueError:
            log.warning(f"Invalid position format: {position_str}. Using default position.")

    try:
        # Create the role
        role = await interaction.guild.create_role(
            name=name,
            color=color,
            hoist=hoist,
            mentionable=mentionable,
            reason=f"Created by {interaction.user} via BISHOP bot"
        )

        # Set position if specified
        if position is not None:
            try:
                await role.edit(position=position)
            except (discord.Forbidden, discord.HTTPException) as e:
                log.warning(f"Could not set role position: {e}")

        log.info(f"Created role {role.name} ({role.id}) in {interaction.guild.name}")
        return True

    except discord.Forbidden:
        log.error(f"Forbidden: Bot lacks permission to create role in {interaction.guild.name}")
        return False
    except discord.HTTPException as e:
        log.error(f"HTTP error creating role: {e}")
        return False
    except Exception as e:
        log.error(f"Error creating role: {e}", exc_info=True)
        return False
