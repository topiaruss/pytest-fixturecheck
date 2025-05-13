"""Fixed validators for pytest-fixturecheck.

This module provides replacements for validators that have issues in the main package.
"""

import functools
import warnings
from typing import Any, Callable, Dict

from .utils import creates_validator


def property_values_validator(
    expected_values: Dict[str, Any],
) -> Callable[[Any, bool], None]:
    """
    Create a validator that checks if the fixture has the expected property values.

    Args:
        expected_values: Dictionary of property names and their expected values
                         Can include a 'strict' key to control validation behavior.
                         If strict=False, mismatches will issue warnings instead of
                         raising exceptions.

    Returns:
        A validator function

    Example:
        @pytest.fixture
        @fixturecheck(property_values_validator({"is_active": True, "username": "testuser"}))
        def user_fixture():
            return User(...)
    """
    # Extract strict parameter if present, default to True
    strict = True
    if "strict" in expected_values:
        strict = expected_values.pop("strict")

    def validator(obj: Any, is_collection_phase: bool = False) -> None:
        # Skip validation during collection phase
        if is_collection_phase:
            return

        for prop_name, expected_value in expected_values.items():
            if not hasattr(obj, prop_name):
                raise AttributeError(
                    f"Property '{prop_name}' missing from {obj.__class__.__name__}"
                )

            actual_value = getattr(obj, prop_name)
            if actual_value != expected_value:
                if strict:
                    raise ValueError(
                        f"Expected {prop_name}={expected_value}, got {actual_value}"
                    )
                else:
                    warnings.warn(
                        f"Expected {prop_name}={expected_value}, got {actual_value}"
                    )

    return validator


# This function works correctly and consistently
def check_property_values(**expected_values: Any) -> Callable[[Any, bool], None]:
    """
    Create a validator that checks if the fixture has the expected property values.

    This is a direct replacement for validators.has_property_values.

    Args:
        expected_values: Keyword arguments of property names and their expected values
                         Can include strict=False to issue warnings instead of raising
                         exceptions when validation fails.

    Returns:
        A validator function

    Example:
        @pytest.fixture
        @fixturecheck(check_property_values(is_active=True, username="testuser"))
        def user_fixture():
            return User(...)

        # Non-strict validation (warnings only)
        @pytest.fixture
        @fixturecheck(check_property_values(strict=False, is_active=True))
        def user_fixture():
            return User(...)
    """
    return property_values_validator(expected_values)


def with_property_values(**expected_values: Any) -> Callable:
    """
    Factory function to create a validator that checks for expected property values.

    This is a direct replacement for decorator.with_property_values.

    Args:
        **expected_values: Keyword arguments of property names and expected values.
                           Can include strict=False to issue warnings instead of
                           raising exceptions when validation fails.

    Example:
        @pytest.fixture
        @with_property_values(name="test", value=42)
        def fixture():
            return TestObject()

        # Non-strict validation (warnings only)
        @pytest.fixture
        @with_property_values(strict=False, name="test", value=42)
        def fixture():
            return TestObject()
    """
    from .decorator import fixturecheck

    # Create the validator function
    validator = property_values_validator(expected_values)

    # Create a decorator that both marks the fixture for validation by pytest
    # and performs validation when called directly
    def decorator(fixture_func):
        # Use fixturecheck to mark for pytest validation
        decorated = fixturecheck(validator)(fixture_func)

        # Add direct validation for tests calling the function directly
        @functools.wraps(decorated)
        def wrapper(*args, **kwargs):
            result = fixture_func(*args, **kwargs)
            # Also validate manually for direct calls
            validator(result, False)  # False = not in collection phase
            return result

        # Copy over the attributes from the fixturecheck decorator
        wrapper._fixturecheck = decorated._fixturecheck
        wrapper._validator = decorated._validator
        wrapper._expect_validation_error = decorated._expect_validation_error

        return wrapper

    return decorator
