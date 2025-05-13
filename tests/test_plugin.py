"""Tests for the pytest-fixturecheck plugin."""

import pytest

from pytest_fixturecheck import fixturecheck


def test_fixturecheck_decorator_exists():
    """Test that the fixturecheck decorator exists."""
    assert callable(fixturecheck)


@fixturecheck
@pytest.fixture
def simple_fixture():
    """A simple fixture that returns a string."""
    return "test"


def test_fixture_with_fixturecheck(simple_fixture):
    """Test that a fixture with fixturecheck works."""
    assert simple_fixture == "test"
