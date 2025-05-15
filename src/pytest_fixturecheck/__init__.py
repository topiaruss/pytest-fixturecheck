"""pytest-fixturecheck - A pytest plugin to validate fixtures before tests."""

import importlib.metadata

from . import validators
from .decorator import (
    fixturecheck,
    with_model_validation,
    with_required_fields,
    with_required_methods,
)
from .django_validators import FieldDoesNotExist_Export as FieldDoesNotExist
from .django_validators import ValidationError_Export as ValidationError
from .django_validators import (
    django_model_has_fields,
    django_model_validates,
    is_django_model,
)
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
    __version__ = "0.4.0"

__all__ = [
    "fixturecheck",
    "creates_validator",
    # Validators
    "is_instance_of",
    "has_required_fields",
    "has_required_methods",
    "has_property_values",  # Keep for backward compatibility
    "property_values_validator",  # Fixed property validator that works with a dictionary
    "check_property_values",  # Fixed property validator that works with keyword arguments
    "with_property_values",  # Fixed with_property_values factory function
    "combines_validators",
    # Django validators
    "is_django_model",
    "django_model_has_fields",
    "django_model_validates",
    # Advanced validators (new in 0.3.4)
    "nested_property_validator",
    "type_check_properties",
    "simple_validator",
    "with_nested_properties",
    "with_type_checks",
    # Decorator factory functions (compatibility, from decorator.py)
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
