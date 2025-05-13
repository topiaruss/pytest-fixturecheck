"""Utility functions for pytest-fixturecheck."""

import inspect
from typing import Any, Callable, TypeVar, Optional

# Type variables for better typing
F = TypeVar("F", bound=Callable[..., Any])
ValidatorFunc = Callable[[Any], None]
PhaseAwareValidatorFunc = Callable[[Any, bool], None]


def creates_validator(func: Callable) -> Callable:
    """Create a validator function from a function that performs validation."""

    import functools  # Import locally to avoid unused import warning

    @functools.wraps(func)
    def validator_wrapper(*args: Any, **kwargs: Any) -> Optional[Callable[[Any, bool], None]]:
        """Wrap the validator function to return a validator function."""
        # Validator function to be returned by the wrapper
        @functools.wraps(func)
        def validator(obj: Any, is_collection_phase: bool = False) -> None:
            """Validate an object using the wrapped validator function."""
            if inspect.isfunction(obj):
                # Skip validation for function objects
                return None
            func(obj, *args, **kwargs)  # Call the function but don't return its result
            return None  # Explicitly return None

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
