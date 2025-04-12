# utils/config_manager.py

import json
import os
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import copy

log = logging.getLogger('MyBot.ConfigManager')

class ConfigManager:
    """
    A class to manage the bot's configuration.
    Provides methods to load, save, and access configuration values.
    """
    
    def __init__(self, config_path: str = "config.json"):
        """
        Initialize the ConfigManager.
        
        Args:
            config_path (str): Path to the config file
        """
        self.config_path = Path(config_path)
        self.config = {}
        self.default_config = {}
        self._load_config()
    
    def _load_config(self) -> None:
        """Load the configuration from the config file."""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                log.info(f"Configuration loaded from {self.config_path}")
            else:
                log.warning(f"Config file {self.config_path} not found. Using default configuration.")
                self.config = {}
        except Exception as e:
            log.error(f"Error loading configuration: {e}")
            self.config = {}
    
    def save_config(self) -> bool:
        """
        Save the current configuration to the config file.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2)
            log.info(f"Configuration saved to {self.config_path}")
            return True
        except Exception as e:
            log.error(f"Error saving configuration: {e}")
            return False
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get a configuration value using a dot-notation path.
        
        Args:
            key_path (str): Dot-notation path to the configuration value (e.g., 'bot.prefix')
            default (Any, optional): Default value to return if the key doesn't exist
            
        Returns:
            Any: The configuration value or the default value
        """
        keys = key_path.split('.')
        value = self.config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key_path: str, value: Any) -> bool:
        """
        Set a configuration value using a dot-notation path.
        
        Args:
            key_path (str): Dot-notation path to the configuration value (e.g., 'bot.prefix')
            value (Any): The value to set
            
        Returns:
            bool: True if successful, False otherwise
        """
        keys = key_path.split('.')
        config_ref = self.config
        
        try:
            # Navigate to the parent of the target key
            for key in keys[:-1]:
                if key not in config_ref:
                    config_ref[key] = {}
                config_ref = config_ref[key]
            
            # Set the value
            config_ref[keys[-1]] = value
            return True
        except Exception as e:
            log.error(f"Error setting configuration value: {e}")
            return False
    
    def get_color(self, color_type: str = "embed_color") -> int:
        """
        Get a color value from the configuration as an integer.
        
        Args:
            color_type (str): The type of color to get (e.g., 'embed_color', 'error_color')
            
        Returns:
            int: The color value as an integer
        """
        color_hex = self.get(f"bot.{color_type}", "#3498db")
        
        # Remove the '#' if present
        if color_hex.startswith('#'):
            color_hex = color_hex[1:]
        
        # Convert hex to int
        try:
            return int(color_hex, 16)
        except ValueError:
            log.warning(f"Invalid color value: {color_hex}. Using default.")
            return int("3498db", 16)  # Default to blue
    
    def get_tier_limits(self, tier_name: str) -> Dict[str, Any]:
        """
        Get the limits for a specific tier.
        
        Args:
            tier_name (str): The name of the tier
            
        Returns:
            Dict[str, Any]: The tier limits
        """
        tier_config = self.get(f"tiers.{tier_name}", {})
        
        # Default values if tier not found
        defaults = {
            "replies": 3,
            "saves": 5,
            "cooldown": 600,
            "cooldown_uses": 3,
            "cooldown_window": 300,
            "color": "#607d8b",
            "icon": "🌑",
            "description": "Basic access"
        }
        
        # Merge defaults with config
        for key, value in defaults.items():
            if key not in tier_config:
                tier_config[key] = value
        
        return tier_config
    
    def get_all_tiers(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all tier configurations.
        
        Returns:
            Dict[str, Dict[str, Any]]: All tier configurations
        """
        return self.get("tiers", {
            "Drifter": self.get_tier_limits("Drifter"),
            "Seeker": self.get_tier_limits("Seeker"),
            "Abysswalker": self.get_tier_limits("Abysswalker")
        })
    
    def is_feature_enabled(self, feature_name: str) -> bool:
        """
        Check if a feature is enabled.
        
        Args:
            feature_name (str): The name of the feature
            
        Returns:
            bool: True if the feature is enabled, False otherwise
        """
        return self.get(f"features.{feature_name}_enabled", True)
    
    def is_owner(self, user_id: int) -> bool:
        """
        Check if a user is an owner.
        
        Args:
            user_id (int): The user ID to check
            
        Returns:
            bool: True if the user is an owner, False otherwise
        """
        owner_ids = self.get("permissions.owner_ids", [])
        return user_id in owner_ids
    
    def add_owner(self, user_id: int) -> bool:
        """
        Add a user to the owner list.
        
        Args:
            user_id (int): The user ID to add
            
        Returns:
            bool: True if successful, False otherwise
        """
        owner_ids = self.get("permissions.owner_ids", [])
        
        if user_id not in owner_ids:
            owner_ids.append(user_id)
            self.set("permissions.owner_ids", owner_ids)
            return self.save_config()
        
        return True  # Already an owner
    
    def remove_owner(self, user_id: int) -> bool:
        """
        Remove a user from the owner list.
        
        Args:
            user_id (int): The user ID to remove
            
        Returns:
            bool: True if successful, False otherwise
        """
        owner_ids = self.get("permissions.owner_ids", [])
        
        if user_id in owner_ids:
            owner_ids.remove(user_id)
            self.set("permissions.owner_ids", owner_ids)
            return self.save_config()
        
        return True  # Not an owner
    
    def get_admin_role_names(self) -> List[str]:
        """
        Get the names of admin roles.
        
        Returns:
            List[str]: The names of admin roles
        """
        return self.get("permissions.admin_role_names", ["Admin", "Administrator", "Moderator"])
    
    def get_premium_role_names(self) -> List[str]:
        """
        Get the names of premium roles.
        
        Returns:
            List[str]: The names of premium roles
        """
        return self.get("permissions.premium_role_names", ["Premium", "Seeker", "Supporter"])
    
    def get_vip_role_names(self) -> List[str]:
        """
        Get the names of VIP roles.
        
        Returns:
            List[str]: The names of VIP roles
        """
        return self.get("permissions.vip_role_names", ["VIP", "Abysswalker", "Patron"])
    
    def get_logging_config(self) -> Dict[str, Any]:
        """
        Get the logging configuration.
        
        Returns:
            Dict[str, Any]: The logging configuration
        """
        return self.get("logging", {
            "enabled": True,
            "level": "INFO",
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            "file_logging": True,
            "console_logging": True,
            "log_commands": True,
            "log_errors": True,
            "log_dm_messages": False,
            "max_log_files": 10,
            "max_log_size_mb": 10
        })
    
    def get_database_config(self) -> Dict[str, Any]:
        """
        Get the database configuration.
        
        Returns:
            Dict[str, Any]: The database configuration
        """
        return self.get("database", {
            "type": "sqlite",
            "path": "market.db",
            "backup_enabled": True,
            "backup_interval_hours": 24,
            "max_backups": 7
        })
    
    def get_maintenance_config(self) -> Dict[str, Any]:
        """
        Get the maintenance configuration.
        
        Returns:
            Dict[str, Any]: The maintenance configuration
        """
        return self.get("maintenance", {
            "grace_period_minutes": 15,
            "notify_users": True,
            "maintenance_channel_id": "",
            "status_update_interval_seconds": 60,
            "auto_disable_after_hours": 24
        })
    
    def get_ui_config(self) -> Dict[str, Any]:
        """
        Get the UI configuration.
        
        Returns:
            Dict[str, Any]: The UI configuration
        """
        return self.get("ui", {
            "use_embeds": True,
            "use_buttons": True,
            "use_select_menus": True,
            "use_modals": True,
            "button_style": "primary",
            "default_timeout": 180,
            "show_timestamps": True,
            "show_user_avatars": True,
            "compact_mode": False,
            "show_typing_indicator": True,
            "show_help_buttons": True,
            "show_tier_indicators": True,
            "animated_responses": True,
            "theme": "dark"
        })
    
    def get_emoji(self, emoji_name: str) -> str:
        """
        Get a custom emoji by name.
        
        Args:
            emoji_name (str): The name of the emoji
            
        Returns:
            str: The emoji character or code
        """
        default_emojis = {
            "loading": "⚙️",
            "success": "✅",
            "error": "❌",
            "warning": "⚠️",
            "info": "ℹ️",
            "premium": "⭐",
            "vip": "🌟",
            "save": "💾",
            "edit": "✏️",
            "delete": "🗑️",
            "share": "📤",
            "download": "📥",
            "award": "🏆",
            "comment": "💬",
            "execute": "▶️",
            "undo": "↩️",
            "help": "❓"
        }
        
        custom_emojis = self.get("ui.custom_emojis", {})
        return custom_emojis.get(emoji_name, default_emojis.get(emoji_name, ""))
    
    def reload_config(self) -> bool:
        """
        Reload the configuration from the config file.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self._load_config()
            return True
        except Exception as e:
            log.error(f"Error reloading configuration: {e}")
            return False
    
    def create_backup(self) -> bool:
        """
        Create a backup of the current configuration.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            backup_path = self.config_path.with_suffix(f".backup.json")
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2)
            log.info(f"Configuration backup created at {backup_path}")
            return True
        except Exception as e:
            log.error(f"Error creating configuration backup: {e}")
            return False
    
    def restore_backup(self) -> bool:
        """
        Restore the configuration from a backup.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            backup_path = self.config_path.with_suffix(f".backup.json")
            if backup_path.exists():
                with open(backup_path, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                self.save_config()
                log.info(f"Configuration restored from {backup_path}")
                return True
            else:
                log.warning(f"Backup file {backup_path} not found.")
                return False
        except Exception as e:
            log.error(f"Error restoring configuration backup: {e}")
            return False
    
    def reset_to_defaults(self) -> bool:
        """
        Reset the configuration to default values.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Load default config from a template or hardcoded values
            default_config_path = Path("default_config.json")
            if default_config_path.exists():
                with open(default_config_path, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
            else:
                # Use hardcoded minimal default config
                self.config = {
                    "bot": {
                        "prefix": "!",
                        "status_type": "listening",
                        "status_text": "/spectre",
                        "embed_color": "#3498db"
                    },
                    "tiers": {
                        "Drifter": {
                            "replies": 3,
                            "saves": 5,
                            "cooldown": 600
                        },
                        "Seeker": {
                            "replies": 5,
                            "saves": 12,
                            "cooldown": 120
                        },
                        "Abysswalker": {
                            "replies": 7,
                            "saves": 30,
                            "cooldown": 0
                        }
                    },
                    "features": {
                        "spectre_enabled": True,
                        "vault_enabled": True,
                        "exchange_enabled": True,
                        "executor_enabled": True
                    }
                }
            
            self.save_config()
            log.info("Configuration reset to defaults")
            return True
        except Exception as e:
            log.error(f"Error resetting configuration: {e}")
            return False

# Create a global instance for easy access
config = ConfigManager()
