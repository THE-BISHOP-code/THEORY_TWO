# commands/premium/ticket_system_command.py
import discord
import logging
import json
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Union

log = logging.getLogger('MyBot.Commands.TicketSystem')

# Store ticket system configuration
# Format: {guild_id: {config}}
TICKET_SYSTEMS = {}

async def execute(interaction, bot, args):
    """
    Creates or manages a ticket system.
    
    Args:
        interaction (discord.Interaction): The interaction that triggered the command
        bot (commands.Bot): The bot instance
        args (dict): Command arguments
            - action (str): The action to perform (setup, config, reset)
            - channel (str): Channel name or ID for the ticket panel
            - category (str): Category name or ID for ticket channels
            - support_role (str): Role name or ID for support staff
            - title (str, optional): Title for the ticket panel embed
            - description (str, optional): Description for the ticket panel embed
            - color (str, optional): Color for the embed in hex format (#RRGGBB)
            - button_text (str, optional): Text for the ticket button
            - welcome_message (str, optional): Message sent when a ticket is created
            - close_on_complete (str, optional): If "true", closes ticket when marked as complete
            - log_channel (str, optional): Channel name or ID for ticket logs
            - max_tickets (str, optional): Maximum number of open tickets per user
    """
    if not interaction.guild:
        log.warning("Cannot manage ticket system: Not in a guild context")
        return False
    
    # Check permissions
    required_permissions = [
        interaction.guild.me.guild_permissions.send_messages,
        interaction.guild.me.guild_permissions.embed_links,
        interaction.guild.me.guild_permissions.manage_channels,
        interaction.guild.me.guild_permissions.manage_roles
    ]
    
    if not all(required_permissions):
        log.warning(f"Bot lacks required permissions in {interaction.guild.name}")
        return False
    
    # Get parameters
    action = args.get('action', 'setup').lower()
    
    try:
        if action == 'setup':
            # Set up a new ticket system
            return await setup_ticket_system(bot, interaction, args)
        elif action == 'config':
            # Update ticket system configuration
            return await config_ticket_system(bot, interaction, args)
        elif action == 'reset':
            # Reset the ticket system
            return await reset_ticket_system(bot, interaction)
        else:
            log.error(f"Invalid action: {action}")
            return False
    except Exception as e:
        log.error(f"Error managing ticket system: {e}", exc_info=True)
        return False

async def setup_ticket_system(bot, interaction, args):
    """Sets up a new ticket system."""
    guild = interaction.guild
    
    # Get parameters
    channel_name_or_id = args.get('channel')
    category_name_or_id = args.get('category')
    support_role_name_or_id = args.get('support_role')
    title = args.get('title', 'Support Tickets')
    description = args.get('description', 'Click the button below to create a support ticket.')
    color_str = args.get('color', '#3498db')
    button_text = args.get('button_text', 'Create Ticket')
    welcome_message = args.get('welcome_message', 'Thank you for creating a ticket. Support staff will be with you shortly.')
    close_on_complete = args.get('close_on_complete', 'true').lower() == 'true'
    log_channel_name_or_id = args.get('log_channel', '')
    max_tickets_str = args.get('max_tickets', '1')
    
    # Validate required parameters
    if not channel_name_or_id:
        log.error("Cannot set up ticket system: No channel specified")
        return False
    
    if not category_name_or_id:
        log.error("Cannot set up ticket system: No category specified")
        return False
    
    if not support_role_name_or_id:
        log.error("Cannot set up ticket system: No support role specified")
        return False
    
    # Find the channel
    panel_channel = None
    try:
        channel_id = int(channel_name_or_id)
        panel_channel = guild.get_channel(channel_id)
    except (ValueError, TypeError):
        panel_channel = discord.utils.get(guild.text_channels, name=channel_name_or_id)
    
    if not panel_channel:
        log.error(f"Channel '{channel_name_or_id}' not found")
        return False
    
    # Find the category
    ticket_category = None
    try:
        category_id = int(category_name_or_id)
        ticket_category = guild.get_channel(category_id)
    except (ValueError, TypeError):
        ticket_category = discord.utils.get(guild.categories, name=category_name_or_id)
    
    if not ticket_category or not isinstance(ticket_category, discord.CategoryChannel):
        log.error(f"Category '{category_name_or_id}' not found")
        return False
    
    # Find the support role
    support_role = None
    try:
        role_id = int(support_role_name_or_id)
        support_role = guild.get_role(role_id)
    except (ValueError, TypeError):
        support_role = discord.utils.get(guild.roles, name=support_role_name_or_id)
    
    if not support_role:
        log.error(f"Role '{support_role_name_or_id}' not found")
        return False
    
    # Find the log channel if specified
    log_channel = None
    if log_channel_name_or_id:
        try:
            channel_id = int(log_channel_name_or_id)
            log_channel = guild.get_channel(channel_id)
        except (ValueError, TypeError):
            log_channel = discord.utils.get(guild.text_channels, name=log_channel_name_or_id)
    
    # Parse max tickets
    try:
        max_tickets = int(max_tickets_str)
        if max_tickets < 1:
            max_tickets = 1
    except ValueError:
        max_tickets = 1
    
    # Create the ticket system configuration
    ticket_config = {
        'panel_channel_id': panel_channel.id,
        'category_id': ticket_category.id,
        'support_role_id': support_role.id,
        'title': title,
        'description': description,
        'color': color_str,
        'button_text': button_text,
        'welcome_message': welcome_message,
        'close_on_complete': close_on_complete,
        'log_channel_id': log_channel.id if log_channel else None,
        'max_tickets': max_tickets,
        'active_tickets': {}  # {user_id: [channel_id, ...]}
    }
    
    # Store the configuration
    TICKET_SYSTEMS[guild.id] = ticket_config
    
    # Create the ticket panel embed
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
    
    # Set footer
    embed.set_footer(text=f"Click the button below to create a support ticket.")
    
    # Create the button
    view = discord.ui.View(timeout=None)
    button = discord.ui.Button(
        style=discord.ButtonStyle.primary,
        label=button_text,
        emoji="🎫",
        custom_id=f"ticket_create_{guild.id}"
    )
    
    # Add the button to the view
    view.add_item(button)
    
    # Send the panel message
    panel_message = await panel_channel.send(embed=embed, view=view)
    
    # Store the panel message ID
    ticket_config['panel_message_id'] = panel_message.id
    
    # Set up the button listener if not already set up
    if not hasattr(bot, '_ticket_button_listener_added'):
        bot.add_listener(on_interaction, 'on_interaction')
        bot._ticket_button_listener_added = True
        log.info("Added ticket system interaction listener")
    
    log.info(f"Set up ticket system in {guild.name}")
    
    return True

async def config_ticket_system(bot, interaction, args):
    """Updates the ticket system configuration."""
    guild = interaction.guild
    
    # Check if a ticket system exists for this guild
    if guild.id not in TICKET_SYSTEMS:
        log.error(f"No ticket system found for {guild.name}")
        return False
    
    # Get the current configuration
    ticket_config = TICKET_SYSTEMS[guild.id]
    
    # Update parameters if provided
    if 'title' in args:
        ticket_config['title'] = args['title']
    
    if 'description' in args:
        ticket_config['description'] = args['description']
    
    if 'color' in args:
        ticket_config['color'] = args['color']
    
    if 'button_text' in args:
        ticket_config['button_text'] = args['button_text']
    
    if 'welcome_message' in args:
        ticket_config['welcome_message'] = args['welcome_message']
    
    if 'close_on_complete' in args:
        ticket_config['close_on_complete'] = args['close_on_complete'].lower() == 'true'
    
    if 'max_tickets' in args:
        try:
            max_tickets = int(args['max_tickets'])
            if max_tickets < 1:
                max_tickets = 1
            ticket_config['max_tickets'] = max_tickets
        except ValueError:
            pass
    
    # Update support role if provided
    if 'support_role' in args:
        support_role_name_or_id = args['support_role']
        support_role = None
        
        try:
            role_id = int(support_role_name_or_id)
            support_role = guild.get_role(role_id)
        except (ValueError, TypeError):
            support_role = discord.utils.get(guild.roles, name=support_role_name_or_id)
        
        if support_role:
            ticket_config['support_role_id'] = support_role.id
    
    # Update log channel if provided
    if 'log_channel' in args:
        log_channel_name_or_id = args['log_channel']
        log_channel = None
        
        if log_channel_name_or_id:
            try:
                channel_id = int(log_channel_name_or_id)
                log_channel = guild.get_channel(channel_id)
            except (ValueError, TypeError):
                log_channel = discord.utils.get(guild.text_channels, name=log_channel_name_or_id)
            
            if log_channel:
                ticket_config['log_channel_id'] = log_channel.id
    
    # Update the panel message if it exists
    if 'panel_message_id' in ticket_config:
        try:
            panel_channel = guild.get_channel(ticket_config['panel_channel_id'])
            if panel_channel:
                panel_message = await panel_channel.fetch_message(ticket_config['panel_message_id'])
                
                # Update the embed
                embed = discord.Embed(
                    title=ticket_config['title'],
                    description=ticket_config['description'],
                    color=discord.Color.blue()
                )
                
                # Set color
                color_str = ticket_config['color']
                if color_str:
                    if color_str.startswith('#'):
                        color_str = color_str[1:]
                    try:
                        color_int = int(color_str, 16)
                        embed.color = discord.Color(color_int)
                    except ValueError:
                        pass
                
                # Set footer
                embed.set_footer(text=f"Click the button below to create a support ticket.")
                
                # Create the button
                view = discord.ui.View(timeout=None)
                button = discord.ui.Button(
                    style=discord.ButtonStyle.primary,
                    label=ticket_config['button_text'],
                    emoji="🎫",
                    custom_id=f"ticket_create_{guild.id}"
                )
                
                # Add the button to the view
                view.add_item(button)
                
                # Update the message
                await panel_message.edit(embed=embed, view=view)
        except (discord.NotFound, discord.Forbidden, discord.HTTPException) as e:
            log.warning(f"Could not update panel message: {e}")
    
    log.info(f"Updated ticket system configuration in {guild.name}")
    
    return True

async def reset_ticket_system(bot, interaction):
    """Resets the ticket system for a guild."""
    guild = interaction.guild
    
    # Check if a ticket system exists for this guild
    if guild.id not in TICKET_SYSTEMS:
        log.error(f"No ticket system found for {guild.name}")
        return False
    
    # Remove the ticket system configuration
    del TICKET_SYSTEMS[guild.id]
    
    log.info(f"Reset ticket system in {guild.name}")
    
    return True

async def on_interaction(interaction):
    """Handles button interactions for the ticket system."""
    if not interaction.guild or not interaction.data or 'custom_id' not in interaction.data:
        return
    
    custom_id = interaction.data['custom_id']
    
    # Handle ticket creation
    if custom_id.startswith('ticket_create_'):
        guild_id = int(custom_id.split('_')[-1])
        
        # Check if this is for our guild
        if interaction.guild.id != guild_id:
            return
        
        # Check if a ticket system exists for this guild
        if guild_id not in TICKET_SYSTEMS:
            return
        
        # Get the ticket system configuration
        ticket_config = TICKET_SYSTEMS[guild_id]
        
        # Check if the user has reached the maximum number of tickets
        user_id = interaction.user.id
        if user_id in ticket_config['active_tickets']:
            active_tickets = ticket_config['active_tickets'][user_id]
            if len(active_tickets) >= ticket_config['max_tickets']:
                await interaction.response.send_message(
                    f"You already have {len(active_tickets)} active ticket(s). Please close your existing ticket(s) before creating a new one.",
                    ephemeral=True
                )
                return
        
        # Create a new ticket
        await create_ticket(interaction, ticket_config)
    
    # Handle ticket actions
    elif custom_id.startswith('ticket_'):
        action = custom_id.split('_')[1]
        channel_id = interaction.channel.id
        
        # Find the guild configuration for this ticket
        guild_id = interaction.guild.id
        if guild_id not in TICKET_SYSTEMS:
            return
        
        ticket_config = TICKET_SYSTEMS[guild_id]
        
        # Check if this is a ticket channel
        is_ticket = False
        ticket_owner = None
        
        for user_id, channels in ticket_config['active_tickets'].items():
            if channel_id in channels:
                is_ticket = True
                ticket_owner = user_id
                break
        
        if not is_ticket:
            return
        
        # Handle the action
        if action == 'close':
            await close_ticket(interaction, ticket_config, ticket_owner)
        elif action == 'complete':
            await complete_ticket(interaction, ticket_config, ticket_owner)
        elif action == 'reopen':
            await reopen_ticket(interaction, ticket_config, ticket_owner)

async def create_ticket(interaction, ticket_config):
    """Creates a new support ticket."""
    guild = interaction.guild
    user = interaction.user
    
    # Get the category
    category = guild.get_channel(ticket_config['category_id'])
    if not category:
        await interaction.response.send_message("Error: Ticket category not found.", ephemeral=True)
        return
    
    # Get the support role
    support_role = guild.get_role(ticket_config['support_role_id'])
    if not support_role:
        await interaction.response.send_message("Error: Support role not found.", ephemeral=True)
        return
    
    # Create the ticket channel
    channel_name = f"ticket-{user.name.lower()}-{len(ticket_config['active_tickets'].get(user.id, []))}"
    
    # Set up permissions
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True, manage_permissions=True),
        user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        support_role: discord.PermissionOverwrite(read_messages=True, send_messages=True)
    }
    
    try:
        # Create the channel
        ticket_channel = await guild.create_text_channel(
            name=channel_name,
            category=category,
            overwrites=overwrites,
            topic=f"Support ticket for {user.name} ({user.id})"
        )
        
        # Add to active tickets
        if user.id not in ticket_config['active_tickets']:
            ticket_config['active_tickets'][user.id] = []
        
        ticket_config['active_tickets'][user.id].append(ticket_channel.id)
        
        # Send welcome message
        embed = discord.Embed(
            title=f"Support Ticket",
            description=ticket_config['welcome_message'],
            color=discord.Color.green()
        )
        
        embed.add_field(name="User", value=user.mention, inline=True)
        embed.add_field(name="Created", value=f"<t:{int(datetime.now().timestamp())}:R>", inline=True)
        
        # Create ticket control buttons
        view = discord.ui.View(timeout=None)
        
        close_button = discord.ui.Button(
            style=discord.ButtonStyle.danger,
            label="Close Ticket",
            emoji="🔒",
            custom_id=f"ticket_close"
        )
        
        complete_button = discord.ui.Button(
            style=discord.ButtonStyle.success,
            label="Mark as Complete",
            emoji="✅",
            custom_id=f"ticket_complete"
        )
        
        view.add_item(close_button)
        view.add_item(complete_button)
        
        # Send the welcome message with buttons
        await ticket_channel.send(f"{user.mention} {support_role.mention}", embed=embed, view=view)
        
        # Log the ticket creation
        if ticket_config['log_channel_id']:
            log_channel = guild.get_channel(ticket_config['log_channel_id'])
            if log_channel:
                log_embed = discord.Embed(
                    title="Ticket Created",
                    description=f"Ticket created by {user.mention}",
                    color=discord.Color.green()
                )
                
                log_embed.add_field(name="Channel", value=ticket_channel.mention, inline=True)
                log_embed.add_field(name="Created", value=f"<t:{int(datetime.now().timestamp())}:R>", inline=True)
                
                await log_channel.send(embed=log_embed)
        
        # Respond to the interaction
        await interaction.response.send_message(f"Your ticket has been created: {ticket_channel.mention}", ephemeral=True)
        
    except discord.Forbidden:
        await interaction.response.send_message("Error: I don't have permission to create a ticket channel.", ephemeral=True)
    except discord.HTTPException as e:
        await interaction.response.send_message(f"Error creating ticket: {e}", ephemeral=True)

async def close_ticket(interaction, ticket_config, ticket_owner):
    """Closes a support ticket."""
    guild = interaction.guild
    channel = interaction.channel
    
    # Update channel permissions to prevent the user from sending messages
    user = guild.get_member(ticket_owner)
    if user:
        await channel.set_permissions(user, read_messages=True, send_messages=False)
    
    # Send a message
    embed = discord.Embed(
        title="Ticket Closed",
        description="This ticket has been closed. The channel will be deleted in 24 hours unless reopened.",
        color=discord.Color.red()
    )
    
    # Create reopen button
    view = discord.ui.View(timeout=None)
    reopen_button = discord.ui.Button(
        style=discord.ButtonStyle.primary,
        label="Reopen Ticket",
        emoji="🔓",
        custom_id=f"ticket_reopen"
    )
    view.add_item(reopen_button)
    
    await interaction.response.send_message(embed=embed, view=view)
    
    # Log the ticket closure
    if ticket_config['log_channel_id']:
        log_channel = guild.get_channel(ticket_config['log_channel_id'])
        if log_channel:
            log_embed = discord.Embed(
                title="Ticket Closed",
                description=f"Ticket closed by {interaction.user.mention}",
                color=discord.Color.red()
            )
            
            log_embed.add_field(name="Channel", value=channel.mention, inline=True)
            log_embed.add_field(name="Closed", value=f"<t:{int(datetime.now().timestamp())}:R>", inline=True)
            
            await log_channel.send(embed=log_embed)

async def complete_ticket(interaction, ticket_config, ticket_owner):
    """Marks a ticket as complete."""
    guild = interaction.guild
    channel = interaction.channel
    
    # Send a message
    embed = discord.Embed(
        title="Ticket Completed",
        description="This ticket has been marked as complete.",
        color=discord.Color.green()
    )
    
    await interaction.response.send_message(embed=embed)
    
    # Log the ticket completion
    if ticket_config['log_channel_id']:
        log_channel = guild.get_channel(ticket_config['log_channel_id'])
        if log_channel:
            log_embed = discord.Embed(
                title="Ticket Completed",
                description=f"Ticket marked as complete by {interaction.user.mention}",
                color=discord.Color.green()
            )
            
            log_embed.add_field(name="Channel", value=channel.mention, inline=True)
            log_embed.add_field(name="Completed", value=f"<t:{int(datetime.now().timestamp())}:R>", inline=True)
            
            await log_channel.send(embed=log_embed)
    
    # Close the ticket if configured to do so
    if ticket_config['close_on_complete']:
        await close_ticket(interaction, ticket_config, ticket_owner)

async def reopen_ticket(interaction, ticket_config, ticket_owner):
    """Reopens a closed ticket."""
    guild = interaction.guild
    channel = interaction.channel
    
    # Update channel permissions to allow the user to send messages again
    user = guild.get_member(ticket_owner)
    if user:
        await channel.set_permissions(user, read_messages=True, send_messages=True)
    
    # Send a message
    embed = discord.Embed(
        title="Ticket Reopened",
        description="This ticket has been reopened.",
        color=discord.Color.green()
    )
    
    # Create ticket control buttons
    view = discord.ui.View(timeout=None)
    
    close_button = discord.ui.Button(
        style=discord.ButtonStyle.danger,
        label="Close Ticket",
        emoji="🔒",
        custom_id=f"ticket_close"
    )
    
    complete_button = discord.ui.Button(
        style=discord.ButtonStyle.success,
        label="Mark as Complete",
        emoji="✅",
        custom_id=f"ticket_complete"
    )
    
    view.add_item(close_button)
    view.add_item(complete_button)
    
    await interaction.response.send_message(embed=embed, view=view)
    
    # Log the ticket reopening
    if ticket_config['log_channel_id']:
        log_channel = guild.get_channel(ticket_config['log_channel_id'])
        if log_channel:
            log_embed = discord.Embed(
                title="Ticket Reopened",
                description=f"Ticket reopened by {interaction.user.mention}",
                color=discord.Color.green()
            )
            
            log_embed.add_field(name="Channel", value=channel.mention, inline=True)
            log_embed.add_field(name="Reopened", value=f"<t:{int(datetime.now().timestamp())}:R>", inline=True)
            
            await log_channel.send(embed=log_embed)

# Initialize the bot variable for event listeners
bot = None

def setup(bot_instance):
    """Sets up the bot instance for event listeners."""
    global bot
    bot = bot_instance
