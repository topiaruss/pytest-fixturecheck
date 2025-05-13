"""Basic test for pytest-fixturecheck functionality."""

import pytest

from pytest_fixturecheck import fixturecheck


@pytest.fixture
def simple_fixture():
    """A simple fixture that returns a string."""
    return "hello world"


@pytest.fixture
@fixturecheck
def checked_fixture():
    """A fixture checked with the fixturecheck decorator."""
    return "checked hello world"


def test_simple_fixture(simple_fixture):
    """Test that a simple fixture works."""
    assert simple_fixture == "hello world"


def test_checked_fixture(checked_fixture):
    """Test that a fixture with the fixturecheck decorator works."""
    assert checked_fixture == "checked hello world"
