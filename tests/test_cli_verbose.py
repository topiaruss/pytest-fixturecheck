"""Tests for the CLI verbose functionality."""

import tempfile
from pathlib import Path

from click.testing import CliRunner

from pytest_fixturecheck.cli import fixturecheck


class TestVerboseReport:
    """Test the verbose options for the report command."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

        # Sample test content with various fixture types
        self.test_content = '''"""Test file with various fixtures."""

import pytest
from pytest_fixturecheck import fixturecheck


def validate_user(obj, is_collection_phase=False):
    """Custom validator function."""
    if is_collection_phase:
        return
    if not hasattr(obj, 'name'):
        raise AttributeError("User must have name")


@pytest.fixture
def simple_fixture():
    """A simple fixture without fixturecheck."""
    return "test"


@pytest.fixture
@fixturecheck()
def checked_fixture():
    """A fixture with default fixturecheck."""
    return {"name": "test"}


@pytest.fixture
@fixturecheck(validate_user)
def validated_fixture(simple_fixture):
    """A fixture with custom validator."""
    return {"name": simple_fixture}


@pytest.fixture
@fixturecheck(validate_user, expect_validation_error=True)
def expected_failure_fixture():
    """A fixture expected to fail."""
    return {}  # Missing name attribute
'''

    def test_report_without_verbose(self):
        """Test basic report without verbose flag."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test_example.py"
            test_file.write_text(self.test_content)

            result = self.runner.invoke(fixturecheck, ["report", "--path", tmpdir])

            assert result.exit_code == 0
            assert "Found 1 opportunities for fixture checks" in result.output
            assert "Found 3 existing fixture checks" in result.output
            # Should not contain verbose headers
            assert "FIXTURE CHECK REPORT" not in result.output
            assert "File:" not in result.output

    def test_report_with_single_verbose(self):
        """Test report with single -v flag."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test_example.py"
            test_file.write_text(self.test_content)

            result = self.runner.invoke(fixturecheck, ["report", "-v", "--path", tmpdir])

            assert result.exit_code == 0

            # Should contain verbose headers
            assert "FIXTURE CHECK REPORT" in result.output
            assert "File: " in result.output
            assert "test_example.py" in result.output

            # Should show opportunities
            assert "Opportunities for fixture checks:" in result.output
            assert "Line 16: simple_fixture" in result.output

            # Should show existing checks
            assert "Existing fixture checks:" in result.output
            assert "Line 23: checked_fixture" in result.output
            assert "Line 30: validated_fixture" in result.output
            assert "Parameters: simple_fixture" in result.output
            assert "Line 37: expected_failure_fixture" in result.output

            # Should NOT show validators with single -v
            assert "Validator:" not in result.output

            # Should show summary
            assert "Found 1 opportunities for fixture checks" in result.output
            assert "Found 3 existing fixture checks" in result.output

    def test_report_with_double_verbose(self):
        """Test report with double -v flag (-vv)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test_example.py"
            test_file.write_text(self.test_content)

            result = self.runner.invoke(fixturecheck, ["report", "-vv", "--path", tmpdir])

            assert result.exit_code == 0

            # Should contain all verbose content from single -v
            assert "FIXTURE CHECK REPORT" in result.output
            assert "File: " in result.output
            assert "Line 23: checked_fixture" in result.output
            assert "Line 30: validated_fixture" in result.output
            assert "Parameters: simple_fixture" in result.output

            # Should ALSO show validators with -vv
            assert "Validator: Default validator" in result.output
            assert "Validator: validate_user" in result.output

    def test_verbose_with_no_fixtures(self):
        """Test verbose output when no fixtures are found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test_empty.py"
            test_file.write_text('"""Empty test file."""\n\ndef test_something():\n    pass\n')

            result = self.runner.invoke(fixturecheck, ["report", "-v", "--path", tmpdir])

            assert result.exit_code == 0
            assert "FIXTURE CHECK REPORT" in result.output
            assert "Found 0 opportunities for fixture checks" in result.output
            assert "Found 0 existing fixture checks" in result.output
            # Should not show file details since no fixtures
            assert "test_empty.py" not in result.output

    def test_verbose_with_complex_validator(self):
        """Test verbose output with complex validator expressions."""
        complex_content = '''"""Test with complex validators."""

import pytest
from pytest_fixturecheck import fixturecheck


@pytest.fixture
@fixturecheck(lambda obj, phase: None)
def lambda_fixture():
    return "test"


@pytest.fixture  
@fixturecheck(validate_user.with_config(strict=True))
def complex_validator_fixture():
    return "test"
'''

        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test_complex.py"
            test_file.write_text(complex_content)

            result = self.runner.invoke(fixturecheck, ["report", "-vv", "--path", tmpdir])

            assert result.exit_code == 0
            assert "Validator:" in result.output

    def test_verbose_multiple_files(self):
        """Test verbose output with multiple test files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # First file
            test_file1 = Path(tmpdir) / "test_file1.py"
            test_file1.write_text("""
import pytest
from pytest_fixturecheck import fixturecheck

@pytest.fixture
def fixture1():
    return "test1"

@pytest.fixture
@fixturecheck()
def checked1():
    return "checked1"
""")

            # Second file
            test_file2 = Path(tmpdir) / "test_file2.py"
            test_file2.write_text("""
import pytest
from pytest_fixturecheck import fixturecheck

@pytest.fixture
def fixture2():
    return "test2"

@pytest.fixture
@fixturecheck()
def checked2():
    return "checked2"
""")

            result = self.runner.invoke(fixturecheck, ["report", "-v", "--path", tmpdir])

            assert result.exit_code == 0
            assert "test_file1.py" in result.output
            assert "test_file2.py" in result.output
            assert "Line 6: fixture1" in result.output
            assert "Line 11: checked1" in result.output
            assert "Line 6: fixture2" in result.output
            assert "Line 11: checked2" in result.output
            assert "Found 2 opportunities for fixture checks" in result.output
            assert "Found 2 existing fixture checks" in result.output

    def test_verbose_with_fixture_parameters(self):
        """Test verbose output shows fixture parameters correctly."""
        param_content = """
import pytest
from pytest_fixturecheck import fixturecheck

@pytest.fixture
def dependency1():
    return "dep1"

@pytest.fixture
def dependency2():
    return "dep2"

@pytest.fixture
def multi_param_fixture(dependency1, dependency2, request):
    return f"{dependency1}-{dependency2}"

@pytest.fixture
@fixturecheck()
def checked_with_params(dependency1, dependency2):
    return f"checked-{dependency1}-{dependency2}"
"""

        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test_params.py"
            test_file.write_text(param_content)

            result = self.runner.invoke(fixturecheck, ["report", "-v", "--path", tmpdir])

            assert result.exit_code == 0
            assert "Parameters: dependency1, dependency2, request" in result.output
            assert "Parameters: dependency1, dependency2" in result.output

    def test_verbose_separator_lines(self):
        """Test that verbose output includes proper separator lines."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test_separators.py"
            test_file.write_text(self.test_content)

            result = self.runner.invoke(fixturecheck, ["report", "-v", "--path", tmpdir])

            assert result.exit_code == 0
            # Should have multiple separator lines
            separator_count = result.output.count("------------------------------")
            assert separator_count >= 4  # At least one per fixture shown

            # Should have file separator
            assert "----------------------------------------" in result.output

    def test_count_flag_compatibility(self):
        """Test that -v count flag works correctly (click count=True)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test_count.py"
            test_file.write_text(self.test_content)

            # Test different ways to specify verbose levels
            result1 = self.runner.invoke(fixturecheck, ["report", "-v", "--path", tmpdir])
            result2 = self.runner.invoke(fixturecheck, ["report", "-vv", "--path", tmpdir])

            assert result1.exit_code == 0
            assert result2.exit_code == 0

            # -v should not show validators
            assert "Validator:" not in result1.output
            # -vv should show validators
            assert "Validator:" in result2.output


class TestVerboseHelp:
    """Test the help text for verbose options."""

    def test_help_shows_verbose_option(self):
        """Test that help shows the verbose option."""
        runner = CliRunner()
        result = runner.invoke(fixturecheck, ["report", "--help"])

        assert result.exit_code == 0
        assert "-v, --verbose" in result.output
        assert "Verbose output" in result.output
        assert "including validators" in result.output
