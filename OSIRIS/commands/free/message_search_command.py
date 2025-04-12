# commands/free/message_search_command.py
"""
Message search command for Discord servers.

This module provides functionality to search for messages in channels based on
various criteria such as content, author, date range, and more.
"""

import discord
import logging
import re
import datetime
from typing import List, Dict, Any, Optional, Union

log = logging.getLogger('MyBot.Commands.MessageSearch')

async def execute(interaction, bot, args):
    """
    Searches for messages in channels based on various criteria.
    
    Args:
        interaction (discord.Interaction): The interaction that triggered the command
        bot (commands.Bot): The bot instance
        args (dict): Command arguments
            - channel (str, optional): Channel name or ID to search in (defaults to current channel)
            - query (str, optional): Text to search for in messages
            - user (str, optional): User ID, mention, or name to filter messages by
            - has_image (str, optional): If "true", only includes messages with images
            - has_file (str, optional): If "true", only includes messages with files
            - has_embed (str, optional): If "true", only includes messages with embeds
            - before (str, optional): Only include messages before this date/time (ISO format or relative time)
            - after (str, optional): Only include messages after this date/time (ISO format or relative time)
            - limit (str, optional): Maximum number of messages to return (default: 25, max: 100)
            - output_channel (str, optional): Channel name or ID to send results to (defaults to current channel)
    """
    if not interaction.guild:
        log.warning("Cannot search messages: Not in a guild context")
        return False
    
    # Get parameters
    channel_name_or_id = args.get('channel', '')
    query = args.get('query', '')
    user_id_or_mention = args.get('user', '')
    has_image_str = args.get('has_image', '').lower()
    has_file_str = args.get('has_file', '').lower()
    has_embed_str = args.get('has_embed', '').lower()
    before_str = args.get('before', '')
    after_str = args.get('after', '')
    limit_str = args.get('limit', '25')
    output_channel_name_or_id = args.get('output_channel', '')
    
    # Find the target channel
    target_channel = interaction.channel
    if channel_name_or_id:
        try:
            channel_id = int(channel_name_or_id)
            found_channel = interaction.guild.get_channel(channel_id)
            if found_channel and isinstance(found_channel, discord.TextChannel):
                target_channel = found_channel
        except (ValueError, TypeError):
            # Not an ID, try to find by name
            found_channel = discord.utils.get(interaction.guild.text_channels, name=channel_name_or_id)
            if found_channel:
                target_channel = found_channel
    
    # Find the output channel
    output_channel = interaction.channel
    if output_channel_name_or_id:
        try:
            channel_id = int(output_channel_name_or_id)
            found_channel = interaction.guild.get_channel(channel_id)
            if found_channel and isinstance(found_channel, discord.TextChannel):
                output_channel = found_channel
        except (ValueError, TypeError):
            # Not an ID, try to find by name
            found_channel = discord.utils.get(interaction.guild.text_channels, name=output_channel_name_or_id)
            if found_channel:
                output_channel = found_channel
    
    # Find the target user if specified
    target_user = None
    if user_id_or_mention:
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
    
    # Parse boolean parameters
    has_image = has_image_str == 'true'
    has_file = has_file_str == 'true'
    has_embed = has_embed_str == 'true'
    
    # Parse date parameters
    before_date = None
    if before_str:
        try:
            # Try ISO format
            before_date = datetime.datetime.fromisoformat(before_str.replace('Z', '+00:00'))
        except ValueError:
            # Try relative time
            try:
                before_date = parse_relative_time(before_str)
            except ValueError:
                await interaction.response.send_message(f":warning: Invalid 'before' date format: {before_str}", ephemeral=True)
                return False
    
    after_date = None
    if after_str:
        try:
            # Try ISO format
            after_date = datetime.datetime.fromisoformat(after_str.replace('Z', '+00:00'))
        except ValueError:
            # Try relative time
            try:
                after_date = parse_relative_time(after_str)
            except ValueError:
                await interaction.response.send_message(f":warning: Invalid 'after' date format: {after_str}", ephemeral=True)
                return False
    
    # Parse limit
    try:
        limit = int(limit_str)
        limit = min(max(1, limit), 100)  # Clamp between 1 and 100
    except ValueError:
        limit = 25  # Default
    
    # Defer the response since this might take a while
    await interaction.response.defer(ephemeral=True)
    
    # Search for messages
    try:
        # Create a list to store matching messages
        matching_messages = []
        
        # Create the message check function
        def message_check(message):
            # Check user filter
            if target_user and message.author.id != target_user.id:
                return False
            
            # Check content filter
            if query and query.lower() not in message.content.lower():
                return False
            
            # Check date filters
            if before_date and message.created_at >= before_date:
                return False
            if after_date and message.created_at <= after_date:
                return False
            
            # Check attachment filters
            if has_image:
                has_img = any(attachment.content_type and attachment.content_type.startswith('image/') for attachment in message.attachments)
                if not has_img:
                    return False
            
            if has_file:
                if not message.attachments:
                    return False
            
            if has_embed:
                if not message.embeds:
                    return False
            
            return True
        
        # Fetch messages
        async for message in target_channel.history(limit=1000):  # Fetch up to 1000 messages
            if message_check(message):
                matching_messages.append(message)
                if len(matching_messages) >= limit:
                    break
        
        # Sort messages by creation time (newest first)
        matching_messages.sort(key=lambda m: m.created_at, reverse=True)
        
        # Create the results embed
        if matching_messages:
            # Create the main embed
            embed = discord.Embed(
                title=f"Message Search Results",
                description=f"Found {len(matching_messages)} messages in {target_channel.mention}",
                color=discord.Color.blue()
            )
            
            # Add search parameters
            search_params = []
            if query:
                search_params.append(f"Query: `{query}`")
            if target_user:
                search_params.append(f"User: {target_user.mention}")
            if has_image:
                search_params.append("Has image: Yes")
            if has_file:
                search_params.append("Has file: Yes")
            if has_embed:
                search_params.append("Has embed: Yes")
            if before_date:
                search_params.append(f"Before: {before_date.strftime('%Y-%m-%d %H:%M:%S')}")
            if after_date:
                search_params.append(f"After: {after_date.strftime('%Y-%m-%d %H:%M:%S')}")
            
            if search_params:
                embed.add_field(name="Search Parameters", value="\n".join(search_params), inline=False)
            
            # Add message results (up to 10 in the main embed)
            for i, message in enumerate(matching_messages[:10]):
                # Format the message content (truncate if too long)
                content = message.content
                if len(content) > 200:
                    content = content[:197] + "..."
                
                # Add attachments info
                attachments_info = ""
                if message.attachments:
                    attachment_types = []
                    for attachment in message.attachments:
                        if attachment.content_type:
                            if attachment.content_type.startswith('image/'):
                                attachment_types.append("Image")
                            else:
                                attachment_types.append("File")
                        else:
                            attachment_types.append("Attachment")
                    
                    attachments_info = f" [{', '.join(attachment_types)}]"
                
                # Add embeds info
                embeds_info = ""
                if message.embeds:
                    embeds_info = f" [{len(message.embeds)} Embed{'s' if len(message.embeds) > 1 else ''}]"
                
                # Format the field
                timestamp = int(message.created_at.timestamp())
                field_value = f"{content}{attachments_info}{embeds_info}\n[Jump to Message]({message.jump_url}) • <t:{timestamp}:R>"
                
                embed.add_field(
                    name=f"{i+1}. {message.author.display_name}",
                    value=field_value,
                    inline=False
                )
            
            # Add a note if there are more results
            if len(matching_messages) > 10:
                embed.set_footer(text=f"Showing 10 of {len(matching_messages)} results. Use a more specific search to narrow down results.")
            
            # Send the results
            await output_channel.send(embed=embed)
            
            # Send a success message
            await interaction.followup.send(f":white_check_mark: Search results sent to {output_channel.mention}.", ephemeral=True)
        else:
            # No results found
            await interaction.followup.send(":information_source: No messages found matching the search criteria.", ephemeral=True)
        
        return True
    except discord.Forbidden:
        await interaction.followup.send(":x: I don't have permission to read messages in the target channel.", ephemeral=True)
        return False
    except discord.HTTPException as e:
        await interaction.followup.send(f":x: Error searching messages: {e}", ephemeral=True)
        return False
    except Exception as e:
        log.error(f"Error searching messages: {e}", exc_info=True)
        await interaction.followup.send(f":x: An error occurred while searching messages: {e}", ephemeral=True)
        return False

def parse_relative_time(time_str):
    """
    Parses a relative time string into a datetime object.
    
    Supported formats:
    - Xh (X hours ago)
    - Xd (X days ago)
    - Xw (X weeks ago)
    - Xm (X months ago)
    - Xy (X years ago)
    - yesterday
    - today
    
    Args:
        time_str (str): The relative time string
        
    Returns:
        datetime.datetime: The parsed datetime object
        
    Raises:
        ValueError: If the time string is invalid
    """
    now = datetime.datetime.now()
    
    # Check for simple relative formats
    if time_str.lower() == 'yesterday':
        return now - datetime.timedelta(days=1)
    elif time_str.lower() == 'today':
        return now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Check for numeric relative formats
    match = re.match(r'^(\d+)([hdwmy])$', time_str.lower())
    if match:
        value = int(match.group(1))
        unit = match.group(2)
        
        if unit == 'h':
            return now - datetime.timedelta(hours=value)
        elif unit == 'd':
            return now - datetime.timedelta(days=value)
        elif unit == 'w':
            return now - datetime.timedelta(weeks=value)
        elif unit == 'm':
            # Approximate months as 30 days
            return now - datetime.timedelta(days=value * 30)
        elif unit == 'y':
            # Approximate years as 365 days
            return now - datetime.timedelta(days=value * 365)
    
    raise ValueError(f"Invalid relative time format: {time_str}")
