"""
Tests for the configuration module.
"""

import os
from sonarqube_scanner.config import load_config


def test_load_valid_config(sample_config_file, mock_env_token):
    """Test loading a valid configuration file."""
    # Load the config
    loaded_config = load_config(sample_config_file)

    # Verify the config was loaded correctly
    assert loaded_config["sonarqube"]["url"] == "http://localhost:9000"
    assert loaded_config["sonarqube"]["token"] == mock_env_token
    assert len(loaded_config["repositories"]) == 1
    assert loaded_config["repositories"][0]["name"] == "test-repo"
    assert loaded_config["repositories"][0]["branches"] == ["main"]


def test_load_nonexistent_config():
    """Test loading a non-existent configuration file."""
    # Attempt to load a non-existent file
    result = load_config("nonexistent_config.yaml")
    # The function logs an error but returns None
    assert result is None


def test_config_without_env_token(sample_config_file):
    """Test loading a configuration without the environment token set."""
    # Make sure the environment variable is not set
    if "SONARQUBE_TOKEN" in os.environ:
        del os.environ["SONARQUBE_TOKEN"]

    # Load the config
    loaded_config = load_config(sample_config_file)

    # Verify the token is None
    assert loaded_config["sonarqube"]["token"] is None
