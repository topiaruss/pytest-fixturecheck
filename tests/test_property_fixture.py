"""Test file for property validation."""

import pytest

from pytest_fixturecheck import check_property_values, fixturecheck


class PropTestObject:
    """Test object with properties."""

    def __init__(self, name="test", value=42):
        self.name = name
        self.value = value


@pytest.fixture
@fixturecheck(check_property_values(name="fixture_test"))
def property_fixture():
    """A fixture with specific property values."""
    return PropTestObject(name="fixture_test")


def test_property_fixture(property_fixture):
    """Test that the property fixture works and passes validation."""
    assert property_fixture.name == "fixture_test"
    assert property_fixture.value == 42
