# commands/free/server_manager_command.py
import discord
import logging
import asyncio
from typing import List, Dict, Any, Optional, Union
import io
import aiohttp

log = logging.getLogger('MyBot.Commands.ServerManager')

async def execute(interaction, bot, args):
    """
    Manages server settings and information.
    
    Args:
        interaction (discord.Interaction): The interaction that triggered the command
        bot (commands.Bot): The bot instance
        args (dict): Command arguments
            - operation (str): The operation to perform (info, rename, icon, banner, splash, region, verification, content_filter, system_channel, rules_channel, public_updates_channel)
            - name (str, optional): New name for the server
            - icon_url (str, optional): URL to the new server icon
            - banner_url (str, optional): URL to the new server banner
            - splash_url (str, optional): URL to the new server splash
            - verification_level (str, optional): New verification level (none, low, medium, high, highest)
            - content_filter (str, optional): New explicit content filter (disabled, no_role, all_members)
            - system_channel (str, optional): New system channel name or ID
            - rules_channel (str, optional): New rules channel name or ID
            - public_updates_channel (str, optional): New public updates channel name or ID
            - reason (str, optional): Reason for the audit log
    """
    if not interaction.guild:
        log.warning("Cannot manage server: Not in a guild context")
        return False
    
    # Check permissions
    if not interaction.guild.me.guild_permissions.manage_guild:
        log.warning(f"Bot lacks permission to manage server in {interaction.guild.name}")
        return False
    
    # Get parameters
    operation = args.get('operation', '').lower()
    name = args.get('name', '')
    icon_url = args.get('icon_url', '')
    banner_url = args.get('banner_url', '')
    splash_url = args.get('splash_url', '')
    verification_level_str = args.get('verification_level', '').lower()
    content_filter_str = args.get('content_filter', '').lower()
    system_channel_name_or_id = args.get('system_channel', '')
    rules_channel_name_or_id = args.get('rules_channel', '')
    public_updates_channel_name_or_id = args.get('public_updates_channel', '')
    reason = args.get('reason', 'Server management command')
    
    # Parse verification level
    verification_level = None
    if verification_level_str:
        verification_levels = {
            'none': discord.VerificationLevel.none,
            'low': discord.VerificationLevel.low,
            'medium': discord.VerificationLevel.medium,
            'high': discord.VerificationLevel.high,
            'highest': discord.VerificationLevel.highest
        }
        
        if verification_level_str in verification_levels:
            verification_level = verification_levels[verification_level_str]
        else:
            await interaction.response.send_message(
                f":warning: Invalid verification level: {verification_level_str}. Must be one of: none, low, medium, high, highest.",
                ephemeral=True
            )
            return False
    
    # Parse content filter
    content_filter = None
    if content_filter_str:
        content_filters = {
            'disabled': discord.ContentFilter.disabled,
            'no_role': discord.ContentFilter.no_role,
            'all_members': discord.ContentFilter.all_members
        }
        
        if content_filter_str in content_filters:
            content_filter = content_filters[content_filter_str]
        else:
            await interaction.response.send_message(
                f":warning: Invalid content filter: {content_filter_str}. Must be one of: disabled, no_role, all_members.",
                ephemeral=True
            )
            return False
    
    # Find the system channel if specified
    system_channel = None
    if system_channel_name_or_id:
        if system_channel_name_or_id.lower() == 'none':
            system_channel = None
        else:
            try:
                channel_id = int(system_channel_name_or_id)
                system_channel = interaction.guild.get_channel(channel_id)
            except (ValueError, TypeError):
                # Not an ID, try to find by name
                system_channel = discord.utils.get(interaction.guild.text_channels, name=system_channel_name_or_id)
            
            if not system_channel:
                await interaction.response.send_message(f":warning: System channel not found: {system_channel_name_or_id}", ephemeral=True)
                return False
    
    # Find the rules channel if specified
    rules_channel = None
    if rules_channel_name_or_id:
        if rules_channel_name_or_id.lower() == 'none':
            rules_channel = None
        else:
            try:
                channel_id = int(rules_channel_name_or_id)
                rules_channel = interaction.guild.get_channel(channel_id)
            except (ValueError, TypeError):
                # Not an ID, try to find by name
                rules_channel = discord.utils.get(interaction.guild.text_channels, name=rules_channel_name_or_id)
            
            if not rules_channel:
                await interaction.response.send_message(f":warning: Rules channel not found: {rules_channel_name_or_id}", ephemeral=True)
                return False
    
    # Find the public updates channel if specified
    public_updates_channel = None
    if public_updates_channel_name_or_id:
        if public_updates_channel_name_or_id.lower() == 'none':
            public_updates_channel = None
        else:
            try:
                channel_id = int(public_updates_channel_name_or_id)
                public_updates_channel = interaction.guild.get_channel(channel_id)
            except (ValueError, TypeError):
                # Not an ID, try to find by name
                public_updates_channel = discord.utils.get(interaction.guild.text_channels, name=public_updates_channel_name_or_id)
            
            if not public_updates_channel:
                await interaction.response.send_message(f":warning: Public updates channel not found: {public_updates_channel_name_or_id}", ephemeral=True)
                return False
    
    # Execute the requested operation
    try:
        if operation == 'info':
            return await server_info(interaction)
        elif operation == 'rename':
            return await rename_server(interaction, name, reason)
        elif operation == 'icon':
            return await set_server_icon(interaction, icon_url, reason)
        elif operation == 'banner':
            return await set_server_banner(interaction, banner_url, reason)
        elif operation == 'splash':
            return await set_server_splash(interaction, splash_url, reason)
        elif operation == 'verification':
            return await set_verification_level(interaction, verification_level, reason)
        elif operation == 'content_filter':
            return await set_content_filter(interaction, content_filter, reason)
        elif operation == 'system_channel':
            return await set_system_channel(interaction, system_channel, reason)
        elif operation == 'rules_channel':
            return await set_rules_channel(interaction, rules_channel, reason)
        elif operation == 'public_updates_channel':
            return await set_public_updates_channel(interaction, public_updates_channel, reason)
        else:
            await interaction.response.send_message(f":warning: Unknown operation: {operation}", ephemeral=True)
            return False
    except Exception as e:
        log.error(f"Error executing server operation {operation}: {e}", exc_info=True)
        await interaction.response.send_message(f":x: Error executing operation: {e}", ephemeral=True)
        return False

async def server_info(interaction):
    """Displays detailed information about the server."""
    guild = interaction.guild
    
    # Create an embed with server information
    embed = discord.Embed(
        title=f"{guild.name} Information",
        description=guild.description or "No description",
        color=discord.Color.blue()
    )
    
    # Add server icon if available
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    
    # Add basic information
    embed.add_field(name="ID", value=guild.id, inline=True)
    embed.add_field(name="Owner", value=f"{guild.owner.mention if guild.owner else 'Unknown'}", inline=True)
    embed.add_field(name="Created", value=f"<t:{int(guild.created_at.timestamp())}:R>", inline=True)
    
    # Add member information
    embed.add_field(name="Members", value=guild.member_count, inline=True)
    embed.add_field(name="Boost Level", value=f"Level {guild.premium_tier}", inline=True)
    embed.add_field(name="Boosts", value=guild.premium_subscription_count, inline=True)
    
    # Add channel information
    text_channels = len(guild.text_channels)
    voice_channels = len(guild.voice_channels)
    categories = len(guild.categories)
    embed.add_field(name="Text Channels", value=text_channels, inline=True)
    embed.add_field(name="Voice Channels", value=voice_channels, inline=True)
    embed.add_field(name="Categories", value=categories, inline=True)
    
    # Add role information
    embed.add_field(name="Roles", value=len(guild.roles) - 1, inline=True)  # Exclude @everyone
    embed.add_field(name="Emojis", value=f"{len(guild.emojis)}/{guild.emoji_limit}", inline=True)
    embed.add_field(name="Stickers", value=f"{len(guild.stickers)}/{guild.sticker_limit}", inline=True)
    
    # Add server settings
    verification_levels = {
        discord.VerificationLevel.none: "None",
        discord.VerificationLevel.low: "Low",
        discord.VerificationLevel.medium: "Medium",
        discord.VerificationLevel.high: "High",
        discord.VerificationLevel.highest: "Highest"
    }
    
    content_filters = {
        discord.ContentFilter.disabled: "Disabled",
        discord.ContentFilter.no_role: "No Role",
        discord.ContentFilter.all_members: "All Members"
    }
    
    embed.add_field(name="Verification Level", value=verification_levels.get(guild.verification_level, "Unknown"), inline=True)
    embed.add_field(name="Content Filter", value=content_filters.get(guild.explicit_content_filter, "Unknown"), inline=True)
    embed.add_field(name="2FA Required", value="Yes" if guild.mfa_level else "No", inline=True)
    
    # Add special channels
    system_channel = guild.system_channel.mention if guild.system_channel else "None"
    rules_channel = guild.rules_channel.mention if guild.rules_channel else "None"
    public_updates_channel = guild.public_updates_channel.mention if guild.public_updates_channel else "None"
    
    embed.add_field(name="System Channel", value=system_channel, inline=True)
    embed.add_field(name="Rules Channel", value=rules_channel, inline=True)
    embed.add_field(name="Updates Channel", value=public_updates_channel, inline=True)
    
    # Add server features
    if guild.features:
        features_str = ", ".join(feature.replace("_", " ").title() for feature in guild.features)
        embed.add_field(name="Features", value=features_str, inline=False)
    
    await interaction.response.send_message(embed=embed, ephemeral=True)
    return True

async def rename_server(interaction, name, reason):
    """Renames the server."""
    if not name:
        await interaction.response.send_message(":warning: Server name is required.", ephemeral=True)
        return False
    
    await interaction.response.defer(ephemeral=True)
    
    try:
        old_name = interaction.guild.name
        await interaction.guild.edit(name=name, reason=reason)
        await interaction.followup.send(f":white_check_mark: Server renamed from `{old_name}` to `{name}`.", ephemeral=True)
        return True
    except discord.Forbidden:
        await interaction.followup.send(":x: I don't have permission to rename the server.", ephemeral=True)
        return False
    except discord.HTTPException as e:
        await interaction.followup.send(f":x: Failed to rename server: {e}", ephemeral=True)
        return False

async def set_server_icon(interaction, icon_url, reason):
    """Sets the server icon from a URL."""
    if not icon_url:
        await interaction.response.send_message(":warning: Icon URL is required.", ephemeral=True)
        return False
    
    await interaction.response.defer(ephemeral=True)
    
    try:
        # Download the image
        async with aiohttp.ClientSession() as session:
            async with session.get(icon_url) as resp:
                if resp.status != 200:
                    await interaction.followup.send(f":x: Failed to download image: HTTP {resp.status}", ephemeral=True)
                    return False
                
                image_data = await resp.read()
        
        # Set the server icon
        await interaction.guild.edit(icon=image_data, reason=reason)
        await interaction.followup.send(":white_check_mark: Server icon updated.", ephemeral=True)
        return True
    except discord.Forbidden:
        await interaction.followup.send(":x: I don't have permission to change the server icon.", ephemeral=True)
        return False
    except discord.HTTPException as e:
        await interaction.followup.send(f":x: Failed to set server icon: {e}", ephemeral=True)
        return False

async def set_server_banner(interaction, banner_url, reason):
    """Sets the server banner from a URL."""
    if not banner_url:
        await interaction.response.send_message(":warning: Banner URL is required.", ephemeral=True)
        return False
    
    # Check if the server has the BANNER feature
    if 'BANNER' not in interaction.guild.features:
        await interaction.response.send_message(":warning: This server does not have the banner feature. It requires Boost Level 2.", ephemeral=True)
        return False
    
    await interaction.response.defer(ephemeral=True)
    
    try:
        # Download the image
        async with aiohttp.ClientSession() as session:
            async with session.get(banner_url) as resp:
                if resp.status != 200:
                    await interaction.followup.send(f":x: Failed to download image: HTTP {resp.status}", ephemeral=True)
                    return False
                
                image_data = await resp.read()
        
        # Set the server banner
        await interaction.guild.edit(banner=image_data, reason=reason)
        await interaction.followup.send(":white_check_mark: Server banner updated.", ephemeral=True)
        return True
    except discord.Forbidden:
        await interaction.followup.send(":x: I don't have permission to change the server banner.", ephemeral=True)
        return False
    except discord.HTTPException as e:
        await interaction.followup.send(f":x: Failed to set server banner: {e}", ephemeral=True)
        return False

async def set_server_splash(interaction, splash_url, reason):
    """Sets the server splash from a URL."""
    if not splash_url:
        await interaction.response.send_message(":warning: Splash URL is required.", ephemeral=True)
        return False
    
    # Check if the server has the INVITE_SPLASH feature
    if 'INVITE_SPLASH' not in interaction.guild.features:
        await interaction.response.send_message(":warning: This server does not have the invite splash feature. It requires Boost Level 1.", ephemeral=True)
        return False
    
    await interaction.response.defer(ephemeral=True)
    
    try:
        # Download the image
        async with aiohttp.ClientSession() as session:
            async with session.get(splash_url) as resp:
                if resp.status != 200:
                    await interaction.followup.send(f":x: Failed to download image: HTTP {resp.status}", ephemeral=True)
                    return False
                
                image_data = await resp.read()
        
        # Set the server splash
        await interaction.guild.edit(splash=image_data, reason=reason)
        await interaction.followup.send(":white_check_mark: Server invite splash updated.", ephemeral=True)
        return True
    except discord.Forbidden:
        await interaction.followup.send(":x: I don't have permission to change the server splash.", ephemeral=True)
        return False
    except discord.HTTPException as e:
        await interaction.followup.send(f":x: Failed to set server splash: {e}", ephemeral=True)
        return False

async def set_verification_level(interaction, verification_level, reason):
    """Sets the server verification level."""
    if verification_level is None:
        await interaction.response.send_message(":warning: Verification level is required.", ephemeral=True)
        return False
    
    await interaction.response.defer(ephemeral=True)
    
    try:
        # Get the current verification level
        old_level = interaction.guild.verification_level
        
        # Set the new verification level
        await interaction.guild.edit(verification_level=verification_level, reason=reason)
        
        # Get the level names for the message
        verification_levels = {
            discord.VerificationLevel.none: "None",
            discord.VerificationLevel.low: "Low",
            discord.VerificationLevel.medium: "Medium",
            discord.VerificationLevel.high: "High",
            discord.VerificationLevel.highest: "Highest"
        }
        
        old_level_name = verification_levels.get(old_level, "Unknown")
        new_level_name = verification_levels.get(verification_level, "Unknown")
        
        await interaction.followup.send(f":white_check_mark: Server verification level changed from `{old_level_name}` to `{new_level_name}`.", ephemeral=True)
        return True
    except discord.Forbidden:
        await interaction.followup.send(":x: I don't have permission to change the server verification level.", ephemeral=True)
        return False
    except discord.HTTPException as e:
        await interaction.followup.send(f":x: Failed to set verification level: {e}", ephemeral=True)
        return False

async def set_content_filter(interaction, content_filter, reason):
    """Sets the server explicit content filter level."""
    if content_filter is None:
        await interaction.response.send_message(":warning: Content filter level is required.", ephemeral=True)
        return False
    
    await interaction.response.defer(ephemeral=True)
    
    try:
        # Get the current content filter
        old_filter = interaction.guild.explicit_content_filter
        
        # Set the new content filter
        await interaction.guild.edit(explicit_content_filter=content_filter, reason=reason)
        
        # Get the filter names for the message
        content_filters = {
            discord.ContentFilter.disabled: "Disabled",
            discord.ContentFilter.no_role: "No Role",
            discord.ContentFilter.all_members: "All Members"
        }
        
        old_filter_name = content_filters.get(old_filter, "Unknown")
        new_filter_name = content_filters.get(content_filter, "Unknown")
        
        await interaction.followup.send(f":white_check_mark: Server content filter changed from `{old_filter_name}` to `{new_filter_name}`.", ephemeral=True)
        return True
    except discord.Forbidden:
        await interaction.followup.send(":x: I don't have permission to change the server content filter.", ephemeral=True)
        return False
    except discord.HTTPException as e:
        await interaction.followup.send(f":x: Failed to set content filter: {e}", ephemeral=True)
        return False

async def set_system_channel(interaction, system_channel, reason):
    """Sets the server system channel."""
    await interaction.response.defer(ephemeral=True)
    
    try:
        # Get the current system channel
        old_channel = interaction.guild.system_channel
        
        # Set the new system channel
        await interaction.guild.edit(system_channel=system_channel, reason=reason)
        
        # Prepare the message
        old_channel_str = old_channel.mention if old_channel else "None"
        new_channel_str = system_channel.mention if system_channel else "None"
        
        await interaction.followup.send(f":white_check_mark: Server system channel changed from {old_channel_str} to {new_channel_str}.", ephemeral=True)
        return True
    except discord.Forbidden:
        await interaction.followup.send(":x: I don't have permission to change the server system channel.", ephemeral=True)
        return False
    except discord.HTTPException as e:
        await interaction.followup.send(f":x: Failed to set system channel: {e}", ephemeral=True)
        return False

async def set_rules_channel(interaction, rules_channel, reason):
    """Sets the server rules channel."""
    await interaction.response.defer(ephemeral=True)
    
    try:
        # Get the current rules channel
        old_channel = interaction.guild.rules_channel
        
        # Set the new rules channel
        await interaction.guild.edit(rules_channel=rules_channel, reason=reason)
        
        # Prepare the message
        old_channel_str = old_channel.mention if old_channel else "None"
        new_channel_str = rules_channel.mention if rules_channel else "None"
        
        await interaction.followup.send(f":white_check_mark: Server rules channel changed from {old_channel_str} to {new_channel_str}.", ephemeral=True)
        return True
    except discord.Forbidden:
        await interaction.followup.send(":x: I don't have permission to change the server rules channel.", ephemeral=True)
        return False
    except discord.HTTPException as e:
        await interaction.followup.send(f":x: Failed to set rules channel: {e}", ephemeral=True)
        return False

async def set_public_updates_channel(interaction, public_updates_channel, reason):
    """Sets the server public updates channel."""
    await interaction.response.defer(ephemeral=True)
    
    try:
        # Get the current public updates channel
        old_channel = interaction.guild.public_updates_channel
        
        # Set the new public updates channel
        await interaction.guild.edit(public_updates_channel=public_updates_channel, reason=reason)
        
        # Prepare the message
        old_channel_str = old_channel.mention if old_channel else "None"
        new_channel_str = public_updates_channel.mention if public_updates_channel else "None"
        
        await interaction.followup.send(f":white_check_mark: Server public updates channel changed from {old_channel_str} to {new_channel_str}.", ephemeral=True)
        return True
    except discord.Forbidden:
        await interaction.followup.send(":x: I don't have permission to change the server public updates channel.", ephemeral=True)
        return False
    except discord.HTTPException as e:
        await interaction.followup.send(f":x: Failed to set public updates channel: {e}", ephemeral=True)
        return False
