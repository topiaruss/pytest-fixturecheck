"""Validators for pytest-fixturecheck.

This module provides factory functions for creating common validators.
"""

import inspect
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, Union

from .utils import creates_validator


def is_instance_of(
    type_or_types: Union[Type, Tuple[Type, ...]],
) -> Callable[[Any, bool], None]:
    """
    Create a validator that checks if the fixture is an instance of the specified type(s).

    Args:
        type_or_types: Type or tuple of types to check against

    Returns:
        A validator function

    Example:
        @pytest.fixture
        @fixturecheck(is_instance_of(User))
        def user_fixture():
            return User(...)
    """

    def validator(obj: Any, is_collection_phase: bool = False) -> None:
        if not isinstance(obj, type_or_types):
            if isinstance(type_or_types, tuple):
                type_names = ", ".join(t.__name__ for t in type_or_types)
                raise TypeError(
                    f"Expected instance of one of ({type_names}), got {type(obj).__name__}"
                )
            else:
                raise TypeError(
                    f"Expected instance of {type_or_types.__name__}, got {type(obj).__name__}"
                )
        validator._is_pytest_fixturecheck_validator = True

    return validator


def has_required_fields(*field_names: str) -> Callable[[Any, bool], None]:
    """
    Create a validator that checks if the fixture has the required fields.

    Args:
        field_names: Names of fields that must be present and non-None

    Returns:
        A validator function

    Example:
        @pytest.fixture
        @fixturecheck(has_required_fields("username", "email"))
        def user_fixture():
            return User(...)
    """

    def validator(obj: Any, is_collection_phase: bool = False) -> None:
        # Skip validation during collection phase or if obj is a function
        if is_collection_phase or inspect.isfunction(obj):
            return

        for field in field_names:
            if not hasattr(obj, field):
                raise AttributeError(
                    f"Required field '{field}' missing from {obj.__class__.__name__}"
                )

            if getattr(obj, field) is None:
                raise ValueError(
                    f"Required field '{field}' is None in {obj.__class__.__name__}"
                )

    return validator


def has_required_methods(*method_names: str) -> Callable[[Any, bool], None]:
    """
    Create a validator that checks if the fixture has the required methods.

    Args:
        method_names: Names of methods that must be present and callable

    Returns:
        A validator function

    Example:
        @pytest.fixture
        @fixturecheck(has_required_methods("save", "delete"))
        def user_fixture():
            return User(...)
    """

    def validator(obj: Any, is_collection_phase: bool = False) -> None:
        for method in method_names:
            if not hasattr(obj, method):
                raise AttributeError(
                    f"Required method '{method}' missing from {obj.__class__.__name__}"
                )

            if not callable(getattr(obj, method)):
                raise TypeError(
                    f"'{method}' is not callable in {obj.__class__.__name__}"
                )
        validator._is_pytest_fixturecheck_validator = True

    return validator


def has_property_values(**expected_values: Any) -> Callable[[Any, bool], None]:
    """
    Create a validator that checks if the fixture has the expected property values.

    Args:
        expected_values: Dictionary of property names and their expected values

    Returns:
        A validator function

    Example:
        @pytest.fixture
        @fixturecheck(has_property_values(is_active=True, username="testuser"))
        def user_fixture():
            return User(...)
    """

    def validator(obj: Any, is_collection_phase: bool = False) -> None:
        for prop_name, expected_value in expected_values.items():
            if not hasattr(obj, prop_name):
                raise AttributeError(
                    f"Property '{prop_name}' missing from {obj.__class__.__name__}"
                )

            actual_value = getattr(obj, prop_name)
            if actual_value != expected_value:
                raise ValueError(
                    f"Expected {prop_name}={expected_value}, got {actual_value}"
                )
        validator._is_pytest_fixturecheck_validator = True

    return validator


def combines_validators(*validators: Callable) -> Callable[[Any, bool], None]:
    """
    Combine multiple validators into a single validator.

    Args:
        validators: Validator functions to combine

    Returns:
        A combined validator function

    Example:
        @pytest.fixture
        @fixturecheck(combines_validators(
            is_instance_of(User),
            has_required_fields("username", "email")
        ))
        def user_fixture():
            return User(...)
    """

    def combined_validator(obj: Any, is_collection_phase: bool = False) -> None:
        for validator in validators:
            validator(obj, is_collection_phase)

        combined_validator._is_pytest_fixturecheck_validator = True

    return combined_validator
