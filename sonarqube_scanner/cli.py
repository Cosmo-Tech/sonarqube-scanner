"""
Command-line interface for the SonarQube Scanner.
"""

import logging
import sys
import click
from pathlib import Path

from .config import load_config
from .scanner import scan_repositories

# Configure logging
logger = logging.getLogger("sonarqube_scanner")


def setup_logging(verbose: bool):
    """Configure logging with appropriate level and format."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


@click.command(help="Scan Git repositories with SonarQube.")
@click.option(
    "-c",
    "--config",
    default="config.yaml",
    show_default=True,
    help="Configuration file path",
)
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose output")
@click.option(
    "-o",
    "--output-dir",
    type=click.Path(),
    help="Repository clone directory (default: ~/temp)",
)
@click.option("-t", "--token", help="SonarQube token (overrides config/env)")
@click.option("-r", "--repo", multiple=True, help="Scan specific repositories only")
def main(config, verbose, output_dir, token, repo):
    """Run SonarQube scans on configured repositories."""
    try:
        # Setup logging
        setup_logging(verbose)

        # Setup output directory
        base_dir = Path(output_dir) if output_dir else Path.home() / "temp"
        base_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Using output directory: {base_dir}")

        # Load and process configuration
        logger.info(f"Loading configuration: {config}")
        config_data = load_config(config)

        if token:
            config_data["sonarqube"]["token"] = token

        if repo:
            # Filter repositories
            repos = config_data["repositories"]
            filtered = [r for r in repos if r["name"] in repo]

            if not filtered:
                logger.error(f"No matching repositories: {', '.join(repo)}")
                return 1

            logger.info(f"Scanning {len(filtered)} repositories")
            config_data["repositories"] = filtered

        # Run scans
        scan_repositories(config_data, base_dir)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        if verbose:
            logger.exception("Details:")
        return 1


if __name__ == "__main__":
    sys.exit(main())
