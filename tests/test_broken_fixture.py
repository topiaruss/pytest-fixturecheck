"""Test file with a broken fixture to demonstrate how pytest-fixturecheck works."""

import pytest

from pytest_fixturecheck import fixturecheck


class Item:
    """A simple item class."""

    def __init__(self, name):
        self.name = name


@fixturecheck
@pytest.fixture
def broken_fixture():
    """This fixture is broken and will raise an exception."""
    # Simulate a broken fixture by trying to access a non-existent attribute
    item = Item("test")
    return item.non_existent_attribute  # This will raise AttributeError


@pytest.mark.xfail(
    reason="This test is expected to fail due to the broken fixture - it demonstrates how fixturecheck works"
)
def test_using_broken_fixture(broken_fixture):
    """This test uses the broken fixture and would fail if the fixture wasn't checked early."""
    assert broken_fixture is not None
