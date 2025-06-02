"""Command-line interface for fixturecheck."""

from pathlib import Path
from typing import Any, Dict

import click

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
@click.option(
    "--verbose",
    "-v",
    count=True,
    help="Verbose output. Use -v for details, -vv for full details including validators",
)
def report(path: str, pattern: str, verbose: int):
    """Generate a report of fixture check opportunities and current usage."""
    test_path = Path(path)
    test_files = find_test_files(test_path, pattern)

    plugin = FixtureCheckPlugin()
    opportunities = 0
    existing_checks = 0

    if verbose > 0:
        click.echo("FIXTURE CHECK REPORT")
        click.echo("=" * 50)

    for test_file in test_files:
        with open(test_file) as f:
            content = f.read()

        if verbose > 0:
            # Get detailed fixture information
            opportunities_details = plugin.get_opportunities_details(content, str(test_file))
            existing_details = plugin.get_existing_checks_details(content, str(test_file))

            if opportunities_details or existing_details:
                click.echo(f"\nFile: {test_file}")
                click.echo("-" * 40)

                if opportunities_details:
                    click.echo("\nOpportunities for fixture checks:")
                    for detail in opportunities_details:
                        _print_fixture_detail(detail, verbose)

                if existing_details:
                    click.echo("\nExisting fixture checks:")
                    for detail in existing_details:
                        _print_fixture_detail(detail, verbose)

        # Count opportunities (fixtures without checks)
        opportunities += plugin.count_opportunities(content)
        # Count existing checks
        existing_checks += plugin.count_existing_checks(content)

    if verbose > 0:
        click.echo("\n" + "=" * 50)

    click.echo(f"Found {opportunities} opportunities for fixture checks")
    click.echo(f"Found {existing_checks} existing fixture checks")


def _print_fixture_detail(detail: Dict[str, Any], verbose: int):
    """Print detailed fixture information based on verbosity level."""
    click.echo(f"  Line {detail['line_number']}: {detail['name']}")

    if detail.get("params"):
        click.echo(f"    Parameters: {', '.join(detail['params'])}")

    if verbose >= 2 and detail.get("validator"):
        click.echo(f"    Validator: {detail['validator']}")

    click.echo("    " + "-" * 30)


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
