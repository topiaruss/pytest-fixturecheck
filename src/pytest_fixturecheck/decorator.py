import functools
import inspect
from typing import Any, Callable, List, Optional, Type, TypeVar, Union, cast

# Create type variables for better typing
F = TypeVar("F", bound=Callable[..., Any])
ValidatorFunc = Callable[[Any, bool], None]

# Import validators and utils
from . import validators
from .utils import creates_validator
from .validators_fix import check_property_values

# Try to import from .django_validators. These names should always be available from there.
# DJANGO_AVAILABLE will be the one defined in django_validators.py
try:
    from .django_validators import DJANGO_AVAILABLE
    from .django_validators import validate_model_fields as django_validate_model_fields
except ImportError:
    # This is a fallback if .django_validators itself is missing or unimportable
    DJANGO_AVAILABLE = False

    def django_validate_model_fields(
        obj: Any,
        fields_to_check: Any = None,
        expect_error: bool = False,
        is_collection_phase: bool = False,
    ) -> None:
        return None


# Fix overload definition by adding overload for each signature variant
def fixturecheck(
    fixture_or_validator: Optional[Union[F, ValidatorFunc]] = None,
    validator: Optional[ValidatorFunc] = None,
    expect_validation_error: Union[bool, Type[Exception]] = False,
) -> Union[F, Callable[[F], F]]:
    # (Removed print(locals()) for now)
    # print(f"FIXTURECHECK_DECORATOR_ENTRY: {{'fixture_or_validator': {fixture_or_validator}, 'validator': {validator}, 'expect_validation_error': {expect_validation_error}}}")

    # This inner function applies the chosen validator to the fixture body
    def _apply_validator_and_wrap(
        fixture_body_func: F, chosen_validator_func: ValidatorFunc
    ) -> F:
        @functools.wraps(fixture_body_func)
        def wrapped_fixture(*args: Any, **kwargs: Any) -> Any:
            return fixture_body_func(*args, **kwargs)

        wrapped_fixture._fixturecheck = True  # type: ignore
        wrapped_fixture._validator = chosen_validator_func  # type: ignore
        wrapped_fixture._expect_validation_error = expect_validation_error  # type: ignore
        return cast(F, wrapped_fixture)

    # Case 1: Direct decorator usage e.g. @fixturecheck (on actual fixture func)
    #         or @fixturecheck(fixture_func_directly_if_0_or_1_param_and_not_creator_or_validator)
    # This is when fixture_or_validator is the fixture body itself.
    # Heuristic: validator kwarg is None, and fixture_or_validator is callable,
    # and it's NOT marked as a validator or creator, and it has < 2 params (or not inspectable).

    _is_validator_check_val = False
    _is_creator_check_val = False
    if callable(fixture_or_validator):  # Only attempt getattr if callable
        try:
            _is_validator_check_val = getattr(
                fixture_or_validator, "_is_pytest_fixturecheck_validator", False
            )
        except AttributeError:
            _is_validator_check_val = (
                False  # Should not happen with default, but being defensive
            )

        try:
            _is_creator_check_val = getattr(
                fixture_or_validator, "_is_pytest_fixturecheck_creator", False
            )
        except AttributeError:
            _is_creator_check_val = (
                False  # Should not happen with default, but being defensive
            )

    if (
        validator is None
        and callable(fixture_or_validator)
        and not _is_validator_check_val
        and not _is_creator_check_val
    ):
        try:
            sig = inspect.signature(fixture_or_validator)
            if len(sig.parameters) < 2:
                # Assumed to be fixture body
                return _apply_validator_and_wrap(
                    cast(F, fixture_or_validator), _default_validator
                )
        except (
            Exception
        ):  # Not inspectable, assume fixture body if other conditions met
            return _apply_validator_and_wrap(
                cast(F, fixture_or_validator), _default_validator
            )
        # If it has >= 2 params, it will be handled by the logic below that returns a decorator

    # Case 2: Called as @fixturecheck(...) or @fixturecheck() or with validator=
    # This means fixturecheck returns a decorator, which will then be applied to the fixture body.
    def _decorator_to_return(fixture_body_func: F) -> F:
        actual_validator_to_use = None

        if validator is not None:  # validator= kwarg was used
            if getattr(validator, "_is_pytest_fixturecheck_creator", False):
                actual_validator_to_use = validator()  # type: ignore # Call factory
            else:
                actual_validator_to_use = (
                    validator  # Use directly (could be validator instance or func)
                )
        elif fixture_or_validator is not None and callable(fixture_or_validator):
            # fixture_or_validator is the first positional arg
            if getattr(fixture_or_validator, "_is_pytest_fixturecheck_creator", False):
                actual_validator_to_use = fixture_or_validator()  # type: ignore # Call factory
            elif getattr(
                fixture_or_validator, "_is_pytest_fixturecheck_validator", False
            ):
                actual_validator_to_use = (
                    fixture_or_validator  # Use marked validator directly
                )
            else:
                # Unmarked callable. Check signature again (it passed the <2 check above or wasn't fixture body)
                try:
                    sig = inspect.signature(fixture_or_validator)
                    if len(sig.parameters) >= 2:  # Unmarked 2-param validator function
                        actual_validator_to_use = fixture_or_validator
                    else:  # Fallback for callable with <2 params not caught as fixture body
                        actual_validator_to_use = _default_validator
                except Exception:
                    actual_validator_to_use = _default_validator
        else:  # Default case (e.g. @fixturecheck() or fixture_or_validator is None/non-callable)
            actual_validator_to_use = _default_validator

        # Safeguard: if factory returned None or validator ended up as None
        if actual_validator_to_use is None:
            actual_validator_to_use = _default_validator

        return _apply_validator_and_wrap(fixture_body_func, actual_validator_to_use)

    return _decorator_to_return


# This is the default validator used if no validator is explicitly provided.
# It tries to be helpful for common cases, e.g., Django models.
def _default_validator(obj: Any, is_collection_phase: bool = False) -> None:
    if is_collection_phase:
        return  # Default validator does nothing during collection

    if DJANGO_AVAILABLE:
        # Only import Model if Django is actually available
        try:
            from django.db.models import Model

            if isinstance(obj, Model):
                # Use the imported (and possibly renamed) validate_model_fields
                django_validate_model_fields(
                    obj=obj,
                    fields_to_check=None,
                    expect_error=False,
                    is_collection_phase=is_collection_phase,
                )
                return
        except ImportError:
            # This case should ideally not be hit if DJANGO_AVAILABLE is true,
            # but as a safeguard, if django.db.models.Model can't be imported, pass through.
            pass

    # If not a Django model or Django not available (or Model import failed),
    # default validator does nothing further.


@functools.wraps(fixturecheck)
def _fixturecheck_nop(*args: Any, **kwargs: Any) -> None:
    pass  # Add pass to fix IndentationError


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
    @fixturecheck.with_required_methods("get_absolute_url", "clean")
    def model_instance(db):
        return MyModel.objects.create(...)
    """
    return lambda fixture: fixturecheck(validators.has_required_methods(*method_names))(
        fixture
    )


def with_model_validation(*field_names: str) -> Callable[[F], F]:
    """
    Factory function to create a validator that checks for Django model validation.

    This is a compatibility wrapper that creates a validator that:
    1. Checks that the fixture result is a Django model
    2. Validates that the specified fields exist
    3. Calls full_clean() to run Django's validation

    Usage:
    @pytest.fixture
    @fixturecheck.with_model_validation("name", "slug")
    def category(db):
        return Category.objects.create(name="Test", slug="test")
    """

    # Create a validator function
    def validator(obj: Any, is_collection_phase: bool = False) -> None:
        if is_collection_phase:
            return

        if not DJANGO_AVAILABLE:
            return

        from .django_validators import (
            django_model_has_fields,
            django_model_validates,
            is_django_model,
        )

        if not is_django_model(obj):
            raise TypeError(f"Expected a Django model instance, got {type(obj)}")

        # Validate fields if specified
        if field_names:
            val_func = django_model_has_fields(*field_names)
            val_func(obj, is_collection_phase)

        # Validate with full_clean
        django_model_validates()(obj, is_collection_phase)

    # Mark as a validator
    validator._is_pytest_fixturecheck_validator = True  # type: ignore

    # Return the decorator
    return lambda fixture: fixturecheck(validator)(fixture)


def with_property_values(**expected_values: Any) -> Callable[[F], F]:
    """
    Factory function to create a validator that checks property values.

    This is a compatibility wrapper for check_property_values.

    Usage:
    @pytest.fixture
    @fixturecheck.with_property_values(name="test", value=42)
    def test_obj():
        obj = TestObj()
        obj.name = "test"
        obj.value = 42
        return obj
    """
    return lambda fixture: fixturecheck(check_property_values(**expected_values))(
        fixture
    )
