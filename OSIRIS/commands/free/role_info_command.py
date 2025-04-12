# commands/free/role_info_command.py
"""
Role info command for Discord servers.

This module provides functionality to view information about a role.
"""

import discord
import logging
from datetime import datetime

log = logging.getLogger('MyBot.Commands.RoleInfo')

async def execute(interaction, bot, args):
    """
    Displays information about a Discord role.

    Args:
        interaction (discord.Interaction): The interaction that triggered the command
        bot (commands.Bot): The bot instance
        args (dict): Command arguments
            - role (str): Role name or ID to get information about
    """
    if not interaction.guild:
        log.warning("Cannot get role info: Not in a guild context")
        await interaction.response.send_message(":warning: This command can only be used in a server.", ephemeral=True)
        return False

    # Get parameters
    role_name_or_id = args.get('role', '')

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

    await interaction.response.defer(ephemeral=True)

    try:
        # Create an embed with role information
        embed = discord.Embed(
            title=f"Role Information: {target_role.name}",
            color=target_role.color if target_role.color.value else discord.Color.light_grey()
        )

        # Add basic information
        embed.add_field(name="ID", value=str(target_role.id), inline=True)
        embed.add_field(name="Color", value=f"#{target_role.color.value:06x}" if target_role.color.value else "None", inline=True)
        embed.add_field(name="Position", value=str(target_role.position), inline=True)
        embed.add_field(name="Hoisted", value="Yes" if target_role.hoist else "No", inline=True)
        embed.add_field(name="Mentionable", value="Yes" if target_role.mentionable else "No", inline=True)
        embed.add_field(name="Managed", value="Yes" if target_role.managed else "No", inline=True)

        # Add creation date
        created_at = int(target_role.id / 4194304) + 1420070400000
        created_at = datetime.fromtimestamp(created_at / 1000)
        embed.add_field(name="Created At", value=created_at.strftime("%Y-%m-%d %H:%M:%S UTC"), inline=False)

        # Add member count
        member_count = len([m for m in interaction.guild.members if target_role in m.roles])
        embed.add_field(name="Members", value=str(member_count), inline=False)

        # Add permissions
        permissions = []
        for perm, value in target_role.permissions:
            if value:
                permissions.append(perm.replace('_', ' ').title())

        if permissions:
            # Split permissions into chunks to avoid hitting the field value limit
            chunks = [permissions[i:i + 10] for i in range(0, len(permissions), 10)]
            for i, chunk in enumerate(chunks):
                embed.add_field(name=f"Permissions {i+1}" if i > 0 else "Permissions", value="\n".join(chunk), inline=False)
        else:
            embed.add_field(name="Permissions", value="None", inline=False)

        # Send the embed
        await interaction.followup.send(embed=embed, ephemeral=True)
        return True
    except Exception as e:
        log.error(f"Error displaying role info: {e}", exc_info=True)
        await interaction.followup.send(f":x: Error displaying role information: {e}", ephemeral=True)
        return False
