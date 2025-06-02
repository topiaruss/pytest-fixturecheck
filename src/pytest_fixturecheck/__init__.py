"""pytest-fixturecheck - A pytest plugin to validate fixtures before tests."""

import importlib.metadata
from typing import Any

from . import validators
from .decorator import (
    fixturecheck,
    with_model_validation,
    with_required_fields,
    with_required_methods,
)


# Create base exception classes to use when Django is not available
class _FieldDoesNotExistBase(Exception):
    """Base class for Django's FieldDoesNotExist when Django is not installed."""

    pass


class _ValidationErrorBase(Exception):
    """Base class for Django's ValidationError when Django is not installed."""

    pass


# Default implementations when Django is not available
DJANGO_AVAILABLE = False


def _is_django_model_fallback(obj: Any) -> bool:
    """Stub for is_django_model when Django is not installed."""
    return False


def _django_model_has_fields_fallback(*args: Any, **kwargs: Any) -> Any:
    """Stub for django_model_has_fields when Django is not installed."""
    raise ImportError("Django is required for django_model_has_fields")


def _django_model_validates_fallback(*args: Any, **kwargs: Any) -> Any:
    """Stub for django_model_validates when Django is not installed."""
    raise ImportError("Django is required for django_model_validates")


# Try to import Django components
try:
    from .django_validators import (
        DJANGO_AVAILABLE,
        FieldDoesNotExist_Export,
        ValidationError_Export,
        django_model_has_fields,
        django_model_validates,
        is_django_model,
    )

    # Use the real Django exceptions
    FieldDoesNotExist = FieldDoesNotExist_Export
    ValidationError = ValidationError_Export

except ImportError:
    # Use our fallback implementations
    FieldDoesNotExist = _FieldDoesNotExistBase
    ValidationError = _ValidationErrorBase
    is_django_model = _is_django_model_fallback
    django_model_has_fields = _django_model_has_fields_fallback
    django_model_validates = _django_model_validates_fallback

from .utils import creates_validator
from .validators import (
    combines_validators,
    has_property_values,
    has_required_fields,
    has_required_methods,
    is_instance_of,
)
from .validators_fix import (
    check_property_values,
    property_values_validator,
    with_property_values,
)

# Advanced validators (new in 0.3.4)
try:
    from .validators_advanced import (
        nested_property_validator,
        simple_validator,
        type_check_properties,
        with_nested_properties,
        with_type_checks,
    )
except ImportError:
    # These might not be available in a partial installation
    pass

# Get version from package metadata
try:
    __version__ = importlib.metadata.version("pytest-fixturecheck")
except ImportError:
    __version__ = "0.6.0"

# Define what gets imported with "from pytest_fixturecheck import *"
__all__ = [
    # Main decorator
    "fixturecheck",
    # Validator decorator
    "creates_validator",
    # Main validators
    "is_instance_of",
    "has_required_fields",
    "has_required_methods",
    "has_property_values",
    "property_values_validator",
    "check_property_values",
    "with_property_values",
    "combines_validators",
    # Django validators
    "DJANGO_AVAILABLE",
    "is_django_model",
    "django_model_has_fields",
    "django_model_validates",
    "FieldDoesNotExist",
    "ValidationError",
    # Advanced validators (new in 0.3.4)
    "nested_property_validator",
    "type_check_properties",
    "simple_validator",
    "with_nested_properties",
    "with_type_checks",
    # Decorator factory functions (from decorator.py, added in __init__)
    "with_required_fields",
    "with_required_methods",
    "with_model_validation",
]

# Add factory functions to fixturecheck
fixturecheck.with_property_values = with_property_values
fixturecheck.with_required_fields = with_required_fields
fixturecheck.with_required_methods = with_required_methods
fixturecheck.with_model_validation = with_model_validation
fixturecheck.with_nested_properties = with_nested_properties
fixturecheck.with_type_checks = with_type_checks

# Add creates_validator to fixturecheck
fixturecheck.creates_validator = creates_validator

# Add validators module directly to fixturecheck
fixturecheck.validators = validators
