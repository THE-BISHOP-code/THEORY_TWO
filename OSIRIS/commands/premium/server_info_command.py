# commands/free/server_info_command.py
import discord
import logging
from datetime import datetime

log = logging.getLogger('MyBot.Commands.ServerInfo')

async def execute(interaction, bot, args):
    """
    Displays information about the server.
    
    Args:
        interaction (discord.Interaction): The interaction that triggered the command
        bot (commands.Bot): The bot instance
        args (dict): Command arguments
            - channel (str, optional): Channel name or ID to send the info to
            - detailed (str, optional): If "true", shows more detailed information
    """
    if not interaction.guild:
        log.warning("Cannot display server info: Not in a guild context")
        return False
    
    # Get parameters
    channel_name_or_id = args.get('channel', '')
    detailed = args.get('detailed', 'false').lower() == 'true'
    
    # Find the channel to send the message to
    target_channel = None
    
    if channel_name_or_id:
        # Try to find by ID first
        try:
            channel_id = int(channel_name_or_id)
            target_channel = interaction.guild.get_channel(channel_id)
        except (ValueError, TypeError):
            # Not an ID, try to find by name
            target_channel = discord.utils.get(interaction.guild.text_channels, name=channel_name_or_id)
    
    # If no channel specified or not found, use the current channel
    if not target_channel:
        target_channel = interaction.channel
    
    # Check if we can send messages to the target channel
    if not target_channel.permissions_for(interaction.guild.me).send_messages:
        log.warning(f"Bot lacks permission to send messages in {target_channel.name}")
        return False
    
    # Get server information
    guild = interaction.guild
    
    # Basic information
    created_at = int(guild.created_at.timestamp())
    member_count = guild.member_count
    online_members = sum(1 for member in guild.members if member.status != discord.Status.offline) if hasattr(guild, 'members') else "Unknown"
    text_channels = len(guild.text_channels)
    voice_channels = len(guild.voice_channels)
    categories = len(guild.categories)
    roles = len(guild.roles) - 1  # Exclude @everyone
    
    # Create the embed
    embed = discord.Embed(
        title=f"{guild.name} Information",
        description=guild.description or "No description",
        color=discord.Color.blue()
    )
    
    # Add server icon if available
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    
    # Add basic fields
    embed.add_field(name="Owner", value=f"{guild.owner.mention if guild.owner else 'Unknown'}", inline=True)
    embed.add_field(name="Created", value=f"<t:{created_at}:R>", inline=True)
    embed.add_field(name="Server ID", value=guild.id, inline=True)
    
    embed.add_field(name="Members", value=member_count, inline=True)
    embed.add_field(name="Online", value=online_members, inline=True)
    embed.add_field(name="Boost Level", value=f"Level {guild.premium_tier}", inline=True)
    
    embed.add_field(name="Text Channels", value=text_channels, inline=True)
    embed.add_field(name="Voice Channels", value=voice_channels, inline=True)
    embed.add_field(name="Categories", value=categories, inline=True)
    
    embed.add_field(name="Roles", value=roles, inline=True)
    embed.add_field(name="Emojis", value=len(guild.emojis), inline=True)
    embed.add_field(name="Stickers", value=len(guild.stickers), inline=True)
    
    # Add detailed information if requested
    if detailed:
        # Verification level
        verification_levels = {
            discord.VerificationLevel.none: "None",
            discord.VerificationLevel.low: "Low",
            discord.VerificationLevel.medium: "Medium",
            discord.VerificationLevel.high: "High",
            discord.VerificationLevel.highest: "Highest"
        }
        embed.add_field(name="Verification Level", value=verification_levels.get(guild.verification_level, "Unknown"), inline=True)
        
        # Content filter
        content_filters = {
            discord.ContentFilter.disabled: "Disabled",
            discord.ContentFilter.no_role: "No Role",
            discord.ContentFilter.all_members: "All Members"
        }
        embed.add_field(name="Content Filter", value=content_filters.get(guild.explicit_content_filter, "Unknown"), inline=True)
        
        # Default notifications
        notification_settings = {
            discord.NotificationLevel.all_messages: "All Messages",
            discord.NotificationLevel.only_mentions: "Only Mentions"
        }
        embed.add_field(name="Default Notifications", value=notification_settings.get(guild.default_notifications, "Unknown"), inline=True)
        
        # Features
        if guild.features:
            features_str = ", ".join(feature.replace("_", " ").title() for feature in guild.features)
            embed.add_field(name="Features", value=features_str, inline=False)
        
        # Top roles (up to 10)
        top_roles = sorted(guild.roles, key=lambda r: r.position, reverse=True)[:10]
        if top_roles:
            roles_str = ", ".join(role.mention for role in top_roles if role.name != "@everyone")
            embed.add_field(name="Top Roles", value=roles_str or "None", inline=False)
    
    # Set footer
    embed.set_footer(text=f"Requested by {interaction.user.name}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
    embed.timestamp = datetime.now()
    
    # Send the embed
    try:
        await target_channel.send(embed=embed)
        log.info(f"Sent server info to #{target_channel.name} in {guild.name}")
        return True
    except discord.Forbidden:
        log.error(f"Forbidden: Bot lacks permission to send embeds to #{target_channel.name}")
        return False
    except discord.HTTPException as e:
        log.error(f"HTTP error sending server info: {e}")
        return False
    except Exception as e:
        log.error(f"Error sending server info: {e}", exc_info=True)
        return False
