"""Test file with validator and fixtures defined inline."""

import inspect

import pytest

from pytest_fixturecheck import fixturecheck


# Define a simple class for testing
class User:
    """A simple user class for testing."""

    def __init__(self, username=None):
        self.username = username


# Define a validator function
def validate_username(obj, is_collection_phase=False):
    """Validate that a user has a username."""
    if is_collection_phase or inspect.isfunction(obj):
        return
    if not hasattr(obj, "username"):
        raise AttributeError("User must have a username")
    if obj.username is None:
        raise ValueError("Username cannot be None")


# Define fixtures with different validation expectations
@pytest.fixture
def simple_fixture():
    """A simple fixture with no validation."""
    return "hello world"


@pytest.fixture
@fixturecheck
def checked_fixture():
    """A fixture with the fixturecheck decorator."""
    return User(username="testuser")


@pytest.fixture
@fixturecheck(validate_username)
def validated_fixture():
    """A fixture with a custom validator."""
    return User(username="testuser")


@pytest.fixture
@fixturecheck(validate_username, expect_validation_error=True)
def expected_to_fail():
    """A fixture expected to fail validation."""
    return User(username=None)


# Tests
def test_simple(simple_fixture):
    """Test using a simple fixture."""
    assert simple_fixture == "hello world"


def test_checked(checked_fixture):
    """Test using a fixture with fixturecheck."""
    assert checked_fixture.username == "testuser"


def test_validated(validated_fixture):
    """Test using a fixture with custom validation."""
    assert validated_fixture.username == "testuser"


def test_expected_to_fail(expected_to_fail):
    """Test using a fixture expected to fail validation."""
    assert expected_to_fail.username is None
