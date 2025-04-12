# commands/free/emoji_manager_command.py
"""
Emoji and sticker management command for Discord servers.

This module provides functionality to create, delete, edit, and list emojis and stickers,
as well as manage emoji roles and other settings.
"""

import discord
import logging
import aiohttp
import io
from typing import List, Dict, Any, Optional, Union

log = logging.getLogger('MyBot.Commands.EmojiManager')

async def execute(interaction, bot, args):
    """
    Manages emojis and stickers in the server.
    
    Args:
        interaction (discord.Interaction): The interaction that triggered the command
        bot (commands.Bot): The bot instance
        args (dict): Command arguments
            - operation (str): The operation to perform (create_emoji, delete_emoji, edit_emoji, list_emojis, 
                              create_sticker, delete_sticker, edit_sticker, list_stickers)
            - name (str, optional): Name for the emoji or sticker
            - url (str, optional): URL of the image to use for the emoji or sticker
            - emoji (str, optional): Emoji name or ID to operate on
            - sticker (str, optional): Sticker name or ID to operate on
            - description (str, optional): Description for the sticker
            - emoji_type (str, optional): Type of sticker (standard, guild, nitro)
            - roles (str, optional): Comma-separated list of role names or IDs that can use the emoji
            - reason (str, optional): Reason for the audit log
    """
    if not interaction.guild:
        log.warning("Cannot manage emojis: Not in a guild context")
        return False
    
    # Check permissions
    if not interaction.guild.me.guild_permissions.manage_emojis:
        log.warning(f"Bot lacks permission to manage emojis in {interaction.guild.name}")
        return False
    
    # Get parameters
    operation = args.get('operation', '').lower()
    name = args.get('name', '')
    url = args.get('url', '')
    emoji_name_or_id = args.get('emoji', '')
    sticker_name_or_id = args.get('sticker', '')
    description = args.get('description', '')
    emoji_type_str = args.get('emoji_type', 'guild').lower()
    roles_str = args.get('roles', '')
    reason = args.get('reason', 'Emoji management command')
    
    # Find the target emoji if specified
    target_emoji = None
    if emoji_name_or_id:
        try:
            emoji_id = int(emoji_name_or_id)
            target_emoji = discord.utils.get(interaction.guild.emojis, id=emoji_id)
        except (ValueError, TypeError):
            # Not an ID, try to find by name
            target_emoji = discord.utils.get(interaction.guild.emojis, name=emoji_name_or_id)
    
    # Find the target sticker if specified
    target_sticker = None
    if sticker_name_or_id:
        try:
            sticker_id = int(sticker_name_or_id)
            target_sticker = discord.utils.get(interaction.guild.stickers, id=sticker_id)
        except (ValueError, TypeError):
            # Not an ID, try to find by name
            target_sticker = discord.utils.get(interaction.guild.stickers, name=sticker_name_or_id)
    
    # Parse roles if specified
    roles = []
    if roles_str:
        role_names_or_ids = [r.strip() for r in roles_str.split(',')]
        for role_name_or_id in role_names_or_ids:
            role = None
            try:
                role_id = int(role_name_or_id)
                role = interaction.guild.get_role(role_id)
            except (ValueError, TypeError):
                # Not an ID, try to find by name
                role = discord.utils.get(interaction.guild.roles, name=role_name_or_id)
            
            if role:
                roles.append(role)
    
    # Parse sticker type
    sticker_format = None
    if emoji_type_str == 'standard':
        sticker_format = discord.StickerFormatType.png
    elif emoji_type_str == 'nitro':
        sticker_format = discord.StickerFormatType.apng
    else:  # guild
        sticker_format = discord.StickerFormatType.png
    
    # Execute the requested operation
    try:
        if operation == 'create_emoji':
            return await create_emoji(interaction, name, url, roles, reason)
        elif operation == 'delete_emoji':
            return await delete_emoji(interaction, target_emoji, reason)
        elif operation == 'edit_emoji':
            return await edit_emoji(interaction, target_emoji, name, roles, reason)
        elif operation == 'list_emojis':
            return await list_emojis(interaction)
        elif operation == 'create_sticker':
            return await create_sticker(interaction, name, description, url, sticker_format, reason)
        elif operation == 'delete_sticker':
            return await delete_sticker(interaction, target_sticker, reason)
        elif operation == 'edit_sticker':
            return await edit_sticker(interaction, target_sticker, name, description, reason)
        elif operation == 'list_stickers':
            return await list_stickers(interaction)
        else:
            await interaction.response.send_message(f":warning: Unknown operation: {operation}", ephemeral=True)
            return False
    except Exception as e:
        log.error(f"Error executing emoji operation {operation}: {e}", exc_info=True)
        await interaction.response.send_message(f":x: Error executing operation: {e}", ephemeral=True)
        return False

async def create_emoji(interaction, name, url, roles, reason):
    """Creates a new emoji in the server."""
    if not name:
        await interaction.response.send_message(":warning: Emoji name is required.", ephemeral=True)
        return False
    
    if not url:
        await interaction.response.send_message(":warning: Emoji image URL is required.", ephemeral=True)
        return False
    
    await interaction.response.defer(ephemeral=True)
    
    try:
        # Check if the server has reached the emoji limit
        emoji_limit = interaction.guild.emoji_limit
        if len(interaction.guild.emojis) >= emoji_limit:
            await interaction.followup.send(f":warning: This server has reached its emoji limit ({emoji_limit}).", ephemeral=True)
            return False
        
        # Download the image
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    await interaction.followup.send(f":warning: Failed to download image: HTTP {resp.status}", ephemeral=True)
                    return False
                
                image_data = await resp.read()
        
        # Create the emoji
        emoji = await interaction.guild.create_custom_emoji(
            name=name,
            image=image_data,
            roles=roles,
            reason=reason
        )
        
        # Send success message
        embed = discord.Embed(
            title="Emoji Created",
            description=f"Emoji {emoji} created successfully",
            color=discord.Color.green()
        )
        
        embed.add_field(name="Name", value=emoji.name, inline=True)
        embed.add_field(name="ID", value=emoji.id, inline=True)
        
        if roles:
            role_mentions = [role.mention for role in roles]
            embed.add_field(name="Restricted to Roles", value=", ".join(role_mentions), inline=False)
        
        await interaction.followup.send(embed=embed, ephemeral=True)
        return True
    except discord.Forbidden:
        await interaction.followup.send(":x: I don't have permission to create emojis in this server.", ephemeral=True)
        return False
    except discord.HTTPException as e:
        await interaction.followup.send(f":x: Failed to create emoji: {e}", ephemeral=True)
        return False

async def delete_emoji(interaction, emoji, reason):
    """Deletes an emoji from the server."""
    if not emoji:
        await interaction.response.send_message(":warning: Emoji not found or not specified.", ephemeral=True)
        return False
    
    await interaction.response.defer(ephemeral=True)
    
    try:
        # Store emoji info before deletion
        emoji_name = emoji.name
        emoji_id = emoji.id
        
        # Delete the emoji
        await emoji.delete(reason=reason)
        
        await interaction.followup.send(f":white_check_mark: Emoji **{emoji_name}** (ID: {emoji_id}) deleted successfully.", ephemeral=True)
        return True
    except discord.Forbidden:
        await interaction.followup.send(":x: I don't have permission to delete emojis in this server.", ephemeral=True)
        return False
    except discord.HTTPException as e:
        await interaction.followup.send(f":x: Failed to delete emoji: {e}", ephemeral=True)
        return False

async def edit_emoji(interaction, emoji, name, roles, reason):
    """Edits an emoji's name and/or role restrictions."""
    if not emoji:
        await interaction.response.send_message(":warning: Emoji not found or not specified.", ephemeral=True)
        return False
    
    if not name and not roles:
        await interaction.response.send_message(":warning: Please provide a new name and/or roles to edit the emoji.", ephemeral=True)
        return False
    
    await interaction.response.defer(ephemeral=True)
    
    try:
        # Prepare the edit parameters
        edit_params = {'reason': reason}
        
        if name:
            edit_params['name'] = name
        
        if roles:
            edit_params['roles'] = roles
        
        # Edit the emoji
        await emoji.edit(**edit_params)
        
        # Prepare a message about what was changed
        changes = []
        if name:
            changes.append(f"name to `{name}`")
        if roles:
            role_names = [role.name for role in roles]
            changes.append(f"role restrictions to `{', '.join(role_names)}`")
        
        changes_str = ", ".join(changes)
        await interaction.followup.send(f":white_check_mark: Emoji {emoji} updated: {changes_str}.", ephemeral=True)
        return True
    except discord.Forbidden:
        await interaction.followup.send(":x: I don't have permission to edit emojis in this server.", ephemeral=True)
        return False
    except discord.HTTPException as e:
        await interaction.followup.send(f":x: Failed to edit emoji: {e}", ephemeral=True)
        return False

async def list_emojis(interaction):
    """Lists all emojis in the server."""
    await interaction.response.defer(ephemeral=True)
    
    try:
        emojis = interaction.guild.emojis
        
        if not emojis:
            await interaction.followup.send(":information_source: This server has no custom emojis.", ephemeral=True)
            return True
        
        # Create an embed with emoji information
        embed = discord.Embed(
            title=f"Emojis in {interaction.guild.name}",
            description=f"Total: {len(emojis)}/{interaction.guild.emoji_limit} emojis",
            color=discord.Color.blue()
        )
        
        # Group emojis by whether they're animated
        static_emojis = [e for e in emojis if not e.animated]
        animated_emojis = [e for e in emojis if e.animated]
        
        # Add static emojis
        if static_emojis:
            static_chunks = [static_emojis[i:i+20] for i in range(0, len(static_emojis), 20)]
            
            for i, chunk in enumerate(static_chunks):
                emoji_list = " ".join([str(emoji) for emoji in chunk])
                embed.add_field(name=f"Static Emojis {i+1}", value=emoji_list or "None", inline=False)
        
        # Add animated emojis
        if animated_emojis:
            animated_chunks = [animated_emojis[i:i+20] for i in range(0, len(animated_emojis), 20)]
            
            for i, chunk in enumerate(animated_chunks):
                emoji_list = " ".join([str(emoji) for emoji in chunk])
                embed.add_field(name=f"Animated Emojis {i+1}", value=emoji_list or "None", inline=False)
        
        # Add restricted emojis
        restricted_emojis = [e for e in emojis if e.roles]
        if restricted_emojis:
            restricted_info = []
            for emoji in restricted_emojis[:10]:  # Limit to 10 to avoid hitting embed limits
                role_names = [role.name for role in emoji.roles]
                restricted_info.append(f"{emoji} - Restricted to: {', '.join(role_names)}")
            
            if len(restricted_emojis) > 10:
                restricted_info.append(f"... and {len(restricted_emojis) - 10} more")
            
            embed.add_field(name="Role-Restricted Emojis", value="\n".join(restricted_info), inline=False)
        
        await interaction.followup.send(embed=embed, ephemeral=True)
        return True
    except discord.Forbidden:
        await interaction.followup.send(":x: I don't have permission to view emojis in this server.", ephemeral=True)
        return False
    except discord.HTTPException as e:
        await interaction.followup.send(f":x: Failed to list emojis: {e}", ephemeral=True)
        return False

async def create_sticker(interaction, name, description, url, sticker_format, reason):
    """Creates a new sticker in the server."""
    if not name:
        await interaction.response.send_message(":warning: Sticker name is required.", ephemeral=True)
        return False
    
    if not url:
        await interaction.response.send_message(":warning: Sticker image URL is required.", ephemeral=True)
        return False
    
    if not description:
        await interaction.response.send_message(":warning: Sticker description is required.", ephemeral=True)
        return False
    
    await interaction.response.defer(ephemeral=True)
    
    try:
        # Check if the server has reached the sticker limit
        sticker_limit = interaction.guild.sticker_limit
        if len(interaction.guild.stickers) >= sticker_limit:
            await interaction.followup.send(f":warning: This server has reached its sticker limit ({sticker_limit}).", ephemeral=True)
            return False
        
        # Download the image
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    await interaction.followup.send(f":warning: Failed to download image: HTTP {resp.status}", ephemeral=True)
                    return False
                
                image_data = await resp.read()
        
        # Create the sticker
        sticker = await interaction.guild.create_sticker(
            name=name,
            description=description,
            emoji="⭐",  # Required emoji name
            file=discord.File(io.BytesIO(image_data), filename="sticker.png"),
            reason=reason
        )
        
        # Send success message
        embed = discord.Embed(
            title="Sticker Created",
            description=f"Sticker **{sticker.name}** created successfully",
            color=discord.Color.green()
        )
        
        embed.add_field(name="Name", value=sticker.name, inline=True)
        embed.add_field(name="ID", value=sticker.id, inline=True)
        embed.add_field(name="Description", value=sticker.description, inline=False)
        
        if sticker.url:
            embed.set_image(url=sticker.url)
        
        await interaction.followup.send(embed=embed, ephemeral=True)
        return True
    except discord.Forbidden:
        await interaction.followup.send(":x: I don't have permission to create stickers in this server.", ephemeral=True)
        return False
    except discord.HTTPException as e:
        await interaction.followup.send(f":x: Failed to create sticker: {e}", ephemeral=True)
        return False

async def delete_sticker(interaction, sticker, reason):
    """Deletes a sticker from the server."""
    if not sticker:
        await interaction.response.send_message(":warning: Sticker not found or not specified.", ephemeral=True)
        return False
    
    await interaction.response.defer(ephemeral=True)
    
    try:
        # Store sticker info before deletion
        sticker_name = sticker.name
        sticker_id = sticker.id
        
        # Delete the sticker
        await sticker.delete(reason=reason)
        
        await interaction.followup.send(f":white_check_mark: Sticker **{sticker_name}** (ID: {sticker_id}) deleted successfully.", ephemeral=True)
        return True
    except discord.Forbidden:
        await interaction.followup.send(":x: I don't have permission to delete stickers in this server.", ephemeral=True)
        return False
    except discord.HTTPException as e:
        await interaction.followup.send(f":x: Failed to delete sticker: {e}", ephemeral=True)
        return False

async def edit_sticker(interaction, sticker, name, description, reason):
    """Edits a sticker's name and/or description."""
    if not sticker:
        await interaction.response.send_message(":warning: Sticker not found or not specified.", ephemeral=True)
        return False
    
    if not name and not description:
        await interaction.response.send_message(":warning: Please provide a new name and/or description to edit the sticker.", ephemeral=True)
        return False
    
    await interaction.response.defer(ephemeral=True)
    
    try:
        # Prepare the edit parameters
        edit_params = {'reason': reason}
        
        if name:
            edit_params['name'] = name
        
        if description:
            edit_params['description'] = description
        
        # Edit the sticker
        await sticker.edit(**edit_params)
        
        # Prepare a message about what was changed
        changes = []
        if name:
            changes.append(f"name to `{name}`")
        if description:
            changes.append(f"description to `{description}`")
        
        changes_str = ", ".join(changes)
        await interaction.followup.send(f":white_check_mark: Sticker **{sticker.name}** updated: {changes_str}.", ephemeral=True)
        return True
    except discord.Forbidden:
        await interaction.followup.send(":x: I don't have permission to edit stickers in this server.", ephemeral=True)
        return False
    except discord.HTTPException as e:
        await interaction.followup.send(f":x: Failed to edit sticker: {e}", ephemeral=True)
        return False

async def list_stickers(interaction):
    """Lists all stickers in the server."""
    await interaction.response.defer(ephemeral=True)
    
    try:
        stickers = interaction.guild.stickers
        
        if not stickers:
            await interaction.followup.send(":information_source: This server has no custom stickers.", ephemeral=True)
            return True
        
        # Create an embed with sticker information
        embed = discord.Embed(
            title=f"Stickers in {interaction.guild.name}",
            description=f"Total: {len(stickers)}/{interaction.guild.sticker_limit} stickers",
            color=discord.Color.blue()
        )
        
        # Add stickers to the embed
        sticker_chunks = [stickers[i:i+10] for i in range(0, len(stickers), 10)]
        
        for i, chunk in enumerate(sticker_chunks):
            sticker_list = []
            for sticker in chunk:
                sticker_list.append(f"• **{sticker.name}** (ID: {sticker.id})\n  {sticker.description}")
            
            embed.add_field(name=f"Stickers {i*10+1}-{i*10+len(chunk)}", value="\n".join(sticker_list), inline=False)
        
        await interaction.followup.send(embed=embed, ephemeral=True)
        return True
    except discord.Forbidden:
        await interaction.followup.send(":x: I don't have permission to view stickers in this server.", ephemeral=True)
        return False
    except discord.HTTPException as e:
        await interaction.followup.send(f":x: Failed to list stickers: {e}", ephemeral=True)
        return False
