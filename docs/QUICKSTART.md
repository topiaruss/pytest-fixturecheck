# Quick Start Guide

This guide will help you get started with pytest-fixturecheck in just a few minutes.

## Installation

```bash
pip install pytest-fixturecheck
```

For Django support:
```bash
pip install pytest-fixturecheck[django]
```

For asyncio support:
```bash
pip install pytest-fixturecheck[asyncio]
```

## Basic Usage

The most basic usage is to simply add the `@fixturecheck` decorator to your fixtures:

```python
import pytest
from pytest_fixturecheck import fixturecheck

@pytest.fixture
@fixturecheck
def user_data():
    return {"username": "testuser", "email": "test@example.com"}
```

This performs a basic check that the fixture returns a non-None value.

## Common Validation Patterns

### Type Validation

Ensure the fixture returns an object of a specific type:

```python
from pytest_fixturecheck import fixturecheck, is_instance_of

@pytest.fixture
@fixturecheck(is_instance_of(dict))
def user_data():
    return {"username": "testuser", "email": "test@example.com"}
```

### Field Validation

Check that an object has specific fields:

```python
from pytest_fixturecheck import fixturecheck, has_required_fields

@pytest.fixture
@fixturecheck(has_required_fields("username", "email"))
def user_data():
    return {"username": "testuser", "email": "test@example.com"}
```

### Property Value Validation

Validate specific values for properties:

```python
from pytest_fixturecheck import fixturecheck, check_property_values

@pytest.fixture
@fixturecheck(check_property_values(is_admin=False, is_active=True))
def regular_user():
    user = User(username="regular")
    user.is_admin = False
    user.is_active = True
    return user
```

### Django Model Validation

For Django models:

```python
from pytest_fixturecheck import fixturecheck, django_model_validates

@pytest.fixture
@fixturecheck(django_model_validates())
def valid_product(db):
    return Product.objects.create(
        name="Test Product",
        price=19.99,
        in_stock=True
    )
```

## Build Your Own Validator

Create a custom validator with the `@creates_validator` decorator:

```python
from pytest_fixturecheck import fixturecheck, creates_validator

@creates_validator
def has_positive_balance(user):
    if not hasattr(user, 'balance'):
        raise AttributeError("User must have a balance")
    if user.balance < 0:
        raise ValueError("User must have a positive balance")

@pytest.fixture
@fixturecheck(has_positive_balance)
def paying_user():
    user = User(username="paying")
    user.balance = 100
    return user
```

## Next Steps

For more detailed documentation:

- [Django Validators](./DJANGO_VALIDATORS.md) - For validating Django models
- [Property Validators](./PROPERTY_VALIDATORS.md) - For detailed property validation
- [Advanced Validators](./ADVANCED_VALIDATORS.md) - For complex validation scenarios 