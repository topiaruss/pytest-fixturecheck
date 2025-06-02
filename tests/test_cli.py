"""Tests for the fixturecheck CLI functionality."""

import os
from pathlib import Path
import pytest
from click.testing import CliRunner

from pytest_fixturecheck.cli import fixturecheck
from pytest_fixturecheck.plugin import FixtureCheckPlugin


@pytest.fixture
def test_dir(tmp_path):
    """Create a temporary directory with test files."""
    # Create a test file with fixtures
    test_file = tmp_path / "test_example.py"
    test_file.write_text("""
import pytest
from pytest_fixturecheck import fixturecheck

@pytest.fixture
def simple_fixture():
    return "test"

@pytest.fixture
@fixturecheck()
def checked_fixture():
    return "checked"

@pytest.fixture
def async_fixture():
    async def _fixture():
        return "async"
    return _fixture
""")

    # Create a conftest.py with fixtures
    conftest = tmp_path / "conftest.py"
    conftest.write_text("""
import pytest
from pytest_fixturecheck import fixturecheck

@pytest.fixture
def shared_fixture():
    return "shared"

@pytest.fixture
@fixturecheck()
def shared_checked_fixture():
    return "shared_checked"
""")

    return tmp_path


def test_report_command(test_dir):
    """Test the report command."""
    runner = CliRunner()
    result = runner.invoke(fixturecheck, ["report", "--path", str(test_dir)])
    
    assert result.exit_code == 0
    assert "Found 3 opportunities for fixture checks" in result.output
    assert "Found 2 existing fixture checks" in result.output


def test_add_command_dry_run(test_dir):
    """Test the add command in dry-run mode."""
    runner = CliRunner()
    result = runner.invoke(fixturecheck, ["add", "--path", str(test_dir), "--dry-run"])
    
    assert result.exit_code == 0
    assert "Would modify" in result.output
    assert "test_example.py" in result.output
    assert "conftest.py" in result.output


def test_add_command(test_dir):
    """Test the add command."""
    runner = CliRunner()
    result = runner.invoke(fixturecheck, ["add", "--path", str(test_dir)])
    
    assert result.exit_code == 0
    assert "Modified" in result.output
    
    # Verify the changes were made
    test_file = test_dir / "test_example.py"
    content = test_file.read_text()
    assert "@fixturecheck()" in content
    assert content.count("@fixturecheck()") == 3  # simple_fixture, checked_fixture (existing), and async_fixture
    
    conftest = test_dir / "conftest.py"
    content = conftest.read_text()
    assert "@fixturecheck()" in content
    assert content.count("@fixturecheck()") == 2  # shared_fixture (added) and shared_checked_fixture (existing)


def test_plugin_count_opportunities():
    """Test the plugin's opportunity counting."""
    plugin = FixtureCheckPlugin()
    
    content = """
import pytest

@pytest.fixture
def fixture1():
    return 1

@pytest.fixture
@fixturecheck()
def fixture2():
    return 2

@pytest.fixture
def fixture3():
    return 3
"""
    assert plugin.count_opportunities(content) == 2  # fixture1 and fixture3


def test_plugin_count_existing_checks():
    """Test the plugin's existing check counting."""
    plugin = FixtureCheckPlugin()
    
    content = """
import pytest

@pytest.fixture
def fixture1():
    return 1

@pytest.fixture
@fixturecheck()
def fixture2():
    return 2

@pytest.fixture
@fixturecheck()
def fixture3():
    return 3
"""
    assert plugin.count_existing_checks(content) == 2  # fixture2 and fixture3


def test_plugin_add_fixture_checks():
    """Test the plugin's fixture check addition."""
    plugin = FixtureCheckPlugin()
    
    content = """
import pytest

@pytest.fixture
def fixture1():
    return 1

@pytest.fixture
@fixturecheck()
def fixture2():
    return 2

@pytest.fixture
def fixture3():
    return 3
"""
    modified = plugin.add_fixture_checks(content)
    assert modified.count("@fixturecheck()") == 3  # All fixtures should have it
    assert "@fixturecheck()" in modified
    assert "fixture1" in modified
    assert "fixture2" in modified
    assert "fixture3" in modified 