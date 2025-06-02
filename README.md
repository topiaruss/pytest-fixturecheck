# pytest-fixturecheck

[![CI](https://github.com/topiaruss/pytest-fixturecheck/actions/workflows/ci.yml/badge.svg)](https://github.com/topiaruss/pytest-fixturecheck/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/topiaruss/pytest-fixturecheck/branch/main/graph/badge.svg)](https://codecov.io/gh/topiaruss/pytest-fixturecheck)
[![PyPI version](https://img.shields.io/pypi/v/pytest-fixturecheck.svg)](https://pypi.org/project/pytest-fixturecheck/0.4.3/)
[![Python Versions](https://img.shields.io/pypi/pyversions/pytest-fixturecheck.svg)](https://pypi.org/project/pytest-fixturecheck/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![AI-assisted](https://img.shields.io/badge/code%20origin-AI--assisted-blueviolet)](#ai-generated-code-disclosure)

A pytest plugin to validate fixtures before they're used in tests.

## Features

- Validates fixtures during test collection, catching errors early
- Auto-detects Django models and validates field access
- Works with any pytest fixture workflow
- **Command-line interface for analyzing and managing fixture checks**
- Flexible validation options:
  - No validator (simple existence check)
  - Custom validator functions
  - Built-in validators for common patterns
  - Validators that expect errors (for testing)
- Supports both synchronous and asynchronous (coroutine) fixtures
- Compatible with pytest-django, pytest-asyncio, and other pytest plugins
- Full test coverage tracking with Codecov integration

## Installation

```bash
pip install pytest-fixturecheck
```

## Documentation

- [Quick Start Guide](docs/QUICKSTART.md)
- [Command-Line Interface (CLI)](docs/CLI.md)
- [Property Validators](docs/PROPERTY_VALIDATORS.md)
- [Django Validators](docs/DJANGO_VALIDATORS.md)
- [Troubleshooting Guide](docs/TROUBLESHOOTING.md)

## Command-Line Interface

pytest-fixturecheck provides a powerful command-line interface to analyze and manage fixture checks in your codebase.

### Report Command

Analyze your test suite to find opportunities for fixture checks and count existing ones:

```bash
# Basic report
fixturecheck report

# Detailed report with fixture information
fixturecheck report -v

# Full report with validator details
fixturecheck report -vv

# Analyze specific directory
fixturecheck report --path tests/

# Use custom file pattern
fixturecheck report --pattern "*_test.py"
```

**Example output:**

```bash
$ fixturecheck report
Found 23 opportunities for fixture checks
Found 15 existing fixture checks

$ fixturecheck report -v
FIXTURE CHECK REPORT
==================================================

File: tests/test_user.py
----------------------------------------

Opportunities for fixture checks:
  Line 12: user_fixture
    Parameters: db
    ------------------------------
  Line 18: admin_user
    Parameters: user_fixture
    ------------------------------

Existing fixture checks:
  Line 25: validated_user
    Parameters: db
    ------------------------------
  Line 32: checked_admin
    Parameters: validated_user
    ------------------------------

==================================================
Found 23 opportunities for fixture checks
Found 15 existing fixture checks

$ fixturecheck report -vv
FIXTURE CHECK REPORT
==================================================

File: tests/test_user.py
----------------------------------------

Existing fixture checks:
  Line 25: validated_user
    Parameters: db
    Validator: Default validator
    ------------------------------
  Line 32: checked_admin
    Parameters: validated_user
    Validator: validate_admin_user
    ------------------------------

==================================================
Found 23 opportunities for fixture checks
Found 15 existing fixture checks
```

### Add Command

Automatically add `@fixturecheck()` decorators to fixtures that don't have them:

```bash
# Dry run - see what would be changed
fixturecheck add --dry-run

# Add decorators to fixtures
fixturecheck add

# Add decorators in specific directory
fixturecheck add --path tests/unit/

# Add decorators with custom pattern
fixturecheck add --pattern "test_*.py"
```

**Example output:**

```bash
$ fixturecheck add --dry-run
Would modify tests/test_user.py
Would modify tests/test_orders.py

$ fixturecheck add
Modified tests/test_user.py
Modified tests/test_orders.py
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

## With custom validator

```python

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

For more details on Django validators, see [docs/DJANGO_VALIDATORS.md](docs/DJANGO_VALIDATORS.md).

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

For more details on property validation, see [docs/PROPERTY_VALIDATORS.md](docs/PROPERTY_VALIDATORS.md).

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

### Advanced Validators

For more complex validation scenarios, pytest-fixturecheck offers advanced validators:

- `nested_property_validator(**expected_values)` - Validates nested properties using dot notation (e.g., `config__resolution`)
- `type_check_properties(**expected_values)` - Validates both property values and their types
- `simple_validator(validator_func)` - Simplified API for creating custom validators
- `with_nested_properties(**expected_values)` - Factory function for nested property validation
- `with_type_checks(**expected_values)` - Factory function for type checking validation

For more details on advanced validators, see [docs/ADVANCED_VALIDATORS.md](docs/ADVANCED_VALIDATORS.md).

## Configuration Options

In your pytest.ini:

```ini
[pytest]
fixturecheck-auto-skip = true  # Automatically skip tests with invalid fixtures instead of failing
```

## Development and Pre-commit Hooks

For developers contributing to pytest-fixturecheck, we use pre-commit hooks to ensure code quality and consistency.

See [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) for details on how to contribute and [docs/PRE_COMMIT_HOOKS.md](docs/PRE_COMMIT_HOOKS.md) for information about the pre-commit hooks.

## AI-Generated Code Disclosure

This project includes significant portions of code that were generated with the assistance of large language models—specifically **Claude 3.7 Sonnet** and **Gemini 2.5 Pro Preview (2024-05-06)**—over an intensive 48-hour development sprint. These tools were used to accelerate scaffolding, explore idiomatic patterns, and propose implementations for specific challenges.

All AI-generated code has been reviewed, integrated, and tested by the author. Transparency is important: this project makes no attempt to conceal the involvement of generative AI, and welcomes scrutiny and feedback. 

If you're curious about the design, want to critique the use of AI in open-source development, or have experience with similar approaches, the author invites comments and contributions from both the AI and broader developer communities.

Your insights—technical, ethical, or otherwise—are welcome.

## Project Tags

This project is tagged with the following keywords to improve discoverability:
- #pytest - A pytest plugin for fixture validation
- #testing - Helps improve test quality and reliability
- #fixtures - Specifically focuses on validating pytest fixtures
- #python - Written in and for Python
- #validation - Provides validation tools for fixture objects
- #ai-assisted — This project was created with the assistance of large language models (LLMs). The author supports the establishment of best practice norms for AI-assisted development and is committed to full and ongoing disclosure.


## License

MIT

