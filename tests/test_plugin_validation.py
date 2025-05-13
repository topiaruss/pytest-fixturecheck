"""Tests for core plugin validation functionality."""

import sys
from unittest.mock import MagicMock, patch

import pytest

from pytest_fixturecheck import fixturecheck
from pytest_fixturecheck.plugin import (
    _mark_dependent_tests_for_skip,
    is_async_fixture,
    pytest_addoption,
    pytest_collection_finish,
    pytest_configure,
    pytest_fixture_setup,
    report_fixture_errors,
)


def test_pytest_addoption():
    """Test that pytest_addoption adds the right configuration options."""
    parser = MagicMock()
    pytest_addoption(parser)
    parser.addini.assert_called_once_with(
        "fixturecheck-auto-skip",
        help="Automatically skip tests with invalid fixtures instead of failing",
        default="false",
        type="bool",
    )


def test_pytest_configure():
    """Test that pytest_configure adds the marker."""
    config = MagicMock()
    pytest_configure(config)
    config.addinivalue_line.assert_called_once_with(
        "markers", "fixturecheck: mark a test as using fixture validation"
    )


def test_is_async_fixture():
    """Test is_async_fixture detection."""

    # Create a mock fixture definition
    async def async_func():
        pass

    def sync_func():
        pass

    # Test async function
    fixturedef = MagicMock()
    fixturedef.func = async_func
    assert is_async_fixture(fixturedef) is True

    # Test async fixture name pattern
    fixturedef = MagicMock()
    fixturedef.func = sync_func
    fixturedef.argname = "async_fixture"
    assert is_async_fixture(fixturedef) is True

    # Test regular fixture - need to patch pytest_asyncio_installed
    with patch("pytest_fixturecheck.plugin.PYTEST_ASYNCIO_INSTALLED", False):
        fixturedef = MagicMock()
        fixturedef.func = sync_func
        fixturedef.argname = "normal_fixture"
        # Make sure unittest attribute doesn't have 'async'
        fixturedef.unittest = "regular"
        assert is_async_fixture(fixturedef) is False


def test_pytest_fixture_setup():
    """Test that pytest_fixture_setup registers fixtures correctly."""

    # Create a fixture function with _fixturecheck attribute
    @fixturecheck
    @pytest.fixture
    def marked_fixture():
        return "test"

    # Setup mocks
    fixturedef = MagicMock()
    fixturedef.func = marked_fixture
    request = MagicMock()
    request.config = MagicMock()
    request.config._fixturecheck_fixtures = set()

    # Test registration
    pytest_fixture_setup(fixturedef, request)

    # Check that the fixture was registered
    assert hasattr(request.config, "_fixturecheck_fixtures")
    assert (
        len(request.config._fixturecheck_fixtures) == 1
    )  # Should have one fixture registered

    # Mock equality check doesn't work well with sets, so instead check that
    # the set is not empty after registration
    assert request.config._fixturecheck_fixtures


def test_report_fixture_errors():
    """Test fixture error reporting."""
    # Create a mock fixturedef with an error
    fixturedef = MagicMock()
    fixturedef.argname = "broken_fixture"

    def mock_fixture():
        pass

    fixturedef.func = mock_fixture
    error = ValueError("Fixture validation failed")
    tb = 'Traceback (most recent call last):\n  File "test.py", line 10, in test\n    raise ValueError("Fixture validation failed")'

    # Capture the output
    with patch("builtins.print") as mock_print:
        report_fixture_errors([(fixturedef, error, tb)])

        # Verify the error was reported
        assert any(
            "Fixture 'broken_fixture'" in call[0][0]
            for call in mock_print.call_args_list
        )
        assert any(
            "ValueError: Fixture validation failed" in call[0][0]
            for call in mock_print.call_args_list
        )


def test_mark_dependent_tests_for_skip():
    """Test marking dependent tests for skipping."""
    # Create a mock session with items
    session = MagicMock()

    # Create a test item that uses our fixture
    item = MagicMock()
    item.fixturenames = ["broken_fixture", "another_fixture"]
    session.items = [item]

    # Create a fixture definition
    fixturedef = MagicMock()
    fixturedef.argname = "broken_fixture"

    # Create an error
    error = ValueError("Fixture validation failed")

    # Mark the tests
    _mark_dependent_tests_for_skip(session, fixturedef, error)

    # Check that the item was marked with a skip marker
    item.add_marker.assert_called_once()
    args, _ = item.add_marker.call_args
    skip_marker = args[0]
    assert "skip" in str(skip_marker)
    assert "broken_fixture" in skip_marker.kwargs["reason"]
    assert "Fixture validation failed" in skip_marker.kwargs["reason"]
