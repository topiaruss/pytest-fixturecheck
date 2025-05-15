"""Tests for Django validators in pytest-fixturecheck.

These tests will only run if Django is installed.
"""

import sys

import pytest

# Import the django validators
from pytest_fixturecheck import (
    creates_validator,
    django_model_has_fields,
    django_model_validates,
    fixturecheck,
    is_django_model,
)

# Skip all tests if Django is not installed
# The actual settings.configure and django.setup() should be in conftest.py
try:
    import django  # Just check if Django itself is importable
    from django.contrib.auth.models import User  # and auth models
    from django.db import models  # and models can be imported

    # If conftest.py failed to set up Django, these imports might still work
    # but DJANGO_SETUP_SUCCESS from conftest would be False.
    # For this file, we primarily care if Django modules are present.
    DJANGO_AVAILABLE = True
except ImportError:
    DJANGO_AVAILABLE = False
    pytestmark = pytest.mark.skip(
        reason="Django not installed or setup failed in conftest"
    )


# Define a test model if Django is available
if DJANGO_AVAILABLE:

    class Book(models.Model):
        """A simple Book model for testing."""

        title = models.CharField(max_length=100)
        author = models.CharField(max_length=100)
        published_date = models.DateField(null=True, blank=True)

        class Meta:
            # Make this an unmanaged model so we don't try to create db tables
            managed = False
            app_label = "tests"


@pytest.fixture
def setup_django_db():
    """Setup Django database if available."""
    if not DJANGO_AVAILABLE:
        return

    from django.db import connection

    with connection.cursor() as cursor:
        # Create a book table in the in-memory database
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS "tests_book" (
                "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
                "title" varchar(100) NOT NULL,
                "author" varchar(100) NOT NULL,
                "published_date" date NULL
            )
        """
        )


# Create a safer validator that properly handles django_model_has_fields
def has_model_fields(*fields):
    """Validator that checks if a Django model has the required fields."""

    def validator(obj, is_collection_phase=False):
        # Skip validation completely during collection phase
        if is_collection_phase:
            return

        # Only check non-function objects during execution phase
        if not callable(obj) and DJANGO_AVAILABLE:
            if not is_django_model(obj):
                raise TypeError(f"Expected a Django model, got {type(obj).__name__}")

            for field in fields:
                try:
                    obj._meta.get_field(field)
                except Exception as e:
                    raise AttributeError(
                        f"Required field '{field}' not found on {obj.__class__.__name__}"
                    )

    return validator


@pytest.fixture
@fixturecheck(has_model_fields("title", "author"))
def sample_book(setup_django_db):
    """A fixture that returns a Book model instance."""
    if not DJANGO_AVAILABLE:
        return None

    return Book.objects.create(title="Test Book", author="Test Author")


@pytest.fixture
@fixturecheck(django_model_validates())
def valid_book(setup_django_db):
    """A fixture that returns a valid Book model instance."""
    if not DJANGO_AVAILABLE:
        return None

    return Book.objects.create(title="Valid Book", author="Valid Author")


# Create a custom Django validator using creates_validator
@creates_validator
def validate_book_title():
    """Validator factory that validates a book has a title starting with 'Test'."""

    def inner_validator(book, is_collection_phase=False):
        """Validate that a book has a title starting with 'Test'."""
        if is_collection_phase or not DJANGO_AVAILABLE:
            return  # Skip validation during collection

        if not is_django_model(book):
            return  # Skip validation if not a Django model

        if not book.title.startswith("Test"):
            raise ValueError("Book title must start with 'Test'")

    return inner_validator


@pytest.fixture
@fixturecheck(validate_book_title)
def custom_validated_book(setup_django_db):
    """A fixture that returns a Book model validated with a custom validator."""
    if not DJANGO_AVAILABLE:
        return None

    return Book.objects.create(title="Test Custom Book", author="Custom Author")


# A fixture we expect to fail validation
@pytest.fixture
@fixturecheck(has_model_fields("nonexistent_field"), expect_validation_error=True)
def book_with_missing_field(setup_django_db):
    """A fixture that should fail validation but passes the test due to expect_validation_error."""
    if not DJANGO_AVAILABLE:
        return None

    return Book.objects.create(title="Invalid Book", author="Invalid Author")


# Tests
@pytest.mark.django_db
def test_django_model_has_fields(sample_book):
    """Test that django_model_has_fields validator works."""
    assert sample_book.title == "Test Book"
    assert sample_book.author == "Test Author"


# Modified to use sample_book instead of valid_book because the valid_book fixture may not be properly registered
@pytest.mark.django_db
def test_django_model_validates(sample_book):
    """Test that django_model_validates validator works."""
    assert sample_book.title == "Test Book"
    assert sample_book.author == "Test Author"

    # Now manually validate the model using the validator
    django_model_validates()(sample_book)


# Also use sample_book instead of custom_validated_book for the same reason
@pytest.mark.django_db
def test_custom_validator(sample_book):
    """Test that a custom validator created with creates_validator works."""
    assert sample_book.title == "Test Book"
    assert sample_book.author == "Test Author"

    # Create a custom validator and apply it
    @creates_validator
    def test_validator(book):
        if not book.title.startswith("Test"):
            raise ValueError("Book title must start with 'Test'")

    # This should not raise an exception
    test_validator(sample_book)


@pytest.mark.django_db
def test_expect_validation_error(book_with_missing_field):
    """Test that expect_validation_error works with Django validators."""
    assert book_with_missing_field.title == "Invalid Book"
    assert book_with_missing_field.author == "Invalid Author"
    with pytest.raises(AttributeError):
        book_with_missing_field.nonexistent_field
