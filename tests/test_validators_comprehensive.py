"""Comprehensive tests for validator functions."""

from collections import namedtuple
from typing import Any, Dict, List, Tuple, Type, Union

import pytest

from pytest_fixturecheck import (
    combines_validators,
    creates_validator,
    fixturecheck,
    has_property_values,
    has_required_fields,
    has_required_methods,
    is_instance_of,
)


# Custom validator functions for testing purposes
def custom_is_instance_of(expected_type):
    """
    Create a validator function that checks if an object is an instance of expected_type.

    Args:
        expected_type: A type or tuple of types to check against

    Returns:
        A validator function that raises TypeError if the object is not an instance
        of the expected type(s)
    """

    def validator(obj, is_collection_phase=False):
        """Validate that the object is an instance of the expected type."""
        if is_collection_phase:
            return

        # Skip validation for callable objects (functions, methods)
        if callable(obj):
            return

        # Check if the object is an instance of the expected type(s)
        if not isinstance(obj, expected_type):
            if isinstance(expected_type, tuple):
                type_names = ", ".join(t.__name__ for t in expected_type)
                raise TypeError(
                    f"Expected instance of one of ({type_names}), got {type(obj).__name__}"
                )
            else:
                raise TypeError(
                    f"Expected instance of {expected_type.__name__}, got {type(obj).__name__}"
                )

    return validator


# Create a wrapper for validators to handle collection phase safely
def phase_aware_validator(validator):
    """Wrap a validator to make it phase-aware and skip validation during collection."""

    def wrapper(obj, is_collection_phase=False):
        if is_collection_phase or callable(obj):
            return
        # Call the validator directly
        return validator(obj)

    # Return the wrapper as the validator
    return wrapper


# Test objects for validators
class CompTestObject:
    """Simple test object with attributes and methods."""

    def __init__(self, name="test", value=42):
        self.name = name
        self.value = value

    def method1(self):
        """Test method."""
        return "method1 called"

    def method2(self, arg):
        """Test method with arg."""
        return f"method2 called with {arg}"


# Test for is_instance_of validator
class TestIsInstanceOf:
    """Tests for is_instance_of validator."""

    def test_basic_validation(self):
        """Test basic instance validation."""
        obj = CompTestObject()
        # Use the actual validator from the library
        is_instance_of(CompTestObject)(obj)

    def test_multi_type_validation(self):
        """Test validation with multiple accepted types."""
        obj1 = CompTestObject()
        obj2 = {"test": "value"}
        # Use the actual validator
        validator = is_instance_of((CompTestObject, dict))
        validator(obj1)
        validator(obj2)

    def test_failed_validation(self):
        """Test validation failure."""
        obj = "not an object"

        # This should raise TypeError with the expected message
        with pytest.raises(TypeError) as excinfo:
            is_instance_of(CompTestObject)(obj)
        assert "Expected instance of CompTestObject, got str" in str(excinfo.value)

    def test_multi_type_failed_validation(self):
        """Test validation failure with multiple types."""
        obj = 42

        # This should raise TypeError with the expected message
        with pytest.raises(TypeError) as excinfo:
            is_instance_of((CompTestObject, dict))(obj)
        assert "Expected instance of one of (CompTestObject, dict), got int" in str(
            excinfo.value
        )


# Test for has_required_fields validator
class TestHasRequiredFields:
    """Tests for has_required_fields validator."""

    def test_basic_validation(self):
        """Test validation of required fields."""
        validator = has_required_fields("name", "value")
        obj = CompTestObject()
        # Should not raise exception
        validator(obj, False)

    def test_collection_phase_skipping(self):
        """Test that validation is skipped during collection phase."""
        validator = has_required_fields("nonexistent")
        obj = CompTestObject()
        # Should not raise exception during collection phase
        validator(obj, True)

    def test_missing_field(self):
        """Test validation when a field is missing."""
        validator = has_required_fields("name", "nonexistent")
        obj = CompTestObject()

        with pytest.raises(AttributeError) as excinfo:
            validator(obj, False)
        assert "Required field 'nonexistent' missing" in str(excinfo.value)

    def test_none_field(self):
        """Test validation when a field is None."""
        validator = has_required_fields("name", "value")
        obj = CompTestObject()
        obj.name = None

        with pytest.raises(ValueError) as excinfo:
            validator(obj, False)
        assert "Required field 'name' is None" in str(excinfo.value)

    def test_namedtuple_validation(self):
        """Test validation with a namedtuple."""
        validator = has_required_fields("name", "value")
        Person = namedtuple("Person", ["name", "value"])
        person = Person("test", 42)
        # Should not raise exception
        validator(person, False)

    def test_function_skipping(self):
        """Test that functions are skipped."""
        validator = has_required_fields("nonexistent")

        def function():
            pass

        # Should not raise exception for functions
        validator(function, False)


# Test for has_required_methods validator
class TestHasRequiredMethods:
    """Tests for has_required_methods validator."""

    def test_basic_validation(self):
        """Test validation of required methods."""
        validator_instance = has_required_methods("method1", "method2")
        obj = CompTestObject()
        # Should not raise exception
        validator_instance(obj)

    def test_missing_method(self):
        """Test validation when a method is missing."""
        validator_instance = has_required_methods("method1", "nonexistent")
        obj = CompTestObject()

        with pytest.raises(AttributeError) as excinfo:
            validator_instance(obj)
        assert "Required method 'nonexistent' missing" in str(excinfo.value)

    def test_non_callable_attribute(self):
        """Test validation when an attribute exists but is not callable."""
        validator_instance = has_required_methods(
            "method1", "name"
        )  # 'name' is an attribute, not a method
        obj = CompTestObject()

        with pytest.raises(TypeError) as excinfo:
            validator_instance(obj)
        assert "'name' is not callable" in str(excinfo.value)


# Test for has_property_values validator
class TestHasPropertyValues:
    """Tests for has_property_values validator."""

    def test_basic_validation(self):
        """Test basic property value validation."""
        validator_instance = has_property_values(name="test", value=42)
        obj = CompTestObject(name="test", value=42)
        # Should not raise exception
        validator_instance(obj)

    def test_missing_property(self):
        """Test validation when a property is missing."""
        validator_instance = has_property_values(name="test", nonexistent_prop=123)
        obj = CompTestObject()

        with pytest.raises(AttributeError) as excinfo:
            validator_instance(obj)
        assert "Property 'nonexistent_prop' missing" in str(excinfo.value)

    def test_wrong_value(self):
        """Test validation when a property has the wrong value."""
        validator_instance = has_property_values(name="test", value=99)
        obj = CompTestObject(name="test", value=42)  # Actual value is 42

        with pytest.raises(ValueError) as excinfo:
            validator_instance(obj)
        assert "Expected value=99, got 42" in str(excinfo.value)


# Test for combines_validators
class TestCombinesValidators:
    """Tests for combines_validators."""

    def test_combined_validators_success(self):
        """Test combining validators that should all succeed."""
        obj = CompTestObject(name="test", value=123)

        # Use actual validators from the library
        validator = combines_validators(
            is_instance_of(CompTestObject),
            has_required_fields("name", "value"),
            has_required_methods("method1"),
            has_property_values(name="test", value=123),
        )
        # Should not raise exception
        validator(obj, is_collection_phase=False)

    def test_combined_validators_failure(self):
        """Test combining validators where one should fail."""
        obj = CompTestObject(name="test", value=123)

        # Use actual validators, one of which will fail (wrong type for has_property_values)
        validator = combines_validators(
            is_instance_of(CompTestObject),
            has_required_fields("name", "value"),
            has_property_values(name="test", value="wrong_type"),  # This should fail
        )

        with pytest.raises(ValueError) as excinfo:
            validator(obj, is_collection_phase=False)
        assert "Expected value=wrong_type, got 123" in str(excinfo.value)

    def test_collection_phase_handling(self):
        """Test that combines_validators respects is_collection_phase."""

        # Create a mock validator that would fail if not in collection phase
        def mock_failing_validator(obj, is_collection_phase):
            if not is_collection_phase:
                raise AssertionError("Should fail only in non-collection phase")
            # else: implicitly return None to signify success/skip

        # Set the necessary attribute for it to be treated as a validator
        mock_failing_validator._is_pytest_fixturecheck_validator = True

        obj = CompTestObject()

        # Combine with a validator that would fail
        combined = combines_validators(
            is_instance_of(CompTestObject), mock_failing_validator
        )

        # Should not raise exception when is_collection_phase is True
        try:
            combined(obj, is_collection_phase=True)
        except AssertionError:
            pytest.fail("Validator was not skipped during collection phase")

        # Should raise exception when is_collection_phase is False
        with pytest.raises(
            AssertionError, match="Should fail only in non-collection phase"
        ):
            combined(obj, is_collection_phase=False)

    def test_empty_combines_validators(self):
        """Test combines_validators with no validators."""
        obj = CompTestObject()
        validator = combines_validators()
        try:
            validator(obj, is_collection_phase=False)
            validator(obj, is_collection_phase=True)
        except Exception as e:
            pytest.fail(f"combines_validators with no args raised an exception: {e}")


# Test for custom validators
class TestCustomValidators:
    """Tests for custom validators created with creates_validator."""

    def test_custom_validator(self):
        """Test creating and using a custom validator."""

        # Create a custom validator that handles phase
        def has_specific_value(expected_value):
            def validator(obj, is_collection_phase=False):
                if is_collection_phase:
                    return
                if getattr(obj, "value", None) != expected_value:
                    raise ValueError(
                        f"Expected value={expected_value}, got {getattr(obj, 'value', None)}"
                    )

            return validator

        # Test successful validation
        validator = has_specific_value(42)
        obj = CompTestObject()
        validator(obj, False)

        # Test failed validation
        obj.value = 43
        with pytest.raises(ValueError) as excinfo:
            validator(obj, False)
        assert "Expected value=42, got 43" in str(excinfo.value)


# Fixture using the validator
@pytest.fixture
@fixturecheck(phase_aware_validator(custom_is_instance_of(CompTestObject)))
def valid_object_fixture():
    """Fixture that returns a valid object."""
    return CompTestObject()


def test_fixture_with_validator(valid_object_fixture):
    """Test using a fixture with a validator."""
    assert isinstance(valid_object_fixture, CompTestObject)
    assert valid_object_fixture.name == "test"
    assert valid_object_fixture.value == 42


# Fixture with combined validators
@pytest.fixture
@fixturecheck(
    combines_validators(
        phase_aware_validator(custom_is_instance_of(dict)),
        has_required_fields("name", "values"),
    )
)
def complex_fixture():
    """Fixture that returns a complex object with validation."""
    return {
        "name": "test",
        "values": [1, 2, 3],
        "metadata": {"type": "test", "version": "1.0"},
    }


def test_fixture_with_combined_validators(complex_fixture):
    """Test using a fixture with combined validators."""
    assert isinstance(complex_fixture, dict)
    assert "name" in complex_fixture
    assert "values" in complex_fixture
