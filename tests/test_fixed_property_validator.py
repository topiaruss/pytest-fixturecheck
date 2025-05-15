"""Test for the fixed property values validator."""

import pytest

from pytest_fixturecheck import (
    fixturecheck,
    property_values_validator,
    with_property_values,
)


class ValTestObject:
    """Test object with properties."""

    def __init__(self, name="test", value=42):
        self.name = name
        self.value = value


def test_property_values_validator():
    """Test the property_values_validator function."""
    # Create a validator
    validator = property_values_validator({"name": "test", "value": 42})

    # Create a test object
    obj = ValTestObject()

    # Should pass validation
    validator(obj, False)

    # Should fail with wrong value
    with pytest.raises(ValueError):
        validator(ValTestObject(name="wrong"), False)


# First define with pytest.fixture, then apply fixturecheck with our validator
@pytest.fixture
@fixturecheck(property_values_validator({"name": "fixture_test"}))
def test_object_fixture():
    """Fixture that returns an object with a specific name."""
    return ValTestObject(name="fixture_test")


def test_with_validated_fixture(test_object_fixture):
    """Test using the fixture with validation."""
    assert test_object_fixture.name == "fixture_test"


# Test the with_property_values factory function
@pytest.fixture
@with_property_values(name="factory_test")
def factory_validated_fixture():
    """Fixture validated with our fixed factory function."""
    return ValTestObject(name="factory_test")


def test_with_factory_validated_fixture(factory_validated_fixture):
    """Test using the fixture with our fixed factory function."""
    assert factory_validated_fixture.name == "factory_test"
