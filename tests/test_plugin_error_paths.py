"""Tests for plugin error paths and edge cases to improve coverage."""

from unittest.mock import Mock, patch

import pytest

from pytest_fixturecheck.plugin import (
    FixtureCheckPlugin,
    _mark_dependent_tests_for_skip,
    is_async_fixture,
    pytest_addoption,
    pytest_collection_finish,
    pytest_configure,
    pytest_fixture_setup,
    report_fixture_errors,
)


class TestPluginErrorPaths:
    """Test error handling paths in the plugin."""

    def test_pytest_addoption_coverage(self):
        """Test pytest_addoption function for coverage."""
        mock_parser = Mock()
        pytest_addoption(mock_parser)

        # Verify addini was called with correct parameters
        mock_parser.addini.assert_called_once_with(
            "fixturecheck-auto-skip",
            help="Automatically skip tests with invalid fixtures instead of failing",
            default="false",
            type="bool",
        )

    def test_pytest_configure_coverage(self):
        """Test pytest_configure function for coverage."""
        mock_config = Mock()
        pytest_configure(mock_config)

        # Verify addinivalue_line was called
        mock_config.addinivalue_line.assert_called_once_with(
            "markers", "fixturecheck: mark a test as using fixture validation"
        )

    def test_is_async_fixture_with_unittest_async(self):
        """Test is_async_fixture with unittest async fixture."""
        mock_fixturedef = Mock()
        mock_fixturedef.func = Mock()
        mock_fixturedef.argname = "regular_fixture"
        mock_fixturedef.unittest = "async fixture"

        # Should detect async via unittest attribute
        assert is_async_fixture(mock_fixturedef) == True

    def test_is_async_fixture_with_async_name_pattern(self):
        """Test is_async_fixture with async name pattern."""
        mock_fixturedef = Mock()
        mock_fixturedef.func = Mock()
        mock_fixturedef.argname = "async_test_fixture"

        # Should detect async via name pattern
        assert is_async_fixture(mock_fixturedef) == True

    def test_is_async_fixture_with_pytest_asyncio_scope(self):
        """Test is_async_fixture with pytest-asyncio scope attribute."""
        mock_fixturedef = Mock()
        mock_fixturedef.func = Mock()
        mock_fixturedef.argname = "regular_fixture"
        mock_fixturedef._pytest_asyncio_scope = "function"

        # Should detect async via pytest-asyncio attribute
        assert is_async_fixture(mock_fixturedef) == True

    def test_pytest_fixture_setup_with_wrapped_function(self):
        """Test pytest_fixture_setup with wrapped function."""
        mock_fixturedef = Mock()
        mock_request = Mock()
        mock_request.config = Mock()

        # Create a nested wrapper structure
        inner_func = Mock()
        inner_func._fixturecheck = True
        inner_func.__wrapped__ = None

        middle_func = Mock()
        middle_func._fixturecheck = False
        middle_func.__wrapped__ = inner_func

        outer_func = Mock()
        outer_func._fixturecheck = False
        outer_func.__wrapped__ = middle_func

        mock_fixturedef.func = outer_func

        pytest_fixture_setup(mock_fixturedef, mock_request)

        # Should detect the fixturecheck marker on the inner function
        assert hasattr(mock_request.config, "_fixturecheck_fixtures")

    def test_pytest_fixture_setup_async_fixture_skip(self):
        """Test pytest_fixture_setup with async fixture gets skip marker."""
        mock_fixturedef = Mock()
        mock_request = Mock()
        mock_request.config = Mock()

        # Setup a function with fixturecheck that is async
        func = Mock()
        func._fixturecheck = True
        func.__wrapped__ = None
        mock_fixturedef.func = func

        # Mock is_async_fixture to return True
        with patch("pytest_fixturecheck.plugin.is_async_fixture", return_value=True):
            pytest_fixture_setup(mock_fixturedef, mock_request)

        # Should set the skip attribute
        assert hasattr(mock_fixturedef, "_fixturecheck_skip")

    def test_pytest_collection_finish_no_fixtures_attribute(self):
        """Test pytest_collection_finish when no fixtures attribute exists."""
        mock_session = Mock()
        mock_session.config = Mock()

        # No _fixturecheck_fixtures attribute
        del mock_session.config._fixturecheck_fixtures

        # Should return early without error
        pytest_collection_finish(mock_session)

    def test_pytest_collection_finish_empty_fixtures(self):
        """Test pytest_collection_finish with empty fixtures."""
        mock_session = Mock()
        mock_session.config = Mock()
        mock_session.config._fixturecheck_fixtures = set()

        # Should return early without error
        pytest_collection_finish(mock_session)

    def test_pytest_collection_finish_with_import_error_in_validator(self):
        """Test pytest_collection_finish handling import errors in validators."""
        mock_session = Mock()
        mock_session.config = Mock()
        mock_session.config.getini = Mock(return_value="false")

        # Create a mock fixture with a validator that raises ImportError
        mock_fixturedef = Mock()
        mock_fixturedef.func = Mock()
        mock_fixturedef.argname = "test_fixture"

        def failing_validator(obj, is_collection_phase):
            raise ImportError("Test import error")

        mock_fixturedef.func._validator = failing_validator
        mock_fixturedef.func._expect_validation_error = False

        mock_session.config._fixturecheck_fixtures = {mock_fixturedef}

        # Mock exit to prevent actual exit
        with patch("pytest_fixturecheck.plugin.pytest.exit") as mock_exit:
            with patch("pytest_fixturecheck.plugin.report_fixture_errors") as mock_report:
                pytest_collection_finish(mock_session)

                # Should report errors and exit
                mock_report.assert_called_once()
                mock_exit.assert_called_once_with("Fixture validation failed", 1)

    def test_pytest_collection_finish_auto_skip_enabled(self):
        """Test pytest_collection_finish with auto-skip enabled."""
        mock_session = Mock()
        mock_session.config = Mock()
        mock_session.config.getini = Mock(return_value="true")  # auto-skip enabled
        mock_session.items = []

        # Create a mock fixture that will fail
        mock_fixturedef = Mock()
        mock_fixturedef.func = Mock()
        mock_fixturedef.argname = "test_fixture"

        def failing_validator(obj, is_collection_phase):
            raise ValueError("Test error")

        mock_fixturedef.func._validator = failing_validator
        mock_fixturedef.func._expect_validation_error = False

        mock_session.config._fixturecheck_fixtures = {mock_fixturedef}

        # Should not exit when auto-skip is enabled
        with patch("pytest_fixturecheck.plugin.pytest.exit") as mock_exit:
            with patch("pytest_fixturecheck.plugin.report_fixture_errors"):
                with patch("pytest_fixturecheck.plugin._mark_dependent_tests_for_skip"):
                    pytest_collection_finish(mock_session)

                    # Should not exit
                    mock_exit.assert_not_called()

    def test_mark_dependent_tests_for_skip(self):
        """Test _mark_dependent_tests_for_skip function."""
        mock_session = Mock()
        mock_fixturedef = Mock()
        mock_fixturedef.argname = "failing_fixture"
        error = ValueError("Test error")

        # Create mock test items
        mock_item1 = Mock()
        mock_item1.fixturenames = ["failing_fixture", "other_fixture"]
        mock_item1.add_marker = Mock()

        mock_item2 = Mock()
        mock_item2.fixturenames = ["other_fixture"]
        mock_item2.add_marker = Mock()

        mock_session.items = [mock_item1, mock_item2]

        _mark_dependent_tests_for_skip(mock_session, mock_fixturedef, error)

        # Only the first item should get the skip marker
        mock_item1.add_marker.assert_called_once()
        mock_item2.add_marker.assert_not_called()

    def test_report_fixture_errors_with_import_error(self, capsys):
        """Test report_fixture_errors with import error."""
        mock_fixturedef = Mock()
        mock_fixturedef.argname = "test_fixture"
        mock_fixturedef.func = lambda: None

        error = ImportError("No module named 'missing_module'")
        traceback_str = "File \"/user/code/test.py\", line 10, in validator\n    import missing_module\nImportError: No module named 'missing_module'"

        failed_fixtures = [(mock_fixturedef, error, traceback_str)]

        report_fixture_errors(failed_fixtures)

        captured = capsys.readouterr()
        assert "FIXTURE VALIDATION ERRORS" in captured.out
        assert "test_fixture" in captured.out
        assert "ImportError" in captured.out

    def test_report_fixture_errors_with_user_code_import_error(self, capsys):
        """Test report_fixture_errors with import error in user code."""
        mock_fixturedef = Mock()
        mock_fixturedef.argname = "test_fixture"
        mock_fixturedef.func = lambda: None

        error = ImportError("No module named 'user_module'")
        traceback_str = """File "/user/code/test.py", line 10, in validator
    import user_module
ImportError: No module named 'user_module'
"""

        failed_fixtures = [(mock_fixturedef, error, traceback_str)]

        report_fixture_errors(failed_fixtures)

        captured = capsys.readouterr()
        assert "POSSIBLE USER CODE ERROR" in captured.out
        assert "/user/code/test.py" in captured.out

    def test_plugin_count_opportunities_with_attribute_fixtures(self):
        """Test counting opportunities with attribute-style fixtures."""
        plugin = FixtureCheckPlugin()

        content = """
import pytest

@pytest.fixture
def normal_fixture():
    return "normal"

@pytest_asyncio.fixture
def async_fixture():
    return "async"
"""

        # Should count both fixtures as opportunities
        assert plugin.count_opportunities(content) == 2

    def test_plugin_add_fixture_checks_with_syntax_error(self):
        """Test add_fixture_checks handling syntax errors."""
        plugin = FixtureCheckPlugin()

        malformed_content = """
import pytest
@pytest.fixture
def broken_fixture(
    # Missing closing parenthesis
"""

        # Should raise SyntaxError
        with pytest.raises(SyntaxError):
            plugin.add_fixture_checks(malformed_content)

    def test_plugin_complex_ast_patterns(self):
        """Test plugin with complex AST patterns."""
        plugin = FixtureCheckPlugin()

        content = """
import pytest
from some.module import fixture as custom_fixture

@custom_fixture
def using_imported_fixture():
    return "custom"

@pytest.fixture()
def fixture_with_call():
    return "call"

@pytest.fixture
def simple_fixture():
    return "simple"
"""

        # Should handle various fixture patterns
        opportunities = plugin.count_opportunities(content)
        assert opportunities >= 2  # At least fixture_with_call and simple_fixture


class TestFixtureCheckPluginEdgeCases:
    """Test edge cases in FixtureCheckPlugin class methods."""

    def test_count_opportunities_empty_file(self):
        """Test count_opportunities with empty file."""
        plugin = FixtureCheckPlugin()
        assert plugin.count_opportunities("") == 0
        assert plugin.count_opportunities("# Just a comment") == 0

    def test_count_existing_checks_empty_file(self):
        """Test count_existing_checks with empty file."""
        plugin = FixtureCheckPlugin()
        assert plugin.count_existing_checks("") == 0

    def test_add_fixture_checks_empty_file(self):
        """Test add_fixture_checks with empty file."""
        plugin = FixtureCheckPlugin()
        content = ""
        assert plugin.add_fixture_checks(content) == content

    def test_add_fixture_checks_preserves_whitespace(self):
        """Test that add_fixture_checks preserves whitespace and formatting."""
        plugin = FixtureCheckPlugin()

        content = """import pytest


@pytest.fixture
def spaced_fixture():
    return "spaced"


def regular_function():
    pass
"""

        modified = plugin.add_fixture_checks(content)

        # Should preserve the spacing structure
        lines = modified.split("\n")
        assert "" in lines  # Empty lines should be preserved
        assert "@fixturecheck()" in modified

    def test_plugin_initialization(self):
        """Test FixtureCheckPlugin initialization."""
        plugin = FixtureCheckPlugin()

        # Should initialize with expected fixture patterns
        expected_patterns = [
            "@pytest.fixture",
            "@fixture",
            "@pytest_asyncio.fixture",
        ]
        assert plugin.fixture_patterns == expected_patterns
