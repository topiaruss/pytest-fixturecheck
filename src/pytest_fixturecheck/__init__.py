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

__version__ = "0.3.0-dev"

__all__ = [
    "fixturecheck",
    "creates_validator",
    
    # Validators
    "is_instance_of",
    "has_required_fields",
    "has_required_methods",
    "has_property_values",
    "combines_validators",
    
    # Django validators
    "is_django_model",
    "django_model_has_fields",
    "django_model_validates",
]
