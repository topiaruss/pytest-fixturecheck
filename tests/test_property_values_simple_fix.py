"""Simple test for fixed property values validation."""

import pytest

from pytest_fixturecheck import fixturecheck, property_values_validator


class SimpleObject:
    """A simple object with properties."""

    def __init__(self, name="test", value=42):
        self.name = name
        self.value = value


def test_direct_validator():
    """Test direct use of the validator."""
    # Create validator with a dictionary
    validator = property_values_validator({"name": "test"})

    # Create object
    obj = SimpleObject()

    # Should pass
    validator(obj, False)

    # Should fail with wrong value
    with pytest.raises(ValueError):
        validator(SimpleObject(name="wrong"), False)


# Define fixture first, then apply decorator
@pytest.fixture
def simple_fixture():
    """Fixture that returns an object with name='fixture_test'."""
    return SimpleObject(name="fixture_test")


# Apply fixturecheck separately (this may avoid the fixture collection issue)
simple_fixture = fixturecheck(property_values_validator({"name": "fixture_test"}))(
    simple_fixture
)


def test_with_fixture(simple_fixture):
    """Test using the fixture with our validator."""
    assert simple_fixture.name == "fixture_test"
