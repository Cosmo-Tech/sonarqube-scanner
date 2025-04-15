# SonarQube Scanner

A Python tool to scan GitHub and Bitbucket Server repositories with SonarQube.

## Requirements

- Python 3.8+
- SonarQube scanner CLI installed and available in PATH
- SonarQube server (Community Edition)
- Git installed
- Access to GitHub or Bitbucket Server repositories (see next section)

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

#### For GitHub
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

### Bitbucket Server Repositories

For private Bitbucket Server repositories, you need to use authentication:

1. Create a Personal Access Token in Bitbucket Server:
  - Go to your Bitbucket Server profile → Personal access tokens
  - Generate a new token with appropriate permissions
  - Copy the token

2. Set the token as an environment variable using the naming convention:
  ```bash
  export BITBUCKET_TOKEN_REPOSITORY_NAME=username:token
  ```

  Note: The token format should be `username:token` for Bitbucket Server authentication. If the user name contains special characters then you should URL-encode it, e.g. `first.last@company.com:token` should become `first.last%40company.com:token`


## Installation and Setup

```bash
uv venv
uv pip install .
```

Adapt the `config.yaml` file if necessary.

Prepare a script `scan.sh` by modifying the example:

```shell
#!/bin/bash
set -ex
export BITBUCKET_TOKEN_REPO_1=first.last%40company.com:BITBUCKET_TOKEN
export GIT_TOKEN_REPO_2=GITHUB_PAT
export SONARQUBE_TOKEN=SQ_TOKEN
cd /home/terminator/sonarqube-scanner
. .venv/bin/activate
sonarqube-scanner --verbose
```

Configure crontab by running `crontab -e` and addapting:

```
0 0 * * * PATH=$PATH:/usr/local/bin; scan.sh > sonarqube_scanner_last_run.log 2>&1
```