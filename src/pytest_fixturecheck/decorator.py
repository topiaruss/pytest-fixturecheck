import functools
import inspect
from typing import Any, Callable, List, Optional, TypeVar, Union, cast

# Create type variables for better typing
F = TypeVar("F", bound=Callable[..., Any])
ValidatorFunc = Callable[[Any, bool], None]

# Import validators and utils
from . import validators
from .utils import creates_validator
from .validators_fix import check_property_values


def fixturecheck(
    fixture_or_validator: Union[F, Optional[ValidatorFunc]] = None,
    validator: Optional[ValidatorFunc] = None,
    expect_validation_error: bool = False,
) -> Union[F, Callable[[F], F]]:
    """
    Decorator to validate pytest fixtures before they're used in tests.

    Can be used in several ways:

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

    3. With expected validation error:
       @fixturecheck(my_validator_function, expect_validation_error=True)
       @pytest.fixture
       def my_fixture():
           ...

    The validator function should accept:
    - The fixture value or fixture function (depending on when it's called)
    - A boolean flag indicating if it's being called during collection phase

    Args:
        fixture_or_validator: Either the fixture function or a validator function
        validator: Optional validator function (not used in the current implementation)
        expect_validation_error: Whether to expect a validation error (for testing validators)

    Returns:
        A decorated fixture function or a decorator function
    """
    # Called as @fixturecheck with no arguments - apply to the function directly
    if (
        fixture_or_validator is not None
        and callable(fixture_or_validator)
        and not hasattr(fixture_or_validator, "__self__")
        and validator is None
    ):
        # Check if this looks like a validator function (has the right signature)
        if len(inspect.signature(fixture_or_validator).parameters) >= 2:
            # This is a validator function - create a decorator to apply later
            validation_func = cast(ValidatorFunc, fixture_or_validator)

            def decorator(fixture: F) -> F:
                @functools.wraps(fixture)
                def wrapped_fixture(*args: Any, **kwargs: Any) -> Any:
                    return fixture(*args, **kwargs)

                # Mark this fixture for validation
                wrapped_fixture._fixturecheck = True  # type: ignore
                wrapped_fixture._validator = validation_func  # type: ignore
                wrapped_fixture._expect_validation_error = expect_validation_error  # type: ignore
                return cast(F, wrapped_fixture)

            return decorator
        else:
            # This is a fixture function - wrap it directly
            fixture = cast(F, fixture_or_validator)

            @functools.wraps(fixture)
            def wrapped_fixture(*args: Any, **kwargs: Any) -> Any:
                return fixture(*args, **kwargs)

            # Mark this fixture for validation
            wrapped_fixture._fixturecheck = True  # type: ignore
            # Use the default validator
            wrapped_fixture._validator = _default_validator  # type: ignore
            wrapped_fixture._expect_validation_error = expect_validation_error  # type: ignore
            return cast(F, wrapped_fixture)
    # Called as @fixturecheck() or with a non-callable validator
    else:
        # This is for cases like @fixturecheck() or @fixturecheck(None)
        validation_func = cast(Optional[ValidatorFunc], fixture_or_validator)

        def decorator(fixture: F) -> F:
            @functools.wraps(fixture)
            def wrapped_fixture(*args: Any, **kwargs: Any) -> Any:
                return fixture(*args, **kwargs)

            # Mark this fixture for validation
            wrapped_fixture._fixturecheck = True  # type: ignore
            wrapped_fixture._validator = validation_func  # type: ignore
            wrapped_fixture._expect_validation_error = expect_validation_error  # type: ignore
            return cast(F, wrapped_fixture)

        return decorator


def _default_validator(obj: Any, is_collection_phase: bool = False) -> None:
    """
    Default validator that auto-detects Django models.

    If the object is a Django model, validate its fields.
    """
    try:
        from .django import validate_model_fields, DJANGO_AVAILABLE

        if DJANGO_AVAILABLE:
            # Check if it's a Django model
            if not is_collection_phase and hasattr(obj, "_meta"):
                try:
                    from django.db.models import Model

                    if isinstance(obj, Model):
                        validate_model_fields(obj, is_collection_phase)
                except (ImportError, TypeError):
                    pass  # Django not available or not a Django model
    except ImportError:
        pass  # Django not available, skip validation


# For backwards compatibility, we'll redefine the old factory functions
def with_required_fields(*field_names: str) -> Callable[[F], F]:
    """
    Factory function to create a validator that checks for required fields.

    This is a compatibility wrapper for validators.has_required_fields.

    Usage:
    @pytest.fixture
    @fixturecheck.with_required_fields("username", "email")
    def user(db):
        return User.objects.create_user(...)
    """
    return lambda fixture: fixturecheck(validators.has_required_fields(*field_names))(
        fixture
    )


def with_required_methods(*method_names: str) -> Callable[[F], F]:
    """
    Factory function to create a validator that checks for required methods.

    This is a compatibility wrapper for validators.has_required_methods.

    Usage:
    @pytest.fixture
    @fixturecheck.with_required_methods("save", "delete")
    def my_object(db):
        return MyObject.objects.create(...)
    """
    return lambda fixture: fixturecheck(validators.has_required_methods(*method_names))(
        fixture
    )


def with_model_validation(*field_names: str) -> Callable[[F], F]:
    """
    Factory function to create a validator that checks for specific Django model fields.

    Usage:
    @pytest.fixture
    @fixturecheck.with_model_validation("username", "email")
    def user(db):
        return User.objects.create_user(...)
    """

    def validator(obj: Any, is_collection_phase: bool = False) -> None:
        if is_collection_phase:
            return  # Skip during collection phase

        try:
            from .django import DJANGO_AVAILABLE, Model
            from django.core.exceptions import FieldDoesNotExist

            if not DJANGO_AVAILABLE:
                raise ImportError("Django is not available")

            if not hasattr(obj, "_meta") or not isinstance(obj, Model):
                raise TypeError(f"Object is not a Django model: {type(obj)}")

            for field_name in field_names:
                try:
                    obj._meta.get_field(field_name)
                except FieldDoesNotExist:
                    raise AttributeError(
                        f"Field '{field_name}' does not exist on model {obj.__class__.__name__}"
                    )

        except ImportError:
            raise ImportError("Django is required for model validation")

    def decorator(fixture: F) -> F:
        return fixturecheck(validator)(fixture)

    return decorator


def with_property_values(**expected_values: Any) -> Callable[[F], F]:
    """
    Factory function to create a validator that checks for expected property values.

    This uses the updated check_property_values that works correctly with keyword arguments.

    Usage:
    @pytest.fixture
    @fixturecheck.with_property_values(is_active=True, username="testuser")
    def user(db):
        return User.objects.create_user(...)
    """
    return lambda fixture: fixturecheck(check_property_values(**expected_values))(
        fixture
    )


# Add the validators module to fixturecheck
fixturecheck.validators = validators  # type: ignore

# Add factory functions as methods to the fixturecheck function (for backward compatibility)
fixturecheck.with_required_fields = with_required_fields  # type: ignore
fixturecheck.with_required_methods = with_required_methods  # type: ignore
fixturecheck.with_model_validation = with_model_validation  # type: ignore
fixturecheck.with_property_values = with_property_values  # type: ignore

# Add the creates_validator decorator to fixturecheck
fixturecheck.creates_validator = creates_validator  # type: ignore
