"""
Tests for the git module.
"""

import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from sonarqube_scanner.git import (
    is_ssh_url,
    get_repo_name,
    get_token_for_repo,
    mask_token_in_url,
    clone_or_update_repository,
    GitError,
)


def test_is_ssh_url():
    """Test SSH URL detection."""
    assert is_ssh_url("git@github.com:org/repo.git") is True
    assert is_ssh_url("https://github.com/org/repo.git") is False
    assert is_ssh_url("git://github.com/org/repo.git") is False


def test_get_repo_name():
    """Test repository name extraction."""
    assert get_repo_name("https://github.com/org/repo.git") == "repo"
    assert get_repo_name("git@github.com:org/repo.git") == "repo"
    assert get_repo_name("https://github.com/org/repo-name.git") == "repo-name"


def test_get_token_for_repo():
    """Test token retrieval from environment variables."""
    with patch.dict(os.environ, {"GIT_TOKEN_TEST_REPO": "test-token"}):
        assert get_token_for_repo("test-repo") == "test-token"

    with patch.dict(os.environ, {}):
        assert get_token_for_repo("test-repo") is None


def test_mask_token_in_url():
    """Test token masking in URLs."""
    # URL with token
    url = "https://token@github.com/org/repo.git"
    assert mask_token_in_url(url) == "https://***@github.com/org/repo.git"

    # URL without token
    url = "https://github.com/org/repo.git"
    assert mask_token_in_url(url) == url


@patch("sonarqube_scanner.git.Repo")
@patch("sonarqube_scanner.git.get_token_for_repo")
def test_clone_or_update_repository_with_token(mock_get_token, mock_repo_class):
    """Test cloning a repository with token authentication."""
    # Setup mocks
    mock_get_token.return_value = "test-token"
    mock_repo = MagicMock()
    mock_repo_class.clone_from.return_value = mock_repo

    # Test cloning a new repository
    base_dir = Path("/tmp")
    repo_url = "https://github.com/org/repo.git"
    repo_name = "repo"
    branch = "main"

    result = clone_or_update_repository(repo_url, repo_name, branch, base_dir)

    # Verify the correct URL with token was used
    expected_auth_url = "https://test-token@github.com/org/repo.git"
    mock_repo_class.clone_from.assert_called_once_with(
        expected_auth_url, base_dir / repo_name
    )
    mock_repo.git.checkout.assert_called_once_with(branch)
    assert result == base_dir / repo_name


@patch("sonarqube_scanner.git.Repo")
@patch("sonarqube_scanner.git.get_token_for_repo")
def test_clone_or_update_repository_without_token(mock_get_token, mock_repo_class):
    """Test cloning a repository without token authentication."""
    # Setup mocks
    mock_get_token.return_value = None
    mock_repo = MagicMock()
    mock_repo_class.clone_from.return_value = mock_repo

    # Test cloning a new repository
    base_dir = Path("/tmp")
    repo_url = "https://github.com/org/repo.git"
    repo_name = "repo"
    branch = "main"

    result = clone_or_update_repository(repo_url, repo_name, branch, base_dir)

    # Verify the original URL was used (no token)
    mock_repo_class.clone_from.assert_called_once_with(repo_url, base_dir / repo_name)
    mock_repo.git.checkout.assert_called_once_with(branch)
    assert result == base_dir / repo_name


@patch("sonarqube_scanner.git.Repo")
@patch("sonarqube_scanner.git.get_token_for_repo")
def test_update_existing_repository_with_token(mock_get_token, mock_repo_class):
    """Test updating an existing repository with token authentication."""
    # Setup mocks
    mock_get_token.return_value = "test-token"
    mock_repo = MagicMock()
    mock_repo_class.return_value = mock_repo

    # Mock that the repository directory exists
    with patch("pathlib.Path.exists", return_value=True):
        base_dir = Path("/tmp")
        repo_url = "https://github.com/org/repo.git"
        repo_name = "repo"
        branch = "main"

        result = clone_or_update_repository(repo_url, repo_name, branch, base_dir)

        # Verify the remote URL was updated with the token
        expected_auth_url = "https://test-token@github.com/org/repo.git"
        mock_repo.remotes.origin.set_url.assert_called_once_with(expected_auth_url)
        mock_repo.remotes.origin.fetch.assert_called_once()
        mock_repo.git.checkout.assert_called_once_with(branch)
        mock_repo.git.reset.assert_called_once_with("--hard", f"origin/{branch}")
        assert result == base_dir / repo_name


@patch("sonarqube_scanner.git.Repo")
@patch("sonarqube_scanner.git.get_token_for_repo")
def test_error_handling_with_token_masking(mock_get_token, mock_repo_class):
    """Test that tokens are masked in error messages."""
    # Setup mocks
    token = "test-token"
    mock_get_token.return_value = token

    # Make clone_from raise an error that includes the token
    error_msg = f"Authentication failed with token {token}"
    mock_repo_class.clone_from.side_effect = Exception(error_msg)

    # Test cloning a repository that will fail
    base_dir = Path("/tmp")
    repo_url = "https://github.com/org/repo.git"
    repo_name = "repo"
    branch = "main"

    with pytest.raises(GitError) as excinfo:
        clone_or_update_repository(repo_url, repo_name, branch, base_dir)

    # Verify the token is masked in the error message
    assert token not in str(excinfo.value)
    assert "***" in str(excinfo.value)
