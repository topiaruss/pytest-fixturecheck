"""Advanced validators for pytest-fixturecheck.

This module provides advanced validators for more complex validation scenarios.
"""

import inspect
import typing
import warnings
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, Union, cast

# Import the fixturecheck function to prevent circular imports when using factory functions
from .decorator import fixturecheck

# Type variable for function annotations
F = TypeVar("F", bound=Callable[..., Any])


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
    strict = True
    if "strict" in expected_values:
        strict = expected_values.pop("strict")

    def validator(obj: Any, is_collection_phase: bool = False) -> None:
        if is_collection_phase:
            return
        for prop_path, expected_value in expected_values.items():
            if "__" in prop_path:
                segments = prop_path.split("__")
                current = obj
                for i, segment in enumerate(segments):
                    if not hasattr(current, segment):
                        error_msg = f"Property '{segment}' missing from object at path '{'.'.join(segments[:i])}'"
                        if strict:
                            raise AttributeError(error_msg)
                        else:
                            warnings.warn(error_msg)
                            break
                    if i == len(segments) - 1:
                        actual_value = getattr(current, segment)
                        if actual_value != expected_value:
                            error_msg = f"Expected {prop_path}={expected_value}, got {actual_value}"
                            if strict:
                                raise ValueError(error_msg)
                            else:
                                warnings.warn(error_msg)
                    else:
                        current = getattr(current, segment)
            else:  # Top-level properties
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
        # Inner validator implicitly returns None on success, or raises error.

    setattr(validator, "_is_pytest_fixturecheck_validator", True)
    return validator


def type_check_properties(**expected_values: Any) -> Callable[[Any, bool], None]:
    """
    Create a validator that checks both property values and their types.
    # ... (docstring as before) ...
    """
    strict = True
    if "strict" in expected_values:
        strict = expected_values.pop("strict")

    type_specs = {}
    value_specs = {}
    for key, value in expected_values.items():
        if key.endswith("__type"):
            prop_name = key[:-6]
            type_specs[prop_name] = value
        else:
            value_specs[key] = value

    def validator(obj: Any, is_collection_phase: bool = False) -> None:
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
            if hasattr(typing, "get_origin") and hasattr(
                typing, "get_args"
            ):  # Handle Union types
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
            if not isinstance(actual_value, expected_type):
                error_msg = f"Expected {prop_name} to be of type {expected_type.__name__}, got {type(actual_value).__name__}"
                if strict:
                    raise TypeError(error_msg)
                else:
                    warnings.warn(error_msg)
        # Inner validator implicitly returns None on success, or raises error.

    setattr(validator, "_is_pytest_fixturecheck_validator", True)
    return validator


class _SimpleValidatorCallable:
    def __init__(self, func_to_call: Callable[[Any], None]):
        self.func_to_call = func_to_call
        self.__name__ = getattr(func_to_call, "__name__", "_simple_validator_instance")
        self.__doc__ = getattr(func_to_call, "__doc__", "")
        self._is_pytest_fixturecheck_validator = True  # Mark the instance

    def __call__(self, obj: Any, is_collection_phase: bool = False) -> None:
        if is_collection_phase:
            return
        try:
            self.func_to_call(obj)
        except Exception as e:
            raise


def simple_validator(func: Callable[[Any], None]) -> _SimpleValidatorCallable:
    """
    Decorator to easily create a validator from a simple function.
    The decorated function should take the fixture object and raise an error if invalid.
    """
    return _SimpleValidatorCallable(func)


def with_nested_properties(
    **expected_values: Any,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Factory function to create a fixture decorator that validates nested properties.
    # ... (docstring as before) ...
    """
    validator_instance = nested_property_validator(**expected_values)

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        return fixturecheck(validator_instance)(func)

    return decorator


def with_type_checks(
    **expected_values: Any,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Factory function to create a fixture decorator that validates property types.
    # ... (docstring as before) ...
    """
    validator_instance = type_check_properties(**expected_values)

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        return fixturecheck(validator_instance)(func)

    return decorator
