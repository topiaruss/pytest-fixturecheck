"""
Example showing how to use pytest-fixturecheck with Django models.

This file demonstrates all the different ways to validate Django model fixtures:
1. Automatic validation with bare @fixturecheck
2. Using factory functions for common validation patterns
3. Flexible decorator ordering
4. Auto-skip functionality
"""

import pytest
from pytest_fixturecheck import fixturecheck

# Mock Django model classes for documentation purposes
# In a real project, these would be your actual Django models

class User:
    """Mock User model."""
    def __init__(self, username, email, is_active=True):
        self.username = username
        self.email = email
        self.is_active = is_active
        self._meta = type('_meta', (), {'get_field': lambda self, name: None})

    def save(self):
        """Save the user."""
        pass

    def delete(self):
        """Delete the user."""
        pass


class Book:
    """Mock Book model."""
    def __init__(self, title, author):
        self.title = title
        self.author = author
        self._meta = type('_meta', (), {'get_field': lambda self, name: None})

    def save(self):
        """Save the book."""
        pass


#
# Example 1: Auto-detected Django model validation
#

@pytest.fixture
@fixturecheck  # Auto-detects Django models
def user_fixture():
    """Create a user with automatic field validation."""
    return User(username="testuser", email="test@example.com")


#
# Example 2: Using factory functions for common validation patterns
#

# Check that specific fields exist
@pytest.fixture
@fixturecheck.with_model_validation("username", "email")
def validated_user():
    """Create a user and validate specific fields exist."""
    return User(username="validateduser", email="validated@example.com")


# Check required fields are present and non-None
@fixturecheck.with_required_fields("username", "email")
@pytest.fixture  # Different decorator order still works
def user_with_fields():
    """Create a user and validate required fields are present."""
    return User(username="fielduser", email="fields@example.com")


# Check required methods are present and callable
@pytest.fixture
@fixturecheck.with_required_methods("save", "delete")
def saveable_user():
    """Create a user and validate it has required methods."""
    return User(username="saveableuser", email="saveable@example.com")


# Check specific property values
@pytest.fixture
@fixturecheck.with_property_values(is_active=True, username="propertyuser")
def user_with_properties():
    """Create a user and validate specific property values."""
    return User(username="propertyuser", email="property@example.com")


#
# Example 3: Custom validator function
#

def validate_user_email(obj, is_collection_phase):
    """Custom validator that checks the email domain."""
    if is_collection_phase:
        return  # No validation during collection phase

    if not hasattr(obj, 'email'):
        raise AttributeError("User object missing email field")

    if not obj.email.endswith('@example.com'):
        raise ValueError(f"Email {obj.email} must end with @example.com")


@pytest.fixture
@fixturecheck(validate_user_email)
def custom_validated_user():
    """Create a user with custom email validation."""
    return User(username="customuser", email="custom@example.com")


#
# Example Tests
#

def test_user_fixture(user_fixture):
    """Test using the auto-validated user fixture."""
    assert user_fixture.username == "testuser"
    assert user_fixture.email == "test@example.com"


def test_validated_user(validated_user):
    """Test using the field-validated user fixture."""
    assert validated_user.username == "validateduser"
    assert validated_user.email == "validated@example.com"


def test_user_with_fields(user_with_fields):
    """Test using the user with required fields."""
    assert user_with_fields.username == "fielduser"
    assert user_with_fields.email == "fields@example.com"


def test_saveable_user(saveable_user):
    """Test using the user with required methods."""
    assert callable(saveable_user.save)
    assert callable(saveable_user.delete)


def test_user_with_properties(user_with_properties):
    """Test using the user with property validation."""
    assert user_with_properties.username == "propertyuser"
    assert user_with_properties.is_active is True


def test_custom_validated_user(custom_validated_user):
    """Test using the custom validated user."""
    assert custom_validated_user.email.endswith("@example.com")


#
# Example of broken fixture (will be skipped if auto-skip is enabled)
#

@pytest.fixture
@fixturecheck.with_property_values(is_active=True, username="wronguser")
def broken_user():
    """This fixture will fail validation because the username doesn't match."""
    return User(username="differentname", email="broken@example.com")


def test_broken_user(broken_user):
    """This test should be skipped if auto-skip is enabled."""
    assert broken_user.username == "wronguser"  # This will never execute with auto-skip
