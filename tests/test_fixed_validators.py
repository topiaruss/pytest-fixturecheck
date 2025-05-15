"""Tests for the fixed validators."""

import pytest

from pytest_fixturecheck import fixturecheck
from pytest_fixturecheck.validators_fix import (
    check_property_values,
    property_values_validator,
    with_property_values,
)


class FixValTestObject:
    """Test object with properties."""

    def __init__(self, name="test", value=42):
        self.name = name
        self.value = value


def test_direct_object():
    """Test a direct object without validation."""
    obj = FixValTestObject(name="direct")
    assert obj.name == "direct"
    assert obj.value == 42


# Test the property_values_validator function
def test_property_values_validator():
    """Test the property_values_validator function."""
    # Create a validator
    validator = property_values_validator({"name": "test", "value": 42})

    # Test with a matching object
    validator(FixValTestObject(), False)

    # Test with a non-matching object
    with pytest.raises(ValueError):
        validator(FixValTestObject(name="wrong"), False)


# Test the check_property_values function
def test_check_property_values():
    """Test the check_property_values function."""
    # Create a validator with keyword arguments
    validator = check_property_values(name="test", value=42)

    # Test with a matching object
    validator(FixValTestObject(), False)

    # Test with a non-matching object
    with pytest.raises(ValueError):
        validator(FixValTestObject(name="wrong"), False)


# Testing fixtures with our validators
@pytest.fixture
@fixturecheck(property_values_validator({"name": "fixture1"}))
def fixture_with_validator():
    """Fixture validated with property_values_validator."""
    return FixValTestObject(name="fixture1")


@pytest.fixture
@fixturecheck(check_property_values(name="fixture2"))
def fixture_with_check_property_values():
    """Fixture validated with check_property_values."""
    return FixValTestObject(name="fixture2")


@pytest.fixture
@with_property_values(name="fixture3")
def fixture_with_factory():
    """Fixture validated with with_property_values factory."""
    return FixValTestObject(name="fixture3")


def test_fixture_with_validator(fixture_with_validator):
    """Test using the fixture_with_validator."""
    assert fixture_with_validator.name == "fixture1"


def test_fixture_with_check_property_values(fixture_with_check_property_values):
    """Test using the fixture_with_check_property_values."""
    assert fixture_with_check_property_values.name == "fixture2"
    assert fixture_with_check_property_values.value == 42


def test_fixture_with_factory(fixture_with_factory):
    """Test using the fixture_with_factory."""
    assert fixture_with_factory.name == "fixture3"
    assert fixture_with_factory.value == 42
