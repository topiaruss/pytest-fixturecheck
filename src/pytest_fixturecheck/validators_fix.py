"""Fixed validators for pytest-fixturecheck.

This module provides replacements for validators that have issues in the main package.
"""

from typing import Any, Callable, Dict

from .utils import creates_validator


def property_values_validator(
    expected_values: Dict[str, Any],
) -> Callable[[Any, bool], None]:
    """
    Create a validator that checks if the fixture has the expected property values.

    Args:
        expected_values: Dictionary of property names and their expected values

    Returns:
        A validator function

    Example:
        @pytest.fixture
        @fixturecheck(property_values_validator({"is_active": True, "username": "testuser"}))
        def user_fixture():
            return User(...)
    """

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
                raise ValueError(
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

    Returns:
        A validator function

    Example:
        @pytest.fixture
        @fixturecheck(check_property_values(is_active=True, username="testuser"))
        def user_fixture():
            return User(...)
    """
    return property_values_validator(expected_values)


def with_property_values(**expected_values: Any) -> Callable:
    """
    Factory function to create a validator that checks for expected property values.

    This is a direct replacement for decorator.with_property_values.

    Example:
        @pytest.fixture
        @with_property_values(name="test", value=42)
        def fixture():
            return TestObject()
    """
    from .decorator import fixturecheck

    return lambda fixture: fixturecheck(property_values_validator(expected_values))(
        fixture
    )
