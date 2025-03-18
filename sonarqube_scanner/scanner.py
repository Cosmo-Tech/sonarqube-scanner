"""
SonarQube scanning functionality.
"""

import logging
import subprocess
from pathlib import Path

from .git import clone_or_update_repository, GitError

logger = logging.getLogger("sonarqube_scanner")

def run_sonar_scanner(
    repo_dir,
    sonar_url,
    sonar_token,
    project_key,
    project_name,
    additional_params
):
    """
    Run SonarQube scanner on repository.
    
    Args:
        repo_dir: Repository directory path
        sonar_url: SonarQube server URL
        sonar_token: SonarQube authentication token
        project_key: SonarQube project key
        project_name: Optional project display name
        additional_params: Optional additional SonarQube parameters
        
    Returns:
        True if scan was successful, False otherwise
    """
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

    # Add any additional parameters
    if additional_params:
        for key, value in additional_params.items():
            cmd.append(f'-D{key}={value}')

    try:
        # Run the scanner
        result = subprocess.run(cmd, capture_output=True, text=True)

        # Check for errors
        if result.returncode != 0:
            logger.error(f"Scanner failed with exit code {result.returncode}")
            logger.error(f"Error output: {result.stderr}")
            return False

        logger.info(f"Scan completed successfully for {project_key}")
        logger.debug(f"Scanner output: {result.stdout}")
        return True
    except subprocess.SubprocessError as e:
        logger.error(f"Subprocess error running scanner: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Error running scanner: {str(e)}")
        return False

def process_branch(
    repo_url,
    branch,
    base_dir,
    sonar_config,
    project_key,
    project_name
):
    """
    Process a single branch of a repository.

    Args:
        repo_url: Git repository URL
        branch: Branch name to scan
        base_dir: Base directory for cloning repositories
        sonar_config: SonarQube configuration
        project_key: SonarQube project key
        project_name: Project display name

    Returns:
        True if scan was successful, False otherwise
    """
    try:
        # Update repository
        repo_dir = clone_or_update_repository(repo_url, branch, base_dir)

        # Add branch information to SonarQube parameters
        additional_params = {
            "sonar.branch.name": branch
        }

        # Run scanner
        success = run_sonar_scanner(
            repo_dir,
            sonar_config['url'],
            sonar_config['token'],
            project_key,
            project_name,
            additional_params
        )

        if success:
            logger.info(f"Successfully scanned {project_name} branch {branch}")
            return True
        else:
            logger.error(f"Failed to scan {project_name} branch {branch}")
            return False

    except GitError as e:
        logger.error(f"Git error processing {project_name} branch {branch}: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Error processing {project_name} branch {branch}: {str(e)}")
        return False

def scan_repository(
    repo_config,
    sonar_config,
    base_dir
):
    """
    Scan a single repository with all its branches.

    Args:
        repo_config: Repository configuration
        sonar_config: SonarQube configuration
        base_dir: Base directory for cloning repositories

    Returns:
        Tuple of (successful scans, total scans)
    """
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
        success = process_branch(
            repo_url, 
            branch, 
            base_dir, 
            sonar_config, 
            project_key, 
            project_name
        )
        logger.info(f"Scanned {repo_name}:{branch}")

def scan_repositories(
    config,
    base_dir
):
    """
    Scan all repositories specified in the configuration.

    Args:
        config: Configuration dictionary
        base_dir: Base directory for cloning repositories

    Returns:
        Tuple of (successful repositories, total repositories)
    """
    sonar_config = config['sonarqube']
    repositories = config['repositories']

    for repo_config in repositories:
        scan_repository(
            repo_config, 
            sonar_config, 
            base_dir
        )