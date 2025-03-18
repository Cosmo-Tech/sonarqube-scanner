"""
Configuration handling for the SonarQube Scanner.
"""

import yaml
import logging
logger = logging.getLogger("sonarqube_scanner")

def load_config(config_path):
    """Load and parse YAML configuration file."""
    try:
        with open(config_path) as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Error reading configuration: {e}")
