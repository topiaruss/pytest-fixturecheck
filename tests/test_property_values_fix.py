"""Test for a simplified property values validator."""

import pytest
from pytest_fixturecheck import fixturecheck
from pytest_fixturecheck.utils import creates_validator


class TestObject:
    """Test object with properties."""
    
    def __init__(self, name="test", value=42):
        self.name = name
        self.value = value


# Create our own property validator function
@creates_validator
def check_properties(obj):
    """Check that properties have the expected values."""
    if obj.name != "test":
        raise ValueError(f"Expected name=test, got {obj.name}")
    if obj.value != 42:
        raise ValueError(f"Expected value=42, got {obj.value}")


def test_custom_validator():
    """Test our custom property validator."""
    # Create a test object
    obj = TestObject()
    
    # Test the validator directly
    check_properties(obj, False)  # Should not raise
    
    # Test with a wrong value
    with pytest.raises(ValueError):
        check_properties(TestObject(name="wrong"), False)


# Test with a fixture
@pytest.fixture
@fixturecheck(check_properties)
def my_valid_object():
    """Fixture with valid object."""
    return TestObject()


@pytest.mark.skip(reason="Fixture discovery issue")
def test_fixture_with_validator(my_valid_object):
    """Test using the fixture with our validator."""
    assert my_valid_object.name == "test"
    assert my_valid_object.value == 42 