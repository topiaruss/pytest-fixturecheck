"""Test file for the expect_validation_error parameter."""

import inspect

import pytest

from pytest_fixturecheck import fixturecheck, has_required_fields


class User:
    """A simple user class for testing."""

    def __init__(self, username=None):
        self.username = username


# Custom validator function
def validate_user(obj, is_collection_phase=False):
    """Validate that a user has a username."""
    if is_collection_phase or inspect.isfunction(obj):
        return
    if not hasattr(obj, "username"):
        raise AttributeError("User must have a username")
    if obj.username is None:
        raise ValueError("Username cannot be None")


@pytest.fixture
@fixturecheck(validate_user)
def valid_user():
    """A fixture with a valid user."""
    return User(username="testuser")


@pytest.fixture
@fixturecheck(validate_user, expect_validation_error=True)
def invalid_user():
    """A fixture with an invalid user that should fail validation."""
    return User(username=None)


def test_valid_user(valid_user):
    """Test that a valid user passes validation."""
    assert valid_user.username == "testuser"


def test_invalid_user(invalid_user):
    """Test that an invalid user still works with expect_validation_error=True."""
    assert invalid_user.username is None
