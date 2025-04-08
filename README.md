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

### GitHub Private Repositories

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

### Bitbucket Server Repositories

The scanner also supports Bitbucket Server repositories:

#### Public Repositories

For public Bitbucket Server repositories, use HTTPS URLs in your configuration:
```yaml
repositories:
 - name: "bitbucket-repo"
   url: "https://bitbucket.example.com/scm/project/repository.git"
   branches: ["main"]
```

#### Private Repositories

For private Bitbucket Server repositories, you need to use authentication:

1. Create a Personal Access Token in Bitbucket Server:
  - Go to your Bitbucket Server profile → Personal access tokens
  - Generate a new token with appropriate permissions
  - Copy the token

2. Set the token as an environment variable using the naming convention:
  ```bash
  export BITBUCKET_TOKEN_REPOSITORY_NAME=username:token
  ```

  For example, if your repository is named "bitbucket-repo" in your configuration:
  ```bash
  export BITBUCKET_TOKEN_BITBUCKET_REPO=username:token
  ```

  Note: The token format should be `username:token` for Bitbucket Server authentication.

3. Configure your repository in the config.yaml file:
  ```yaml
  repositories:
    - name: "bitbucket-repo"
      url: "https://bitbucket.example.com/scm/project/repository.git"
      branches: ["main"]
  ```

You can also set a global Bitbucket token that will be used for all Bitbucket repositories:
```bash
export BITBUCKET_TOKEN=username:token
```


## Installation and Setup

```bash
uv venv
uv pip install .
```

Adapt the `config.yaml` file if necessary.

Configure crontab by running `crontab -e` and adapting the code:

```
0 0 * * * export GIT_TOKEN_REPO1=ghp_xxxxxxxxxxxx && export GIT_TOKEN_REPO2=ghp_xxxxxxxxxxxx && export BITBUCKET_TOKEN_REPO3=username:token && export SONARQUBE_TOKEN=<replace with Global Scan Token>; PATH=$PATH:/usr/local/bin; $HOME/sonarqube-scanner/.venv/bin/sonarqube-scanner -c $HOME/sonarqube-scanner/config.yaml > $HOME/sonarqube_scanner_last_run.log 2>&1
```
Replace `GIT_TOKEN_REPO1`, `GIT_TOKEN_REPO2`, and `BITBUCKET_TOKEN_REPO3` with your actual repository names and tokens.
Replace `GIT_TOKEN_REPO1` and `GIT_TOKEN_REPO2` with your actual repository names and tokens.