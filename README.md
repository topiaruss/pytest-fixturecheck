# pytest-fixturecheck

```
  _____        _            _    _____ _      _                    _____  _               _    
 |  __ \      | |          | |  |  __ (_)    | |                  / ____|| |             | |   
 | |__) |_   _| |_ ___  ___| |_ | |__) _ ____| |_ _   _ _ __ ___ | |     | |__   ___  ___| | __
 |  ___/| | | | __/ _ \/ __| __||  ___/ |_  /| __| | | | '__/ _ \| |     | '_ \ / _ \/ __| |/ /
 | |    | |_| | ||  __/\__ \ |_ | |   | |/ / | |_| |_| | | |  __/| |____ | | | |  __/ (__|   < 
 |_|     \__, |\__\___||___/\__||_|   |_/___(_)__|\__,_|_|  \___| \_____||_| |_|\___|\___|_|\_\
          __/ |                                                                                 
         |___/                                                                                  
```

[![PyPI version](https://img.shields.io/pypi/v/pytest-fixturecheck.svg)](https://pypi.org/project/pytest-fixturecheck/)
[![Python Versions](https://img.shields.io/pypi/pyversions/pytest-fixturecheck.svg)](https://pypi.org/project/pytest-fixturecheck/)
[![CI](https://github.com/topiaruss/pytest-fixturecheck/actions/workflows/ci.yml/badge.svg)](https://github.com/topiaruss/pytest-fixturecheck/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/topiaruss/pytest-fixturecheck/branch/main/graph/badge.svg)](https://codecov.io/gh/topiaruss/pytest-fixturecheck)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A pytest plugin to validate fixtures before they're used in tests. Catch broken fixtures early before they cause confusing test failures.

## The Problem

In complex test suites, particularly when using Django or other ORMs, fixtures can silently break due to model changes. For example:

- A database model field gets renamed, but fixtures that create test data aren't updated
- A fixture depends on another fixture that changes its return structure
- Schema migrations occur but fixture setup code isn't updated

This causes confusing test failures because the error appears in the test using the fixture, not in the fixture itself. It can be hard to diagnose that a broken fixture is the culprit, not the actual test logic.

## Why pytest-fixturecheck?

- **Early Detection**: Identifies fixture issues before tests run
- **Clear Error Messages**: Points directly to the broken fixture, not symptoms
- **Django Integration**: Special validation for Django model fields
- **Simple API**: Just add a decorator to fixtures you want validated
- **Zero Overhead**: Only runs during collection, doesn't slow down normal testing

## What's New in v0.2.0

- **Auto-detection of Django models**: No validator needed for basic Django model validation
- **Decorator order flexibility**: Works with `@fixturecheck` before or after `@pytest.fixture`
- **Factory functions**: Simplified validation with built-in validators
- **Auto-skip functionality**: Optionally skip tests with broken fixtures instead of failing
- **Phase-aware validation**: Validators can access both the fixture function and its return value

## Installation

```bash
pip install pytest-fixturecheck
```

## Usage

### Basic Usage

Add the `@fixturecheck` decorator to any fixture you want to validate:

```python
from pytest_fixturecheck import fixturecheck

@fixturecheck
@pytest.fixture
def author():
    return Author.objects.create(name="Marian Brook")
```

This will execute the fixture once during collection time to verify it can run without errors. With Django models, it will automatically validate field access without requiring a custom validator.

### Advanced Usage with Factory Functions

```python
# Validate that specific fields exist and are non-None
@pytest.fixture
@fixturecheck.with_required_fields("username", "email")
def user(db):
    return User.objects.create_user(username="testuser", email="test@example.com")

# Validate that specific methods exist and are callable
@fixturecheck.with_required_methods("save", "delete")
@pytest.fixture
def book(db):
    return Book.objects.create(title="Test Book")

# Validate that specific model fields exist
@pytest.fixture
@fixturecheck.with_model_validation("title", "author", "publisher")
def book(db):
    return Book.objects.create(title="Test Book")

# Validate property values
@pytest.fixture
@fixturecheck.with_property_values(is_active=True, is_staff=False)
def staff_user(db):
    return User.objects.create_user(username="staffuser", is_active=True, is_staff=False)
```

### Custom Validators

You can create custom validators that validate both the fixture function (during collection) and the fixture result:

```python
def validate_user_permissions(obj, is_collection_phase):
    if is_collection_phase:
        # Validate the fixture function itself
        # This runs during test collection
        pass
    else:
        # Validate the fixture result
        # This runs during fixture execution
        if not hasattr(obj, 'has_perm'):
            raise AttributeError("User missing permission method")
            
        # Check that user has expected permissions
        if not obj.has_perm('auth.add_user'):
            raise ValueError("User missing required permission")

@pytest.fixture
@fixturecheck(validate_user_permissions)
def admin_user(db):
    return User.objects.create_superuser(
        username="admin", email="admin@example.com", password="password"
    )
```

### Auto-Skip Functionality

You can configure pytest-fixturecheck to skip tests with broken fixtures instead of failing completely. Add this to your `pytest.ini`:

```ini
[pytest]
fixturecheck-auto-skip = true
```

When enabled, tests using broken fixtures will be skipped with a clear reason showing the fixture error.

## Django Integration Examples

Here's a complete example showing common Django fixture patterns with validation:

```python
# conftest.py
import pytest
from pytest_fixturecheck import fixturecheck
from myapp.models import Author, Publisher, Book

@pytest.fixture
@fixturecheck  # Auto-detects Django models - no validator needed!
def author(db):
    """Create a test author."""
    return Author.objects.create(name="Jane Austen")

@pytest.fixture
@fixturecheck  # Auto-detects Django models
def publisher(db):
    """Create a test publisher."""
    return Publisher.objects.create(name="Classic Books Ltd")

@pytest.fixture
@fixturecheck.with_model_validation("title", "author", "publisher")
def book(db, author, publisher):
    """Create a test book with validated fields."""
    return Book.objects.create(
        title="Pride and Prejudice",
        author=author,
        publisher=publisher,
        year_published=1813
    )

# Use a custom validator for complex validation logic
def validate_book_relations(obj, is_collection_phase):
    if is_collection_phase:
        return  # Skip during collection phase
        
    # Validate that the book has the right relations
    if not hasattr(obj, 'author') or not obj.author:
        raise ValueError("Book must have an author")
        
    if not hasattr(obj, 'publisher') or not obj.publisher:
        raise ValueError("Book must have a publisher")
            
@pytest.fixture
@fixturecheck(validate_book_relations)
def sequel(db, book):
    """Create a sequel book with relation validation."""
    return Book.objects.create(
        title="Sense and Sensibility",
        author=book.author,
        publisher=book.publisher,
        year_published=1811
    )
```

## How It Works

The plugin works by:

1. Discovering fixtures marked with `@fixturecheck`
2. During test collection, executing those fixtures in isolation to verify they work
3. Catching and reporting errors before any tests run
4. Displaying clear error messages pointing directly to fixture issues

## Error Output Example

When a fixture is broken, you'll get a clear error message before any tests run:

```
================================================================================
FIXTURE VALIDATION ERRORS
================================================================================

Fixture 'book' in tests/conftest.py:42 failed validation:
  AttributeError: Field 'title' does not exist on model Book. Did the field name change?
  
================================================================================
Fix these fixture issues before running your tests.
================================================================================
```

## Visual Demo

![pytest-fixturecheck in action](https://github.com/topiaruss/pytest-fixturecheck/raw/main/docs/images/fixturecheck-demo.gif)

*The GIF above shows how pytest-fixturecheck catches a broken fixture during test collection, before any tests run.*

## Compatible With

- Python 3.8+
- pytest 6.0.0+
- Django 3.0+ (optional, for Django-specific validation)

## Comparison with Other Tools

| Feature                       | pytest-fixturecheck | pytest-django | factory_boy | standard pytest |
| ----------------------------- | :-----------------: | :-----------: | :---------: | :-------------: |
| Early fixture validation      |          ✅          |       ❌       |      ❌      |        ❌        |
| Django model field validation |          ✅          |       ❌       |      ❌      |        ❌        |
| Clear fixture error reporting |          ✅          |       ❌       |      ❌      |        ❌        |
| Validator extensibility       |          ✅          |       ❌       |      ❌      |        ❌        |
| Simple decorator API          |          ✅          |       ❌       |      ❌      |        ❌        |

While other tools are great for fixture management, pytest-fixturecheck is uniquely focused on validating fixtures *before* tests run, catching issues early in the testing process.

## Contributing

Contributions are welcome! Check out the [Contributing Guidelines](CONTRIBUTING.md) for more information.

To set up the development environment:

```bash
# Clone the repository
git clone https://github.com/topiaruss/pytest-fixturecheck.git
cd pytest-fixturecheck

# Install development dependencies
uv pip install -e ".[dev]"

# Run tests
make test-all
```

## License

MIT License
