# commands/free/role_assign_command.py
"""
Role assign command for Discord servers.

This module provides functionality to assign a role to a user.
"""

import discord
import logging

log = logging.getLogger('MyBot.Commands.RoleAssign')

async def execute(interaction, bot, args):
    """
    Assigns a Discord role to a user.

    Args:
        interaction (discord.Interaction): The interaction that triggered the command
        bot (commands.Bot): The bot instance
        args (dict): Command arguments
            - role (str): Role name or ID to assign
            - user (str): User ID or mention to assign the role to
            - reason (str, optional): Reason for the audit log
    """
    if not interaction.guild:
        log.warning("Cannot assign role: Not in a guild context")
        await interaction.response.send_message(":warning: This command can only be used in a server.", ephemeral=True)
        return False

    # Check permissions
    if not interaction.guild.me.guild_permissions.manage_roles:
        log.warning(f"Bot lacks permission to manage roles in {interaction.guild.name}")
        await interaction.response.send_message(":warning: I don't have permission to manage roles in this server.", ephemeral=True)
        return False

    # Get parameters
    role_name_or_id = args.get('role', '')
    user_id_or_mention = args.get('user', '')
    reason = args.get('reason', 'Role assignment command')

    if not role_name_or_id:
        await interaction.response.send_message(":warning: Role name or ID is required.", ephemeral=True)
        return False

    if not user_id_or_mention:
        await interaction.response.send_message(":warning: User ID or mention is required.", ephemeral=True)
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
        await interaction.response.send_message(":warning: I cannot assign a role that is higher than or equal to my highest role.", ephemeral=True)
        return False

    # Find the target user
    target_user = None
    try:
        # Check if it's a mention
        if user_id_or_mention.startswith('<@') and user_id_or_mention.endswith('>'):
            user_id = int(user_id_or_mention[2:-1].replace('!', ''))
            target_user = interaction.guild.get_member(user_id)
        else:
            # Try as a user ID
            user_id = int(user_id_or_mention)
            target_user = interaction.guild.get_member(user_id)
    except (ValueError, TypeError):
        # Not an ID or mention, try to find by name
        target_user = discord.utils.get(interaction.guild.members, name=user_id_or_mention)

    if not target_user:
        await interaction.response.send_message(f":warning: User '{user_id_or_mention}' not found in this server.", ephemeral=True)
        return False

    await interaction.response.defer(ephemeral=True)

    try:
        # Check if the user already has the role
        if target_role in target_user.roles:
            await interaction.followup.send(f":information_source: User {target_user.mention} already has the role `{target_role.name}`.", ephemeral=True)
            return True

        # Assign the role
        await target_user.add_roles(target_role, reason=reason)
        await interaction.followup.send(f":white_check_mark: Role `{target_role.name}` assigned to {target_user.mention}.", ephemeral=True)
        return True
    except discord.Forbidden:
        await interaction.followup.send(":x: I don't have permission to assign this role.", ephemeral=True)
        return False
    except discord.HTTPException as e:
        await interaction.followup.send(f":x: Failed to assign role: {e}", ephemeral=True)
        return False
