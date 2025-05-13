# pytest-fixturecheck

A pytest plugin to validate fixtures before they're used in tests.

## Features

- Validates fixtures during test collection, catching errors early
- Auto-detects Django models and validates field access
- Works with any pytest fixture workflow
- Flexible validation options:
  - No validator (simple existence check)
  - Custom validator functions
  - Built-in validators for common patterns
  - Validators that expect errors (for testing)
- Supports both synchronous and asynchronous (coroutine) fixtures
- Compatible with pytest-django, pytest-asyncio, and other pytest plugins

## Installation

```bash
pip install pytest-fixturecheck
```

## Basic Usage

```python
import pytest
from pytest_fixturecheck import fixturecheck

# Simplest form - basic validation
@pytest.fixture
@fixturecheck
def my_fixture():
    # This fixture will be validated before tests run
    return "hello world"

# With custom validator
def validate_user(obj, is_collection_phase=False):
    if is_collection_phase:
        # Skip validation during collection phase
        return
    if not hasattr(obj, 'username'):
        raise AttributeError("User object must have a username")
    if obj.username is None:
        raise ValueError("Username cannot be None")

@pytest.fixture
@fixturecheck(validate_user)
def user():
    # This fixture will be validated using the custom validator
    return User(username="testuser")
```

## Using Built-in Validators

```python
from pytest_fixturecheck import fixturecheck, is_instance_of, has_required_fields, check_property_values

@pytest.fixture
@fixturecheck(is_instance_of(User))
def user_fixture():
    # This fixture must return an instance of User
    return User(username="testuser")

@pytest.fixture
@fixturecheck(has_required_fields("username", "email"))
def complete_user_fixture():
    # This fixture must return an object with username and email fields
    return User(username="testuser", email="user@example.com")

@pytest.fixture
@fixturecheck(check_property_values(username="testuser", is_active=True))
def active_user_fixture():
    # This fixture must return an object with username="testuser" and is_active=True
    return User(username="testuser", is_active=True)
```

## Django Support

```python
from pytest_fixturecheck import fixturecheck, django_model_has_fields, django_model_validates

# Validate specific model fields exist
@pytest.fixture
@fixturecheck(django_model_has_fields("username", "email"))
def user_model(db):
    # This fixture must return a Django model with username and email fields
    return User.objects.create(username="testuser", email="user@example.com")

# Validate a model passes Django's built-in validation
@pytest.fixture
@fixturecheck(django_model_validates())
def validated_model(db):
    # This fixture must return a Django model that passes Django's validation
    return MyModel.objects.create(name="Test", valid_field=True)
```

## Creating Custom Validators

```python
from pytest_fixturecheck import fixturecheck, creates_validator, combines_validators, is_instance_of

# Create a custom validator
@creates_validator
def has_valid_email(user):
    if not hasattr(user, "email"):
        raise AttributeError("User must have an email field")
    if not user.email or "@" not in user.email:
        raise ValueError("User must have a valid email")

# Combine multiple validators
combined_validator = combines_validators(
    is_instance_of(User),
    has_required_fields("username", "email"),
    has_valid_email
)

@pytest.fixture
@fixturecheck(combined_validator)
def validated_user():
    # This fixture will be validated with all combined validators
    return User(username="testuser", email="user@example.com")
```

## Property Validation

There are three ways to validate property values:

```python
from pytest_fixturecheck import (
    fixturecheck, property_values_validator, check_property_values, with_property_values
)

# 1. Using a dictionary with property_values_validator
@pytest.fixture
@fixturecheck(property_values_validator({"name": "test", "value": 42}))
def object_fixture():
    return TestObject(name="test", value=42)

# 2. Using keyword arguments with check_property_values
@pytest.fixture
@fixturecheck(check_property_values(name="test", value=42))
def object_fixture2():
    return TestObject(name="test", value=42)

# 3. Using the factory function with_property_values
@pytest.fixture
@with_property_values(name="test", value=42)
def object_fixture3():
    return TestObject(name="test", value=42)
```

For more details on property validation, see [PROPERTY_VALIDATORS.md](PROPERTY_VALIDATORS.md).

## Testing Validators

```python
from pytest_fixturecheck import fixturecheck

# Expect a validation error - useful for negative testing
@pytest.fixture
@fixturecheck(has_required_fields("nonexistent_field"), expect_validation_error=True)
def fixture_missing_field():
    # This fixture is expected to fail validation, but the test will still pass
    return User(username="testuser")  # Intentionally missing the field
```

## Available Validators

- `is_instance_of(type_or_types)` - Validates object is an instance of the specified type(s)
- `has_required_fields(*field_names)` - Validates object has the specified fields
- `has_required_methods(*method_names)` - Validates object has the specified methods
- `has_property_values(**expected_values)` - Validates object properties match expected values (legacy)
- `property_values_validator(expected_values_dict)` - Validates object properties with a dictionary
- `check_property_values(**expected_values)` - Validates object properties with keyword arguments
- `with_property_values(**expected_values)` - Factory function for property validation
- `combines_validators(*validators)` - Combines multiple validators
- `django_model_has_fields(*field_names)` - Validates Django model has the specified fields
- `django_model_validates()` - Validates Django model passes Django's validation

## Configuration Options

In your pytest.ini:

```ini
[pytest]
fixturecheck-auto-skip = true  # Automatically skip tests with invalid fixtures instead of failing
```

## Development and Pre-commit Hooks

For developers contributing to pytest-fixturecheck, we use pre-commit hooks to ensure code quality and consistency.

See [PRE_COMMIT_HOOKS.md](PRE_COMMIT_HOOKS.md) for details on the available hooks and how to use them.

## License

MIT
