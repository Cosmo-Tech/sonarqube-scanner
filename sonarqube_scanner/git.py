"""
Git operations for the SonarQube Scanner.
"""

import logging
from pathlib import Path
from git import Repo
from git.exc import GitCommandError

logger = logging.getLogger("sonarqube_scanner")

class GitError(Exception):
    """Exception raised for Git operation errors."""
    pass

def get_repo_name(repo_url):
    """Extract repository name from Git URL."""
    return repo_url.split('/')[-1].replace('.git', '')

def clone_or_update_repository(
    repo_url,
    branch,
    base_dir
):
    """
    Clone or update a repository for a specific branch.

    Args:
        repo_url: Git repository URL
        branch: Branch name to checkout
        base_dir: Base directory for cloning repositories

    Returns:
        Path to the repository directory

    Raises:
        GitError: If Git operations fail
    """
    repo_name = get_repo_name(repo_url)
    target = base_dir / repo_name

    try:
        if target.exists():
            logger.info(f"Updating repository: {repo_name}")
            repo = Repo(target)
            repo.remotes.origin.fetch()
            repo.git.checkout(branch)
            repo.git.reset('--hard', f'origin/{branch}')
            logger.info(f"Updated {repo_name} to {branch}")
        else:
            logger.info(f"Cloning repository: {repo_name}")
            repo = Repo.clone_from(repo_url, target)
            if branch not in ("main", "master"):
                repo.git.checkout(branch)
            logger.info(f"Cloned {repo_name} branch {branch}")

        return target

    except GitCommandError as e:
        raise GitError(f"Git operation failed: {e}")
    except Exception as e:
        raise GitError(f"Unexpected error: {e}")