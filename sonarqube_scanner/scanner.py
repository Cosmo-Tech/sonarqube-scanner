"""
SonarQube scanning functionality.
"""

import logging
import subprocess

from .git import clone_or_update_repository, GitError

logger = logging.getLogger("sonarqube_scanner")


def run_sonar_scanner(repo_dir, sonar_url, sonar_token, repo_name, branch_name):
    """
    Run SonarQube scanner on repository.

    Args:
        repo_dir: Repository directory path
        sonar_url: SonarQube server URL
        sonar_token: SonarQube authentication token
        repo_name: Repository name
        branch_name: Branch name being scanned

    Returns:
        True if scan was successful, False otherwise
    """
    logger.info(f"Running SonarQube scanner on {repo_dir}")

    # Generate project key from repo name and branch
    project_key = f"{repo_name}-{branch_name}".replace("/", "-")
    project_name = f"{repo_name} ({branch_name})"

    # Build command with required parameters
    cmd = [
        "sonar-scanner",
        f"-Dsonar.host.url={sonar_url}",
        f"-Dsonar.token={sonar_token}",
        f"-Dsonar.projectKey={project_key}",
        f"-Dsonar.projectName={project_name}",
        f"-Dsonar.projectBaseDir={repo_dir}",
        "-Dsonar.coverage.exclusions=**",
        "-X"
    ]

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


def process_branch(repo_url, repo_name, branch, base_dir, sonar_config):
    """
    Process a single branch of a repository.

    Args:
        repo_url: Git repository URL
        repo_name: Repository name
        branch: Branch name to scan
        base_dir: Base directory for cloning repositories
        sonar_config: SonarQube configuration

    Returns:
        True if scan was successful, False otherwise
    """
    try:
        # Update repository
        repo_dir = clone_or_update_repository(repo_url, branch, base_dir)

        # Run scanner
        success = run_sonar_scanner(
            repo_dir, sonar_config["url"], sonar_config["token"], repo_name, branch
        )

        if success:
            logger.info(f"Successfully scanned {repo_name} branch {branch}")
            return True
        else:
            logger.error(f"Failed to scan {repo_name} branch {branch}")
            return False

    except GitError as e:
        logger.error(f"Git error processing {repo_name} branch {branch}: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Error processing {repo_name} branch {branch}: {str(e)}")
        return False


def scan_repository(repo_config, sonar_config, base_dir):
    """
    Scan a single repository with all its branches.

    Args:
        repo_config: Repository configuration
        sonar_config: SonarQube configuration
        base_dir: Base directory for cloning repositories

    Returns:
        None
    """
    repo_name = repo_config["name"]
    repo_url = repo_config["url"]
    branches = repo_config["branches"]

    logger.info(f"Processing repository: {repo_name}")

    # Process each branch
    for branch in branches:
        logger.info(f"Processing branch: {branch}")
        success = process_branch(repo_url, repo_name, branch, base_dir, sonar_config)
        logger.info(
            f"Scan {'succeeded' if success else 'failed'} for {repo_name}:{branch}"
        )


def scan_repositories(config, base_dir):
    """
    Scan all repositories specified in the configuration.

    Args:
        config: Configuration dictionary
        base_dir: Base directory for cloning repositories

    Returns:
        Tuple of (successful repositories, total repositories)
    """
    sonar_config = config["sonarqube"]
    repositories = config["repositories"]

    for repo_config in repositories:
        scan_repository(repo_config, sonar_config, base_dir)
