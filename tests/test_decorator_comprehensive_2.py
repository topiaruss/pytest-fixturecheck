"""Additional comprehensive tests for decorator.py."""

from unittest.mock import MagicMock, patch

import pytest

from pytest_fixturecheck import validators
from pytest_fixturecheck.decorator import _default_validator, fixturecheck


class TestFixturecheckWithValidator:
    """Test fixturecheck with different validator patterns."""

    def test_fixturecheck_with_validator_function(self):
        """Test fixturecheck with a validator function argument."""

        # Create a validator function with the right signature
        def validator(obj, is_collection_phase=False):
            assert isinstance(obj, int)

        # Create a fixture with the validator
        @fixturecheck(validator)
        def fixture():
            return 42

        # Check that fixture is properly decorated
        assert hasattr(fixture, "_fixturecheck")
        assert fixture._fixturecheck is True
        assert hasattr(fixture, "_validator")
        assert fixture._validator is validator
        assert hasattr(fixture, "_expect_validation_error")
        assert fixture._expect_validation_error is False

        # Check that fixture works
        assert fixture() == 42

    def test_fixturecheck_with_expect_validation_error(self):
        """Test fixturecheck with expect_validation_error=True."""

        # Create a validator function
        def validator(obj, is_collection_phase=False):
            raise ValueError("Expected validation error")

        # Create a fixture with expect_validation_error=True
        @fixturecheck(validator, expect_validation_error=True)
        def fixture():
            return "invalid"

        # Check that fixture is properly decorated with expect_validation_error
        assert hasattr(fixture, "_fixturecheck")
        assert fixture._fixturecheck is True
        assert hasattr(fixture, "_validator")
        assert fixture._validator is validator
        assert hasattr(fixture, "_expect_validation_error")
        assert fixture._expect_validation_error is True

        # The fixture itself should work normally
        assert fixture() == "invalid"

    def test_fixturecheck_with_two_argument_validator(self):
        """Test fixturecheck with a validator that takes two arguments."""

        # Create a validator function with complex logic
        def complex_validator(obj, is_collection_phase=False):
            if is_collection_phase:
                return  # Skip during collection
            assert isinstance(obj, dict)
            assert "key" in obj

        # Create a fixture with the validator
        @fixturecheck(complex_validator)
        def fixture():
            return {"key": "value"}

        # Check that fixture is properly decorated
        assert hasattr(fixture, "_fixturecheck")
        assert fixture._fixturecheck is True
        assert hasattr(fixture, "_validator")
        assert fixture._validator is complex_validator


class TestDefaultValidator:
    """Test the _default_validator function."""

    def test_default_validator_basic(self):
        """Test _default_validator with a basic object."""
        # Test with a simple object
        obj = {"test": "value"}

        # Should not raise any exception
        _default_validator(obj)

        # Test with different types
        _default_validator(["test"])
        _default_validator("test")
        _default_validator(123)

    def test_default_validator_collection_phase(self):
        """Test _default_validator skips during collection phase."""
        # Create a mock object that would normally fail validation
        obj = MagicMock()

        # This should not raise, as collection phase skips validation
        _default_validator(obj, is_collection_phase=True)


class TestWithModelValidation:
    """Test the with_model_validation factory function."""

    def test_with_model_validation_decorator(self):
        """Test that with_model_validation returns a decorator."""
        # Create a fixture decorator
        decorator = fixturecheck.with_model_validation("field1", "field2")
        assert callable(decorator)

        # Create a fixture
        @decorator
        def fixture():
            return MagicMock()

        # Check that fixture is properly decorated
        assert hasattr(fixture, "_fixturecheck")
        assert fixture._fixturecheck is True
        assert hasattr(fixture, "_validator")
        assert callable(fixture._validator)

    def test_validator_function_signature(self):
        """Test that the validator function from with_model_validation has the correct signature."""
        # Get the validator function
        validator_func = fixturecheck.with_model_validation("field1")

        # Decorate a test fixture
        @validator_func
        def fixture():
            pass

        # Check that the validator has the correct signature
        import inspect

        sig = inspect.signature(fixture._validator)
        assert "obj" in sig.parameters
        assert len(sig.parameters) >= 1

        # Check that the validator accepts is_collection_phase
        try:
            fixture._validator(MagicMock(), is_collection_phase=True)
        except Exception as e:
            if not isinstance(
                e, ImportError
            ):  # ImportError is expected if Django is not available
                pytest.fail(
                    f"Validator should accept is_collection_phase but raised: {e}"
                )


class TestFactoryFunctionAttributes:
    """Test that fixturecheck has the expected factory function attributes."""

    def test_factory_attributes(self):
        """Test the factory function attributes on fixturecheck."""
        # Check that fixturecheck has the factory function attributes
        assert hasattr(fixturecheck, "with_required_fields")
        assert callable(fixturecheck.with_required_fields)

        assert hasattr(fixturecheck, "with_required_methods")
        assert callable(fixturecheck.with_required_methods)

        assert hasattr(fixturecheck, "with_model_validation")
        assert callable(fixturecheck.with_model_validation)

        assert hasattr(fixturecheck, "with_property_values")
        assert callable(fixturecheck.with_property_values)

        assert hasattr(fixturecheck, "validators")
        assert fixturecheck.validators is validators
