"""Comprehensive tests for AsyncIO compatibility."""

import asyncio
import inspect
from unittest.mock import MagicMock, patch

import pytest
import pytest_asyncio

from pytest_fixturecheck import fixturecheck
from pytest_fixturecheck.plugin import is_async_fixture
from pytest_fixturecheck.utils import is_async_function, is_coroutine


# Create a wrapper for validators to handle collection phase safely
def phase_aware_validator(validator_func):
    """Wrap a validator to make it phase-aware and skip validation during collection."""

    def wrapper(obj, is_collection_phase=False):
        if is_collection_phase or callable(obj):
            return
        return validator_func(obj)

    return wrapper


# Test async function detection
class TestAsyncDetection:
    """Tests for async function detection."""

    def test_is_async_function(self):
        """Test detection of async functions."""

        # Define async function
        async def async_func():
            return "async"

        # Define regular function
        def sync_func():
            return "sync"

        # Test detection
        assert is_async_function(async_func) is True
        assert is_async_function(sync_func) is False

    def test_is_coroutine(self):
        """Test detection of coroutine objects."""

        # Create coroutine object
        async def async_func():
            return "async"

        coroutine_obj = async_func()

        try:
            # Test detection
            assert is_coroutine(coroutine_obj) is True
            assert is_coroutine("not a coroutine") is False
        finally:
            # Clean up the coroutine to avoid RuntimeWarning
            asyncio.get_event_loop().run_until_complete(coroutine_obj)


# Test async fixture validators
@pytest.mark.asyncio
async def test_async_fixture_with_validator():
    """Test async fixture with validator."""

    # Define fixture validator - handle function objects
    def safe_validator(obj, is_collection_phase=False):
        if is_collection_phase or callable(obj):
            return
        assert isinstance(obj, str)
        assert obj == "async fixture value"

    # Define async fixture with validator
    @fixturecheck(safe_validator)
    @pytest.fixture
    async def async_fixture():
        await asyncio.sleep(0.01)  # Simulate async operation
        return "async fixture value"

    # Create mock request
    request = MagicMock()
    fixturedef = MagicMock()
    fixturedef.func = async_fixture

    # Test that the fixture is detected as async
    assert is_async_fixture(fixturedef) is True

    # The actual test runs during execution, not during collection
    # The plugin handles this by skipping validation during collection
    # for async fixtures and validating during execution


# Properly mocking pytest_asyncio is complex, so we'll test plugin interactions
# with async fixtures by direct function calls
class TestAsyncFixtureHandling:
    """Tests for async fixture handling in the plugin."""

    def test_async_fixture_detection(self):
        """Test the detection of async fixtures."""

        # Create a fixture definition with an async function
        async def async_func():
            return "async"

        fixturedef = MagicMock()
        fixturedef.func = async_func

        assert is_async_fixture(fixturedef) is True

    def test_async_name_pattern_detection(self):
        """Test the detection of async fixtures by name pattern."""

        # Create a fixture definition with a name pattern
        def sync_func():
            return "sync"

        fixturedef = MagicMock()
        fixturedef.func = sync_func
        fixturedef.argname = "async_fixture"

        assert is_async_fixture(fixturedef) is True

    def test_pytest_asyncio_attribute(self):
        """Test the detection of pytest-asyncio fixtures."""

        # Create a fixture definition with pytest-asyncio attribute
        def sync_func():
            return "sync"

        fixturedef = MagicMock()
        fixturedef.func = sync_func
        fixturedef.argname = "normal_fixture"
        fixturedef._pytest_asyncio_scope = "function"

        # Need to patch PYTEST_ASYNCIO_INSTALLED
        with patch("pytest_fixturecheck.plugin.PYTEST_ASYNCIO_INSTALLED", True):
            assert is_async_fixture(fixturedef) is True


@pytest.mark.asyncio
async def test_async_fixture_validation_result():
    """Test validation of async fixture results.

    This test validates that the plugin can handle async fixtures.
    Since we can't directly call the fixture in this test, we'll
    simulate the behavior by creating an async function and
    validating its output.
    """

    # Define a test async function
    async def async_test_func():
        await asyncio.sleep(0.01)
        return {"value": "async"}

    # Call the function to get a coroutine
    coro = async_test_func()

    # Assert it's a coroutine
    assert asyncio.iscoroutine(coro)

    # Wait for the result
    result = await coro

    # Validate the result
    assert isinstance(result, dict)
    assert result["value"] == "async"

    # Simulate the validation that would happen in the plugin
    def validate_dict(obj):
        assert isinstance(obj, dict)
        assert obj.get("value") == "async"

    # The plugin would wait for the coroutine and then validate
    validate_dict(result)
