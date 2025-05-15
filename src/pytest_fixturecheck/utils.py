"""Utility functions for pytest-fixturecheck."""

import inspect
from typing import Any, Callable, Optional, TypeVar

# Type variables for better typing
F = TypeVar("F", bound=Callable[..., Any])
ValidatorFunc = Callable[[Any], None]
PhaseAwareValidatorFunc = Callable[[Any, bool], None]


def creates_validator(func: Callable) -> Callable:
    """Create a validator function from a function that performs validation.

    This decorator is intended to wrap a function that contains the core
    validation logic. The wrapped function should typically take the object
    to be validated as its first argument, followed by any other parameters
    needed for the validation.

    `@creates_validator` transforms your logic function into a factory.
    When this factory is called (potentially with arguments for your logic),
    it returns the actual validator function. This returned validator will
    be phase-aware (i.e., it accepts `obj` and `is_collection_phase`).

    Example:
        from pytest_fixturecheck import fixturecheck, creates_validator

        @creates_validator
        def my_custom_check(obj, expected_value):
            if not hasattr(obj, 'some_attr') or obj.some_attr != expected_value:
                raise ValueError(f"Attribute 'some_attr' did not match {expected_value} for {obj}")

        # Usage in a test or fixture setup:
        # validator_instance = my_custom_check(expected_value=100)
        # @fixturecheck(validator_instance)
        # def my_fixture(): ...

        # Or, if no parameters for the logic:
        @creates_validator
        def simple_obj_check(obj):
            if not hasattr(obj, 'id'):
                raise AttributeError("Missing 'id' attribute")

        # validator_instance_simple = simple_obj_check()
        # @fixturecheck(validator_instance_simple)
        # def other_fixture(): ...
    """

    import functools  # Import locally to avoid unused import warning

    @functools.wraps(func)
    def validator_wrapper(
        *args: Any, **kwargs: Any
    ) -> Optional[Callable[[Any, bool], None]]:
        """Wrap the validator function to return a validator function."""

        # Validator function to be returned by the wrapper
        @functools.wraps(func)
        def validator(obj: Any, is_collection_phase: bool = False) -> None:
            """Validate an object using the wrapped validator function."""
            if inspect.isfunction(obj):
                # Skip validation for function objects
                return None
            # Call the original validation function (func) with the object to be validated,
            # and any arguments that were passed when the validator instance was created.
            func(obj, *args, **kwargs)
            # Validators should return None on success. Exceptions signal failure.
            return None

        # Copy metadata from the original function
        validator._validator = True  # type: ignore
        validator._fixturecheck = True  # type: ignore
        validator._expect_validation_error = False  # type: ignore

        return validator

    return validator_wrapper


def is_async_function(func: Any) -> bool:
    """
    Check if a function is an async function.

    Args:
        func: The function to check

    Returns:
        True if the function is async, False otherwise
    """
    return inspect.iscoroutinefunction(func)


def is_coroutine(obj: Any) -> bool:
    """
    Check if an object is a coroutine.

    Args:
        obj: The object to check

    Returns:
        True if the object is a coroutine, False otherwise
    """
    return inspect.iscoroutine(obj)
