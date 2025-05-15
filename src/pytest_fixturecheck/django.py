"""
Re-export Django-specific validation functions for backward compatibility.

This module is maintained for backward compatibility with existing code.
New code should import directly from django_validators.
"""

from typing import Any, Callable, List, Optional

from .django_validators import (
    DJANGO_AVAILABLE,
    django_model_has_fields,
    django_model_validates,
    is_django_model,
    validate_model_fields,
)

__all__ = [
    "DJANGO_AVAILABLE",
    "is_django_model",
    "validate_model_fields",
    "django_model_has_fields",
    "django_model_validates",
]
