"""Minimal test for has_property_values validator."""

import pytest

from pytest_fixturecheck.validators_fix import check_property_values


class SimpleObject:
    """A simple object with a name property."""

    def __init__(self, name="test"):
        self.name = name


def test_direct_validator_usage():
    """Test using the validator directly."""
    # Create validator
    name_validator = check_property_values(name="test")

    # Create object
    obj = SimpleObject()

    # This should not raise an exception
    name_validator(obj, False)

    # Validate with a different name - should raise ValueError
    with pytest.raises(ValueError):
        name_validator(SimpleObject(name="wrong"), False)
