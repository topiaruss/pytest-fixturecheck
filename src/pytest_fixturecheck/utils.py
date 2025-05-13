"""Utility functions for pytest-fixturecheck."""

import functools
import inspect
from typing import Any, Callable, TypeVar, cast

# Type variables for better typing
F = TypeVar("F", bound=Callable[..., Any])
ValidatorFunc = Callable[[Any], None]
PhaseAwareValidatorFunc = Callable[[Any, bool], None]


def creates_validator(validator_func: Callable) -> PhaseAwareValidatorFunc:
    """
    Convert a simple validator function into one that handles both collection and execution phases.
    
    This decorator simplifies creating validators by handling the phase checking internally.
    The wrapped validator only needs to define validation logic for the actual fixture value.
    
    Args:
        validator_func: A function that validates a fixture value
        
    Returns:
        A phase-aware validator function
        
    Example:
        @creates_validator
        def validate_user(user):
            if not hasattr(user, "username"):
                raise AttributeError("User must have username")
    """
    @functools.wraps(validator_func)
    def wrapped(obj: Any, is_collection_phase: bool = False) -> None:
        # Skip validation during collection phase or if obj is a function
        if is_collection_phase or inspect.isfunction(obj):
            return
        
        # Call the original validator with just the object
        return validator_func(obj)
    
    return wrapped


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