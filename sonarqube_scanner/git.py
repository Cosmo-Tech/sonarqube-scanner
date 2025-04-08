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


def is_github_url(repo_url):
    """Check if the URL is for GitHub."""
    return "github.com" in repo_url


def get_repo_name(repo_url):
    """Extract repository name from Git URL."""
    return repo_url.split("/")[-1].replace(".git", "")


def get_token_for_repo(repo_name, is_github=True):
    """
    Get token from environment variable for a repository.

    Args:
        repo_name: Repository name
        is_github: Whether this is a GitHub repository (True) or Bitbucket Server (False)

    Returns:
        Token string or None if not found
    """
    # Normalize repo name for environment variable
    normalized_name = repo_name.upper().replace("-", "_")

    # Check for repository-specific token
    if is_github:
        env_var = f"GIT_TOKEN_{normalized_name}"
    else:
        env_var = f"BITBUCKET_TOKEN_{normalized_name}"

    token = os.getenv(env_var)

    # If no repo-specific token, try generic token
    if not token:
        if is_github:
            token = os.getenv("GITHUB_TOKEN")
        else:
            token = os.getenv("BITBUCKET_TOKEN")

    return token


def apply_auth_to_url(repo_url, token, is_github=True):
    """
    Apply authentication to repository URL.

    Args:
        repo_url: Repository URL
        token: Authentication token
        is_github: Whether this is a GitHub repository (True) or Bitbucket Server (False)

    Returns:
        URL with authentication applied
    """
    if not token:
        return repo_url

    if is_github:
        # GitHub format: https://{token}@github.com/...
        return repo_url.replace("https://", f"https://{token}@")
    else:
        # Bitbucket Server format: https://{username}:{token}@server/scm/...
        if ":" in token:  # Token includes username
            auth = token
        else:
            # Default to 'x-token-auth' as username if only token is provided
            auth = f"x-token-auth:{token}"
        return repo_url.replace("https://", f"https://{auth}@")


def mask_token_in_url(url):
    """Mask token in URL for logging purposes."""
    if "@" in url and "://" in url:
        protocol = url.split("://")[0]
        rest = url.split("://")[1].split("@")[1]
        return f"{protocol}://***@{rest}"
    return url


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

    # Determine if this is a GitHub repository
    is_github = is_github_url(repo_url)

    # Get token from environment variable
    token = get_token_for_repo(repo_name, is_github)

    # Convert SSH URLs to HTTPS URLs
    if is_ssh_url(repo_url):
        logger.error("Only https supported")
        raise RuntimeError

    # Apply token to URL if available
    auth_url = apply_auth_to_url(repo_url, token, is_github)

    if token:
        repo_type = "GitHub" if is_github else "Bitbucket Server"
        logger.info(f"Using token authentication for {repo_name} ({repo_type})")
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
