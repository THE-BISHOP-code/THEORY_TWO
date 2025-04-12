# commands/free/message_send_command.py
import discord
import logging

log = logging.getLogger('MyBot.Commands.MessageSend')

async def execute(interaction, bot, args):
    """
    Sends a message to a specified channel.
    
    Args:
        interaction (discord.Interaction): The interaction that triggered the command
        bot (commands.Bot): The bot instance
        args (dict): Command arguments
            - channel (str): The name or ID of the channel to send the message to
            - content (str): The content of the message
            - embed (bool, optional): Whether to send the content as an embed
    """
    if not interaction.guild:
        log.warning("Cannot send message: Not in a guild context")
        return False
    
    # Check permissions
    if not interaction.guild.me.guild_permissions.send_messages:
        log.warning(f"Bot lacks permission to send messages in {interaction.guild.name}")
        return False
    
    # Get parameters
    channel_name_or_id = args.get('channel')
    content = args.get('content')
    
    if not channel_name_or_id:
        log.error("Cannot send message: No channel specified")
        return False
    
    if not content:
        log.error("Cannot send message: No content provided")
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
    
    # Check if we should send as embed
    use_embed = args.get('embed', 'false').lower() == 'true'
    
    try:
        if use_embed:
            embed = discord.Embed(description=content, color=discord.Color.blue())
            await target_channel.send(embed=embed)
        else:
            await target_channel.send(content)
        
        log.info(f"Sent message to #{target_channel.name} ({target_channel.id}) in {interaction.guild.name}")
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
