"""Test configuration for pytest-fixturecheck."""

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


@pytest.fixture
@fixturecheck(has_required_fields("email"), expect_validation_error=True)
def missing_email_user():
    """A fixture with a user that's missing the expected email field."""
    return User(username="testuser") 