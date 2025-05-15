"""Test for a simplified property values validator."""

import pytest

from pytest_fixturecheck import fixturecheck


class PropFixTestObject:
    """Test object with properties."""

    def __init__(self, name="test", value=42):
        self.name = name
        self.value = value


# Simple direct validator function without the decorator
def direct_check_properties(obj, is_collection_phase=False):
    """Check that properties have the expected values directly."""
    if is_collection_phase:
        return

    if not isinstance(obj, PropFixTestObject):
        return

    if obj.name != "test":
        raise ValueError(f"Expected name=test, got {obj.name}")
    if obj.value != 42:
        raise ValueError(f"Expected value=42, got {obj.value}")


# Create validator for fixturecheck
def check_properties():
    """Create a validator for fixturecheck."""
    return direct_check_properties


def test_custom_validator():
    """Test our custom property validator."""
    # Create a test object
    obj = PropFixTestObject()

    # Test the validator directly
    direct_check_properties(obj, False)  # Should not raise

    # Test with a wrong value - this should raise a ValueError
    wrong_obj = PropFixTestObject(name="wrong")
    with pytest.raises(ValueError):
        direct_check_properties(wrong_obj, False)


# Test with a fixture
@pytest.fixture
@fixturecheck(check_properties())
def my_valid_object():
    """Fixture with valid object."""
    return PropFixTestObject()


@pytest.mark.skip(reason="Fixture discovery issue")
def test_fixture_with_validator(my_valid_object):
    """Test using the fixture with our validator."""
    assert my_valid_object.name == "test"
    assert my_valid_object.value == 42
