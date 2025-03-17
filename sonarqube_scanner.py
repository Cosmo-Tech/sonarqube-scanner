#!/usr/bin/env python3
"""
SonarQube Scanner - Scan Cosmo-Tech repositories with SonarQube.
"""

import sys
import subprocess
import logging
import click
import yaml
import git
import os
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def load_config(config_path):
    """Load configuration from YAML file"""
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Failed to load configuration from {config_path}: {str(e)}")
        sys.exit(1)

def run_sonar_scanner(repo_dir, sonar_url, sonar_token, project_key, project_name=None):
    """Run SonarQube scanner on repository"""
    logger.info(f"Running SonarQube scanner on {repo_dir}")

    # Build command with required parameters
    cmd = [
        'sonar-scanner',
        f'-Dsonar.host.url={sonar_url}',
        f'-Dsonar.token={sonar_token}',
        f'-Dsonar.projectKey={project_key}',
        f'-Dsonar.projectBaseDir={repo_dir}'
    ]
    
    # Add optional project name if provided
    if project_name:
        cmd.append(f'-Dsonar.projectName={project_name}')
    
    try:
        # Run the scanner
        logger.debug(f"Executing command: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Check for errors
        if result.returncode != 0:
            logger.error(f"Scanner failed with exit code {result.returncode}")
            logger.error(f"Error output: {result.stderr}")
            return False
        
        logger.info(f"Scan completed successfully for {project_key}")
        logger.debug(f"Scanner output: {result.stdout}")
        return True
    except Exception as e:
        logger.error(f"Error running scanner: {str(e)}")
        return False

def clone_or_update_repository(repo_url, branch, base_dir):
    """Clone or update a repository for a specific branch"""
    repo_name = repo_url.split('/')[-1].replace('.git','')
    target = Path(base_dir) / repo_name
    if target.exists():
        logger.info(f"Repository already exists pulling branch {branch} of {repo_name}")
        repo = git.Repo(target)
        repo.git.checkout(branch)
        repo.remotes.origin.fetch()
        repo.git.checkout(branch)
        repo.git.reset('--hard', f'origin/{branch}')
    else:
        logger.info(f"cloning {repo_name}")
        repo = git.Repo.clone_from(
            url= repo_url,
            to_path = target
        )
    return target

def process_branch(repo_url, branch, base_dir, sonar_config, project_key, project_name):
    """Process a single branch of a repository"""
    try:
        # Update repository
        repo_dir = clone_or_update_repository(repo_url, branch, base_dir)
        # Run scanner
        success = run_sonar_scanner(
            repo_dir,
            sonar_config['url'],
            sonar_config['token'],
            project_key,
            project_name
        )
        if success:
            logger.info(f"Successfully scanned {project_name} branch {branch}")
        else:
            logger.error(f"Failed to scan {project_name} branch {branch}")
            
    except Exception as e:
        logger.error(f"Error processing {project_name} branch {branch}: {str(e)}")

def scan_repository(repo_config, sonar_config, base_dir):
    """Scan a single repository with all its branches"""
    repo_name = repo_config['name']
    repo_url = repo_config['url']
    project_key = repo_config['project_key']
    branches = repo_config['branches']
    
    # Get optional project name if available
    project_name = repo_config.get('project_name', repo_name)
    
    logger.info(f"Processing repository: {repo_name}")
    
    # Process each branch
    for branch in branches:
        logger.info(f"Processing branch: {branch}")
        process_branch(repo_url, branch, base_dir, sonar_config, project_key, project_name)

@click.command()
@click.option('--config', '-c', 
              default='config.yaml',
              help='Path to configuration file (default: config.yaml)')
@click.option('--verbose', '-v', 
              is_flag=True,
              help='Enable verbose output')
def main(config, verbose):
    """Scan GitHub repositories with SonarQube."""
    # Set log level based on verbosity
    if verbose:
        logger.setLevel(logging.DEBUG)
    
    # Load configuration
    logger.info(f"Loading configuration from {config}")
    config_data = load_config(config)
    # Validate configuration
    if 'sonarqube' not in config_data:
        logger.error("Missing 'sonarqube' section in configuration")
        sys.exit(1)
    if 'repositories' not in config_data:
        logger.error("Missing 'repositories' section in configuration")
        sys.exit(1)
    
    # Extract SonarQube configuration
    sonar_config = config_data['sonarqube']
    sonar_config['token'] = os.getenv('SONARQUBE_TOKEN')
    if 'url' not in sonar_config:
        logger.error("SonarQube configuration must include 'url'")
        sys.exit(1)

    for repo_config in config_data['repositories']:
        # Validate repository configuration
        required_fields = ['name', 'url', 'branches', 'project_key']
        missing_fields = [field for field in required_fields if field not in repo_config]
        
        if missing_fields:
            logger.error(f"Repository configuration missing required fields: {', '.join(missing_fields)}")
            continue
        
        # Scan repository
        scan_repository(repo_config, sonar_config, '/home/dsellis/temp')
    
    logger.info("Scanning process completed")

if __name__ == "__main__":
    main()