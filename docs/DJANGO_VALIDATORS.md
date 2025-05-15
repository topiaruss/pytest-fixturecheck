# Django Validators for pytest-fixturecheck

This document describes the Django-specific validators available in pytest-fixturecheck.

## Overview

Django models often have specific validation requirements that go beyond basic property validation. The pytest-fixturecheck package includes validators designed specifically for Django models that help ensure your fixtures are returning valid Django model instances.

## Available Django Validators

### is_django_model

```python
from pytest_fixturecheck import fixturecheck
from pytest_fixturecheck.django_validators import is_django_model

@pytest.fixture
@fixturecheck(is_django_model)
def my_model_fixture(db):
    return MyModel.objects.create(name="test")
```

This validator checks if the returned object is a Django model instance. It's more robust than simple `isinstance()` checks and works well in testing environments.

### django_model_has_fields

```python
from pytest_fixturecheck import fixturecheck
from pytest_fixturecheck.django_validators import django_model_has_fields

@pytest.fixture
@fixturecheck(django_model_has_fields("name", "email", "is_active"))
def user_model_fixture(db):
    return User.objects.create(
        name="Test User", 
        email="test@example.com", 
        is_active=True
    )
```

This validator checks that a Django model has the specified fields. It will raise a validation error if any of the fields are missing.

Parameters:
- `*required_fields`: Field names to check for
- `allow_empty`: When `False` (default), fields must not be `None`

### django_model_validates

```python
from pytest_fixturecheck import fixturecheck
from pytest_fixturecheck.django_validators import django_model_validates

@pytest.fixture
@fixturecheck(django_model_validates())
def validated_model_fixture(db):
    return MyModel.objects.create(name="Test Model")
```

This validator calls `full_clean()` on the model to ensure it passes Django's built-in validation. This is useful for ensuring that your models satisfy all constraints.

## Compatibility

The Django validators are designed to be compatible with both:
- Standard pytest fixtures
- pytest-django fixtures

## Graceful Degradation

All Django validators will gracefully handle environments where Django is not installed by skipping validation. This allows your tests to run even in environments without Django.

## Collection Phase Support

All Django validators respect the `is_collection_phase` parameter and will skip validation during the collection phase. This prevents errors when pytest is collecting tests and fixtures.

## Test Support

For testing, pytest-fixturecheck also exports Django exceptions:

```python
from pytest_fixturecheck.django_validators import ValidationError, FieldDoesNotExist

# These can be used in tests, even when Django is not installed
```

This allows you to write tests that catch Django-specific exceptions without requiring Django to be installed.

## Advanced Usage: Manual Validation

You can use the validators directly in your code:

```python
from pytest_fixturecheck.django_validators import is_django_model, validate_model_fields

def my_function(obj):
    # Check if object is a Django model
    if is_django_model(obj):
        # Validate specific fields
        validate_model_fields(obj, fields_to_check=["name", "email"])
        # Do something with the validated model
        return obj.name
    return None
```

## Compatibility Layer

For backward compatibility, pytest-fixturecheck also includes a `django.py` module that re-exports the Django validators from `django_validators.py`. This ensures that existing code continues to work. 