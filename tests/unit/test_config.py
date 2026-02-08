"""
Unit tests for configuration utilities.
"""

from pathlib import Path
from unittest.mock import mock_open, patch

import pytest
from utils.config import _deep_merge, load_config, save_config


@pytest.mark.unit
class TestConfigUtils:
    """Test suite for configuration utilities."""

    def test_deep_merge_simple(self):
        """Test deep merge with simple dictionaries."""
        base = {"a": 1, "b": 2}
        update = {"b": 3, "c": 4}

        result = _deep_merge(base, update)

        assert result == {"a": 1, "b": 3, "c": 4}
        # Ensure original unchanged
        assert base == {"a": 1, "b": 2}

    def test_deep_merge_nested(self):
        """Test deep merge with nested dictionaries."""
        base = {
            "logging": {"level": "INFO", "path": "logs/app.log"},
            "network": {"interface": "eth0"},
        }
        update = {"logging": {"level": "DEBUG"}, "ui": {"fullscreen": True}}

        result = _deep_merge(base, update)

        assert result["logging"]["level"] == "DEBUG"
        assert result["logging"]["path"] == "logs/app.log"
        assert result["network"]["interface"] == "eth0"
        assert result["ui"]["fullscreen"] is True

    def test_load_config_no_file(self):
        """Test loading config when file doesn't exist."""
        with patch("utils.config.get_config_path") as mock_path:
            mock_path.return_value = Path("/nonexistent/config.yml")

            config = load_config()

            # Should return default config
            assert "logging" in config
            assert "network" in config
            assert "ui" in config

    def test_load_config_with_file(self):
        """Test loading config from YAML file."""
        yaml_content = """
logging:
  level: DEBUG
network:
  interface: eth0
"""

        with (
            patch("utils.config.get_config_path") as mock_path,
            patch("builtins.open", mock_open(read_data=yaml_content)),
            patch("pathlib.Path.exists", return_value=True),
        ):
            mock_path.return_value = Path("config.yml")

            config = load_config()

            assert config["logging"]["level"] == "DEBUG"
            assert config["network"]["interface"] == "eth0"
            # Default values should still be present
            assert "ui" in config

    def test_save_config_success(self):
        """Test saving configuration successfully."""
        config = {"logging": {"level": "INFO"}, "network": {"interface": "eth0"}}

        mock_file = mock_open()
        with (
            patch("utils.config.get_config_path") as mock_path,
            patch("builtins.open", mock_file),
            patch("pathlib.Path.mkdir"),
        ):
            mock_path.return_value = Path("config.yml")

            result = save_config(config)

            assert result is True
            mock_file.assert_called_once()

    def test_save_config_error(self):
        """Test save config handles errors."""
        config = {"test": "data"}

        with (
            patch("utils.config.get_config_path") as mock_path,
            patch("builtins.open", side_effect=PermissionError()),
        ):
            mock_path.return_value = Path("config.yml")

            result = save_config(config)

            assert result is False

    def test_load_config_invalid_yaml(self):
        """Test loading config with invalid YAML."""
        invalid_yaml = "{ invalid yaml content ]["

        with (
            patch("utils.config.get_config_path") as mock_path,
            patch("builtins.open", mock_open(read_data=invalid_yaml)),
            patch("pathlib.Path.exists", return_value=True),
        ):
            mock_path.return_value = Path("config.yml")

            config = load_config()

            # Should return default config on error
            assert "logging" in config
            assert "network" in config
