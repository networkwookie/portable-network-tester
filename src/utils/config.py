"""
Configuration management utilities.
"""
from pathlib import Path
from typing import Any

import yaml
from loguru import logger


def get_config_path() -> Path:
    """Get the configuration file path."""
    # Check for config in multiple locations
    config_locations = [
        Path("config.yml"),
        Path("config.yaml"),
        Path.home() / ".config" / "network-tester" / "config.yml",
        Path("/etc/network-tester/config.yml"),
    ]

    for path in config_locations:
        if path.exists():
            return path

    # Return default location
    return Path("config.yml")


def load_config() -> dict[str, Any]:
    """
    Load configuration from YAML file.
    
    Returns:
        Configuration dictionary with defaults
    """
    default_config = {
        "logging": {
            "level": "INFO",
            "path": "logs/network_tester.log"
        },
        "network": {
            "interface": None,  # Auto-detect
            "test_hosts": {
                "dns": "google.com",
                "internet": "8.8.8.8"
            }
        },
        "ui": {
            "fullscreen": False,
            "width": 800,
            "height": 480
        }
    }

    config_path = get_config_path()

    if not config_path.exists():
        logger.info(f"Config file not found, using defaults: {config_path}")
        return default_config

    try:
        with open(config_path) as f:
            user_config = yaml.safe_load(f) or {}

        # Merge with defaults
        config = _deep_merge(default_config, user_config)
        logger.info(f"Loaded configuration from {config_path}")
        return config

    except Exception as e:
        logger.error(f"Error loading config from {config_path}: {e}")
        return default_config


def save_config(config: dict[str, Any]) -> bool:
    """
    Save configuration to YAML file.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        True if successful, False otherwise
    """
    config_path = get_config_path()

    try:
        # Create directory if needed
        config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)

        logger.info(f"Saved configuration to {config_path}")
        return True

    except Exception as e:
        logger.error(f"Error saving config to {config_path}: {e}")
        return False


def _deep_merge(base: dict, update: dict) -> dict:
    """
    Deep merge two dictionaries.
    
    Args:
        base: Base dictionary
        update: Dictionary with updates
        
    Returns:
        Merged dictionary
    """
    result = base.copy()

    for key, value in update.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value

    return result
