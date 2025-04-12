# commands/free/webhook_manager_command.py
"""
Webhook management command for Discord servers.

This module provides functionality to create, delete, edit, and list webhooks,
as well as send messages through webhooks with customizable content and appearance.
"""

import discord
import logging
import json
import aiohttp
from typing import List, Dict, Any, Optional, Union

log = logging.getLogger('MyBot.Commands.WebhookManager')

async def execute(interaction, bot, args):
    """
    Manages webhooks and sends messages through them.
    
    Args:
        interaction (discord.Interaction): The interaction that triggered the command
        bot (commands.Bot): The bot instance
        args (dict): Command arguments
            - operation (str): The operation to perform (create, delete, edit, list, send)
            - channel (str, optional): Channel name or ID to operate on
            - webhook_id (str, optional): Webhook ID to operate on
            - webhook_url (str, optional): Webhook URL to operate on
            - name (str, optional): Name for the webhook
            - avatar_url (str, optional): Avatar URL for the webhook
            - content (str, optional): Content of the message to send
            - username (str, optional): Username to use when sending a message
            - avatar_override (str, optional): Avatar URL to use when sending a message
            - embed (str, optional): If "true", sends an embed
            - embed_json (str, optional): JSON string of the embed to send
            - thread (str, optional): Thread name or ID to send the message to
            - reason (str, optional): Reason for the audit log
    """
    if not interaction.guild:
        log.warning("Cannot manage webhooks: Not in a guild context")
        return False
    
    # Check permissions
    if not interaction.guild.me.guild_permissions.manage_webhooks:
        log.warning(f"Bot lacks permission to manage webhooks in {interaction.guild.name}")
        return False
    
    # Get parameters
    operation = args.get('operation', '').lower()
    channel_name_or_id = args.get('channel', '')
    webhook_id = args.get('webhook_id', '')
    webhook_url = args.get('webhook_url', '')
    name = args.get('name', '')
    avatar_url = args.get('avatar_url', '')
    content = args.get('content', '')
    username = args.get('username', '')
    avatar_override = args.get('avatar_override', '')
    embed_str = args.get('embed', '').lower()
    embed_json = args.get('embed_json', '')
    thread_name_or_id = args.get('thread', '')
    reason = args.get('reason', 'Webhook management command')
    
    # Find the target channel if specified
    target_channel = None
    if channel_name_or_id:
        try:
            channel_id = int(channel_name_or_id)
            target_channel = interaction.guild.get_channel(channel_id)
        except (ValueError, TypeError):
            # Not an ID, try to find by name
            target_channel = discord.utils.get(interaction.guild.text_channels, name=channel_name_or_id)
    
    # Find the target thread if specified
    target_thread = None
    if thread_name_or_id:
        try:
            thread_id = int(thread_name_or_id)
            target_thread = interaction.guild.get_thread(thread_id)
        except (ValueError, TypeError):
            # Not an ID, try to find by name
            for thread in interaction.guild.threads:
                if thread.name == thread_name_or_id:
                    target_thread = thread
                    break
    
    # Parse embed flag
    use_embed = embed_str == 'true'
    
    # Parse embed JSON if provided
    embed_data = None
    if embed_json:
        try:
            embed_data = json.loads(embed_json)
        except json.JSONDecodeError:
            await interaction.response.send_message(f":warning: Invalid embed JSON: {embed_json}", ephemeral=True)
            return False
    
    # Execute the requested operation
    try:
        if operation == 'create':
            return await create_webhook(interaction, target_channel, name, avatar_url, reason)
        elif operation == 'delete':
            return await delete_webhook(interaction, target_channel, webhook_id, webhook_url, reason)
        elif operation == 'edit':
            return await edit_webhook(interaction, target_channel, webhook_id, webhook_url, name, avatar_url, reason)
        elif operation == 'list':
            return await list_webhooks(interaction, target_channel)
        elif operation == 'send':
            return await send_webhook_message(interaction, target_channel, webhook_id, webhook_url, content, username, avatar_override, use_embed, embed_data, target_thread)
        else:
            await interaction.response.send_message(f":warning: Unknown operation: {operation}", ephemeral=True)
            return False
    except Exception as e:
        log.error(f"Error executing webhook operation {operation}: {e}", exc_info=True)
        await interaction.response.send_message(f":x: Error executing operation: {e}", ephemeral=True)
        return False

async def create_webhook(interaction, channel, name, avatar_url, reason):
    """Creates a new webhook in the specified channel."""
    if not channel:
        await interaction.response.send_message(":warning: Channel not found or not specified.", ephemeral=True)
        return False
    
    if not name:
        await interaction.response.send_message(":warning: Webhook name is required.", ephemeral=True)
        return False
    
    await interaction.response.defer(ephemeral=True)
    
    try:
        # Create the webhook
        webhook_params = {
            'name': name,
            'reason': reason
        }
        
        if avatar_url:
            # Download the avatar image
            async with aiohttp.ClientSession() as session:
                async with session.get(avatar_url) as resp:
                    if resp.status == 200:
                        avatar_bytes = await resp.read()
                        webhook_params['avatar'] = avatar_bytes
                    else:
                        await interaction.followup.send(f":warning: Failed to download avatar image: HTTP {resp.status}", ephemeral=True)
        
        webhook = await channel.create_webhook(**webhook_params)
        
        # Send success message with webhook details
        embed = discord.Embed(
            title="Webhook Created",
            description=f"Webhook created successfully in {channel.mention}",
            color=discord.Color.green()
        )
        
        embed.add_field(name="Name", value=webhook.name, inline=True)
        embed.add_field(name="ID", value=webhook.id, inline=True)
        embed.add_field(name="URL", value=webhook.url, inline=False)
        
        if webhook.avatar:
            embed.set_thumbnail(url=webhook.avatar.url)
        
        await interaction.followup.send(embed=embed, ephemeral=True)
        return True
    except discord.Forbidden:
        await interaction.followup.send(":x: I don't have permission to create webhooks in this channel.", ephemeral=True)
        return False
    except discord.HTTPException as e:
        await interaction.followup.send(f":x: Failed to create webhook: {e}", ephemeral=True)
        return False

async def delete_webhook(interaction, channel, webhook_id, webhook_url, reason):
    """Deletes a webhook by ID or URL."""
    await interaction.response.defer(ephemeral=True)
    
    try:
        webhook = None
        
        # Try to find the webhook by ID first
        if webhook_id:
            try:
                webhook_id_int = int(webhook_id)
                webhook = await interaction.guild.fetch_webhook(webhook_id_int)
            except (ValueError, discord.NotFound):
                pass
        
        # If not found by ID, try by URL
        if not webhook and webhook_url:
            try:
                webhook = await discord.Webhook.from_url(webhook_url, session=bot.session)
                
                # Check if the webhook belongs to this guild
                if webhook.guild_id != interaction.guild.id:
                    await interaction.followup.send(":warning: The specified webhook does not belong to this server.", ephemeral=True)
                    return False
            except (ValueError, discord.NotFound):
                pass
        
        # If still not found and channel is specified, list webhooks in that channel
        if not webhook and channel:
            webhooks = await channel.webhooks()
            if not webhooks:
                await interaction.followup.send(f":warning: No webhooks found in {channel.mention}.", ephemeral=True)
                return False
            
            # If only one webhook exists, use that one
            if len(webhooks) == 1:
                webhook = webhooks[0]
            else:
                # Multiple webhooks, show a list and ask for clarification
                webhook_list = "\n".join([f"• **{w.name}** (ID: {w.id})" for w in webhooks])
                await interaction.followup.send(
                    f":information_source: Multiple webhooks found in {channel.mention}. Please specify a webhook ID:\n\n{webhook_list}",
                    ephemeral=True
                )
                return False
        
        if not webhook:
            await interaction.followup.send(":warning: Webhook not found. Please provide a valid webhook ID or URL.", ephemeral=True)
            return False
        
        # Store webhook info before deletion
        webhook_name = webhook.name
        webhook_channel = webhook.channel
        
        # Delete the webhook
        await webhook.delete(reason=reason)
        
        await interaction.followup.send(
            f":white_check_mark: Webhook **{webhook_name}** deleted successfully from {webhook_channel.mention}.",
            ephemeral=True
        )
        return True
    except discord.Forbidden:
        await interaction.followup.send(":x: I don't have permission to delete this webhook.", ephemeral=True)
        return False
    except discord.HTTPException as e:
        await interaction.followup.send(f":x: Failed to delete webhook: {e}", ephemeral=True)
        return False

async def edit_webhook(interaction, channel, webhook_id, webhook_url, name, avatar_url, reason):
    """Edits a webhook's name and/or avatar."""
    if not name and not avatar_url:
        await interaction.response.send_message(":warning: Please provide a new name and/or avatar URL to edit the webhook.", ephemeral=True)
        return False
    
    await interaction.response.defer(ephemeral=True)
    
    try:
        webhook = None
        
        # Try to find the webhook by ID first
        if webhook_id:
            try:
                webhook_id_int = int(webhook_id)
                webhook = await interaction.guild.fetch_webhook(webhook_id_int)
            except (ValueError, discord.NotFound):
                pass
        
        # If not found by ID, try by URL
        if not webhook and webhook_url:
            try:
                webhook = await discord.Webhook.from_url(webhook_url, session=bot.session)
                
                # Check if the webhook belongs to this guild
                if webhook.guild_id != interaction.guild.id:
                    await interaction.followup.send(":warning: The specified webhook does not belong to this server.", ephemeral=True)
                    return False
            except (ValueError, discord.NotFound):
                pass
        
        # If still not found and channel is specified, list webhooks in that channel
        if not webhook and channel:
            webhooks = await channel.webhooks()
            if not webhooks:
                await interaction.followup.send(f":warning: No webhooks found in {channel.mention}.", ephemeral=True)
                return False
            
            # If only one webhook exists, use that one
            if len(webhooks) == 1:
                webhook = webhooks[0]
            else:
                # Multiple webhooks, show a list and ask for clarification
                webhook_list = "\n".join([f"• **{w.name}** (ID: {w.id})" for w in webhooks])
                await interaction.followup.send(
                    f":information_source: Multiple webhooks found in {channel.mention}. Please specify a webhook ID:\n\n{webhook_list}",
                    ephemeral=True
                )
                return False
        
        if not webhook:
            await interaction.followup.send(":warning: Webhook not found. Please provide a valid webhook ID or URL.", ephemeral=True)
            return False
        
        # Prepare edit parameters
        edit_params = {'reason': reason}
        
        if name:
            edit_params['name'] = name
        
        if avatar_url:
            # Download the avatar image
            async with aiohttp.ClientSession() as session:
                async with session.get(avatar_url) as resp:
                    if resp.status == 200:
                        avatar_bytes = await resp.read()
                        edit_params['avatar'] = avatar_bytes
                    else:
                        await interaction.followup.send(f":warning: Failed to download avatar image: HTTP {resp.status}", ephemeral=True)
        
        # Edit the webhook
        webhook = await webhook.edit(**edit_params)
        
        # Send success message with updated webhook details
        embed = discord.Embed(
            title="Webhook Updated",
            description=f"Webhook updated successfully in {webhook.channel.mention}",
            color=discord.Color.green()
        )
        
        embed.add_field(name="Name", value=webhook.name, inline=True)
        embed.add_field(name="ID", value=webhook.id, inline=True)
        embed.add_field(name="URL", value=webhook.url, inline=False)
        
        if webhook.avatar:
            embed.set_thumbnail(url=webhook.avatar.url)
        
        await interaction.followup.send(embed=embed, ephemeral=True)
        return True
    except discord.Forbidden:
        await interaction.followup.send(":x: I don't have permission to edit this webhook.", ephemeral=True)
        return False
    except discord.HTTPException as e:
        await interaction.followup.send(f":x: Failed to edit webhook: {e}", ephemeral=True)
        return False

async def list_webhooks(interaction, channel):
    """Lists all webhooks in the server or a specific channel."""
    await interaction.response.defer(ephemeral=True)
    
    try:
        if channel:
            # List webhooks in the specified channel
            webhooks = await channel.webhooks()
            
            if not webhooks:
                await interaction.followup.send(f":information_source: No webhooks found in {channel.mention}.", ephemeral=True)
                return True
            
            embed = discord.Embed(
                title=f"Webhooks in #{channel.name}",
                description=f"Found {len(webhooks)} webhook{'s' if len(webhooks) != 1 else ''}",
                color=discord.Color.blue()
            )
        else:
            # List all webhooks in the server
            webhooks = await interaction.guild.webhooks()
            
            if not webhooks:
                await interaction.followup.send(f":information_source: No webhooks found in this server.", ephemeral=True)
                return True
            
            embed = discord.Embed(
                title=f"Webhooks in {interaction.guild.name}",
                description=f"Found {len(webhooks)} webhook{'s' if len(webhooks) != 1 else ''}",
                color=discord.Color.blue()
            )
        
        # Group webhooks by channel
        webhooks_by_channel = {}
        for webhook in webhooks:
            channel_id = webhook.channel_id
            if channel_id not in webhooks_by_channel:
                webhooks_by_channel[channel_id] = []
            webhooks_by_channel[channel_id].append(webhook)
        
        # Add webhooks to the embed
        for channel_id, channel_webhooks in webhooks_by_channel.items():
            channel_obj = interaction.guild.get_channel(channel_id)
            channel_name = f"#{channel_obj.name}" if channel_obj else f"Unknown Channel ({channel_id})"
            
            webhook_list = "\n".join([f"• **{w.name}** (ID: {w.id})" for w in channel_webhooks])
            embed.add_field(name=channel_name, value=webhook_list, inline=False)
        
        await interaction.followup.send(embed=embed, ephemeral=True)
        return True
    except discord.Forbidden:
        await interaction.followup.send(":x: I don't have permission to view webhooks.", ephemeral=True)
        return False
    except discord.HTTPException as e:
        await interaction.followup.send(f":x: Failed to list webhooks: {e}", ephemeral=True)
        return False

async def send_webhook_message(interaction, channel, webhook_id, webhook_url, content, username, avatar_override, use_embed, embed_data, thread):
    """Sends a message through a webhook."""
    if not content and not use_embed:
        await interaction.response.send_message(":warning: Please provide content or an embed for the webhook message.", ephemeral=True)
        return False
    
    await interaction.response.defer(ephemeral=True)
    
    try:
        webhook = None
        
        # Try to find the webhook by ID first
        if webhook_id:
            try:
                webhook_id_int = int(webhook_id)
                webhook = await interaction.guild.fetch_webhook(webhook_id_int)
            except (ValueError, discord.NotFound):
                pass
        
        # If not found by ID, try by URL
        if not webhook and webhook_url:
            try:
                webhook = await discord.Webhook.from_url(webhook_url, session=bot.session)
                
                # Check if the webhook belongs to this guild
                if webhook.guild_id != interaction.guild.id:
                    await interaction.followup.send(":warning: The specified webhook does not belong to this server.", ephemeral=True)
                    return False
            except (ValueError, discord.NotFound):
                pass
        
        # If still not found and channel is specified, list webhooks in that channel
        if not webhook and channel:
            webhooks = await channel.webhooks()
            if not webhooks:
                await interaction.followup.send(f":warning: No webhooks found in {channel.mention}.", ephemeral=True)
                return False
            
            # If only one webhook exists, use that one
            if len(webhooks) == 1:
                webhook = webhooks[0]
            else:
                # Multiple webhooks, show a list and ask for clarification
                webhook_list = "\n".join([f"• **{w.name}** (ID: {w.id})" for w in webhooks])
                await interaction.followup.send(
                    f":information_source: Multiple webhooks found in {channel.mention}. Please specify a webhook ID:\n\n{webhook_list}",
                    ephemeral=True
                )
                return False
        
        if not webhook:
            await interaction.followup.send(":warning: Webhook not found. Please provide a valid webhook ID or URL.", ephemeral=True)
            return False
        
        # Prepare the webhook parameters
        webhook_params = {}
        
        if content:
            webhook_params['content'] = content
        
        if username:
            webhook_params['username'] = username
        
        if avatar_override:
            webhook_params['avatar_url'] = avatar_override
        
        if thread:
            webhook_params['thread'] = thread
        
        # Create an embed if requested
        if use_embed:
            embed = None
            
            if embed_data:
                # Create an embed from the provided JSON data
                embed = discord.Embed()
                
                if 'title' in embed_data:
                    embed.title = embed_data['title']
                
                if 'description' in embed_data:
                    embed.description = embed_data['description']
                
                if 'color' in embed_data:
                    try:
                        if isinstance(embed_data['color'], str):
                            if embed_data['color'].startswith('#'):
                                color_hex = embed_data['color'][1:]
                                embed.color = discord.Color(int(color_hex, 16))
                            else:
                                embed.color = discord.Color(int(embed_data['color'], 16))
                        else:
                            embed.color = discord.Color(embed_data['color'])
                    except (ValueError, TypeError):
                        embed.color = discord.Color.blue()
                
                if 'url' in embed_data:
                    embed.url = embed_data['url']
                
                if 'timestamp' in embed_data and embed_data['timestamp']:
                    embed.timestamp = datetime.datetime.now()
                
                # Add author if provided
                if 'author' in embed_data:
                    author_name = embed_data['author'].get('name', '')
                    author_url = embed_data['author'].get('url', None)
                    author_icon_url = embed_data['author'].get('icon_url', None)
                    
                    if author_name:
                        embed.set_author(name=author_name, url=author_url, icon_url=author_icon_url)
                
                # Add thumbnail if provided
                if 'thumbnail' in embed_data and 'url' in embed_data['thumbnail']:
                    embed.set_thumbnail(url=embed_data['thumbnail']['url'])
                
                # Add image if provided
                if 'image' in embed_data and 'url' in embed_data['image']:
                    embed.set_image(url=embed_data['image']['url'])
                
                # Add footer if provided
                if 'footer' in embed_data:
                    footer_text = embed_data['footer'].get('text', '')
                    footer_icon_url = embed_data['footer'].get('icon_url', None)
                    
                    if footer_text:
                        embed.set_footer(text=footer_text, icon_url=footer_icon_url)
                
                # Add fields if provided
                if 'fields' in embed_data and isinstance(embed_data['fields'], list):
                    for field in embed_data['fields']:
                        if 'name' in field and 'value' in field:
                            inline = field.get('inline', False)
                            embed.add_field(name=field['name'], value=field['value'], inline=inline)
            else:
                # Create a simple embed with the content
                embed = discord.Embed(
                    description=content,
                    color=discord.Color.blue()
                )
                
                # Remove content from webhook params since we're using it in the embed
                if 'content' in webhook_params:
                    del webhook_params['content']
            
            webhook_params['embeds'] = [embed]
        
        # Send the webhook message
        await webhook.send(**webhook_params)
        
        # Send success message
        target_channel = webhook.channel
        if thread:
            thread_mention = f"thread {thread.mention}" if hasattr(thread, 'mention') else f"thread {thread}"
            await interaction.followup.send(f":white_check_mark: Message sent through webhook **{webhook.name}** in {target_channel.mention} ({thread_mention}).", ephemeral=True)
        else:
            await interaction.followup.send(f":white_check_mark: Message sent through webhook **{webhook.name}** in {target_channel.mention}.", ephemeral=True)
        
        return True
    except discord.Forbidden:
        await interaction.followup.send(":x: I don't have permission to execute this webhook.", ephemeral=True)
        return False
    except discord.HTTPException as e:
        await interaction.followup.send(f":x: Failed to send webhook message: {e}", ephemeral=True)
        return False

# Initialize the bot variable for webhook operations
bot = None

def setup(bot_instance):
    """Sets up the bot instance for webhook operations."""
    global bot
    bot = bot_instance
