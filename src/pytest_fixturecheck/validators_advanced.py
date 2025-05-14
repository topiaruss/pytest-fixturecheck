"""Advanced validators for pytest-fixturecheck.

This module provides more advanced validation features beyond the core validators:
- Nested property validation with dot notation (e.g., 'config__resolution')
- Type checking validators
- Simplified validator API that handles collection phase automatically
"""

import typing
import warnings
from typing import Any, Callable, Dict, Optional, Type, Union

from .utils import creates_validator
from .decorator import fixturecheck


@creates_validator
def nested_property_validator(**expected_values: Any) -> Callable[[Any, bool], None]:
    """
    Create a validator that properly supports nested properties with dot notation.

    Args:
        **expected_values: Property paths and their expected values.
            Can use '__' for nested properties, e.g., 'config__resolution'="1280x720"
            Can include strict=False to issue warnings instead of raising exceptions.

    Returns:
        A validator function that checks nested properties

    Example:
        @pytest.fixture
        @fixturecheck(nested_property_validator(
            name="Test",
            config__resolution="1280x720",
            config__frame_rate=30
        ))
        def camera():
            return Camera("Test", Config("1280x720", 30))
    """
    # Extract strict parameter if present, default to True
    strict = True
    if "strict" in expected_values:
        strict = expected_values.pop("strict")

    def validator(obj: Any, is_collection_phase: bool = False) -> None:
        # Skip validation during collection phase
        if is_collection_phase:
            return

        for prop_path, expected_value in expected_values.items():
            # Handle nested properties with __ notation
            if "__" in prop_path:
                # Split the path into segments
                segments = prop_path.split("__")
                current = obj

                # Navigate through the object hierarchy
                for i, segment in enumerate(segments):
                    if not hasattr(current, segment):
                        error_msg = f"Property '{segment}' missing from object at path '{'.'.join(segments[:i])}'"
                        if strict:
                            raise AttributeError(error_msg)
                        else:
                            warnings.warn(error_msg)
                            break

                    # If this is the last segment, check the value
                    if i == len(segments) - 1:
                        actual_value = getattr(current, segment)
                        if actual_value != expected_value:
                            error_msg = f"Expected {prop_path}={expected_value}, got {actual_value}"
                            if strict:
                                raise ValueError(error_msg)
                            else:
                                warnings.warn(error_msg)
                    else:
                        # Move to the next level in the hierarchy
                        current = getattr(current, segment)
            else:
                # Handle top-level properties
                if not hasattr(obj, prop_path):
                    error_msg = (
                        f"Property '{prop_path}' missing from {obj.__class__.__name__}"
                    )
                    if strict:
                        raise AttributeError(error_msg)
                    else:
                        warnings.warn(error_msg)
                        continue

                actual_value = getattr(obj, prop_path)
                if actual_value != expected_value:
                    error_msg = (
                        f"Expected {prop_path}={expected_value}, got {actual_value}"
                    )
                    if strict:
                        raise ValueError(error_msg)
                    else:
                        warnings.warn(error_msg)

    return validator


@creates_validator
def type_check_properties(**expected_values: Any) -> Callable[[Any, bool], None]:
    """
    Create a validator that checks both property values and their types.

    Args:
        **expected_values: Property names and their expected values or types.
            For type checking only, use the special syntax: "property_name__type": type
            For both value and type checking, provide both entries.
            Can include strict=False to issue warnings instead of raising exceptions.

    Returns:
        A validator function that checks property types

    Example:
        @pytest.fixture
        @fixturecheck(type_check_properties(
            username="testuser",
            username__type=str,
            age=30,
            age__type=int
        ))
        def user():
            return User("testuser", 30)
    """
    # Extract strict parameter if present, default to True
    strict = True
    if "strict" in expected_values:
        strict = expected_values.pop("strict")

    # Separate type specs from value specs
    type_specs = {}
    value_specs = {}

    for key, value in expected_values.items():
        if key.endswith("__type"):
            # Extract property name by removing __type suffix
            prop_name = key[:-6]
            type_specs[prop_name] = value
        else:
            value_specs[key] = value

    def validator(obj: Any, is_collection_phase: bool = False) -> None:
        # Skip validation during collection phase
        if is_collection_phase:
            return

        # Validate property values
        for prop_name, expected_value in value_specs.items():
            if not hasattr(obj, prop_name):
                error_msg = (
                    f"Property '{prop_name}' missing from {obj.__class__.__name__}"
                )
                if strict:
                    raise AttributeError(error_msg)
                else:
                    warnings.warn(error_msg)
                    continue

            actual_value = getattr(obj, prop_name)
            if actual_value != expected_value:
                error_msg = f"Expected {prop_name}={expected_value}, got {actual_value}"
                if strict:
                    raise ValueError(error_msg)
                else:
                    warnings.warn(error_msg)

        # Validate property types
        for prop_name, expected_type in type_specs.items():
            if not hasattr(obj, prop_name):
                error_msg = (
                    f"Property '{prop_name}' missing from {obj.__class__.__name__}"
                )
                if strict:
                    raise AttributeError(error_msg)
                else:
                    warnings.warn(error_msg)
                    continue

            actual_value = getattr(obj, prop_name)

            # Handle Union types (e.g., typing.Union[str, None])
            if hasattr(typing, "get_origin") and hasattr(typing, "get_args"):
                origin = typing.get_origin(expected_type)
                if origin is typing.Union:
                    type_args = typing.get_args(expected_type)
                    if not any(isinstance(actual_value, t) for t in type_args):
                        error_msg = f"Expected {prop_name} to be one of types {type_args}, got {type(actual_value)}"
                        if strict:
                            raise TypeError(error_msg)
                        else:
                            warnings.warn(error_msg)
                    continue

            # Standard type check
            if not isinstance(actual_value, expected_type):
                error_msg = f"Expected {prop_name} to be of type {expected_type.__name__}, got {type(actual_value).__name__}"
                if strict:
                    raise TypeError(error_msg)
                else:
                    warnings.warn(error_msg)

    return validator


def simple_validator(
    validator_func: Callable[[Any], None],
) -> Callable[[Any], Callable]:
    """
    A decorator that simplifies creating validators by handling the collection phase logic automatically.

    Args:
        validator_func: A function that validates an object but doesn't handle collection phase

    Returns:
        A decorator to apply to fixtures

    Example:
        @simple_validator
        def validate_user(user):
            if not hasattr(user, "username"):
                raise AttributeError("User must have username")

        @pytest.fixture
        @validate_user
        def user_fixture():
            return User("testuser")
    """

    def wrapped_validator(obj: Any, is_collection_phase: bool = False) -> None:
        if is_collection_phase:
            return
        validator_func(obj)

    # Apply the creates_validator decorator to get proper function attributes
    wrapped_validator = creates_validator(wrapped_validator)

    def decorator(func: Callable) -> Callable:
        return fixturecheck(wrapped_validator)(func)

    return decorator


def with_nested_properties(**expected_values: Any) -> Callable[[Any], Any]:
    """
    Factory function to create a fixture decorator that validates nested properties.

    Args:
        **expected_values: Property paths and their expected values.
            Can use '__' for nested properties, e.g., 'config__resolution'="1280x720"
            Can include strict=False to issue warnings instead of raising exceptions.

    Returns:
        A decorator to apply to fixtures

    Example:
        @pytest.fixture
        @with_nested_properties(
            name="Test Camera",
            config__resolution="1280x720"
        )
        def camera():
            return Camera("Test Camera", Config("1280x720", 30))
    """
    validator = nested_property_validator(**expected_values)

    def decorator(func: Callable) -> Callable:
        return fixturecheck(validator)(func)

    return decorator


def with_type_checks(**expected_values: Any) -> Callable[[Any], Any]:
    """
    Factory function to create a fixture decorator that validates property types.

    Args:
        **expected_values: Property names and their expected values or types.
            For type checking only, use the special syntax: "property_name__type": type
            For both value and type checking, provide both entries.
            Can include strict=False to issue warnings instead of raising exceptions.

    Returns:
        A decorator to apply to fixtures

    Example:
        @pytest.fixture
        @with_type_checks(
            username="testuser",
            username__type=str,
            age=30,
            age__type=int
        )
        def user():
            return User("testuser", 30)
    """
    validator = type_check_properties(**expected_values)

    def decorator(func: Callable) -> Callable:
        return fixturecheck(validator)(func)

    return decorator
