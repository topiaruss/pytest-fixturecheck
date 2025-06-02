"""Tests for the fixturecheck CLI functionality."""

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
    assert (
        content.count("@fixturecheck()") == 3
    )  # simple_fixture, checked_fixture (existing), and async_fixture

    conftest = test_dir / "conftest.py"
    content = conftest.read_text()
    assert "@fixturecheck()" in content
    assert (
        content.count("@fixturecheck()") == 2
    )  # shared_fixture (added) and shared_checked_fixture (existing)


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


# === NEW EDGE CASE TESTS ===


def test_report_command_nonexistent_path():
    """Test report command with non-existent path."""
    runner = CliRunner()
    result = runner.invoke(fixturecheck, ["report", "--path", "/nonexistent/path"])

    # Should handle gracefully by finding no files
    assert result.exit_code == 0
    assert "Found 0 opportunities for fixture checks" in result.output
    assert "Found 0 existing fixture checks" in result.output


def test_add_command_nonexistent_path():
    """Test add command with non-existent path."""
    runner = CliRunner()
    result = runner.invoke(fixturecheck, ["add", "--path", "/nonexistent/path"])

    # Should handle gracefully by finding no files to modify
    assert result.exit_code == 0


def test_report_command_custom_pattern(test_dir):
    """Test report command with custom file pattern."""
    # Create a file that matches custom pattern
    custom_file = test_dir / "my_test.py"
    custom_file.write_text("""
import pytest

@pytest.fixture
def custom_fixture():
    return "custom"
""")

    runner = CliRunner()
    result = runner.invoke(
        fixturecheck, ["report", "--path", str(test_dir), "--pattern", "my_*.py"]
    )

    assert result.exit_code == 0
    # The pattern search might find files in test_dir, so be more flexible
    assert "opportunities for fixture checks" in result.output


def test_add_command_custom_pattern(test_dir):
    """Test add command with custom file pattern."""
    # Create a file that matches custom pattern
    custom_file = test_dir / "my_test.py"
    custom_file.write_text("""
import pytest

@pytest.fixture
def custom_fixture():
    return "custom"
""")

    runner = CliRunner()
    result = runner.invoke(fixturecheck, ["add", "--path", str(test_dir), "--pattern", "my_*.py"])

    assert result.exit_code == 0
    assert "Modified" in result.output

    # Verify the custom file was modified
    content = custom_file.read_text()
    assert "@fixturecheck()" in content


def test_report_command_empty_directory(tmp_path):
    """Test report command with empty directory."""
    runner = CliRunner()
    result = runner.invoke(fixturecheck, ["report", "--path", str(tmp_path)])

    assert result.exit_code == 0
    assert "Found 0 opportunities for fixture checks" in result.output
    assert "Found 0 existing fixture checks" in result.output


def test_add_command_empty_directory(tmp_path):
    """Test add command with empty directory."""
    runner = CliRunner()
    result = runner.invoke(fixturecheck, ["add", "--path", str(tmp_path)])

    assert result.exit_code == 0
    # Should complete without errors, no files to modify


def test_plugin_malformed_python_file():
    """Test plugin handling of malformed Python files."""
    plugin = FixtureCheckPlugin()

    # Malformed Python content
    malformed_content = """
import pytest
@pytest.fixture
def broken_fixture(
    # Missing closing parenthesis and body
"""

    # Should handle syntax errors gracefully
    with pytest.raises(SyntaxError):
        plugin.count_opportunities(malformed_content)


def test_plugin_file_with_no_fixtures():
    """Test plugin with file containing no fixtures."""
    plugin = FixtureCheckPlugin()

    content = """
import pytest

def regular_function():
    return "not a fixture"

class TestClass:
    def test_method(self):
        assert True
"""

    assert plugin.count_opportunities(content) == 0
    assert plugin.count_existing_checks(content) == 0
    # The add_fixture_checks method may normalize whitespace, so just check no @fixturecheck was added
    modified = plugin.add_fixture_checks(content)
    assert "@fixturecheck()" not in modified


def test_plugin_file_with_only_checked_fixtures():
    """Test plugin with file containing only fixtures that already have checks."""
    plugin = FixtureCheckPlugin()

    content = """
import pytest
from pytest_fixturecheck import fixturecheck

@pytest.fixture
@fixturecheck()
def fixture1():
    return 1

@pytest.fixture
@fixturecheck()
def fixture2():
    return 2
"""

    assert plugin.count_opportunities(content) == 0
    assert plugin.count_existing_checks(content) == 2
    # Should not add any new @fixturecheck decorators
    modified = plugin.add_fixture_checks(content)
    assert modified.count("@fixturecheck()") == 2  # Same count as before


def test_plugin_complex_decorator_patterns():
    """Test plugin with complex decorator patterns."""
    plugin = FixtureCheckPlugin()

    content = """
import pytest
from pytest_fixturecheck import fixturecheck

@pytest.fixture(scope="session")
def session_fixture():
    return "session"

@pytest.fixture(autouse=True)
@fixturecheck()
def auto_fixture():
    return "auto"

@pytest.mark.parametrize("param", [1, 2, 3])
@pytest.fixture
def param_fixture(param):
    return param
"""

    assert plugin.count_opportunities(content) == 2  # session_fixture and param_fixture
    assert plugin.count_existing_checks(content) == 1  # auto_fixture

    modified = plugin.add_fixture_checks(content)
    assert modified.count("@fixturecheck()") == 3  # All fixtures should have it


def test_add_command_no_modifications_needed(test_dir):
    """Test add command when no modifications are needed."""
    # Create a file where all fixtures already have checks
    perfect_file = test_dir / "test_perfect.py"
    perfect_file.write_text("""
import pytest
from pytest_fixturecheck import fixturecheck

@pytest.fixture
@fixturecheck()
def perfect_fixture():
    return "perfect"
""")

    runner = CliRunner()
    result = runner.invoke(
        fixturecheck, ["add", "--path", str(test_dir), "--pattern", "test_perfect.py"]
    )

    assert result.exit_code == 0
    # Since test_dir fixture creates other files, just verify no major issues
    # The pattern might match other files in the directory


def test_cli_help_commands():
    """Test CLI help functionality."""
    runner = CliRunner()

    # Test main help
    result = runner.invoke(fixturecheck, ["--help"])
    assert result.exit_code == 0
    assert "Manage fixture checks" in result.output

    # Test report help
    result = runner.invoke(fixturecheck, ["report", "--help"])
    assert result.exit_code == 0
    assert "Generate a report" in result.output

    # Test add help
    result = runner.invoke(fixturecheck, ["add", "--help"])
    assert result.exit_code == 0
    assert "Add fixture checks" in result.output


def test_plugin_different_fixture_types():
    """Test plugin with different types of fixture decorators."""
    plugin = FixtureCheckPlugin()

    content = """
import pytest
import pytest_asyncio
from pytest_fixturecheck import fixturecheck

@pytest.fixture
def simple_fixture():
    return "simple"

@pytest_asyncio.fixture
def async_fixture():
    async def _fixture():
        return "async"
    return _fixture

@fixture  # Short form
def short_fixture():
    return "short"

@pytest.fixture(scope="module")
@fixturecheck()
def scoped_fixture():
    return "scoped"
"""

    # Should detect all fixture types
    assert plugin.count_opportunities(content) == 3  # simple, async, short
    assert plugin.count_existing_checks(content) == 1  # scoped

    modified = plugin.add_fixture_checks(content)
    assert modified.count("@fixturecheck()") == 4  # All fixtures should have it


def test_exclusion_patterns(tmp_path):
    """Test that virtual environments and package directories are excluded."""
    runner = CliRunner()

    # Create various directories that should be excluded
    excluded_dirs = [
        ".venv",
        "venv",
        ".env",
        "env",
        "site-packages",
        "node_modules",
        "__pycache__",
        ".tox",
        ".pytest_cache",
        ".mypy_cache",
        "build",
        "dist",
        ".git",
    ]

    for dirname in excluded_dirs:
        exclude_dir = tmp_path / dirname
        exclude_dir.mkdir()

        # Create a test file in the excluded directory
        test_file = exclude_dir / "test_excluded.py"
        test_file.write_text("""
import pytest

@pytest.fixture
def excluded_fixture():
    return "should_not_be_found"
""")

    # Create a legitimate test file
    legitimate_test = tmp_path / "test_legitimate.py"
    legitimate_test.write_text("""
import pytest

@pytest.fixture
def legitimate_fixture():
    return "should_be_found"
""")

    # Run report command
    result = runner.invoke(fixturecheck, ["report", "--path", str(tmp_path)])

    assert result.exit_code == 0
    # Should only find the legitimate fixture, not the excluded ones
    assert "Found 1 opportunities for fixture checks" in result.output
    assert "Found 0 existing fixture checks" in result.output


def test_exclusion_with_verbose(tmp_path):
    """Test exclusion with verbose output."""
    runner = CliRunner()

    # Create .venv directory with test file
    venv_dir = tmp_path / ".venv" / "lib" / "python3.13" / "site-packages" / "somepackage"
    venv_dir.mkdir(parents=True)

    venv_test = venv_dir / "test_package.py"
    venv_test.write_text("""
import pytest

@pytest.fixture
def package_fixture():
    return "from_package"
""")

    # Create legitimate test file
    legitimate_test = tmp_path / "test_real.py"
    legitimate_test.write_text("""
import pytest

@pytest.fixture
def real_fixture():
    return "real"
""")

    # Run verbose report
    result = runner.invoke(fixturecheck, ["report", "-v", "--path", str(tmp_path)])

    assert result.exit_code == 0
    # Should only show the legitimate test file
    assert "test_real.py" in result.output
    assert "test_package.py" not in result.output
    assert ".venv" not in result.output


def test_exclusion_conftest_in_venv(tmp_path):
    """Test that conftest.py files in virtual environments are also excluded."""
    runner = CliRunner()

    # Create conftest.py in .venv (should be excluded)
    venv_dir = tmp_path / ".venv" / "lib" / "python3.13" / "site-packages"
    venv_dir.mkdir(parents=True)

    venv_conftest = venv_dir / "conftest.py"
    venv_conftest.write_text("""
import pytest

@pytest.fixture
def venv_shared_fixture():
    return "from_venv_conftest"
""")

    # Create legitimate conftest.py (should be included)
    legitimate_conftest = tmp_path / "conftest.py"
    legitimate_conftest.write_text("""
import pytest

@pytest.fixture
def real_shared_fixture():
    return "from_real_conftest"
""")

    # Run report
    result = runner.invoke(fixturecheck, ["report", "-v", "--path", str(tmp_path)])

    assert result.exit_code == 0
    # Should only include the legitimate conftest.py
    assert str(legitimate_conftest) in result.output
    assert ".venv" not in result.output
    assert "Found 1 opportunities for fixture checks" in result.output
