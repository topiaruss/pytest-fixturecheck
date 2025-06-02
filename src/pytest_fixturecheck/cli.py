"""Command-line interface for fixturecheck."""

import click
from pathlib import Path
from typing import List, Optional

from .plugin import FixtureCheckPlugin
from .utils import find_test_files


@click.group()
def fixturecheck():
    """Manage fixture checks in your pytest test suite."""
    pass


@fixturecheck.command()
@click.option(
    "--path",
    "-p",
    default=".",
    help="Path to search for test files (default: current directory)",
)
@click.option(
    "--pattern",
    "-P",
    default="test_*.py",
    help="Pattern to match test files (default: test_*.py)",
)
def report(path: str, pattern: str):
    """Generate a report of fixture check opportunities and current usage."""
    test_path = Path(path)
    test_files = find_test_files(test_path, pattern)
    
    plugin = FixtureCheckPlugin()
    opportunities = 0
    existing_checks = 0
    
    for test_file in test_files:
        with open(test_file) as f:
            content = f.read()
            # Count opportunities (fixtures without checks)
            opportunities += plugin.count_opportunities(content)
            # Count existing checks
            existing_checks += plugin.count_existing_checks(content)
    
    click.echo(f"Found {opportunities} opportunities for fixture checks")
    click.echo(f"Found {existing_checks} existing fixture checks")


@fixturecheck.command()
@click.option(
    "--path",
    "-p",
    default=".",
    help="Path to search for test files (default: current directory)",
)
@click.option(
    "--pattern",
    "-P",
    default="test_*.py",
    help="Pattern to match test files (default: test_*.py)",
)
@click.option(
    "--dry-run",
    "-d",
    is_flag=True,
    help="Show what would be added without making changes",
)
def add(path: str, pattern: str, dry_run: bool):
    """Add fixture checks to test files."""
    test_path = Path(path)
    test_files = find_test_files(test_path, pattern)
    
    plugin = FixtureCheckPlugin()
    
    for test_file in test_files:
        with open(test_file) as f:
            content = f.read()
        
        modified_content = plugin.add_fixture_checks(content)
        
        if modified_content != content:
            if dry_run:
                click.echo(f"Would modify {test_file}")
            else:
                with open(test_file, "w") as f:
                    f.write(modified_content)
                click.echo(f"Modified {test_file}")


if __name__ == "__main__":
    fixturecheck() 