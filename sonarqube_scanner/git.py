"""
Git operations for the SonarQube Scanner.
"""

import logging
import os
from git import Repo
from git.exc import GitCommandError

logger = logging.getLogger("sonarqube_scanner")


class GitError(Exception):
    """Exception raised for Git operation errors."""

    pass


def is_ssh_url(repo_url):
    """Check if the repository URL uses SSH protocol."""
    return repo_url.startswith("git@")


def get_repo_name(repo_url):
    """Extract repository name from Git URL."""
    return repo_url.split("/")[-1].replace(".git", "")


def get_token_for_repo(repo_name):
    """Get token from environment variable for a repository."""
    env_var = f"GIT_TOKEN_{repo_name.upper().replace('-', '_')}"
    return os.getenv(env_var)


def mask_token_in_url(url):
    """Mask token in URL for logging purposes."""
    if "@" in url and "://" in url:
        protocol = url.split("://")[0]
        auth_part = url.split("://")[1].split("@")[0]
        rest = url.split("://")[1].split("@")[1]
        return f"{protocol}://***@{rest}"
    return url


def convert_ssh_to_https(repo_url):
    """Convert SSH URL to HTTPS URL."""
    if is_ssh_url(repo_url):
        # Convert git@github.com:org/repo.git to https://github.com/org/repo.git
        domain = repo_url.split('@')[1].split(':')[0]
        path = repo_url.split(':')[1]
        https_url = f"https://{domain}/{path}"
        logger.info(f"Converted SSH URL to HTTPS: {https_url}")
        return https_url
    return repo_url


def update_repository(repo, branch):
    """fetch from remote with https or ssh and switch to branch"""
    repo.remotes.origin.fetch()
    repo.git.checkout(branch)
    repo.git.reset("--hard", f"origin/{branch}")


def clone_or_update_repository(repo_url, repo_name, branch, base_dir):
    """
    Clone or update a repository for a specific branch with token authentication.

    Args:
        repo_url: Git repository URL (HTTPS or SSH)
        repo_name: Repository name
        branch: Branch name to checkout
        base_dir: Base directory for cloning repositories

    Returns:
        Path to the repository directory

    Raises:
        GitError: If Git operations fail
    """
    target = base_dir / repo_name
    
    # Get token from environment variable
    token = get_token_for_repo(repo_name)
    
    # Convert SSH URLs to HTTPS URLs
    repo_url = convert_ssh_to_https(repo_url)
    
    # Apply token to URL if available
    auth_url = repo_url
    if token:
        # Format: https://{token}@github.com/org/repo.git
        auth_url = repo_url.replace("https://", f"https://{token}@")
        logger.info(f"Using token authentication for {repo_name}")
    else:
        logger.info(f"No token found for {repo_name}, using public access")
    
    # For logging, mask the token
    masked_url = mask_token_in_url(auth_url)
    
    try:
        if target.exists():
            logger.info(f"Updating repository: {repo_name} from {masked_url}")
            repo = Repo(target)
            
            # Update remote URL with token if available
            repo.remotes.origin.set_url(auth_url)
            
            # Update repository
            repo.remotes.origin.fetch()
            repo.git.checkout(branch)
            repo.git.reset("--hard", f"origin/{branch}")
            logger.info(f"Updated {repo_name} to {branch}")
                
        else:
            logger.info(f"Cloning repository: {repo_name} from {masked_url}")
            
            # Clone with token authentication if available
            repo = Repo.clone_from(auth_url, target)
            
            # Checkout branch
            repo.git.checkout(branch)
            logger.info(f"Cloned {repo_name} branch {branch}")
            
        return target
        
    except GitCommandError as e:
        # Mask token in error messages
        error_msg = str(e)
        if token and token in error_msg:
            error_msg = error_msg.replace(token, "***")
        raise GitError(f"Git operation failed: {error_msg}")
    except Exception as e:
        # Mask token in general exception messages too
        error_msg = str(e)
        if token and token in error_msg:
            error_msg = error_msg.replace(token, "***")
        raise GitError(f"Unexpected error: {error_msg}")
