"""
Shared pytest fixtures and utilities for sonarqube-scanner tests.
"""

import os
import pytest
import tempfile
import yaml

@pytest.fixture
def sample_config_file():
    """
    Create a temporary sample configuration file for testing.
    
    Returns:
        str: Path to the temporary configuration file
    """
    # Create a temporary config file
    config_data = {
        'sonarqube': {
            'url': 'http://localhost:9000'
        },
        'repositories': [
            {
                'name': 'test-repo',
                'url': 'https://github.com/test/repo.git',
                'branches': ['main']
            }
        ]
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as temp:
        yaml.dump(config_data, temp)
        temp_path = temp.name
    
    yield temp_path
    
    # Clean up after the test
    if os.path.exists(temp_path):
        os.unlink(temp_path)

@pytest.fixture
def mock_env_token():
    """
    Set up and tear down a mock SONARQUBE_TOKEN environment variable.
    
    Returns:
        str: The token value
    """
    token = 'test-token'
    os.environ['SONARQUBE_TOKEN'] = token
    
    yield token
    
    # Clean up
    os.environ.pop('SONARQUBE_TOKEN', None)