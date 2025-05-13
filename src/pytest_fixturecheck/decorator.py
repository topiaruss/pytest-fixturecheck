import functools
import inspect
from typing import Any, Callable, Optional, TypeVar, Union, cast

# Create type variables for better typing
F = TypeVar("F", bound=Callable[..., Any])
ValidatorFunc = Callable[[Any], None]


def fixturecheck(
    fixture_or_validator: Union[F, Optional[ValidatorFunc]] = None,
    validator: Optional[ValidatorFunc] = None,
) -> Union[F, Callable[[F], F]]:
    """
    Decorator to validate pytest fixtures before they're used in tests.

    Can be used in two ways:

    1. As a simple decorator:
       @fixturecheck
       @pytest.fixture
       def my_fixture():
           ...

    2. With a validator function:
       @fixturecheck(my_validator_function)
       @pytest.fixture
       def my_fixture():
           ...

    The validator function should accept the fixture return value and
    optionally raise exceptions for invalid fixtures.

    Args:
        fixture_or_validator: Either the fixture function or a validator function
        validator: Optional validator function (not used in the current implementation)

    Returns:
        A decorated fixture function or a decorator function
    """
    # Called as @fixturecheck
    if callable(fixture_or_validator) and validator is None:
        fixture = cast(F, fixture_or_validator)

        @functools.wraps(fixture)
        def wrapped_fixture(*args: Any, **kwargs: Any) -> Any:
            return fixture(*args, **kwargs)

        # Mark this fixture for validation
        wrapped_fixture._fixturecheck = True  # type: ignore
        wrapped_fixture._validator = None  # type: ignore
        return cast(F, wrapped_fixture)

    # Called as @fixturecheck(validator_func)
    else:
        validation_func = cast(Optional[ValidatorFunc], fixture_or_validator)

        def decorator(fixture: F) -> F:
            @functools.wraps(fixture)
            def wrapped_fixture(*args: Any, **kwargs: Any) -> Any:
                return fixture(*args, **kwargs)

            # Mark this fixture for validation
            wrapped_fixture._fixturecheck = True  # type: ignore
            wrapped_fixture._validator = validation_func  # type: ignore
            return cast(F, wrapped_fixture)

        return decorator
