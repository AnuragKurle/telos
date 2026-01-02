"""Configuration management for screen time tracker."""

import os
import yaml
from pathlib import Path
from typing import Dict, Any


class ConfigManager:
    """Manages loading and saving configuration."""

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

        self._validate_config()
        self._expand_paths()
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

        if self.config['gemini']['api_key'] == "YOUR_GEMINI_API_KEY_HERE":
            raise ValueError(
                "Please set your Gemini API key in config.yaml\n"
                "Get your API key from: https://aistudio.google.com/app/apikey"
            )

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


def load_config(config_path: str = "config.yaml") -> ConfigManager:
    """Load configuration from file."""
    manager = ConfigManager(config_path)
    manager.load()
    return manager
