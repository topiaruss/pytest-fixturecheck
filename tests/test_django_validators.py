"""Tests for Django validators in pytest-fixturecheck.

These tests will only run if Django is installed.
"""

import pytest
import sys

# Import the django validators
from pytest_fixturecheck import (
    fixturecheck,
    is_django_model,
    django_model_has_fields,
    django_model_validates,
    creates_validator,
)

# Skip all tests if Django is not installed
try:
    import django
    from django.conf import settings
    
    # Configure minimal Django settings for tests
    if not settings.configured:
        settings.configure(
            DATABASES={
                'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': ':memory:',
                }
            },
            INSTALLED_APPS=[
                'django.contrib.auth',
                'django.contrib.contenttypes',
            ],
        )
        django.setup()
        
    from django.contrib.auth.models import User
    from django.db import models
    
    DJANGO_AVAILABLE = True
except ImportError:
    DJANGO_AVAILABLE = False
    pytestmark = pytest.mark.skip(reason="Django not installed")


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
            app_label = 'tests'


@pytest.fixture
def setup_django_db():
    """Setup Django database if available."""
    if not DJANGO_AVAILABLE:
        return
    
    from django.db import connection
    with connection.cursor() as cursor:
        # Create a book table in the in-memory database
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS "tests_book" (
                "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
                "title" varchar(100) NOT NULL,
                "author" varchar(100) NOT NULL,
                "published_date" date NULL
            )
        ''')


@pytest.mark.skipif(not DJANGO_AVAILABLE, reason="Django not installed")
@pytest.fixture
@fixturecheck(django_model_has_fields("title", "author"))
def sample_book(setup_django_db):
    """A fixture that returns a Book model instance."""
    if not DJANGO_AVAILABLE:
        return None
    
    return Book.objects.create(
        title="Test Book",
        author="Test Author"
    )


@pytest.mark.skipif(not DJANGO_AVAILABLE, reason="Django not installed")
@pytest.fixture
@fixturecheck(django_model_validates())
def valid_book(setup_django_db):
    """A fixture that returns a valid Book model instance."""
    if not DJANGO_AVAILABLE:
        return None
    
    return Book.objects.create(
        title="Valid Book",
        author="Valid Author"
    )


# Create a custom Django validator using creates_validator
@creates_validator
def validate_book_title(book):
    """Validate that a book has a title starting with 'Test'."""
    if not is_django_model(book):
        raise TypeError("Expected a Django model")
    
    if not book.title.startswith("Test"):
        raise ValueError("Book title must start with 'Test'")


@pytest.mark.skipif(not DJANGO_AVAILABLE, reason="Django not installed")
@pytest.fixture
@fixturecheck(validate_book_title)
def custom_validated_book(setup_django_db):
    """A fixture that returns a Book model validated with a custom validator."""
    if not DJANGO_AVAILABLE:
        return None
    
    return Book.objects.create(
        title="Test Custom Book",
        author="Custom Author"
    )


# A fixture we expect to fail validation
@pytest.mark.skipif(not DJANGO_AVAILABLE, reason="Django not installed")
@pytest.fixture
@fixturecheck(django_model_has_fields("nonexistent_field"), expect_validation_error=True)
def book_with_missing_field(setup_django_db):
    """A fixture that should fail validation but passes the test due to expect_validation_error."""
    if not DJANGO_AVAILABLE:
        return None
    
    return Book.objects.create(
        title="Invalid Book",
        author="Invalid Author"
    )


# Tests
@pytest.mark.skipif(not DJANGO_AVAILABLE, reason="Django not installed")
def test_django_model_has_fields(sample_book):
    """Test that django_model_has_fields validator works."""
    assert sample_book.title == "Test Book"
    assert sample_book.author == "Test Author"


@pytest.mark.skipif(not DJANGO_AVAILABLE, reason="Django not installed")
def test_django_model_validates(valid_book):
    """Test that django_model_validates validator works."""
    assert valid_book.title == "Valid Book"
    assert valid_book.author == "Valid Author"


@pytest.mark.skipif(not DJANGO_AVAILABLE, reason="Django not installed")
def test_custom_validator(custom_validated_book):
    """Test that a custom validator created with creates_validator works."""
    assert custom_validated_book.title == "Test Custom Book"
    assert custom_validated_book.author == "Custom Author"


@pytest.mark.skipif(not DJANGO_AVAILABLE, reason="Django not installed")
def test_expect_validation_error(book_with_missing_field):
    """Test that expect_validation_error works with Django validators."""
    assert book_with_missing_field.title == "Invalid Book"
    assert book_with_missing_field.author == "Invalid Author"
    with pytest.raises(AttributeError):
        book_with_missing_field.nonexistent_field 