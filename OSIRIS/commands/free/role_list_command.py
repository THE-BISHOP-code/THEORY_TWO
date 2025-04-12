# commands/free/role_list_command.py
"""
Role list command for Discord servers.

This module provides functionality to list all roles in a server.
"""

import discord
import logging

log = logging.getLogger('MyBot.Commands.RoleList')

async def execute(interaction, bot, args):
    """
    Lists all roles in a Discord server.

    Args:
        interaction (discord.Interaction): The interaction that triggered the command
        bot (commands.Bot): The bot instance
        args (dict): Command arguments (none required)
    """
    if not interaction.guild:
        log.warning("Cannot list roles: Not in a guild context")
        await interaction.response.send_message(":warning: This command can only be used in a server.", ephemeral=True)
        return False

    await interaction.response.defer(ephemeral=True)

    try:
        # Get all roles sorted by position (highest first)
        roles = sorted(interaction.guild.roles, key=lambda r: r.position, reverse=True)

        # Create an embed with role information
        embed = discord.Embed(
            title=f"Roles in {interaction.guild.name}",
            description=f"Total: {len(roles)} roles",
            color=discord.Color.blue()
        )

        # Add roles to the embed
        role_chunks = []
        current_chunk = []
        current_length = 0

        for role in roles:
            # Format: @Role Name (ID: 123456789) - 10 members
            member_count = len([m for m in interaction.guild.members if role in m.roles])
            role_text = f"{role.mention} (ID: {role.id}) - {member_count} members"
            
            # Check if adding this role would exceed the field value limit
            if current_length + len(role_text) + 1 > 1024:  # +1 for newline
                role_chunks.append("\n".join(current_chunk))
                current_chunk = [role_text]
                current_length = len(role_text)
            else:
                current_chunk.append(role_text)
                current_length += len(role_text) + 1  # +1 for newline

        # Add any remaining roles
        if current_chunk:
            role_chunks.append("\n".join(current_chunk))

        # Add chunks to embed fields
        for i, chunk in enumerate(role_chunks):
            embed.add_field(name=f"Roles {i+1}" if i > 0 else "Roles", value=chunk, inline=False)

        # Send the embed
        await interaction.followup.send(embed=embed, ephemeral=True)
        return True
    except Exception as e:
        log.error(f"Error listing roles: {e}", exc_info=True)
        await interaction.followup.send(f":x: Error listing roles: {e}", ephemeral=True)
        return False
