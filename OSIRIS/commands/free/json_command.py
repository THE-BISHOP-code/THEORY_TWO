# commands/free/json_command.py
import json
import logging
import importlib
from pathlib import Path
import sys

# Add parent directory to path for imports
BASE_DIR = Path(__file__).parent.parent.parent
sys.path.append(str(BASE_DIR))

# Define paths
FREE_COMMANDS_DIR = BASE_DIR / "commands" / "free"
PREMIUM_COMMANDS_DIR = BASE_DIR / "commands" / "premium"

# Logger
log = logging.getLogger('MyBot.ExecutorCog.JsonCommand')

async def execute(interaction, bot, args):
    """
    Executes a command specified in JSON format.
    
    Args:
        interaction: The Discord interaction
        bot: The Discord bot instance
        args: Dictionary containing the JSON string in the 'data' key
    """
    if 'data' not in args:
        log.error("No JSON data provided to json_command")
        return
    
    try:
        # Parse the JSON data
        json_data = json.loads(args['data'])
        
        # Extract the command name
        if 'command' not in json_data:
            log.error("No command specified in JSON data")
            return
            
        command_name = json_data['command']
        
        # Remove the '_command' suffix if present
        if command_name.endswith('_command'):
            command_name = command_name[:-8]
            
        log.info(f"JSON command handler executing: {command_name}")
        
        # Find the command module
        module = None
        for directory in [FREE_COMMANDS_DIR, PREMIUM_COMMANDS_DIR]:
            module_filename = f"{command_name}_command.py"
            module_path = directory / module_filename
            if module_path.is_file():
                module_name_import = f"commands.{'free' if directory == FREE_COMMANDS_DIR else 'premium'}.{command_name}_command"
                try:
                    # Use importlib to load the module dynamically
                    module = importlib.import_module(module_name_import)
                    # Reload module in case it was updated since bot start
                    module = importlib.reload(module)
                    break
                except Exception as e:
                    log.error(f"Error importing command module {module_name_import}: {e}")
                    return
        
        if not module:
            log.error(f"Command module not found for {command_name}")
            return
            
        # Convert JSON data to args format expected by the command
        command_args = {}
        for key, value in json_data.items():
            if key != 'command':
                command_args[key] = str(value)
                
        # Execute the command
        if hasattr(module, 'execute') and callable(module.execute):
            await module.execute(interaction=interaction, bot=bot, args=command_args)
            log.info(f"Successfully executed JSON command: {command_name}")
        else:
            log.error(f"Command module {command_name} does not have a valid execute function")
            
    except json.JSONDecodeError as e:
        log.error(f"Error parsing JSON data: {e}")
    except Exception as e:
        log.error(f"Error executing JSON command: {e}", exc_info=True)
