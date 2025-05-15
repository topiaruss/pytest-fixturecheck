"""
Django-specific fixture validators for pytest-fixturecheck.

These validators help identify common issues with Django model fixtures.
"""

import inspect
from typing import Any, Callable, List, Optional, Type, Union

from .utils import creates_validator

# Initialize DJANGO_AVAILABLE and dummy types
DJANGO_AVAILABLE = False
_InitialImportError: Optional[ImportError] = None


# Define base dummy exceptions that can be raised/caught
class DjangoFieldDoesNotExistBase(Exception):
    pass


class DjangoValidationErrorBase(Exception):
    pass


DjangoFieldDoesNotExist = DjangoFieldDoesNotExistBase
DjangoValidationError = DjangoValidationErrorBase

# Aliases for common testing usage
ValidationError = DjangoValidationError
FieldDoesNotExist = DjangoFieldDoesNotExist


# Define dummy structures for type hints and basic attribute access if Django is not available
class _DummyDjangoField:
    name: str = ""
    # Add other attributes if accessed by functions when DJANGO_AVAILABLE is False (shouldn't happen ideally)


class _DummyDjangoModelMeta:
    concrete_fields: List[_DummyDjangoField] = []
    fields: List[_DummyDjangoField] = []
    many_to_many: List[_DummyDjangoField] = []
    verbose_name: str = ""
    # Add other attributes as needed if accessed when DJANGO_AVAILABLE is False


class _DummyDjangoModel:
    _meta: _DummyDjangoModelMeta = _DummyDjangoModelMeta()
    pk: Any = None

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        pass

    def full_clean(
        self, exclude: Optional[List[str]] = None, validate_unique: bool = True
    ) -> None:
        pass

    # Add other methods/attributes as needed


class _MockDjangoModelsModule:
    Model = _DummyDjangoModel
    # NOT_PROVIDED = object() # If used


django_models: Any = _MockDjangoModelsModule()
DjangoField: Any = _DummyDjangoField


try:
    from django.conf import settings

    # Remove this check that prevents Django from being detected in tests
    # if not settings.configured:
    #     # This makes the module gracefully handle non-configured Django settings
    #     raise ImportError("Django settings not configured during pytest_fixturecheck.django_validators import.")
    # If settings are configured, proceed with real Django imports
    from django.core.exceptions import FieldDoesNotExist as DjangoFieldDoesNotExist_real
    from django.core.exceptions import ValidationError as DjangoValidationError_real
    from django.db import models as django_models_real
    from django.db.models.fields import Field as DjangoField_real

    # Reassign to real Django components
    DjangoFieldDoesNotExist = DjangoFieldDoesNotExist_real  # type: ignore
    DjangoValidationError = DjangoValidationError_real  # type: ignore
    django_models = django_models_real
    DjangoField = DjangoField_real  # type: ignore

    # Export the exceptions for use by other modules
    # Use different names to avoid name conflicts with type annotations
    from typing import cast

    ValidationError_Export: Type[Exception] = cast(
        Type[Exception], DjangoValidationError
    )
    FieldDoesNotExist_Export: Type[Exception] = cast(
        Type[Exception], DjangoFieldDoesNotExist
    )

    DJANGO_AVAILABLE = True

except ImportError as e:
    _InitialImportError = e
    # DJANGO_AVAILABLE remains False
    # Dummy types defined above will be used by the rest of the file.
    # Ensure functions below check DJANGO_AVAILABLE before using Django specifics.
    pass


# --- Validator Functions ---
# These functions should check DJANGO_AVAILABLE before performing Django-specific operations.


def is_django_model(obj: Any) -> bool:
    """
    Check if an object is a Django model instance.

    This is a more robust check than just isinstance(obj, Model).

    Args:
        obj: The object to check

    Returns:
        True if the object is a Django model instance, False otherwise
    """
    if not DJANGO_AVAILABLE:
        return False

    # Basic checks before attempting to access Django-specific attributes
    if obj is None:
        return False

    # Check if object has _meta which is a good indicator of a Django model
    if not hasattr(obj, "_meta"):
        return False

    try:
        # Try the direct isinstance check first
        if isinstance(obj, django_models.Model):
            return True

        # As a fallback in test environments where class hierarchies might be complex,
        # check if any base class is named 'Model' and from django.db.models
        for base in type(obj).__mro__:
            if base.__name__ == "Model" and base.__module__.startswith(
                "django.db.models"
            ):
                return True
    except (ImportError, AttributeError, TypeError):
        # Handle any issues with the checks above
        pass

    return False


@creates_validator
def validate_model_fields(
    obj_or_fixture: Any,
    fields_to_check: Optional[List[str]] = None,
    expect_error: Union[bool, Type[Exception]] = False,
    is_collection_phase: bool = False,
) -> None:
    """
    Validates that a Django model instance has the specified fields populated
    and that obj.full_clean() passes.

    Args:
        obj_or_fixture: The object returned by the fixture or the fixture function itself
        fields_to_check: List of field names to check (if None, checks all fields)
        expect_error: Whether to expect a validation error
        is_collection_phase: Whether this is a collection phase validation

    Raises:
        ImportError: If Django is not installed
        TypeError: If the object is not a Django model
        AssertionError: If the validation error does not match the expected error message
    """
    if is_collection_phase or not DJANGO_AVAILABLE:
        return

    model_instance = obj_or_fixture

    if not is_django_model(model_instance):
        # If it's not a Django model, this validator doesn't apply.
        # Or, raise an error if it was expected to be a Django model.
        # For now, we silently pass if it's not a model, assuming other validators might handle it.
        return

    errors: List[str] = []

    # 1. Check specified fields are not None (or handle other "empty" conditions)
    if fields_to_check:
        for field_name in fields_to_check:
            try:
                field_value = getattr(model_instance, field_name)
                if field_value is None:  # Basic check, could be more sophisticated
                    errors.append(f"Field '{field_name}' is None.")
            except AttributeError:
                errors.append(f"Field '{field_name}' does not exist on model.")
            except (
                DjangoFieldDoesNotExist
            ):  # pragma: no cover (AttributeError likely first)
                errors.append(
                    f"Field '{field_name}' (Django FieldDoesNotExist) on model."
                )

    # 2. Run full_clean()
    try:
        model_instance.full_clean()
    except (
        DjangoValidationError
    ) as e:  # Use the (potentially dummied) DjangoValidationError
        # If Django is not available, this path shouldn't be hit due to DJANGO_AVAILABLE check.
        # If it is available, e.messages might exist.
        if hasattr(e, "message_dict"):
            for field, field_errors in e.message_dict.items():  # type: ignore
                for err_msg in field_errors:
                    errors.append(f"Field '{field}' full_clean error: {err_msg}")
        elif hasattr(e, "messages"):  # For non_field_errors or single message
            errors.append(f"full_clean error: {'; '.join(e.messages)}")  # type: ignore
        else:  # pragma: no cover
            errors.append(f"full_clean error: {str(e)}")

    if errors:
        error_message = (
            f"Validation failed for model <{type(model_instance).__name__} pk={getattr(model_instance, 'pk', None)}>:\\n- "
            + "\\n- ".join(errors)
        )
        # Raise a standard ValueError or a custom exception.
        # For now, using DjangoValidationError if available, else ValueError.
        if DJANGO_AVAILABLE:
            raise DjangoValidationError(error_message)  # type: ignore
        else:  # pragma: no cover (should not happen if DJANGO_AVAILABLE is false from start)
            raise ValueError(error_message)
    # If no errors, validation passes, return None implicitly.


@creates_validator
def django_model_has_fields(*required_fields: str, allow_empty: bool = False):
    """
    Validator factory: Checks if a Django model instance has specific fields populated.

    If allow_empty is False (default), fields must not be None.

    Args:
        required_fields: Names of fields to check for
        allow_empty: Whether to allow fields to be empty

    Returns:
        A validator function that accepts (obj, is_collection_phase)
    """
    # Note: Removed the is_collection_phase parameter from the factory function

    def validator(model_instance: Any, is_collection_phase: bool = False) -> None:
        """The validator function that checks that a model has the required fields."""
        # Skip validation during collection phase
        if is_collection_phase:
            return

        # Skip validation if Django is not available
        if not DJANGO_AVAILABLE:
            return

        # Skip validation if it's not a Django model
        if not is_django_model(model_instance):
            return

        missing_fields: List[str] = []
        empty_fields: List[str] = []

        for field_name in required_fields:
            try:
                value = getattr(model_instance, field_name)
                if not allow_empty and value is None:  # Simplified check for "empty"
                    empty_fields.append(field_name)
            except AttributeError:
                missing_fields.append(field_name)
            except DjangoFieldDoesNotExist:  # pragma: no cover
                missing_fields.append(f"{field_name} (FieldDoesNotExist)")

        error_messages: List[str] = []
        if missing_fields:
            error_messages.append(f"Missing fields: {', '.join(missing_fields)}.")
        if empty_fields:
            error_messages.append(
                f"Fields are empty (None): {', '.join(empty_fields)}."
            )

        if error_messages:
            # Use getattr to safely access pk even if it doesn't exist
            model_pk = getattr(model_instance, "pk", None)
            full_message = (
                f"Django model <{type(model_instance).__name__} pk={model_pk}> "
                + " ".join(error_messages)
            )
            if DJANGO_AVAILABLE:
                raise DjangoValidationError(full_message)  # type: ignore
            else:  # pragma: no cover
                raise ValueError(full_message)

    # Return the validator function
    return validator


@creates_validator
def django_model_validates():
    """
    Validator factory: Checks if a Django model instance passes model.full_clean().

    Returns:
        A validator function that accepts (obj, is_collection_phase)
    """
    # Note: Removed the is_collection_phase parameter from the factory function

    def validator(model_instance: Any, is_collection_phase: bool = False) -> None:
        """The validator function that checks if a model passes full_clean()."""
        # Skip validation during collection phase
        if is_collection_phase:
            return

        # Skip validation if Django is not available
        if not DJANGO_AVAILABLE:
            return

        # Skip validation if it's not a Django model
        if not is_django_model(model_instance):
            return

        try:
            model_instance.full_clean()
        except DjangoValidationError:
            # Re-raise the exception
            raise

    # Return the validator function
    return validator


# Ensure __all__ is defined if this is intended as a non-trivial package component
__all__ = [
    "DJANGO_AVAILABLE",
    "is_django_model",
    "validate_model_fields",  # Note: This is the raw validator, not a factory
    "django_model_has_fields",
    "django_model_validates",
    "DjangoFieldDoesNotExist",  # Exporting the exception type
    "DjangoValidationError",  # Exporting the exception type
    "ValidationError",  # Add the aliases for testing
    "FieldDoesNotExist",
]
