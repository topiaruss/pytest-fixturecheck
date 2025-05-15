"""
Tests to verify the behavior of the 'strict' parameter in property validators.

These tests verify that the strict parameter works as expected in the validators:
- strict=True (default): Raises exceptions for mismatched properties
- strict=False: Issues warnings for mismatched properties
"""

import warnings

import pytest

from pytest_fixturecheck import fixturecheck
from pytest_fixturecheck.validators_fix import (
    check_property_values,
    with_property_values,
)


class StrictParamTestObject:
    def __init__(self, name, value):
        self.name = name
        self.value = value


def test_strict_parameter_default_in_check_property_values():
    """Test that strict=True (default) raises exceptions in check_property_values."""

    # Create a validator with default strict behavior
    validator = check_property_values(name="test", value=42)

    # Create a test object with mismatched values
    obj = StrictParamTestObject("wrong", 99)

    # The validator should raise an exception by default
    with pytest.raises(ValueError):
        validator(obj, False)  # False = not in collection phase


def test_strict_parameter_true_in_check_property_values():
    """Test that strict=True raises exceptions in check_property_values."""

    # Create a validator with explicit strict=True
    validator = check_property_values(strict=True, name="test", value=42)

    # Create a test object with mismatched values
    obj = StrictParamTestObject("wrong", 99)

    # The validator should raise an exception with strict=True
    with pytest.raises(ValueError):
        validator(obj, False)  # False = not in collection phase


def test_strict_parameter_false_in_check_property_values():
    """Test that strict=False issues warnings in check_property_values."""

    # Create a validator with strict=False
    validator = check_property_values(strict=False, name="test", value=42)

    # Create a test object with mismatched values
    obj = StrictParamTestObject("wrong", 99)

    # The validator should issue warnings, not exceptions with strict=False
    with warnings.catch_warnings(record=True) as recorded_warnings:
        warnings.simplefilter("always")

        # Should not raise an exception
        validator(obj, False)  # False = not in collection phase

        # Should have issued warnings for each mismatched property
        assert len(recorded_warnings) == 2
        assert "Expected name=test" in str(recorded_warnings[0].message)
        assert "Expected value=42" in str(recorded_warnings[1].message)


def test_strict_parameter_default_in_with_property_values():
    """Test that strict=True (default) raises exceptions in with_property_values."""

    # Create a validator with default strict behavior
    validator = with_property_values(name="test", value=42)

    # Define a fixture function that returns a mismatched object
    def fixture_func():
        return StrictParamTestObject("wrong", 99)

    # Apply the validator to the fixture function
    decorated_func = validator(fixture_func)

    # The validator should raise an exception by default
    with pytest.raises(ValueError):
        decorated_func()


def test_strict_parameter_true_in_with_property_values():
    """Test that strict=True raises exceptions in with_property_values."""

    # Create a validator with explicit strict=True
    validator = with_property_values(strict=True, name="test", value=42)

    # Define a fixture function that returns a mismatched object
    def fixture_func():
        return StrictParamTestObject("wrong", 99)

    # Apply the validator to the fixture function
    decorated_func = validator(fixture_func)

    # The validator should raise an exception with strict=True
    with pytest.raises(ValueError):
        decorated_func()


def test_strict_parameter_false_in_with_property_values():
    """Test that strict=False issues warnings in with_property_values."""

    # Create a validator with strict=False
    validator = with_property_values(strict=False, name="test", value=42)

    # Define a fixture function that returns a mismatched object
    def fixture_func():
        return StrictParamTestObject("wrong", 99)

    # Apply the validator to the fixture function
    decorated_func = validator(fixture_func)

    # The validator should issue warnings, not exceptions with strict=False
    with warnings.catch_warnings(record=True) as recorded_warnings:
        warnings.simplefilter("always")

        # Should not raise an exception
        result = decorated_func()

        # Should have issued warnings for each mismatched property
        assert len(recorded_warnings) == 2
        assert "Expected name=test" in str(recorded_warnings[0].message)
        assert "Expected value=42" in str(recorded_warnings[1].message)

        # Should still return the fixture result
        assert result.name == "wrong"
        assert result.value == 99
