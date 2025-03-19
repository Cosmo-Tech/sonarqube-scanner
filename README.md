# SonarQube Scanner

A Python tool to scan GitHub repositories with SonarQube.


## Requirements

- Python 3.8+
- SonarQube scanner CLI installed and available in PATH
- Git installed
- Access to GitHub repositories
- SonarQube server (Community Edition)

## Installation and Setup

```bash
uv venv
uv pip install .
```

Adapt the `config.yaml` file if necessary.

Configure crontab by running `crontab -e` and adapting the code:

```
0 0 * * * export SONARQUBE_TOKEN=<replace with Global Scan Token>; PATH=$PATH:/usr/local/bin; $HOME/sonarqube-scanner/.venv/bin/sonarqube-scanner -c $HOME/sonarqube-scanner/config.yaml > $HOME/sonarqube_scanner_last_run.log 2&>1
```