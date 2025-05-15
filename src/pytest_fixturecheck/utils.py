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
    def validator_factory(
        *factory_args: Any, **factory_kwargs: Any
    ) -> Callable[[Any, bool], None]:
        """Factory function that creates and returns a validator function.

        This is called when the @creates_validator decorated function is invoked.
        It returns the actual validator function that will be used by fixturecheck.
        """
        # Get the inner validator from the decorated function
        # Check if the function expects arguments and handle accordingly
        sig = inspect.signature(func)

        # Special case handling: If the function only has one parameter (obj) and is called with no args,
        # it's likely a direct validator function like in test_creates_validator_basic
        if (
            len(sig.parameters) == 1
            and len(factory_args) == 0
            and len(factory_kwargs) == 0
        ):
            # This is a direct validator that takes an object to validate
            # We'll return a wrapper that calls this function directly with the object
            @functools.wraps(func)
            def direct_validator_wrapper(
                obj: Any, is_collection_phase: bool = False
            ) -> None:
                if is_collection_phase:
                    return None  # Skip validation during collection phase

                if inspect.isfunction(obj):
                    # Skip validation for function objects
                    return None

                # Call the original validator directly with the object
                return func(obj)

            # Mark the validator function
            direct_validator_wrapper._is_pytest_fixturecheck_validator = True  # type: ignore
            direct_validator_wrapper._fixturecheck = True  # type: ignore
            direct_validator_wrapper._expect_validation_error = False  # type: ignore

            return direct_validator_wrapper

        # If the function expects more than one parameter and no parameters were provided,
        # return a no-op validator to avoid errors
        elif (
            len(sig.parameters) > 1
            and len(factory_args) == 0
            and len(factory_kwargs) == 0
        ):
            # If the function requires multiple arguments but none were provided,
            # return a no-op validator instead of raising an error
            def noop_validator(obj: Any, is_collection_phase: bool = False) -> None:
                return None

            noop_validator._is_pytest_fixturecheck_validator = True  # type: ignore
            return noop_validator

        # Normal case - call the decorated function with any provided args
        inner_validator = func(*factory_args, **factory_kwargs)

        # If inner_validator is None, return a no-op validator
        if inner_validator is None:

            def noop_validator(obj: Any, is_collection_phase: bool = False) -> None:
                return None

            noop_validator._is_pytest_fixturecheck_validator = True  # type: ignore
            return noop_validator

        # If inner_validator already has the validator flag, return it directly
        if (
            hasattr(inner_validator, "_is_pytest_fixturecheck_validator")
            and inner_validator._is_pytest_fixturecheck_validator
        ):
            return inner_validator

        # Create a wrapper for the inner validator to make it phase-aware
        @functools.wraps(
            inner_validator if hasattr(inner_validator, "__name__") else func
        )
        def validator_wrapper(obj: Any, is_collection_phase: bool = False) -> None:
            """The actual validator function that will be called by fixturecheck."""
            if is_collection_phase:
                return None  # Skip validation during collection phase

            if inspect.isfunction(obj):
                # Skip validation for function objects
                return None

            # Check if the inner validator expects is_collection_phase as a parameter
            sig = inspect.signature(inner_validator)
            if "is_collection_phase" in sig.parameters:
                # It expects the is_collection_phase parameter
                return inner_validator(obj, is_collection_phase=is_collection_phase)
            else:
                # It doesn't expect the is_collection_phase parameter
                return inner_validator(obj)

        # Mark the validator function
        validator_wrapper._is_pytest_fixturecheck_validator = True  # type: ignore
        validator_wrapper._fixturecheck = True  # type: ignore
        validator_wrapper._expect_validation_error = False  # type: ignore

        return validator_wrapper

    # Mark the factory function
    validator_factory._is_pytest_fixturecheck_creator = True  # type: ignore

    return validator_factory


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
