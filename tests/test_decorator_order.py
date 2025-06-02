"""Test file that demonstrates the correct decorator order for pytest-fixturecheck."""

import pytest

from pytest_fixturecheck import fixturecheck


# Function order 1: @pytest.fixture first, then @fixturecheck (CORRECT)
@pytest.fixture
@fixturecheck()
def fixture_order1():
    """A fixture with pytest.fixture before fixturecheck (correct)."""
    return "order1"


# Function order 2: @pytest.fixture first, then @fixturecheck (CORRECT)
@pytest.fixture
@fixturecheck()
def fixture_order2():
    """A fixture with pytest.fixture before fixturecheck (correct)."""
    return "order2"


def test_fixture_order1(fixture_order1):
    """Test that fixture with correct decorator order works."""
    assert fixture_order1 == "order1"


def test_fixture_order2(fixture_order2):
    """Test that fixture with correct decorator order works."""
    assert fixture_order2 == "order2"
