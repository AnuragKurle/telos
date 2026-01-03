"""Configuration management for screen time tracker."""

import os
import yaml
from pathlib import Path
from typing import Dict, Any


class ConfigManager:
    """Manages loading and saving configuration."""
    
    # Config schema version
    CURRENT_VERSION = 2  # Version 2 adds backend, trial, account sections

    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = Path(config_path)
        self.config: Dict[str, Any] = {}

    def load(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            raise FileNotFoundError(
                f"Configuration file not found: {self.config_path}\n"
                f"Please copy config.yaml.example to config.yaml and add your Gemini API key."
            )

        with open(self.config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        self._migrate_config()
        self._validate_config()
        self._expand_paths()
        self._set_defaults()
        return self.config

    def save(self, config: Dict[str, Any]) -> None:
        """Save configuration to YAML file."""
        with open(self.config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        self.config = config

    def _validate_config(self) -> None:
        """Validate required configuration fields."""
        required_fields = [
            ('gemini', 'api_key'),
            ('gemini', 'model'),
            ('capture', 'interval_seconds'),
            ('storage', 'database_path'),
        ]

        for *path, field in required_fields:
            config_section = self.config
            for key in path:
                if key not in config_section:
                    raise ValueError(f"Missing required config section: {key}")
                config_section = config_section[key]

            if field not in config_section:
                raise ValueError(f"Missing required config field: {'.'.join(path + [field])}")

        # Only validate API key if backend is disabled (local mode)
        backend_enabled = self.config.get('backend', {}).get('enabled', False)
        api_key = self.config['gemini']['api_key']
        
        if not backend_enabled:
            # Local mode - API key is required
            if api_key in ("YOUR_GEMINI_API_KEY_HERE", "BACKEND_MODE_NO_KEY_NEEDED", ""):
                raise ValueError(
                    "Local mode requires a Gemini API key.\n"
                    "Run 'telos setup' to configure, or enable backend mode.\n"
                    "Get API key from: https://aistudio.google.com/app/apikey"
                )

    def _migrate_config(self) -> None:
        """Migrate configuration from older versions to current schema."""
        current_version = self.config.get('schema_version', 1)
        
        if current_version >= self.CURRENT_VERSION:
            return  # Already at current version
        
        # Migration from v1 to v2: Add backend, trial, account sections
        if current_version == 1:
            print("Migrating configuration to version 2...")
            
            # Add backend section if missing
            if 'backend' not in self.config:
                self.config['backend'] = {
                    'enabled': False,
                    'url': "",
                    'fallback_to_local': True,
                }
            
            # Add trial section if missing
            if 'trial' not in self.config:
                self.config['trial'] = {
                    'start_date': "",
                    'duration_days': 7,
                    'upgrade_prompts_shown': 0,
                }
            
            # Add account section if missing
            if 'account' not in self.config:
                self.config['account'] = {
                    'auth_type': "anonymous",
                    'user_id': "",
                    'email': "",
                }
            
            # Update version
            self.config['schema_version'] = 2
            
            # Save migrated config
            self.save(self.config)
            print("Configuration migrated successfully.")
    
    def _set_defaults(self) -> None:
        """Set default values for optional fields."""
        # Ensure backend section has all fields
        backend = self.config.get('backend', {})
        backend.setdefault('enabled', False)
        backend.setdefault('url', "")
        backend.setdefault('fallback_to_local', True)
        self.config['backend'] = backend
        
        # Ensure trial section has all fields
        trial = self.config.get('trial', {})
        trial.setdefault('start_date', "")
        trial.setdefault('duration_days', 7)
        trial.setdefault('upgrade_prompts_shown', 0)
        self.config['trial'] = trial
        
        # Ensure account section has all fields
        account = self.config.get('account', {})
        account.setdefault('auth_type', "anonymous")
        account.setdefault('user_id', "")
        account.setdefault('email', "")
        self.config['account'] = account

    def _expand_paths(self) -> None:
        """Expand ~ and environment variables in paths."""
        db_path = self.config['storage']['database_path']
        expanded = os.path.expanduser(os.path.expandvars(db_path))
        self.config['storage']['database_path'] = expanded

        db_dir = Path(expanded).parent
        db_dir.mkdir(parents=True, exist_ok=True)

    def get(self, *keys: str, default: Any = None) -> Any:
        """Get nested configuration value.

        Example:
            config.get('gemini', 'api_key')
            config.get('capture', 'interval_seconds', default=30)
        """
        value = self.config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value


def find_config_path() -> Path:
    """Find config.yaml in standard locations.
    
    Search order:
    1. Current working directory (for development)
    2. User data directory (~/.telos/)
    """
    # Check current directory first (development mode)
    cwd_config = Path("config.yaml")
    if cwd_config.exists():
        return cwd_config
    
    # Check user data directory (pip install mode)
    user_config = Path.home() / ".telos" / "config.yaml"
    if user_config.exists():
        return user_config
    
    # Default to user config path (will show helpful error)
    return user_config


def load_config(config_path: str = None) -> ConfigManager:
    """Load configuration from file.
    
    Args:
        config_path: Optional explicit path. If None, searches standard locations.
    """
    if config_path is None:
        config_path = str(find_config_path())
    
    manager = ConfigManager(config_path)
    manager.load()
    return manager
