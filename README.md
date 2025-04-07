# SonarQube Scanner

A Python tool to scan GitHub repositories with SonarQube.

## Requirements

- Python 3.8+
- SonarQube scanner CLI installed and available in PATH
- SonarQube server (Community Edition)
- Git installed
- Access to GitHub repositories (see next section)

## Repository Access Setup

The scanner supports both HTTPS and SSH URLs for repository access:

### Public Repositories

For public repositories, you use HTTPS URLs in your configuration:
```yaml
repositories:
  - url: https://github.com/organization/repository.git
    branch: main
```

### Private Repositories

For private repositories, use SSH URLs and set up SSH access:

1. Generate an SSH key in the VM where the scanner is installed, e.g:
```bash
ssh-keygen -t ed25519 -f ~/.ssh/scanner -C "sonarqube-scanner@cosmotech.com"
```

2. Configure the SSH agent:
```bash
eval $(ssh-agent -s)
ssh-add ~/.ssh/scanner
```

3. Display the public key:
```bash
cat ~/.ssh/scanner.pub
```

4. Add the deploy key to each private repository:
   - Go to repository Settings → Deploy keys → Add deploy key
   - Give it a title (e.g., "SonarQube Scanner")
   - Paste your public key
   - Click "Add key"


## Installation and Setup

```bash
uv venv
uv pip install .
```

Adapt the `config.yaml` file if necessary.

Configure crontab by running `crontab -e` and adapting the code:

```
0 0 * * * eval $(ssh-agent -s) > /dev/null && ssh-add ~/.ssh/scanner > /dev/null 2>&1 && export SONARQUBE_TOKEN=<replace with Global Scan Token>; PATH=$PATH:/usr/local/bin; $HOME/sonarqube-scanner/.venv/bin/sonarqube-scanner -c $HOME/sonarqube-scanner/config.yaml > $HOME/sonarqube_scanner_last_run.log 2>&1
```