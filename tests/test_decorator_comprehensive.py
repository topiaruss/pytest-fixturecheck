"""Comprehensive tests for the fixturecheck decorator."""

import inspect
from functools import wraps
from unittest.mock import MagicMock, patch

import pytest

from pytest_fixturecheck import fixturecheck
from pytest_fixturecheck.decorator import _default_validator
from pytest_fixturecheck.decorator import fixturecheck as fixturecheck_raw


# Test basic decorator functionality
class TestDecoratorBasics:
    """Tests for basic decorator functionality."""

    def test_decorator_marks_function(self):
        """Test that the decorator marks the function with _fixturecheck."""

        # Define a test validator
        def validator(obj, is_collection_phase=False):
            pass  # Don't return anything (None)

        # Direct test through the raw decorator to skip fixture wrapping
        def test_function():
            return "test"

        # Apply decorator directly
        wrapped = fixturecheck_raw(validator)(test_function)

        # Check the type and attributes
        print(f"Type of wrapped is: {type(wrapped)}")
        print(f"wrapped attributes: {dir(wrapped)}")

        # Check that the function is marked
        assert hasattr(wrapped, "_fixturecheck")
        assert wrapped._fixturecheck is True

        # Check that the validator is stored
        assert hasattr(wrapped, "_validator")
        assert wrapped._validator is validator

    def test_decorator_preserves_function_metadata(self):
        """Test that the decorator preserves function metadata."""

        # Define a function with docstring and other metadata
        def test_function():
            """Test function docstring."""
            return "test"

        # Apply decorator directly
        decorated = fixturecheck_raw(lambda x, is_collection_phase=False: True)(
            test_function
        )

        # Check that metadata is preserved
        assert decorated.__name__ == "test_function"
        assert decorated.__doc__ == "Test function docstring."
        assert inspect.signature(decorated) == inspect.signature(test_function)

    def test_decorator_without_validator(self):
        """Test that the decorator works without a validator."""

        # Apply decorator without validator directly
        def test_function():
            return "test"

        # Apply decorator directly
        wrapped = fixturecheck_raw(test_function)

        # Check that the function is marked
        assert hasattr(wrapped, "_fixturecheck")
        assert wrapped._fixturecheck is True

        # Check that validator is the default validator
        assert hasattr(wrapped, "_validator")
        assert wrapped._validator is _default_validator


# Test decorator order
class TestDecoratorOrder:
    """Tests for different decorator orderings."""

    def test_fixturecheck_before_fixture(self):
        """Test decorator when fixturecheck is applied before pytest.fixture."""

        # Define a test function
        def test_function():
            return "test"

        # Apply fixturecheck first
        wrapped = fixturecheck_raw(lambda x, is_collection_phase=False: True)(
            test_function
        )

        # Then apply pytest.fixture
        fixture_func = pytest.fixture(wrapped)

        # Check that the function is marked
        assert hasattr(fixture_func, "_fixturecheck")
        assert fixture_func._fixturecheck is True

    def test_fixturecheck_after_fixture(self):
        """Test decorator when fixturecheck is applied after pytest.fixture."""

        # Define a test function
        def test_function():
            return "test"

        # Apply pytest.fixture first
        fixture_func = pytest.fixture(test_function)

        # Then apply fixturecheck
        wrapped = fixturecheck_raw(lambda x, is_collection_phase=False: True)(
            fixture_func
        )

        # Check that the function is marked
        assert hasattr(wrapped, "_fixturecheck")
        assert wrapped._fixturecheck is True


# Test with additional decorators
class TestWithAdditionalDecorators:
    """Tests for interaction with additional decorators."""

    def test_with_multiple_decorators(self):
        """Test that fixturecheck works with multiple decorators."""

        # Define a custom decorator
        def custom_decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)

            return wrapper

        # Define a test function
        def test_function():
            return "test"

        # Apply decorators directly in order
        decorated = custom_decorator(test_function)
        fixture_func = pytest.fixture(decorated)
        wrapped = fixturecheck_raw(lambda x, is_collection_phase=False: True)(
            fixture_func
        )

        # Check that the function is still marked
        assert hasattr(wrapped, "_fixturecheck")
        assert wrapped._fixturecheck is True


# Test expect_validation_error parameter
class TestExpectValidationErrorParameter:
    """Tests for the expect_validation_error parameter."""

    def test_expect_validation_error_parameter(self):
        """Test that the expect_validation_error parameter is stored."""

        # Define a test function
        def test_function():
            return "test"

        # Apply decorator with expect_validation_error
        wrapped = fixturecheck_raw(
            lambda x, is_collection_phase=False: True, expect_validation_error=True
        )(test_function)

        # Check that expect_validation_error is stored
        assert hasattr(wrapped, "_expect_validation_error")
        assert wrapped._expect_validation_error is True

    def test_expect_validation_error_default(self):
        """Test that expect_validation_error defaults to False."""

        # Define a test function
        def test_function():
            return "test"

        # Apply decorator without expect_validation_error
        wrapped = fixturecheck_raw(lambda x, is_collection_phase=False: True)(
            test_function
        )

        # Check that expect_validation_error is False
        assert hasattr(wrapped, "_expect_validation_error")
        assert wrapped._expect_validation_error is False


# Test call signature
class TestCallSignature:
    """Tests for different call signatures of the decorator."""

    def test_as_function_with_validator(self):
        """Test using the decorator as a function with a validator."""

        # Define a validator
        def validator(obj, is_collection_phase=False):
            return True

        # Apply decorator as a function
        decorated = fixturecheck_raw(validator)

        # Check that it returns a function
        assert callable(decorated)

        # Apply the returned function to a test function
        test_function = lambda: "test"
        result = decorated(test_function)

        # Check that the result is properly decorated
        assert hasattr(result, "_fixturecheck")
        assert result._fixturecheck is True
        assert hasattr(result, "_validator")
        assert result._validator is validator

    def test_as_function_without_validator(self):
        """Test using the decorator as a function without a validator."""
        # Apply decorator directly to a function
        test_function = lambda: "test"
        result = fixturecheck_raw(test_function)

        # Check that the result is properly decorated
        assert hasattr(result, "_fixturecheck")
        assert result._fixturecheck is True
        assert hasattr(result, "_validator")
        assert result._validator is _default_validator

    def test_as_decorator_with_validator(self):
        """Test using the decorator with a validator."""

        # Define a test function
        def test_function():
            return "test"

        # Apply decorator directly
        wrapped = fixturecheck_raw(lambda x, is_collection_phase=False: True)(
            test_function
        )

        # Check that the function is properly decorated
        assert hasattr(wrapped, "_fixturecheck")
        assert wrapped._fixturecheck is True
        assert hasattr(wrapped, "_validator")
        assert callable(wrapped._validator)

    def test_as_decorator_without_validator(self):
        """Test using the decorator without a validator."""

        # Define a test function
        def test_function():
            return "test"

        # Apply decorator directly
        wrapped = fixturecheck_raw(test_function)

        # Check that the function is properly decorated
        assert hasattr(wrapped, "_fixturecheck")
        assert wrapped._fixturecheck is True
        assert hasattr(wrapped, "_validator")
        assert wrapped._validator is _default_validator
