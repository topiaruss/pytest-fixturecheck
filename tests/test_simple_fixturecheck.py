"""Simple test file with a fixture that uses the fixturecheck decorator."""

import pytest

from pytest_fixturecheck import fixturecheck


@pytest.fixture
@fixturecheck
def checked_fixture():
    """A fixture that uses the fixturecheck decorator."""
    return "hello world"


def test_checked_fixture(checked_fixture):
    """Test using a fixture that has been checked."""
    assert checked_fixture == "hello world"
