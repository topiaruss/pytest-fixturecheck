"""
Re-export Django-specific validation functions for backward compatibility.

This module is maintained for backward compatibility with existing code.
New code should import directly from django_validators.
"""

from typing import Callable, Any, Optional, List

from .django_validators import (
    DJANGO_AVAILABLE,
    is_django_model,
    validate_model_fields,
    django_model_has_fields,
    django_model_validates,
)

__all__ = [
    "DJANGO_AVAILABLE",
    "is_django_model",
    "validate_model_fields",
    "django_model_has_fields",
    "django_model_validates",
]
