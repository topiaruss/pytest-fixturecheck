"""Tests for the fixed property values validator."""

import pytest

from pytest_fixturecheck import fixturecheck, property_values_validator


class PropFixedTestObject:
    """Test object with properties."""

    def __init__(self, name="test", value=42):
        self.name = name
        self.value = value


def test_fixed_validator():
    """Test our fixed property values validator."""
    # Create validator with dictionary of expected values
    validator = property_values_validator({"name": "test", "value": 42})

    # Create a test object
    obj = PropFixedTestObject()

    # Test validation - should not raise
    validator(obj, False)

    # Test with a wrong value - should raise
    with pytest.raises(ValueError):
        validator(PropFixedTestObject(name="wrong"), False)

    # Test with missing property - should raise
    with pytest.raises(AttributeError):
        validator(object(), False)  # Plain object has no 'name' attribute


@pytest.fixture
@fixturecheck(property_values_validator({"name": "fixture_test"}))
def test_property_fixture():
    """Fixture with specific property value."""
    return PropFixedTestObject(name="fixture_test")


def test_fixture_with_property_validator(test_property_fixture):
    """Test using a fixture with our fixed validator."""
    assert test_property_fixture.name == "fixture_test"
