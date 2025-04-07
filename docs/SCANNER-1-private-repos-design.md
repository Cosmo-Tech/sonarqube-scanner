# Technical Design: Token Authentication for Private Repositories via Environment Variables

## Overview

This document outlines the technical design for implementing token-based authentication for private repositories in the SonarQube Scanner tool. Currently, the tool uses SSH authentication with a hardcoded SSH key path. This enhancement will replace that approach with GitHub personal access tokens for HTTPS URLs, loaded exclusively from environment variables.

## Related JIRA Ticket

- [SCANNER-1](https://sellisd.atlassian.net/browse/SCANNER-1): Add support for cloning private repositories with HTTPS authentication

## Current Implementation

The current implementation in `git.py` uses:
- Public repositories via HTTPS (no authentication)
- Private repositories via SSH with a hardcoded SSH key path (`~/.ssh/scanner`)

The relevant code in `git.py`:

```python
def is_ssh_url(repo_url):
    """Check if the repository URL uses SSH protocol."""
    return repo_url.startswith("git@")

def clone_or_update_repository(repo_url, branch, base_dir):
    # ...
    ssh_cmd = "ssh -i ~/.ssh/scanner"
    # ...
    if is_ssh_url(repo_url):
        git_context = repo.git.custom_environment(GIT_SSH_COMMAND=ssh_cmd)
        with git_context:
            # SSH operations
    else:
        # HTTPS operations (no auth)
```

## Proposed Changes

### 1. Environment Variable Naming Convention

Define a standard naming convention for repository tokens:

```
GIT_TOKEN_{REPOSITORY_NAME}
```

Where `{REPOSITORY_NAME}` is the uppercase repository name with hyphens replaced by underscores.

For example:
- Repository name: "private-repo"
- Environment variable: `GIT_TOKEN_PRIVATE_REPO`

### 2. Git Module Enhancements

Modify the `git.py` module to:
- Remove SSH-specific code
- Check for environment variables containing tokens
- Apply token authentication for HTTPS URLs
- Convert SSH URLs to HTTPS URLs

### 3. Documentation Updates

- Update README.md to remove SSH authentication instructions
- Add instructions for token authentication via environment variables
- Add examples for setting up environment variables

## Implementation Details

### Git Module Changes

Update `git.py` to use tokens from environment variables:

```python
def get_token_for_repo(repo_name):
    """Get token from environment variable for a repository."""
    env_var = f"GIT_TOKEN_{repo_name.upper().replace('-', '_')}"
    return os.getenv(env_var)

def clone_or_update_repository(repo_url, repo_name, branch, base_dir):
    """
    Clone or update a repository for a specific branch with token authentication.
    
    Args:
        repo_url: Repository URL
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
    if repo_url.startswith("git@"):
        # Convert git@github.com:org/repo.git to https://github.com/org/repo.git
        domain = repo_url.split('@')[1].split(':')[0]
        path = repo_url.split(':')[1]
        repo_url = f"https://{domain}/{path}"
        logger.info(f"Converted SSH URL to HTTPS: {repo_url}")
    
    # Apply token to URL if available
    auth_url = repo_url
    if token:
        # Format: https://{token}@github.com/org/repo.git
        auth_url = repo_url.replace("https://", f"https://{token}@")
        logger.info(f"Using token authentication for {repo_name}")
    else:
        logger.info(f"No token found for {repo_name}, using public access")
    
    try:
        if target.exists():
            logger.info(f"Updating repository: {repo_name}")
            repo = Repo(target)
            
            # Update remote URL with token if available
            repo.remotes.origin.set_url(auth_url)
            
            # Update repository
            repo.remotes.origin.fetch()
            repo.git.checkout(branch)
            repo.git.reset("--hard", f"origin/{branch}")
            logger.info(f"Updated {repo_name} to {branch}")
                
        else:
            logger.info(f"Cloning repository: {repo_name}")
            
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
        raise GitError(f"Unexpected error: {e}")
```

### Scanner Module Changes

Update `scanner.py` to pass the repository name:

```python
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
        # Update repository with auth support
        repo_dir = clone_or_update_repository(repo_url, repo_name, branch, base_dir)
        
        # Run scanner
        success = run_sonar_scanner(
            repo_dir, sonar_config["url"], sonar_config["token"], 
            repo_name, branch
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
```

### Logging Enhancements

Add a utility function to mask tokens in logs:

```python
def mask_token_in_url(url):
    """Mask token in URL for logging purposes."""
    if "@" in url and "://" in url:
        protocol = url.split("://")[0]
        auth_part = url.split("://")[1].split("@")[0]
        rest = url.split("://")[1].split("@")[1]
        return f"{protocol}://***@{rest}"
    return url
```

### README Updates

The README.md file will need to be updated to remove SSH instructions and add token authentication instructions:

```markdown
## Repository Access Setup

The scanner supports both public and private repositories:

### Public Repositories

For public repositories, you use HTTPS URLs in your configuration:
```yaml
repositories:
  - name: "public-repo"
    url: "https://github.com/organization/repository.git"
    branches: ["main"]
```

### Private Repositories

For private repositories, you need to use a personal access token set as an environment variable:

1. Generate a personal access token in GitHub:
   - Go to GitHub Settings → Developer settings → Personal access tokens
   - Generate a new token with `repo` scope
   - Copy the token

2. Set the token as an environment variable using the naming convention:
   ```bash
   export GIT_TOKEN_REPOSITORY_NAME=ghp_xxxxxxxxxxxx
   ```

   For example, if your repository is named "private-repo" in your configuration:
   ```bash
   export GIT_TOKEN_PRIVATE_REPO=ghp_xxxxxxxxxxxx
   ```

3. Configure your repository in the config.yaml file:
   ```yaml
   repositories:
     - name: "private-repo"
       url: "https://github.com/organization/private-repo.git"
       branches: ["main"]
   ```

4. For crontab setup, include the environment variable:
   ```
   0 0 * * * export GIT_TOKEN_PRIVATE_REPO=ghp_xxxxxxxxxxxx; export SONARQUBE_TOKEN=<replace with Global Scan Token>; PATH=$PATH:/usr/local/bin; $HOME/sonarqube-scanner/.venv/bin/sonarqube-scanner -c $HOME/sonarqube-scanner/config.yaml > $HOME/sonarqube_scanner_last_run.log 2>&1
   ```
```

## Security Considerations

1. **Token Storage**:
   - Tokens are stored only in environment variables
   - No tokens in configuration files
   - Mask tokens in logs

2. **URL Handling**:
   - When logging URLs, tokens should be masked
   - Example: `https://***@github.com/org/repo.git`

3. **Error Handling**:
   - Authentication errors should not expose tokens in error messages

## Testing Plan

1. **Unit Tests**:
   - Test environment variable loading
   - Test URL transformation with tokens
   - Test token masking in logs
   - Test SSH to HTTPS URL conversion

2. **Integration Tests**:
   - Test cloning private repositories with token authentication
   - Test updating private repositories with token authentication
   - Test converting existing SSH repositories to HTTPS with tokens

3. **Manual Tests**:
   - Verify scanning of private repositories works end-to-end
   - Verify tokens are not exposed in logs

## Implementation Timeline

1. **Day 1**: Implement Git module changes and environment variable handling
2. **Day 2**: Implement logging enhancements and testing
3. **Day 3**: Update documentation and perform integration testing
4. **Day 4**: Address feedback and finalize implementation

## Conclusion

This design outlines the approach for implementing token-based authentication for private repositories in the SonarQube Scanner, with tokens loaded exclusively from environment variables. The implementation will enhance the tool's capabilities while maintaining security best practices for token handling.