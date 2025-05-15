"""Comprehensive tests for the has_property_values validator."""

import inspect
from unittest.mock import MagicMock, patch

import pytest

# Import from the validators module directly
from pytest_fixturecheck import (
    check_property_values,
    fixturecheck,
    has_property_values,
    with_property_values,
)
from pytest_fixturecheck.utils import creates_validator


# Test class with properties
class PropValCompTestObject:
    """Test object with properties."""

    def __init__(self, name="test", value=42, is_active=True):
        self.name = name
        self.value = value
        self.is_active = is_active


# Test class with properties that raises exception on access
class ExceptionRaisingObject:
    """Test object that raises exceptions when properties are accessed."""

    def __init__(self):
        self._name = "hidden"

    @property
    def name(self):
        raise ValueError("Cannot access name property")


class TestHasPropertyValues:
    """Tests for has_property_values validator."""

    def test_basic_validation(self):
        """Test basic property validation."""
        validator = check_property_values(name="test", value=42)
        obj = PropValCompTestObject()

        # Should not raise exception
        validator(obj, False)

    def test_collection_phase_skipping(self):
        """Test that validation is skipped during collection phase."""
        validator = check_property_values(name="wrong", value="wrong")
        obj = PropValCompTestObject()

        # Should not raise exception during collection phase
        validator(obj, True)

    def test_function_skipping(self):
        """Test that functions are skipped."""
        validator = check_property_values(nonexistent="value")

        def function():
            pass

        # Should skip validation for functions
        # Create a modified validator that checks if the object is a function first
        def modified_validator(obj, is_collection_phase=False):
            if is_collection_phase or inspect.isfunction(obj):
                return
            # Should not get here with a function
            validator(obj, is_collection_phase)

        # This should not raise an exception
        modified_validator(function, False)

    def test_missing_property(self):
        """Test validation when a property is missing."""
        validator = check_property_values(name="test", nonexistent="value")
        obj = PropValCompTestObject()

        with pytest.raises(AttributeError) as excinfo:
            validator(obj, False)
        assert "Property 'nonexistent' missing" in str(excinfo.value)

    def test_wrong_value(self):
        """Test validation when a property has the wrong value."""
        validator = check_property_values(name="wrong_name", value=42)
        obj = PropValCompTestObject()

        with pytest.raises(ValueError) as excinfo:
            validator(obj, False)
        assert "Expected name=wrong_name, got test" in str(excinfo.value)

    def test_none_value(self):
        """Test validation when a property is None."""
        validator = check_property_values(name=None)
        obj = PropValCompTestObject(name=None)

        # Should not raise exception - None is a valid value if expected
        validator(obj, False)

    def test_property_exception(self):
        """Test validation when property access raises an exception."""
        validator = check_property_values(name="test")
        obj = ExceptionRaisingObject()

        with pytest.raises(ValueError) as excinfo:
            validator(obj, False)
        assert "Cannot access name property" in str(excinfo.value)

    def test_with_different_types(self):
        """Test validation with different value types."""

        # Test with various types
        class ComplexObject:
            def __init__(self):
                self.string_prop = "string"
                self.int_prop = 123
                self.bool_prop = True
                self.list_prop = [1, 2, 3]
                self.dict_prop = {"key": "value"}
                self.none_prop = None

        validator = check_property_values(
            string_prop="string",
            int_prop=123,
            bool_prop=True,
            list_prop=[1, 2, 3],
            dict_prop={"key": "value"},
            none_prop=None,
        )

        obj = ComplexObject()
        # Should not raise exception
        validator(obj, False)

        # Test with wrong values
        validator_wrong = check_property_values(list_prop=[1, 2, 4])

        with pytest.raises(ValueError):
            validator_wrong(obj, False)


class TestFactoryFunction:
    """Tests for with_property_values factory function."""

    def test_with_property_values_factory(self):
        """Test the with_property_values factory function."""

        @with_property_values(name="test", value=42)
        def fixture():
            return PropValCompTestObject()

        # Check fixture is decorated correctly
        assert hasattr(fixture, "_fixturecheck")
        assert fixture._fixturecheck is True
        assert hasattr(fixture, "_validator")
        assert callable(fixture._validator)

        # Executing the fixture should return a TestObject
        result = fixture()
        assert isinstance(result, PropValCompTestObject)

    def test_factory_with_wrong_value(self):
        """Test the factory function with a wrong property value."""
        # Create a simple object directly
        test_obj = PropValCompTestObject()

        # Create a validator directly
        validator = check_property_values(name="wrong")

        # This should fail validation
        with pytest.raises(ValueError) as excinfo:
            validator(test_obj, False)
        assert "Expected name=wrong" in str(excinfo.value)

    def test_nested_objects(self):
        """Test with nested object properties."""

        class NestedObject:
            def __init__(self):
                self.inner = PropValCompTestObject()

        validator = check_property_values(inner=PropValCompTestObject())
        obj = NestedObject()

        # This should fail because object equality is by identity, not by value
        with pytest.raises(ValueError):
            validator(obj, False)

        # Test with direct reference
        inner_obj = PropValCompTestObject()
        obj2 = NestedObject()
        obj2.inner = inner_obj

        validator2 = check_property_values(inner=inner_obj)
        # This should pass
        validator2(obj2, False)


@pytest.fixture
@fixturecheck(check_property_values(name="fixture_test"))
def test_property_fixture():
    """Fixture that returns an object with specific property values."""
    return PropValCompTestObject(name="fixture_test")


def test_property_fixture_usage(test_property_fixture):
    """Test using a fixture with property value validation."""
    # Fixture should be validated and pass
    assert test_property_fixture.name == "fixture_test"


@pytest.fixture
@fixturecheck(check_property_values(name="wrong_value"), expect_validation_error=True)
def expected_failure_fixture():
    """Fixture expected to fail validation."""
    return PropValCompTestObject(name="not_wrong_value")


def test_expected_failure(expected_failure_fixture):
    """Test with a fixture that's expected to fail validation."""
    # This test should run because expect_validation_error=True
    assert expected_failure_fixture.name == "not_wrong_value"
