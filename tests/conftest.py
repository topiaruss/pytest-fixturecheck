"""Test configuration for pytest-fixturecheck."""

import inspect
import pytest

from pytest_fixturecheck import fixturecheck, has_required_fields
from pytest_fixturecheck.utils import creates_validator


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


# Fixed property values validator that works with a dictionary
def conftest_property_values_validator(expected_values):
    """
    Create a validator that checks if the fixture has the expected property values.
    
    Args:
        expected_values: Dictionary of property names and their expected values
        
    Returns:
        A validator function
    """
    @creates_validator
    def validator(obj):
        for prop_name, expected_value in expected_values.items():
            if not hasattr(obj, prop_name):
                raise AttributeError(f"Property '{prop_name}' missing from {obj.__class__.__name__}")
            
            actual_value = getattr(obj, prop_name)
            if actual_value != expected_value:
                raise ValueError(f"Expected {prop_name}={expected_value}, got {actual_value}")
    
    return validator


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


class TestObject:
    """Test object with properties for property validation tests."""
    
    def __init__(self, name="test", value=42):
        self.name = name
        self.value = value


@pytest.fixture
@fixturecheck(conftest_property_values_validator({"name": "fixture_test"}))
def property_fixture():
    """A fixture with specific property values."""
    return TestObject(name="fixture_test") 