"""pytest-fixturecheck - A pytest plugin to validate fixtures before tests."""

from .decorator import fixturecheck
from .validators import (
    is_instance_of,
    has_required_fields,
    has_required_methods,
    has_property_values,
    combines_validators,
)
from .django import (
    is_django_model,
    django_model_has_fields,
    django_model_validates,
)
from .utils import creates_validator
from .validators_fix import (
    property_values_validator,
    check_property_values,
    with_property_values,
)

__version__ = "0.3.1"

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
    "with_property_values",    # Fixed with_property_values factory function
    "combines_validators",
    
    # Django validators
    "is_django_model",
    "django_model_has_fields",
    "django_model_validates",
]

# Add our fixed with_property_values to fixturecheck
fixturecheck.with_property_values = with_property_values
