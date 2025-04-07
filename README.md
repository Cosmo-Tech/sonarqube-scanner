# SonarQube Scanner

A Python tool to scan GitHub repositories with SonarQube.

## Requirements

- Python 3.8+
- SonarQube scanner CLI installed and available in PATH
- SonarQube server (Community Edition)
- Git installed
- Access to GitHub repositories (see next section)

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


## Installation and Setup

```bash
uv venv
uv pip install .
```

Adapt the `config.yaml` file if necessary.

Configure crontab by running `crontab -e` and adapting the code:

```
0 0 * * * export GIT_TOKEN_REPO1=ghp_xxxxxxxxxxxx && export GIT_TOKEN_REPO2=ghp_xxxxxxxxxxxx && export SONARQUBE_TOKEN=<replace with Global Scan Token>; PATH=$PATH:/usr/local/bin; $HOME/sonarqube-scanner/.venv/bin/sonarqube-scanner -c $HOME/sonarqube-scanner/config.yaml > $HOME/sonarqube_scanner_last_run.log 2>&1
```

Replace `GIT_TOKEN_REPO1` and `GIT_TOKEN_REPO2` with your actual repository names and tokens.