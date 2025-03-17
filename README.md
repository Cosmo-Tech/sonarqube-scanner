# SonarQube Scanner

A simple Python tool to scan GitHub repositories with SonarQube.


## Requirements

- Python 3.8+
- SonarQube scanner CLI installed and available in PATH
- Git installed
- Access to GitHub repositories
- SonarQube server (Community Edition)

## Installation

Using uv:

```bash
uv pip install -e .
```

## Configuration

Edit the `config.yaml` file to specify:

1. SonarQube server URL and token
2. List of repositories to scan with their branches

Example configuration:

```yaml
# SonarQube server configuration
sonarqube:
  url: "http://localhost:9000"
  token: "your-sonarqube-token"

# Repositories to scan
repositories:
  - name: "repo1"
    url: "https://github.com/organization/repo1.git"
    branches: ["main"]
    project_key: "org:repo1"
    
  - name: "repo2"
    url: "https://github.com/organization/repo2.git"
    branches: ["main"]
    project_key: "org:repo2"
```

## Usage

Run the scanner:

```bash
sonar-scan
```

## Future Enhancements

- Scheduling capabilities
- Parallel scanning
- Result reporting and notifications
- Integration with CI/CD systems