"""pytest-fixturecheck - A pytest plugin to validate fixtures before tests."""

import importlib.metadata

from . import validators
from .decorator import (
    fixturecheck,
    with_model_validation,
    with_required_fields,
    with_required_methods,
)

# Django validators - only import if Django is available
try:
    from .django_validators import (
        FieldDoesNotExist_Export as FieldDoesNotExist,
        ValidationError_Export as ValidationError,
        django_model_has_fields,
        django_model_validates,
        is_django_model,
        DJANGO_AVAILABLE,
    )
except ImportError:
    # Stub types for when Django is not installed
    DJANGO_AVAILABLE = False

    class FieldDoesNotExist(Exception):
        """Stub for Django's FieldDoesNotExist when Django is not installed."""

        pass

    class ValidationError(Exception):
        """Stub for Django's ValidationError when Django is not installed."""

        pass

    def is_django_model(obj):
        """Stub for is_django_model when Django is not installed."""
        return False

    def django_model_has_fields(*args, **kwargs):
        """Stub for django_model_has_fields when Django is not installed."""
        raise ImportError("Django is required for django_model_has_fields")

    def django_model_validates(*args, **kwargs):
        """Stub for django_model_validates when Django is not installed."""
        raise ImportError("Django is required for django_model_validates")


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
except importlib.metadata.PackageNotFoundError:
    # Package is not installed, use a default version
    __version__ = "0.4.3"

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
