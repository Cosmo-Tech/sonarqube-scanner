# SonarQube Scanner

A Python tool to scan GitHub repositories with SonarQube.


## Requirements

- Python 3.8+
- SonarQube scanner CLI installed and available in PATH
- Git installed
- Access to GitHub repositories
- SonarQube server (Community Edition)

## Installation

### Using uv

```bash
uv pip install -e .
```

## Configuration

Edit the `config.yaml` file to specify:

1. SonarQube server URL and token
2. List of repositories to scan with their branches

## Usage

### Command Line

Run the scanner with default configuration:

```bash
sonar-scan
```