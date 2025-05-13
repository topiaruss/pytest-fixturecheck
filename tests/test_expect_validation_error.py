"""Test file for the expect_validation_error parameter."""

import inspect

import pytest

from pytest_fixturecheck import fixturecheck, has_required_fields


class User:
    """A simple user class for testing."""

    def __init__(self, username=None):
        self.username = username


# This validator expects the username to be set
def validate_username(obj, is_collection_phase=False):
    """Custom validator that checks for a username."""
    if is_collection_phase or inspect.isfunction(obj):
        return
    if not hasattr(obj, "username"):
        raise AttributeError("User must have a username attribute")
    if obj.username is None:
        raise ValueError("Username cannot be None")


# Fixture with a validator that should pass
@fixturecheck(validate_username)
@pytest.fixture
def valid_user():
    """A fixture with a valid user."""
    return User(username="testuser")


# Fixture with a validator that should fail
@fixturecheck(validate_username, expect_validation_error=True)
@pytest.fixture
def invalid_user():
    """A fixture with an invalid user that should fail validation."""
    return User(username=None)


# Another way to define an invalid fixture - with a factory function
@fixturecheck(has_required_fields("email"), expect_validation_error=True)
@pytest.fixture
def missing_email_user():
    """A fixture with a user that's missing the expected email field."""
    return User(username="testuser")


# Test that valid fixture works
def test_valid_user(valid_user):
    """Test that a fixture with a valid validator works."""
    assert valid_user.username == "testuser"


# Test that we can create a fixture we expect to fail validation
def test_invalid_user(invalid_user):
    """Test that a fixture with an invalid validator doesn't fail the test when we expect it to fail."""
    assert invalid_user.username is None


# Test with the factory function validator
def test_missing_email_user(missing_email_user):
    """Test that a fixture missing an expected field doesn't fail when we expect it to fail."""
    assert missing_email_user.username == "testuser"
    assert not hasattr(missing_email_user, "email")
