# commands/premium/reaction_roles_command.py
import discord
import logging
import json
import asyncio
from typing import Dict, List, Optional, Tuple, Union

log = logging.getLogger('MyBot.Commands.ReactionRoles')

# Store active reaction role messages
# Format: {message_id: {emoji: role_id}}
REACTION_ROLES = {}

async def execute(interaction, bot, args):
    """
    Creates or manages a reaction role message.
    
    Args:
        interaction (discord.Interaction): The interaction that triggered the command
        bot (commands.Bot): The bot instance
        args (dict): Command arguments
            - action (str): The action to perform (create, add, remove, clear)
            - channel (str): Channel name or ID for the message
            - message_id (str, optional): ID of an existing message to use
            - title (str, optional): Title for the embed
            - description (str, optional): Description for the embed
            - color (str, optional): Color for the embed in hex format (#RRGGBB)
            - roles (str): JSON string of roles to add (array of objects with emoji, role, description)
            - unique (str, optional): If "true", users can only have one role from this message
    """
    if not interaction.guild:
        log.warning("Cannot manage reaction roles: Not in a guild context")
        return False
    
    # Check permissions
    required_permissions = [
        interaction.guild.me.guild_permissions.send_messages,
        interaction.guild.me.guild_permissions.embed_links,
        interaction.guild.me.guild_permissions.add_reactions,
        interaction.guild.me.guild_permissions.manage_roles
    ]
    
    if not all(required_permissions):
        log.warning(f"Bot lacks required permissions in {interaction.guild.name}")
        return False
    
    # Get parameters
    action = args.get('action', 'create').lower()
    channel_name_or_id = args.get('channel')
    message_id_str = args.get('message_id', '')
    title = args.get('title', 'Reaction Roles')
    description = args.get('description', 'React to get roles!')
    color_str = args.get('color', '#3498db')
    roles_json = args.get('roles', '[]')
    unique = args.get('unique', 'false').lower() == 'true'
    
    if not channel_name_or_id:
        log.error("Cannot manage reaction roles: No channel specified")
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
        log.error(f"Cannot manage reaction roles: Channel '{channel_name_or_id}' not found")
        return False
    
    # Parse the roles JSON
    try:
        roles_data = json.loads(roles_json)
        if not isinstance(roles_data, list):
            log.error("Invalid roles format: must be a JSON array")
            return False
    except json.JSONDecodeError:
        log.error(f"Invalid JSON for roles: {roles_json}")
        return False
    
    # Process based on action
    try:
        if action == 'create':
            # Create a new reaction roles message
            return await create_reaction_roles(bot, interaction, target_channel, title, description, color_str, roles_data, unique)
        elif action == 'add':
            # Add roles to an existing message
            if not message_id_str:
                log.error("Cannot add reaction roles: No message ID specified")
                return False
            
            try:
                message_id = int(message_id_str)
                return await add_reaction_roles(bot, interaction, target_channel, message_id, roles_data)
            except ValueError:
                log.error(f"Invalid message ID: {message_id_str}")
                return False
        elif action == 'remove':
            # Remove roles from an existing message
            if not message_id_str:
                log.error("Cannot remove reaction roles: No message ID specified")
                return False
            
            try:
                message_id = int(message_id_str)
                return await remove_reaction_roles(bot, interaction, target_channel, message_id, roles_data)
            except ValueError:
                log.error(f"Invalid message ID: {message_id_str}")
                return False
        elif action == 'clear':
            # Clear all reaction roles from an existing message
            if not message_id_str:
                log.error("Cannot clear reaction roles: No message ID specified")
                return False
            
            try:
                message_id = int(message_id_str)
                return await clear_reaction_roles(bot, interaction, target_channel, message_id)
            except ValueError:
                log.error(f"Invalid message ID: {message_id_str}")
                return False
        else:
            log.error(f"Invalid action: {action}")
            return False
    except Exception as e:
        log.error(f"Error managing reaction roles: {e}", exc_info=True)
        return False

async def create_reaction_roles(bot, interaction, channel, title, description, color_str, roles_data, unique):
    """Creates a new reaction roles message."""
    # Validate roles data
    role_mappings = {}
    role_descriptions = []
    
    for role_item in roles_data:
        if not isinstance(role_item, dict):
            continue
        
        emoji_str = role_item.get('emoji')
        role_name_or_id = role_item.get('role')
        role_description = role_item.get('description', '')
        
        if not emoji_str or not role_name_or_id:
            continue
        
        # Find the role
        role = None
        try:
            role_id = int(role_name_or_id)
            role = interaction.guild.get_role(role_id)
        except (ValueError, TypeError):
            # Not an ID, try to find by name
            role = discord.utils.get(interaction.guild.roles, name=role_name_or_id)
        
        if not role:
            log.warning(f"Role '{role_name_or_id}' not found")
            continue
        
        # Check if the bot can assign this role
        if role.position >= interaction.guild.me.top_role.position:
            log.warning(f"Bot cannot assign role '{role.name}' due to hierarchy")
            continue
        
        # Add to mappings
        role_mappings[emoji_str] = role.id
        
        # Add to descriptions
        if role_description:
            role_descriptions.append(f"{emoji_str} **{role.name}** - {role_description}")
        else:
            role_descriptions.append(f"{emoji_str} **{role.name}**")
    
    if not role_mappings:
        log.error("No valid roles provided")
        return False
    
    # Create the embed
    embed = discord.Embed(
        title=title,
        description=description,
        color=discord.Color.blue()
    )
    
    # Set color if provided
    if color_str:
        if color_str.startswith('#'):
            color_str = color_str[1:]
        try:
            color_int = int(color_str, 16)
            embed.color = discord.Color(color_int)
        except ValueError:
            log.warning(f"Invalid color format: {color_str}. Using default color.")
    
    # Add role descriptions to the embed
    if role_descriptions:
        embed.add_field(name="Available Roles", value="\n".join(role_descriptions), inline=False)
    
    # Add note about unique roles if applicable
    if unique:
        embed.add_field(name="Note", value="You can only have one role from this message at a time.", inline=False)
    
    # Set footer
    embed.set_footer(text=f"React with the emoji to get the role. Remove your reaction to remove the role.")
    
    # Send the message
    message = await channel.send(embed=embed)
    
    # Add reactions
    for emoji_str in role_mappings.keys():
        try:
            await message.add_reaction(emoji_str)
        except discord.HTTPException:
            log.warning(f"Could not add reaction {emoji_str}")
    
    # Store the reaction roles data
    REACTION_ROLES[message.id] = {
        'roles': role_mappings,
        'unique': unique,
        'guild_id': interaction.guild.id,
        'channel_id': channel.id
    }
    
    # Save to database or file (placeholder)
    # In a real implementation, you would save this to a database
    log.info(f"Created reaction roles message {message.id} in {channel.name}")
    
    # Set up the event listener if not already set up
    if not hasattr(bot, '_reaction_roles_listener_added'):
        bot.add_listener(on_raw_reaction_add, 'on_raw_reaction_add')
        bot.add_listener(on_raw_reaction_remove, 'on_raw_reaction_remove')
        bot._reaction_roles_listener_added = True
        log.info("Added reaction role event listeners")
    
    return True

async def add_reaction_roles(bot, interaction, channel, message_id, roles_data):
    """Adds roles to an existing reaction roles message."""
    try:
        # Get the message
        message = await channel.fetch_message(message_id)
    except (discord.NotFound, discord.Forbidden, discord.HTTPException):
        log.error(f"Could not find message {message_id} in {channel.name}")
        return False
    
    # Check if this is a reaction roles message
    if message_id not in REACTION_ROLES:
        log.error(f"Message {message_id} is not a reaction roles message")
        return False
    
    # Get the current roles
    current_roles = REACTION_ROLES[message_id]['roles']
    unique = REACTION_ROLES[message_id]['unique']
    
    # Process new roles
    added_roles = {}
    for role_item in roles_data:
        if not isinstance(role_item, dict):
            continue
        
        emoji_str = role_item.get('emoji')
        role_name_or_id = role_item.get('role')
        
        if not emoji_str or not role_name_or_id:
            continue
        
        # Skip if this emoji is already used
        if emoji_str in current_roles:
            log.warning(f"Emoji {emoji_str} is already used in this message")
            continue
        
        # Find the role
        role = None
        try:
            role_id = int(role_name_or_id)
            role = interaction.guild.get_role(role_id)
        except (ValueError, TypeError):
            # Not an ID, try to find by name
            role = discord.utils.get(interaction.guild.roles, name=role_name_or_id)
        
        if not role:
            log.warning(f"Role '{role_name_or_id}' not found")
            continue
        
        # Check if the bot can assign this role
        if role.position >= interaction.guild.me.top_role.position:
            log.warning(f"Bot cannot assign role '{role.name}' due to hierarchy")
            continue
        
        # Add to mappings
        added_roles[emoji_str] = role.id
    
    if not added_roles:
        log.error("No valid roles to add")
        return False
    
    # Update the embed
    embed = message.embeds[0] if message.embeds else discord.Embed(title="Reaction Roles")
    
    # Update the Available Roles field
    role_descriptions = []
    for emoji_str, role_id in {**current_roles, **added_roles}.items():
        role = interaction.guild.get_role(role_id)
        if role:
            role_descriptions.append(f"{emoji_str} **{role.name}**")
    
    # Find the Available Roles field or add a new one
    field_index = None
    for i, field in enumerate(embed.fields):
        if field.name == "Available Roles":
            field_index = i
            break
    
    if field_index is not None:
        embed.set_field_at(field_index, name="Available Roles", value="\n".join(role_descriptions), inline=False)
    else:
        embed.add_field(name="Available Roles", value="\n".join(role_descriptions), inline=False)
    
    # Update the message
    await message.edit(embed=embed)
    
    # Add reactions for new roles
    for emoji_str in added_roles.keys():
        try:
            await message.add_reaction(emoji_str)
        except discord.HTTPException:
            log.warning(f"Could not add reaction {emoji_str}")
    
    # Update the stored data
    REACTION_ROLES[message_id]['roles'].update(added_roles)
    
    # Save to database or file (placeholder)
    log.info(f"Added {len(added_roles)} roles to reaction roles message {message_id}")
    
    return True

async def remove_reaction_roles(bot, interaction, channel, message_id, roles_data):
    """Removes roles from an existing reaction roles message."""
    try:
        # Get the message
        message = await channel.fetch_message(message_id)
    except (discord.NotFound, discord.Forbidden, discord.HTTPException):
        log.error(f"Could not find message {message_id} in {channel.name}")
        return False
    
    # Check if this is a reaction roles message
    if message_id not in REACTION_ROLES:
        log.error(f"Message {message_id} is not a reaction roles message")
        return False
    
    # Get the current roles
    current_roles = REACTION_ROLES[message_id]['roles']
    
    # Process roles to remove
    removed_emojis = []
    for role_item in roles_data:
        if not isinstance(role_item, dict):
            continue
        
        emoji_str = role_item.get('emoji')
        
        if not emoji_str:
            continue
        
        # Skip if this emoji is not used
        if emoji_str not in current_roles:
            log.warning(f"Emoji {emoji_str} is not used in this message")
            continue
        
        # Add to list of emojis to remove
        removed_emojis.append(emoji_str)
    
    if not removed_emojis:
        log.error("No valid roles to remove")
        return False
    
    # Update the embed
    embed = message.embeds[0] if message.embeds else discord.Embed(title="Reaction Roles")
    
    # Remove the specified roles
    for emoji_str in removed_emojis:
        if emoji_str in current_roles:
            del current_roles[emoji_str]
    
    # Update the Available Roles field
    role_descriptions = []
    for emoji_str, role_id in current_roles.items():
        role = interaction.guild.get_role(role_id)
        if role:
            role_descriptions.append(f"{emoji_str} **{role.name}**")
    
    # Find the Available Roles field
    field_index = None
    for i, field in enumerate(embed.fields):
        if field.name == "Available Roles":
            field_index = i
            break
    
    if field_index is not None:
        if role_descriptions:
            embed.set_field_at(field_index, name="Available Roles", value="\n".join(role_descriptions), inline=False)
        else:
            # Remove the field if no roles left
            embed.remove_field(field_index)
    
    # Update the message
    await message.edit(embed=embed)
    
    # Remove reactions
    for emoji_str in removed_emojis:
        try:
            await message.clear_reaction(emoji_str)
        except discord.HTTPException:
            log.warning(f"Could not remove reaction {emoji_str}")
    
    # Update the stored data
    REACTION_ROLES[message_id]['roles'] = current_roles
    
    # If no roles left, consider removing the message from tracking
    if not current_roles:
        del REACTION_ROLES[message_id]
        log.info(f"Removed all roles from reaction roles message {message_id}")
    else:
        log.info(f"Removed {len(removed_emojis)} roles from reaction roles message {message_id}")
    
    return True

async def clear_reaction_roles(bot, interaction, channel, message_id):
    """Clears all reaction roles from an existing message."""
    try:
        # Get the message
        message = await channel.fetch_message(message_id)
    except (discord.NotFound, discord.Forbidden, discord.HTTPException):
        log.error(f"Could not find message {message_id} in {channel.name}")
        return False
    
    # Check if this is a reaction roles message
    if message_id not in REACTION_ROLES:
        log.error(f"Message {message_id} is not a reaction roles message")
        return False
    
    # Update the embed
    embed = message.embeds[0] if message.embeds else discord.Embed(title="Reaction Roles")
    
    # Find and remove the Available Roles field
    field_index = None
    for i, field in enumerate(embed.fields):
        if field.name == "Available Roles":
            field_index = i
            break
    
    if field_index is not None:
        embed.remove_field(field_index)
    
    # Find and remove the Note field if it exists
    field_index = None
    for i, field in enumerate(embed.fields):
        if field.name == "Note":
            field_index = i
            break
    
    if field_index is not None:
        embed.remove_field(field_index)
    
    # Update the message
    await message.edit(embed=embed)
    
    # Clear all reactions
    await message.clear_reactions()
    
    # Remove from tracking
    del REACTION_ROLES[message_id]
    
    log.info(f"Cleared all reaction roles from message {message_id}")
    
    return True

# Event listeners for reaction roles
async def on_raw_reaction_add(payload):
    """Handles adding roles when a reaction is added."""
    # Check if this is a reaction role message
    if payload.message_id not in REACTION_ROLES:
        return
    
    # Get the reaction role data
    reaction_data = REACTION_ROLES[payload.message_id]
    
    # Check if this is the right guild
    if payload.guild_id != reaction_data['guild_id']:
        return
    
    # Check if this emoji is used for a role
    emoji = str(payload.emoji)
    if emoji not in reaction_data['roles']:
        return
    
    # Get the guild and member
    guild = discord.utils.find(lambda g: g.id == payload.guild_id, bot.guilds)
    if not guild:
        return
    
    member = guild.get_member(payload.user_id)
    if not member or member.bot:
        return
    
    # Get the role
    role_id = reaction_data['roles'][emoji]
    role = guild.get_role(role_id)
    if not role:
        return
    
    try:
        # If unique, remove other roles from this message
        if reaction_data['unique']:
            for other_emoji, other_role_id in reaction_data['roles'].items():
                if other_emoji != emoji:
                    other_role = guild.get_role(other_role_id)
                    if other_role and other_role in member.roles:
                        await member.remove_roles(other_role)
                        
                        # Remove the reaction
                        channel = guild.get_channel(payload.channel_id)
                        if channel:
                            message = await channel.fetch_message(payload.message_id)
                            if message:
                                try:
                                    # Find the user's reaction with this emoji
                                    for reaction in message.reactions:
                                        if str(reaction.emoji) == other_emoji:
                                            await reaction.remove(member)
                                            break
                                except discord.HTTPException:
                                    pass
        
        # Add the role
        await member.add_roles(role)
        log.info(f"Added role {role.name} to {member.name} via reaction roles")
    except discord.Forbidden:
        log.error(f"Forbidden: Bot lacks permission to manage roles")
    except discord.HTTPException as e:
        log.error(f"HTTP error managing roles: {e}")

async def on_raw_reaction_remove(payload):
    """Handles removing roles when a reaction is removed."""
    # Check if this is a reaction role message
    if payload.message_id not in REACTION_ROLES:
        return
    
    # Get the reaction role data
    reaction_data = REACTION_ROLES[payload.message_id]
    
    # Check if this is the right guild
    if payload.guild_id != reaction_data['guild_id']:
        return
    
    # Check if this emoji is used for a role
    emoji = str(payload.emoji)
    if emoji not in reaction_data['roles']:
        return
    
    # Get the guild and member
    guild = discord.utils.find(lambda g: g.id == payload.guild_id, bot.guilds)
    if not guild:
        return
    
    member = guild.get_member(payload.user_id)
    if not member or member.bot:
        return
    
    # Get the role
    role_id = reaction_data['roles'][emoji]
    role = guild.get_role(role_id)
    if not role:
        return
    
    try:
        # Remove the role
        await member.remove_roles(role)
        log.info(f"Removed role {role.name} from {member.name} via reaction roles")
    except discord.Forbidden:
        log.error(f"Forbidden: Bot lacks permission to manage roles")
    except discord.HTTPException as e:
        log.error(f"HTTP error managing roles: {e}")

# Initialize the bot variable for event listeners
bot = None

def setup(bot_instance):
    """Sets up the bot instance for event listeners."""
    global bot
    bot = bot_instance
