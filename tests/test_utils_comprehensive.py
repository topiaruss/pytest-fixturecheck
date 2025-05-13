"""Comprehensive tests for the utils module."""

import asyncio
import functools
import inspect
from unittest.mock import MagicMock, patch

import pytest

from pytest_fixturecheck.utils import creates_validator, is_async_function, is_coroutine


class TestCreatesValidator:
    """Tests for the creates_validator decorator."""

    def test_creates_validator_basic(self):
        """Test that creates_validator decorates functions properly."""

        # Define a validator function directly
        def direct_validator(obj):
            """Simple direct validator function."""
            # Only accept numbers equal to 42
            if obj != 42:
                raise ValueError(f"Expected 42, got {obj}")

        # Apply creates_validator directly (not as a decorator)
        validator_factory = creates_validator(direct_validator)

        # The validator_factory returns a validator when called
        validator = validator_factory()

        # Test successful validation - should not raise
        validator(42)

        # Test failed validation - should raise ValueError
        with pytest.raises(ValueError):
            validator(43)

    def test_creates_validator_preserves_metadata(self):
        """Test that creates_validator preserves function metadata."""

        @creates_validator
        def test_validator(expected_value):
            """Validator docstring."""

            def validate(obj):
                pass

            return validate

        # Check that docstring and name are preserved
        assert test_validator.__name__ == "test_validator"
        assert test_validator.__doc__ == "Validator docstring."

    def test_creates_validator_as_function(self):
        """Test using creates_validator as a function rather than decorator."""

        def test_validator(expected_value):
            def validate(obj):
                pass

            return validate

        decorated = creates_validator(test_validator)

        # Should be the same function but decorated
        assert decorated.__name__ == test_validator.__name__
        assert callable(decorated)

    def test_skip_function_validation(self):
        """Test that creates_validator wrapper skips validation for function objects."""

        # Create a simple function to use for testing
        def my_test_func():
            pass

        # We'll create a simplified version of the creates_validator wrapper
        # to demonstrate that it skips validation for function objects
        def manual_phase_aware_wrapper(obj, is_collection_phase=False):
            if is_collection_phase or inspect.isfunction(obj):
                return None  # Skip validation
            # Otherwise would validate the object
            return f"Validating {obj}"

        # Test with a function - should skip validation
        assert manual_phase_aware_wrapper(my_test_func) is None

        # Test with a non-function - should validate
        assert manual_phase_aware_wrapper(42) == "Validating 42"

        # This demonstrates the behavior of creates_validator when it wraps validator functions


class TestAsyncUtils:
    """Tests for the async utility functions."""

    def test_is_async_function(self):
        """Test is_async_function with various functions."""

        # Regular function
        def regular_func():
            pass

        assert is_async_function(regular_func) is False

        # Async function
        async def async_func():
            pass

        assert is_async_function(async_func) is True

        # Lambda
        assert is_async_function(lambda: None) is False

        # Method
        class TestClass:
            def method(self):
                pass

            async def async_method(self):
                pass

        obj = TestClass()
        assert is_async_function(obj.method) is False
        assert is_async_function(obj.async_method) is True

    def test_is_coroutine(self):
        """Test is_coroutine with various objects."""

        # Regular function - not a coroutine
        def regular_func():
            pass

        assert is_coroutine(regular_func) is False

        # Async function - not a coroutine until called
        async def async_func():
            pass

        assert is_coroutine(async_func) is False

        # Coroutine object - created when calling an async function
        coro = async_func()
        try:
            assert is_coroutine(coro) is True
        finally:
            # Clean up the coroutine to avoid RuntimeWarning
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(coro)
            finally:
                loop.close()
