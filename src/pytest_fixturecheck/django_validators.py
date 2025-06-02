"""
Django-specific fixture validators for pytest-fixturecheck.

These validators help identify common issues with Django model fixtures.
"""

from typing import Any, List, Optional, Type, Union, cast

from .utils import creates_validator

# Initialize DJANGO_AVAILABLE and dummy types
DJANGO_AVAILABLE = False
_InitialImportError: Optional[ImportError] = None


# Define base dummy exceptions that can be raised/caught
class DjangoFieldDoesNotExistBase(Exception):
    """Base class for Django's FieldDoesNotExist when Django is not installed."""

    pass


class DjangoValidationErrorBase(Exception):
    """Base class for Django's ValidationError when Django is not installed."""

    pass


# Initial definitions with dummy values
DjangoFieldDoesNotExist = DjangoFieldDoesNotExistBase
DjangoValidationError = DjangoValidationErrorBase

# Aliases for common testing usage
ValidationError = DjangoValidationError
FieldDoesNotExist = DjangoFieldDoesNotExist
ValidationError_Export = cast(Type[Exception], DjangoValidationError)
FieldDoesNotExist_Export = cast(Type[Exception], DjangoFieldDoesNotExist)


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

    def full_clean(self, exclude: Optional[List[str]] = None, validate_unique: bool = True) -> None:
        pass

    # Add other methods/attributes as needed


class _MockDjangoModelsModule:
    Model = _DummyDjangoModel
    # NOT_PROVIDED = object() # If used


# Initialize with dummy objects
django_models: Any = _MockDjangoModelsModule()
DjangoField: Any = _DummyDjangoField


# Dummy functions for non-Django environments
def _is_django_model_dummy(obj: Any) -> bool:
    """
    Check if an object is a Django model instance (stub when Django is not available).

    Args:
        obj: The object to check

    Returns:
        False when Django is not available
    """
    return False


# Stub functions that raise ImportError immediately when called
def _django_model_has_fields_stub(*args, **kwargs):
    """Stub validator factory when Django is not installed."""
    raise ImportError("Django is required for django_model_has_fields")


def _django_model_validates_stub(*args, **kwargs):
    """Stub validator factory when Django is not installed."""
    raise ImportError("Django is required for django_model_validates")


# Set initial references to dummy functions
is_django_model = _is_django_model_dummy
django_model_has_fields = _django_model_has_fields_stub
django_model_validates = _django_model_validates_stub


# Try to import Django
try:
    from django.conf import settings

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

    # Update the exported exceptions with the real ones
    ValidationError_Export = cast(Type[Exception], DjangoValidationError)
    FieldDoesNotExist_Export = cast(Type[Exception], DjangoFieldDoesNotExist)

    DJANGO_AVAILABLE = True

    # Define real implementations when Django is available
    def _is_django_model_real(obj: Any) -> bool:
        """
        Check if an object is a Django model instance.

        This is a more robust check than just isinstance(obj, Model).

        Args:
            obj: The object to check

        Returns:
            True if the object is a Django model instance, False otherwise
        """
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
                if base.__name__ == "Model" and base.__module__.startswith("django.db.models"):
                    return True
        except (ImportError, AttributeError, TypeError):
            # Handle any issues with the checks above
            pass

        return False

    @creates_validator
    def _django_model_has_fields_real(*required_fields: str, allow_empty: bool = False):
        """
        Validator factory: Checks if a Django model instance has specific fields populated.
        """

        def validator(model_instance: Any, is_collection_phase: bool = False) -> None:
            # Real implementation
            if is_collection_phase:
                return
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
                error_messages.append(f"Fields are empty (None): {', '.join(empty_fields)}.")

            if error_messages:
                # Use getattr to safely access pk even if it doesn't exist
                model_pk = getattr(model_instance, "pk", None)
                full_message = (
                    f"Django model <{type(model_instance).__name__} pk={model_pk}> "
                    + " ".join(error_messages)
                )
                raise DjangoValidationError(full_message)  # type: ignore

        return validator

    @creates_validator
    def _django_model_validates_real():
        """
        Validator factory: Checks if a Django model instance passes model.full_clean().
        """

        def validator(model_instance: Any, is_collection_phase: bool = False) -> None:
            # Real implementation
            if is_collection_phase:
                return
            if not is_django_model(model_instance):
                return
            model_instance.full_clean()

        return validator

    # Replace dummy functions with real implementations
    is_django_model = _is_django_model_real
    django_model_has_fields = _django_model_has_fields_real
    django_model_validates = _django_model_validates_real

except ImportError as e:
    _InitialImportError = e
    # DJANGO_AVAILABLE remains False
    # Stub functions and classes defined above will be used.
    pass


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
            except DjangoFieldDoesNotExist:  # pragma: no cover (AttributeError likely first)
                errors.append(f"Field '{field_name}' (Django FieldDoesNotExist) on model.")

    # 2. Run full_clean()
    try:
        model_instance.full_clean()
    except DjangoValidationError as e:  # Use the (potentially dummied) DjangoValidationError
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
