# commands/free/user_manager_command.py
"""
User management command for Discord servers.

This module provides comprehensive functionality to manage users, including viewing
user information, roles, avatars, banners, activity, join dates, and setting nicknames.
"""

import discord
import logging
from typing import List, Dict, Any, Optional, Union
import datetime

log = logging.getLogger('MyBot.Commands.UserManager')

async def execute(interaction, bot, args):
    """
    Manages user information and actions.

    Args:
        interaction (discord.Interaction): The interaction that triggered the command
        bot (commands.Bot): The bot instance
        args (dict): Command arguments
            - operation (str): The operation to perform (info, roles, avatar, banner, activity, joined, created, nickname)
            - user (str, optional): User ID, mention, or name to operate on
            - nickname (str, optional): New nickname for the user
            - reason (str, optional): Reason for the audit log
    """
    if not interaction.guild:
        log.warning("Cannot manage users: Not in a guild context")
        return False

    # Get parameters
    operation = args.get('operation', '').lower()
    user_id_or_mention = args.get('user', '')
    nickname = args.get('nickname', '')
    reason = args.get('reason', 'User management command')

    # Find the target user
    target_user = None

    # If no user specified, use the command user
    if not user_id_or_mention:
        target_user = interaction.user
    else:
        # Check if it's a mention
        if user_id_or_mention.startswith('<@') and user_id_or_mention.endswith('>'):
            user_id_str = user_id_or_mention.strip('<@!>')
            try:
                user_id = int(user_id_str)
                target_user = interaction.guild.get_member(user_id)
            except (ValueError, TypeError):
                pass
        else:
            # Try to find by ID first
            try:
                user_id = int(user_id_or_mention)
                target_user = interaction.guild.get_member(user_id)
            except (ValueError, TypeError):
                # Not an ID, try to find by name
                target_user = discord.utils.get(interaction.guild.members, name=user_id_or_mention)
                if not target_user:
                    # Try to find by display name
                    target_user = discord.utils.get(interaction.guild.members, display_name=user_id_or_mention)

    if not target_user:
        await interaction.response.send_message(f":warning: User not found: {user_id_or_mention}", ephemeral=True)
        return False

    # Execute the requested operation
    try:
        if operation == 'info':
            return await user_info(interaction, target_user)
        elif operation == 'roles':
            return await user_roles(interaction, target_user)
        elif operation == 'avatar':
            return await user_avatar(interaction, target_user)
        elif operation == 'banner':
            return await user_banner(interaction, target_user)
        elif operation == 'activity':
            return await user_activity(interaction, target_user)
        elif operation == 'joined':
            return await user_joined(interaction, target_user)
        elif operation == 'created':
            return await user_created(interaction, target_user)
        elif operation == 'nickname':
            return await set_nickname(interaction, target_user, nickname, reason)
        else:
            await interaction.response.send_message(f":warning: Unknown operation: {operation}", ephemeral=True)
            return False
    except Exception as e:
        log.error(f"Error executing user operation {operation}: {e}", exc_info=True)
        await interaction.response.send_message(f":x: Error executing operation: {e}", ephemeral=True)
        return False

async def user_info(interaction, user):
    """Displays detailed information about a user."""
    await interaction.response.defer(ephemeral=True)

    # Create an embed with user information
    embed = discord.Embed(
        title=f"User Information: {user.name}",
        color=user.color
    )

    # Add user avatar
    if user.avatar:
        embed.set_thumbnail(url=user.avatar.url)

    # Add basic information
    embed.add_field(name="ID", value=user.id, inline=True)
    embed.add_field(name="Display Name", value=user.display_name, inline=True)
    embed.add_field(name="Bot", value="Yes" if user.bot else "No", inline=True)

    # Add join dates
    created_at = int(user.created_at.timestamp())
    joined_at = int(user.joined_at.timestamp()) if user.joined_at else "Unknown"

    embed.add_field(name="Created", value=f"<t:{created_at}:R>", inline=True)
    embed.add_field(name="Joined", value=f"<t:{joined_at}:R>" if isinstance(joined_at, int) else joined_at, inline=True)

    # Add role information
    role_count = len(user.roles) - 1  # Exclude @everyone
    top_role = user.top_role.mention if user.top_role.name != "@everyone" else "None"

    embed.add_field(name="Roles", value=f"{role_count} roles", inline=True)
    embed.add_field(name="Top Role", value=top_role, inline=True)
    embed.add_field(name="Color", value=f"#{user.color.value:06x}" if user.color.value else "None", inline=True)

    # Add status and activity if available
    if hasattr(user, 'status'):
        status_map = {
            discord.Status.online: "🟢 Online",
            discord.Status.idle: "🟡 Idle",
            discord.Status.dnd: "🔴 Do Not Disturb",
            discord.Status.offline: "⚫ Offline"
        }

        status = status_map.get(user.status, "Unknown")
        embed.add_field(name="Status", value=status, inline=True)

    if hasattr(user, 'activity') and user.activity:
        activity_type_map = {
            discord.ActivityType.playing: "Playing",
            discord.ActivityType.streaming: "Streaming",
            discord.ActivityType.listening: "Listening to",
            discord.ActivityType.watching: "Watching",
            discord.ActivityType.custom: "Custom",
            discord.ActivityType.competing: "Competing in"
        }

        activity_type = activity_type_map.get(user.activity.type, "Unknown")
        activity_name = user.activity.name

        embed.add_field(name="Activity", value=f"{activity_type} {activity_name}", inline=True)

    # Add server-specific permissions if available
    if hasattr(user, 'guild_permissions'):
        key_permissions = []
        if user.guild_permissions.administrator:
            key_permissions.append("Administrator")
        if user.guild_permissions.ban_members:
            key_permissions.append("Ban Members")
        if user.guild_permissions.kick_members:
            key_permissions.append("Kick Members")
        if user.guild_permissions.manage_guild:
            key_permissions.append("Manage Server")
        if user.guild_permissions.manage_channels:
            key_permissions.append("Manage Channels")
        if user.guild_permissions.manage_roles:
            key_permissions.append("Manage Roles")
        if user.guild_permissions.manage_messages:
            key_permissions.append("Manage Messages")
        if user.guild_permissions.mention_everyone:
            key_permissions.append("Mention Everyone")

        if key_permissions:
            embed.add_field(name="Key Permissions", value=", ".join(key_permissions), inline=False)

    await interaction.followup.send(embed=embed, ephemeral=True)
    return True

async def user_roles(interaction, user):
    """Displays the roles of a user."""
    await interaction.response.defer(ephemeral=True)

    # Get all roles except @everyone
    roles = [role for role in user.roles if role.name != "@everyone"]

    if not roles:
        await interaction.followup.send(f":information_source: {user.mention} has no roles.", ephemeral=True)
        return True

    # Sort roles by position
    roles.sort(reverse=True, key=lambda r: r.position)

    # Create an embed with role information
    embed = discord.Embed(
        title=f"Roles for {user.name}",
        description=f"Total: {len(roles)} roles",
        color=user.color
    )

    # Add roles to the embed
    role_chunks = [roles[i:i+20] for i in range(0, len(roles), 20)]

    for i, chunk in enumerate(role_chunks):
        role_list = "\n".join([f"{role.mention} (ID: {role.id})" for role in chunk])
        embed.add_field(name=f"Roles {i*20+1}-{i*20+len(chunk)}", value=role_list, inline=False)

    await interaction.followup.send(embed=embed, ephemeral=True)
    return True

async def user_avatar(interaction, user):
    """Displays the avatar of a user."""
    await interaction.response.defer(ephemeral=True)

    if not user.avatar:
        await interaction.followup.send(f":information_source: {user.mention} has no custom avatar.", ephemeral=True)
        return True

    # Create an embed with the avatar
    embed = discord.Embed(
        title=f"Avatar for {user.name}",
        color=user.color
    )

    embed.set_image(url=user.avatar.url)

    # Add links to different formats and sizes
    formats = ["png", "jpg", "webp"]
    sizes = [128, 256, 512, 1024, 2048]

    links = []
    for fmt in formats:
        for size in sizes:
            links.append(f"[{fmt} {size}px]({user.avatar.with_format(fmt).with_size(size)})")

    embed.add_field(name="Download Links", value=" | ".join(links), inline=False)

    await interaction.followup.send(embed=embed, ephemeral=True)
    return True

async def user_banner(interaction, user):
    """Displays the banner of a user."""
    await interaction.response.defer(ephemeral=True)

    # Fetch the user to get the banner
    try:
        user = await interaction.client.fetch_user(user.id)
    except discord.HTTPException as e:
        await interaction.followup.send(f":x: Failed to fetch user: {e}", ephemeral=True)
        return False

    if not user.banner:
        await interaction.followup.send(f":information_source: {user.mention} has no banner.", ephemeral=True)
        return True

    # Create an embed with the banner
    embed = discord.Embed(
        title=f"Banner for {user.name}",
        color=user.color
    )

    embed.set_image(url=user.banner.url)

    # Add links to different formats and sizes
    formats = ["png", "jpg", "webp"]
    sizes = [128, 256, 512, 1024, 2048]

    links = []
    for fmt in formats:
        for size in sizes:
            links.append(f"[{fmt} {size}px]({user.banner.with_format(fmt).with_size(size)})")

    embed.add_field(name="Download Links", value=" | ".join(links), inline=False)

    await interaction.followup.send(embed=embed, ephemeral=True)
    return True

async def user_activity(interaction, user):
    """Displays the activity of a user."""
    await interaction.response.defer(ephemeral=True)

    if not hasattr(user, 'activity') or not user.activity:
        await interaction.followup.send(f":information_source: {user.mention} has no current activity.", ephemeral=True)
        return True

    # Create an embed with the activity information
    embed = discord.Embed(
        title=f"Activity for {user.name}",
        color=user.color
    )

    # Map activity types to readable strings
    activity_type_map = {
        discord.ActivityType.playing: "Playing",
        discord.ActivityType.streaming: "Streaming",
        discord.ActivityType.listening: "Listening to",
        discord.ActivityType.watching: "Watching",
        discord.ActivityType.custom: "Custom",
        discord.ActivityType.competing: "Competing in"
    }

    activity_type = activity_type_map.get(user.activity.type, "Unknown")

    # Add basic activity information
    embed.add_field(name="Type", value=activity_type, inline=True)
    embed.add_field(name="Name", value=user.activity.name, inline=True)

    # Add details based on activity type
    if isinstance(user.activity, discord.Game):
        # Game activity
        if user.activity.start:
            start_time = datetime.datetime.fromtimestamp(user.activity.start.timestamp())
            elapsed = datetime.datetime.now() - start_time
            hours, remainder = divmod(int(elapsed.total_seconds()), 3600)
            minutes, seconds = divmod(remainder, 60)

            elapsed_str = f"{hours}h {minutes}m {seconds}s"
            embed.add_field(name="Elapsed Time", value=elapsed_str, inline=True)

    elif isinstance(user.activity, discord.Streaming):
        # Streaming activity
        if user.activity.url:
            embed.add_field(name="URL", value=user.activity.url, inline=True)
        if user.activity.game:
            embed.add_field(name="Game", value=user.activity.game, inline=True)

    elif isinstance(user.activity, discord.Spotify):
        # Spotify activity
        embed.add_field(name="Title", value=user.activity.title, inline=True)
        embed.add_field(name="Artist", value=user.activity.artist, inline=True)
        embed.add_field(name="Album", value=user.activity.album, inline=True)

        if user.activity.duration:
            duration_seconds = user.activity.duration.total_seconds()
            minutes, seconds = divmod(int(duration_seconds), 60)
            embed.add_field(name="Duration", value=f"{minutes}:{seconds:02d}", inline=True)

        if user.activity.start and user.activity.end:
            elapsed = datetime.datetime.now() - user.activity.start
            total = user.activity.end - user.activity.start

            if total.total_seconds() > 0:
                progress = min(1.0, elapsed.total_seconds() / total.total_seconds())
                progress_bar = "▓" * int(progress * 10) + "░" * (10 - int(progress * 10))

                elapsed_minutes, elapsed_seconds = divmod(int(elapsed.total_seconds()), 60)
                total_minutes, total_seconds = divmod(int(total.total_seconds()), 60)

                embed.add_field(
                    name="Progress",
                    value=f"{elapsed_minutes}:{elapsed_seconds:02d} {progress_bar} {total_minutes}:{total_seconds:02d}",
                    inline=False
                )

        if user.activity.album_cover_url:
            embed.set_thumbnail(url=user.activity.album_cover_url)

    elif isinstance(user.activity, discord.CustomActivity):
        # Custom activity
        if user.activity.emoji:
            embed.add_field(name="Emoji", value=f"{user.activity.emoji}", inline=True)

        if user.activity.state:
            embed.add_field(name="Status", value=user.activity.state, inline=True)

    await interaction.followup.send(embed=embed, ephemeral=True)
    return True

async def user_joined(interaction, user):
    """Displays when a user joined the server."""
    await interaction.response.defer(ephemeral=True)

    if not user.joined_at:
        await interaction.followup.send(f":information_source: Join date for {user.mention} is not available.", ephemeral=True)
        return True

    # Create an embed with the join information
    embed = discord.Embed(
        title=f"Join Information for {user.name}",
        color=user.color
    )

    # Add join date
    joined_at = int(user.joined_at.timestamp())
    embed.add_field(name="Joined Server", value=f"<t:{joined_at}:F> (<t:{joined_at}:R>)", inline=False)

    # Calculate server age
    server_age = datetime.datetime.now() - user.joined_at
    years, days = divmod(server_age.days, 365)
    months, days = divmod(days, 30)

    age_parts = []
    if years > 0:
        age_parts.append(f"{years} year{'s' if years != 1 else ''}")
    if months > 0:
        age_parts.append(f"{months} month{'s' if months != 1 else ''}")
    if days > 0 or not age_parts:
        age_parts.append(f"{days} day{'s' if days != 1 else ''}")

    server_age_str = ", ".join(age_parts)
    embed.add_field(name="Server Age", value=server_age_str, inline=False)

    # Add join position if available
    try:
        # Sort members by join date
        sorted_members = sorted(interaction.guild.members, key=lambda m: m.joined_at or datetime.datetime.now())

        # Find the user's position
        position = sorted_members.index(user) + 1

        # Calculate percentile
        percentile = (position / len(sorted_members)) * 100

        embed.add_field(
            name="Join Position",
            value=f"{position} of {len(sorted_members)} ({percentile:.1f}%)",
            inline=False
        )
    except Exception as e:
        log.warning(f"Failed to calculate join position: {e}")

    await interaction.followup.send(embed=embed, ephemeral=True)
    return True

async def user_created(interaction, user):
    """Displays when a user account was created."""
    await interaction.response.defer(ephemeral=True)

    # Create an embed with the account creation information
    embed = discord.Embed(
        title=f"Account Information for {user.name}",
        color=user.color
    )

    # Add creation date
    created_at = int(user.created_at.timestamp())
    embed.add_field(name="Account Created", value=f"<t:{created_at}:F> (<t:{created_at}:R>)", inline=False)

    # Calculate account age
    account_age = datetime.datetime.now() - user.created_at
    years, days = divmod(account_age.days, 365)
    months, days = divmod(days, 30)

    age_parts = []
    if years > 0:
        age_parts.append(f"{years} year{'s' if years != 1 else ''}")
    if months > 0:
        age_parts.append(f"{months} month{'s' if months != 1 else ''}")
    if days > 0 or not age_parts:
        age_parts.append(f"{days} day{'s' if days != 1 else ''}")

    account_age_str = ", ".join(age_parts)
    embed.add_field(name="Account Age", value=account_age_str, inline=False)

    # Calculate time between account creation and joining the server
    if user.joined_at:
        join_delay = user.joined_at - user.created_at

        if join_delay.total_seconds() < 0:
            # This shouldn't happen, but just in case
            embed.add_field(name="Time Before Joining", value="Error: Join date is before creation date", inline=False)
        else:
            years, days = divmod(join_delay.days, 365)
            months, days = divmod(days, 30)
            hours, remainder = divmod(int(join_delay.total_seconds()), 3600)
            minutes, seconds = divmod(remainder, 60)

            delay_parts = []
            if years > 0:
                delay_parts.append(f"{years} year{'s' if years != 1 else ''}")
            if months > 0:
                delay_parts.append(f"{months} month{'s' if months != 1 else ''}")
            if days > 0:
                delay_parts.append(f"{days} day{'s' if days != 1 else ''}")
            if hours > 0:
                delay_parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
            if minutes > 0 or not delay_parts:
                delay_parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")

            delay_str = ", ".join(delay_parts)
            embed.add_field(name="Time Before Joining", value=delay_str, inline=False)

    await interaction.followup.send(embed=embed, ephemeral=True)
    return True

async def set_nickname(interaction, user, nickname, reason):
    """Sets a nickname for a user."""
    # Check if the bot has permission to manage nicknames
    if not interaction.guild.me.guild_permissions.manage_nicknames:
        await interaction.response.send_message(":x: I don't have permission to manage nicknames.", ephemeral=True)
        return False

    # Check if the user is the bot owner or has a higher role than the bot
    if user.top_role.position >= interaction.guild.me.top_role.position and user.id != interaction.guild.owner_id:
        await interaction.response.send_message(":warning: I cannot change the nickname of a user with a higher role than me.", ephemeral=True)
        return False

    await interaction.response.defer(ephemeral=True)

    try:
        # Get the old nickname
        old_nickname = user.nick or user.name

        # Set the new nickname
        await user.edit(nick=nickname or None, reason=reason)

        # Prepare the message
        if nickname:
            await interaction.followup.send(f":white_check_mark: Nickname for {user.mention} changed from `{old_nickname}` to `{nickname}`.", ephemeral=True)
        else:
            await interaction.followup.send(f":white_check_mark: Nickname for {user.mention} reset from `{old_nickname}` to their username.", ephemeral=True)

        return True
    except discord.Forbidden:
        await interaction.followup.send(":x: I don't have permission to change this user's nickname.", ephemeral=True)
        return False
    except discord.HTTPException as e:
        await interaction.followup.send(f":x: Failed to set nickname: {e}", ephemeral=True)
        return False
