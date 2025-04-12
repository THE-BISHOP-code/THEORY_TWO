# commands/premium/message_advanced_command.py
import discord
import logging
import json
import re
from datetime import datetime

log = logging.getLogger('MyBot.Commands.MessageAdvanced')

async def execute(interaction, bot, args):
    """
    Sends an advanced message with rich formatting options.
    
    Args:
        interaction (discord.Interaction): The interaction that triggered the command
        bot (commands.Bot): The bot instance
        args (dict): Command arguments
            - channel (str): Channel name or ID to send the message to
            - content (str, optional): The text content of the message
            - embed (str, optional): If "true", sends as an embed
            - title (str, optional): Title for the embed
            - description (str, optional): Description for the embed
            - color (str, optional): Color for the embed in hex format (#RRGGBB)
            - image (str, optional): URL of an image to include
            - thumbnail (str, optional): URL of a thumbnail to include
            - author (str, optional): Author name for the embed
            - author_icon (str, optional): URL of the author icon
            - footer (str, optional): Footer text for the embed
            - footer_icon (str, optional): URL of the footer icon
            - timestamp (str, optional): If "true", includes current timestamp
            - fields (str, optional): JSON string of fields to add (array of objects with name, value, inline)
    """
    if not interaction.guild:
        log.warning("Cannot send advanced message: Not in a guild context")
        return False
    
    # Check permissions
    if not interaction.guild.me.guild_permissions.send_messages:
        log.warning(f"Bot lacks permission to send messages in {interaction.guild.name}")
        return False
    
    # Get parameters
    channel_name_or_id = args.get('channel')
    content = args.get('content', '')
    use_embed = args.get('embed', 'false').lower() == 'true'
    
    if not channel_name_or_id:
        log.error("Cannot send message: No channel specified")
        return False
    
    # Find the channel
    target_channel = None
    
    # Try to find by ID first
    try:
        channel_id = int(channel_name_or_id)
        target_channel = interaction.guild.get_channel(channel_id)
    except (ValueError, TypeError):
        # Not an ID, try to find by name
        target_channel = discord.utils.get(interaction.guild.text_channels, name=channel_name_or_id)
    
    if not target_channel:
        log.error(f"Cannot send message: Channel '{channel_name_or_id}' not found")
        return False
    
    # Check if we can send messages to the target channel
    if not target_channel.permissions_for(interaction.guild.me).send_messages:
        log.warning(f"Bot lacks permission to send messages in {target_channel.name}")
        return False
    
    try:
        if use_embed:
            # Create the embed
            embed = discord.Embed()
            
            # Set title if provided
            title = args.get('title')
            if title:
                embed.title = title
            
            # Set description if provided
            description = args.get('description')
            if description:
                embed.description = description
            elif content:
                # Use content as description if no description provided
                embed.description = content
            
            # Set color if provided
            color_str = args.get('color')
            if color_str:
                if color_str.startswith('#'):
                    color_str = color_str[1:]
                try:
                    color_int = int(color_str, 16)
                    embed.color = discord.Color(color_int)
                except ValueError:
                    log.warning(f"Invalid color format: {color_str}. Using default color.")
                    embed.color = discord.Color.blue()
            else:
                embed.color = discord.Color.blue()
            
            # Set image if provided
            image_url = args.get('image')
            if image_url:
                embed.set_image(url=image_url)
            
            # Set thumbnail if provided
            thumbnail_url = args.get('thumbnail')
            if thumbnail_url:
                embed.set_thumbnail(url=thumbnail_url)
            
            # Set author if provided
            author_name = args.get('author')
            author_icon = args.get('author_icon')
            if author_name:
                embed.set_author(name=author_name, icon_url=author_icon if author_icon else None)
            
            # Set footer if provided
            footer_text = args.get('footer')
            footer_icon = args.get('footer_icon')
            if footer_text:
                embed.set_footer(text=footer_text, icon_url=footer_icon if footer_icon else None)
            
            # Set timestamp if requested
            if args.get('timestamp', 'false').lower() == 'true':
                embed.timestamp = datetime.now()
            
            # Add fields if provided
            fields_json = args.get('fields')
            if fields_json:
                try:
                    fields = json.loads(fields_json)
                    if isinstance(fields, list):
                        for field in fields:
                            if isinstance(field, dict) and 'name' in field and 'value' in field:
                                name = field['name']
                                value = field['value']
                                inline = field.get('inline', False)
                                embed.add_field(name=name, value=value, inline=inline)
                except json.JSONDecodeError:
                    log.warning(f"Invalid JSON for fields: {fields_json}")
            
            # Send the embed
            await target_channel.send(embed=embed)
        else:
            # Send a regular message
            await target_channel.send(content)
        
        log.info(f"Sent advanced message to #{target_channel.name} in {interaction.guild.name}")
        return True
    except discord.Forbidden:
        log.error(f"Forbidden: Bot lacks permission to send message to #{target_channel.name}")
        return False
    except discord.HTTPException as e:
        log.error(f"HTTP error sending message: {e}")
        return False
    except Exception as e:
        log.error(f"Error sending message: {e}", exc_info=True)
        return False
