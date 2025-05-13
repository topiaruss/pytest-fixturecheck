"""Simple test file with a basic fixture."""

import pytest


@pytest.fixture
def simple_fixture():
    """A simple fixture that returns a string."""
    return "hello world"


def test_simple_fixture(simple_fixture):
    """Test using a simple fixture."""
    assert simple_fixture == "hello world"
