"""
Tests for the git module.
"""

import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from sonarqube_scanner.git import (
    is_ssh_url,
    is_github_url,
    get_repo_name,
    get_token_for_repo,
    mask_token_in_url,
    apply_auth_to_url,
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


def test_is_github_url():
    """Test GitHub URL detection."""
    assert is_github_url("https://github.com/org/repo.git") is True
    assert is_github_url("git@github.com:org/repo.git") is True
    assert is_github_url("https://bitbucket.example.com/scm/project/repo.git") is False


def test_get_repo_name_bitbucket_server():
    """Test repository name extraction for Bitbucket Server URLs."""
    assert get_repo_name("https://bitbucket.example.com/scm/project/repo.git") == "repo"
    assert get_repo_name("https://bitbucket.example.com/scm/project/repo-name.git") == "repo-name"


def test_get_token_for_repo_github():
    """Test token retrieval from environment variables for GitHub repositories."""
    with patch.dict(os.environ, {"GIT_TOKEN_TEST_REPO": "test-token"}):
        assert get_token_for_repo("test-repo", is_github=True) == "test-token"

    with patch.dict(os.environ, {"GITHUB_TOKEN": "global-token"}):
        assert get_token_for_repo("test-repo", is_github=True) == "global-token"

    with patch.dict(os.environ, {}):
        assert get_token_for_repo("test-repo", is_github=True) is None


def test_get_token_for_repo_bitbucket():
    """Test token retrieval from environment variables for Bitbucket repositories."""
    with patch.dict(os.environ, {"BITBUCKET_TOKEN_TEST_REPO": "test-token"}):
        assert get_token_for_repo("test-repo", is_github=False) == "test-token"

    with patch.dict(os.environ, {"BITBUCKET_TOKEN": "global-token"}):
        assert get_token_for_repo("test-repo", is_github=False) == "global-token"

    with patch.dict(os.environ, {}):
        assert get_token_for_repo("test-repo", is_github=False) is None


def test_apply_auth_to_url_github():
    """Test applying authentication to GitHub URLs."""
    repo_url = "https://github.com/org/repo.git"
    token = "test-token"
    
    # Test with GitHub URL
    auth_url = apply_auth_to_url(repo_url, token, is_github=True)
    assert auth_url == "https://test-token@github.com/org/repo.git"
    
    # Test with no token
    auth_url = apply_auth_to_url(repo_url, None, is_github=True)
    assert auth_url == repo_url


def test_apply_auth_to_url_bitbucket():
    """Test applying authentication to Bitbucket Server URLs."""
    repo_url = "https://bitbucket.example.com/scm/project/repo.git"
    
    # Test with token only (should add default username)
    token = "test-token"
    auth_url = apply_auth_to_url(repo_url, token, is_github=False)
    assert auth_url == "https://x-token-auth:test-token@bitbucket.example.com/scm/project/repo.git"
    
    # Test with username:token format
    token = "username:test-token"
    auth_url = apply_auth_to_url(repo_url, token, is_github=False)
    assert auth_url == "https://username:test-token@bitbucket.example.com/scm/project/repo.git"
    
    # Test with no token
    auth_url = apply_auth_to_url(repo_url, None, is_github=False)
    assert auth_url == repo_url


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
@patch("sonarqube_scanner.git.is_github_url")
def test_clone_or_update_repository_with_token(mock_is_github, mock_get_token, mock_repo_class):
    """Test cloning a repository with token authentication."""
    # Setup mocks
    mock_is_github.return_value = True
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
@patch("sonarqube_scanner.git.is_github_url")
def test_clone_or_update_repository_without_token(mock_is_github, mock_get_token, mock_repo_class):
    """Test cloning a repository without token authentication."""
    # Setup mocks
    mock_is_github.return_value = True
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
@patch("sonarqube_scanner.git.is_github_url")
def test_update_existing_repository_with_token(mock_is_github, mock_get_token, mock_repo_class):
    """Test updating an existing repository with token authentication."""
    # Setup mocks
    mock_is_github.return_value = True
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
@patch("sonarqube_scanner.git.is_github_url")
def test_error_handling_with_token_masking(mock_is_github, mock_get_token, mock_repo_class):
    """Test that tokens are masked in error messages."""
    # Setup mocks
    mock_is_github.return_value = True
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


@patch("sonarqube_scanner.git.Repo")
@patch("sonarqube_scanner.git.get_token_for_repo")
@patch("sonarqube_scanner.git.is_github_url")
def test_clone_bitbucket_server_repository(mock_is_github, mock_get_token, mock_repo_class):
    """Test cloning a Bitbucket Server repository with token authentication."""
    # Setup mocks
    mock_is_github.return_value = False
    mock_get_token.return_value = "username:test-token"
    mock_repo = MagicMock()
    mock_repo_class.clone_from.return_value = mock_repo

    # Test cloning a new repository
    base_dir = Path("/tmp")
    repo_url = "https://bitbucket.example.com/scm/project/repo.git"
    repo_name = "repo"
    branch = "main"

    result = clone_or_update_repository(repo_url, repo_name, branch, base_dir)

    # Verify the correct URL with token was used
    expected_auth_url = "https://username:test-token@bitbucket.example.com/scm/project/repo.git"
    mock_repo_class.clone_from.assert_called_once_with(
        expected_auth_url, base_dir / repo_name
    )
    mock_repo.git.checkout.assert_called_once_with(branch)
    assert result == base_dir / repo_name


@patch("sonarqube_scanner.git.Repo")
@patch("sonarqube_scanner.git.get_token_for_repo")
@patch("sonarqube_scanner.git.is_github_url")
def test_update_bitbucket_server_repository(mock_is_github, mock_get_token, mock_repo_class):
    """Test updating a Bitbucket Server repository with token authentication."""
    # Setup mocks
    mock_is_github.return_value = False
    mock_get_token.return_value = "username:test-token"
    mock_repo = MagicMock()
    mock_repo_class.return_value = mock_repo

    # Mock that the repository directory exists
    with patch("pathlib.Path.exists", return_value=True):
        base_dir = Path("/tmp")
        repo_url = "https://bitbucket.example.com/scm/project/repo.git"
        repo_name = "repo"
        branch = "main"

        result = clone_or_update_repository(repo_url, repo_name, branch, base_dir)

        # Verify the remote URL was updated with the token
        expected_auth_url = "https://username:test-token@bitbucket.example.com/scm/project/repo.git"
        mock_repo.remotes.origin.set_url.assert_called_once_with(expected_auth_url)
        mock_repo.remotes.origin.fetch.assert_called_once()
        mock_repo.git.checkout.assert_called_once_with(branch)
        mock_repo.git.reset.assert_called_once_with("--hard", f"origin/{branch}")
        assert result == base_dir / repo_name
