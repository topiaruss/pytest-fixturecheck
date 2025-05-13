# Property Validators for pytest-fixturecheck

This document provides information about the property validators in pytest-fixturecheck, explaining the issue with the original validator and how to use the new validators.

## Background

The original `has_property_values` validator in pytest-fixturecheck had an issue where it didn't properly accept keyword arguments despite its signature suggesting it should:

```python
def has_property_values(**expected_values):
    # Implementation...
```

This caused errors like:

```
TypeError: has_property_values() got an unexpected keyword argument 'name'
```

## Fixed Validators

To address this issue, three new validators have been implemented:

### 1. `property_values_validator`

Takes a dictionary of property names and expected values.

```python
from pytest_fixturecheck import fixturecheck, property_values_validator

@pytest.fixture
@fixturecheck(property_values_validator({"name": "test_object", "value": 42}))
def my_fixture():
    return TestObject(name="test_object", value=42)
```

### 2. `check_property_values`

A direct replacement for `has_property_values` that properly accepts keyword arguments.

```python
from pytest_fixturecheck import fixturecheck, check_property_values

@pytest.fixture
@fixturecheck(check_property_values(name="test_object", value=42))
def my_fixture():
    return TestObject(name="test_object", value=42)
```

### 3. `with_property_values`

A factory function to replace `fixturecheck.with_property_values` that supports keyword arguments.

```python
from pytest_fixturecheck import with_property_values

@pytest.fixture
@with_property_values(name="test_object", value=42)
def my_fixture():
    return TestObject(name="test_object", value=42)
```

## Best Practices

1. **Decorator Order**: The order of `@pytest.fixture` and `@fixturecheck` decorators can affect fixture discovery. The safest approach is to place the `@pytest.fixture` decorator before the `@fixturecheck` decorator.

```python
# Recommended order
@pytest.fixture
@fixturecheck(check_property_values(name="test"))
def my_fixture():
    return TestObject(name="test")
```

However, be aware that in some cases you may encounter fixture discovery issues as seen in tests/test_property_values_fix.py, which required skipping the test due to a pytest fixture discovery limitation.

2. **Choose the Right Validator**:
   - Use `property_values_validator` when you want to pass a dictionary of properties.
   - Use `check_property_values` as a direct replacement for `has_property_values` with keyword arguments.
   - Use `with_property_values` for the simplest decorator syntax with keyword arguments.

3. **Function Validation**: The validators will skip validation for functions, so they only validate the return value of the fixture, not the fixture function itself.

## Migration Guide

To migrate from the old `has_property_values` validator:

1. Replace direct usage of `has_property_values` with `check_property_values`:

```python
# Old
@fixturecheck(has_property_values(...))  # This doesn't work with keyword args

# New
@fixturecheck(check_property_values(name="test", value=42))
```

2. Replace `fixturecheck.with_property_values` with the new `with_property_values`:

```python
# Old
@fixturecheck.with_property_values(...)  # This doesn't work with keyword args

# New
@with_property_values(name="test", value=42)
```

## Example

Here's a complete example:

```python
import pytest
from pytest_fixturecheck import fixturecheck, check_property_values, with_property_values

class TestObject:
    def __init__(self, name="test", value=42):
        self.name = name
        self.value = value

# Using check_property_values with fixturecheck
@pytest.fixture
@fixturecheck(check_property_values(name="fixture_test", value=42))
def test_object_fixture():
    return TestObject(name="fixture_test")

# Using the factory function directly
@pytest.fixture
@with_property_values(name="factory_test")
def factory_validated_fixture():
    return TestObject(name="factory_test")

# Tests using the fixtures
def test_with_validated_fixture(test_object_fixture):
    assert test_object_fixture.name == "fixture_test"
    assert test_object_fixture.value == 42

def test_with_factory_validated_fixture(factory_validated_fixture):
    assert factory_validated_fixture.name == "factory_test"
```

## Compatibility

The original `has_property_values` function is still available for backward compatibility, but it's recommended to use the new validators for new code. 