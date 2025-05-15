import functools
import inspect
from typing import Any, Callable, List, Optional, TypeVar, Union, cast, overload

# Create type variables for better typing
F = TypeVar("F", bound=Callable[..., Any])
ValidatorFunc = Callable[[Any, bool], None]

# Import validators and utils
from . import validators
from .utils import creates_validator
from .validators_fix import check_property_values


@overload
def fixturecheck(fixture_or_validator: F) -> F:
    ...

def fixturecheck(
    fixture_or_validator: Optional[Union[F, ValidatorFunc]] = None,
    validator: Optional[ValidatorFunc] = None,
    expect_validation_error: Union[bool, type[Exception]] = False,
) -> Union[F, Callable[[F], F]]:
    # (Removed print(locals()) for now)
    # print(f"FIXTURECHECK_DECORATOR_ENTRY: {{'fixture_or_validator': {fixture_or_validator}, 'validator': {validator}, 'expect_validation_error': {expect_validation_error}}}")

    # Case 1: fixture_or_validator is explicitly a validator instance (or function acting as one)
    if validator is None and getattr(fixture_or_validator, "_is_pytest_fixturecheck_validator", False):
        actual_validator_to_use = cast(ValidatorFunc, fixture_or_validator)
        # print(f"FIXTURECHECK_DEBUG: Using marked validator: {actual_validator_to_use!r}")

        def decorator_for_marked_validator(fixture_body: F) -> F:
            @functools.wraps(fixture_body)
            def wrapped_fixture(*args: Any, **kwargs: Any) -> Any:
                return fixture_body(*args, **kwargs)
            wrapped_fixture._fixturecheck = True # type: ignore
            wrapped_fixture._validator = actual_validator_to_use # type: ignore
            wrapped_fixture._expect_validation_error = expect_validation_error # type: ignore
            return cast(F, wrapped_fixture)
        return decorator_for_marked_validator

    # Case 2: Default behavior / other validators / fixture body processing
    # This is the original logic path, slightly re-ordered for clarity
    if (
        fixture_or_validator is not None
        and callable(fixture_or_validator)
        # and not hasattr(fixture_or_validator, "__self__") # Not strictly needed if we check for marker first
        and validator is None
        # AND it's NOT a marked validator (already handled above)
        and not getattr(fixture_or_validator, "_is_pytest_fixturecheck_validator", False)
    ):
        num_params = -1
        try:
            sig = inspect.signature(fixture_or_validator)
            num_params = len(sig.parameters)
        except Exception:
            pass # Error inspecting, num_params remains -1

        if num_params >= 2: # Potential unmarked validator (e.g. user-defined, takes obj & phase)
            validation_func = cast(ValidatorFunc, fixture_or_validator)
            # print(f"FIXTURECHECK_DEBUG: Using unmarked 2-param validator: {validation_func!r}")
            def decorator_for_unmarked_validator(fixture: F) -> F:
                # ... (same wrapping as decorator_for_marked_validator) ...
                @functools.wraps(fixture)
                def wrapped_fixture(*args: Any, **kwargs: Any) -> Any:
                    return fixture(*args, **kwargs)
                wrapped_fixture._fixturecheck = True; wrapped_fixture._validator = validation_func; wrapped_fixture._expect_validation_error = expect_validation_error
                return cast(F, wrapped_fixture)
            return decorator_for_unmarked_validator
        else: # Assumed to be fixture body (0 or 1 param), or error in signature
            fixture_body_to_wrap = cast(F, fixture_or_validator)
            # print(f"FIXTURECHECK_DEBUG: Treating as fixture body (or 1-param validator to use default): {fixture_body_to_wrap!r}")
            @functools.wraps(fixture_body_to_wrap)
            def wrapped_direct_fixture(*args: Any, **kwargs: Any) -> Any:
                return fixture_body_to_wrap(*args, **kwargs)
            wrapped_direct_fixture._fixturecheck = True # type: ignore
            wrapped_direct_fixture._validator = _default_validator # type: ignore
            wrapped_direct_fixture._expect_validation_error = expect_validation_error # type: ignore
            return cast(F, wrapped_direct_fixture)
    else: # Called as @fixturecheck() or with explicit validator=validator_func or fixture_or_validator is None
        validator_to_assign = validator if validator is not None else _default_validator
        if fixture_or_validator is not None and not callable(fixture_or_validator) and validator is None:
            # This case implies @fixturecheck(non_callable_thing) which is an error or needs specific handling.
            # For now, assume validator_to_assign (default or None) applies.
            # This also covers @fixturecheck(None, expect_validation_error=True)
            if fixture_or_validator is not None: # e.g. @fixturecheck(None) or @fixturecheck(True) (if bool was validator)
                 validator_to_assign = cast(ValidatorFunc, fixture_or_validator) # This path seems problematic for non-callables

        def decorator_for_factory_style(fixture: F) -> F:
            @functools.wraps(fixture)
            def wrapped_fixture(*args: Any, **kwargs: Any) -> Any:
                return fixture(*args, **kwargs)
            wrapped_fixture._fixturecheck = True # type: ignore
            wrapped_fixture._validator = validator_to_assign # type: ignore
            wrapped_fixture._expect_validation_error = expect_validation_error # type: ignore
            return cast(F, wrapped_fixture)
        return decorator_for_factory_style


def _default_validator(obj: Any, is_collection_phase: bool = False) -> None:
    """
    Default validator that auto-detects Django models.

    If the object is a Django model, validate its fields.
    """
    try:
        from .django import DJANGO_AVAILABLE, validate_model_fields

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
            from django.core.exceptions import FieldDoesNotExist

            from .django import DJANGO_AVAILABLE, Model

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

    You can use strict=False to have validation issue warnings instead of exceptions.

    Usage:
    @pytest.fixture
    @fixturecheck.with_property_values(is_active=True, username="testuser")
    def user(db):
        return User.objects.create_user(...)

    # Non-strict validation (warnings instead of errors)
    @pytest.fixture
    @fixturecheck.with_property_values(strict=False, is_active=True)
    def user(db):
        return User.objects.create_user(...)
    """
    # Use the check_property_values function that was imported at the top of the file
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
