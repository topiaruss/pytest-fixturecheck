"""Test configuration for pytest-fixturecheck."""

import inspect
import pytest

# Configure Django settings centrally for all tests that might need it
try:
    import django
    from django.conf import settings

    if not settings.configured:
        settings.configure(
            DATABASES={
                "default": {
                    "ENGINE": "django.db.backends.sqlite3",
                    "NAME": ":memory:",
                }
            },
            INSTALLED_APPS=[
                "django.contrib.auth",
                "django.contrib.contenttypes",
                # "pytest_fixturecheck.tests", # Removed this, as it's not an importable module
            ],
            # Minimal other settings if required by auth or other apps
            SECRET_KEY='dummysecret',
        )
    DJANGO_SETUP_SUCCESS = True
except ImportError:
    DJANGO_SETUP_SUCCESS = False


from pytest_fixturecheck import fixturecheck, has_required_fields
from pytest_fixturecheck.utils import creates_validator
from pytest_fixturecheck.validators_advanced import nested_property_validator
from pytest_fixturecheck.validators import is_instance_of


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
                raise AttributeError(
                    f"Property '{prop_name}' missing from {obj.__class__.__name__}"
                )

            actual_value = getattr(obj, prop_name)
            if actual_value != expected_value:
                raise ValueError(
                    f"Expected {prop_name}={expected_value}, got {actual_value}"
                )

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


# Added from test_advanced_validators_comprehensive.py for working_camera_fixture
class Config:
    def __init__(self, resolution: str, frame_rate: int):
        self.resolution = resolution
        self.frame_rate = frame_rate

class Camera:
    def __init__(self, name: str, config: Config):
        self.name = name
        self.config = config

# Define the validator instance separately
_working_camera_validator_instance = nested_property_validator(
    name="Test", config__resolution="1280x720", config__frame_rate=30
)

@pytest.fixture
@fixturecheck(validator=_working_camera_validator_instance)
def working_camera_fixture():
    return Camera("Test", Config("1280x720", 30))
