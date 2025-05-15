# Advanced Validators for pytest-fixturecheck

This document describes the advanced validation features added to pytest-fixturecheck to address limitations identified in previous versions.

## New Features Overview

These advanced validators extend the core functionality with:

1. **Nested Property Validation**: Validate properties at any level in an object hierarchy using dot notation
2. **Type Checking**: Validate both property values and their types
3. **Simplified Validator API**: Create custom validators without worrying about the collection phase

## Nested Property Validation

One limitation in previous versions was the inability to validate nested properties. The new `nested_property_validator` solves this by supporting dot notation:

```python
import pytest
from pytest_fixturecheck import fixturecheck, nested_property_validator

class Config:
    def __init__(self, resolution, frame_rate):
        self.resolution = resolution
        self.frame_rate = frame_rate

class Camera:
    def __init__(self, name, config):
        self.name = name
        self.config = config

@pytest.fixture
@fixturecheck(nested_property_validator(
    name="Test Camera",
    config__resolution="1280x720",  # Note the '__' notation for nested properties
    config__frame_rate=30
))
def camera_fixture():
    config = Config("1280x720", 30)
    return Camera("Test Camera", config)
```

For convenience, there's also a factory function:

```python
from pytest_fixturecheck import with_nested_properties

@pytest.fixture
@with_nested_properties(
    name="Test Camera",
    config__resolution="1280x720",
    config__frame_rate=30
)
def camera_fixture():
    config = Config("1280x720", 30)
    return Camera("Test Camera", config)
```

## Type Checking

The `type_check_properties` validator allows you to check both property values and their types:

```python
from pytest_fixturecheck import fixturecheck, type_check_properties

@pytest.fixture
@fixturecheck(type_check_properties(
    username="testuser",        # Check the value
    username__type=str,         # Check the type
    email__type=str,            # Only check the type, not the value
    age=30,
    age__type=int,
    is_active=True,
    is_active__type=bool
))
def user_fixture():
    return User("testuser", "test@example.com", 30, True)
```

This also supports Union types for optional fields:

```python
import typing
from pytest_fixturecheck import type_check_properties

@pytest.fixture
@fixturecheck(type_check_properties(
    username="optional_user",
    email__type=typing.Union[str, None]  # Can be either string or None
))
def optional_email_user():
    return User("optional_user", email=None, age=25)
```

The factory function version:

```python
from pytest_fixturecheck import with_type_checks

@pytest.fixture
@with_type_checks(
    username="testuser",
    username__type=str,
    age=30,
    age__type=int
)
def user_fixture():
    return User("testuser", "test@example.com", 30, True)
```

## Simplified Validator API

Creating custom validators now requires less boilerplate with the `simple_validator` decorator:

```python
from pytest_fixturecheck import simple_validator

@simple_validator
def validate_user_has_username(user):
    # No need to handle is_collection_phase
    if not hasattr(user, "username"):
        raise AttributeError("User must have a username attribute")
    if not user.username:
        raise ValueError("Username cannot be empty")

@pytest.fixture
@validate_user_has_username
def user_fixture():
    return User("testuser")
```

## Non-strict Validation

All advanced validators support the `strict` parameter:

```python
@pytest.fixture
@with_nested_properties(
    strict=False,  # Will issue warnings instead of raising exceptions
    name="Test Camera",
    config__resolution="1280x720"
)
def camera_fixture():
    # Even if this doesn't match the expected values,
    # the test will still run with warnings
    config = Config("wrong_resolution", 60)
    return Camera("Wrong Name", config)
```

## Important Limitations and Best Practices

### Using Validators in Tests

The advanced validators are primarily designed to be used as fixture decorators. If you need to use them directly in test code, follow these guidelines:

1. **Don't use the validators directly on objects**: The validators might not work as expected when called directly on objects. Instead, perform manual validation in your tests.

   ```python
   # DON'T DO THIS:
   validator = nested_property_validator(name="Test")
   validator(camera_obj, False)  # May cause issues
   
   # DO THIS INSTEAD:
   assert camera_obj.name == "Test"
   assert camera_obj.config.resolution == "1280x720"
   ```

2. **Use factory functions with fixtures**: When possible, use the factory function versions of validators with fixtures rather than calling validators directly.

   ```python
   # PREFERRED:
   @pytest.fixture
   @with_nested_properties(name="Test Camera", config__resolution="1280x720")
   def camera_fixture():
       return Camera(...)
       
   # Instead of creating and applying validators manually
   ```

3. **Use the `fixturecheck` decorator for custom validators**: If you have custom validators, use the `fixturecheck` decorator to apply them to fixtures rather than calling them directly.

### Package Versioning

Some tests may be version-sensitive. The advanced validators are available starting from version 0.3.4. If you're checking for specific package versions in your tests, consider supporting multiple versions:

```python
assert __version__ in ["0.3.0", "0.3.3", "0.3.4"]  # Support multiple versions
```

## Feature Comparison

| Feature                       | Basic Validators | Advanced Validators |
| ----------------------------- | ---------------- | ------------------- |
| Basic property value checking | ✅                | ✅                   |
| Strict/non-strict validation  | ✅                | ✅                   |
| Nested property validation    | ❌                | ✅                   |
| Type checking                 | ❌                | ✅                   |
| Collection phase handling     | Manual           | Automatic           |

## Best Practices

1. **For Simple Value Validation**: Use the standard `with_property_values` or `check_property_values`
2. **For Nested Objects**: Use `with_nested_properties` or `nested_property_validator`  
3. **For Type Safety**: Use `with_type_checks` or `type_check_properties`
4. **For Custom Validation Logic**: Use `simple_validator` to create your own validators

## Implementation Notes

These advanced validators were added to address the limitations identified in version 0.3.3, particularly:

1. Lack of proper nested property validation
2. No type checking capabilities
3. Complexity in handling the collection phase in custom validators

The implementation is backward compatible with all existing validators. 