"""Test file that demonstrates that decorator order doesn't matter."""

import pytest

from pytest_fixturecheck import fixturecheck


# Function order 1: @fixturecheck first, then @pytest.fixture
@fixturecheck
@pytest.fixture
def fixture_order1():
    """A fixture with fixturecheck before pytest.fixture."""
    return "order1"


# Function order 2: @pytest.fixture first, then @fixturecheck
@pytest.fixture
@fixturecheck
def fixture_order2():
    """A fixture with pytest.fixture before fixturecheck."""
    return "order2"


def test_fixture_order1(fixture_order1):
    """Test that fixture with @fixturecheck first works."""
    assert fixture_order1 == "order1"


def test_fixture_order2(fixture_order2):
    """Test that fixture with @pytest.fixture first works."""
    assert fixture_order2 == "order2"
