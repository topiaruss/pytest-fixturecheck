"""
Django-specific fixture validators for pytest-fixturecheck.

These validators help identify common issues with Django model fixtures.
"""

import inspect
from typing import Any, List, Optional, Type, Union

try:
    from django.core.exceptions import FieldDoesNotExist
    from django.db import models
    from django.db.models import Model
    from django.db.models.fields import Field

    DJANGO_AVAILABLE = True
except ImportError:
    DJANGO_AVAILABLE = False

    # Define stub types for type checking
    class StubModel:
        """Stub class for Model when Django is not available."""

        pass

    class StubField:
        """Stub class for Field when Django is not available."""

        pass

    # Alias the stub classes to the expected names
    Model = StubModel  # type: ignore
    Field = StubField  # type: ignore


def validate_model_fields(obj: Any) -> None:
    """
    Validate that all fields accessed in a Django model fixture exist.

    This helps catch issues where model fields have been renamed or removed
    but fixture code hasn't been updated.

    Args:
        obj: The object returned by the fixture, expected to be a Django model

    Raises:
        ImportError: If Django is not installed
        TypeError: If the object is not a Django model
        AttributeError: If a field being accessed doesn't exist on the model
    """
    if not DJANGO_AVAILABLE:
        raise ImportError(
            "Django integration requires Django to be installed. "
            "Please install Django or remove the validate_model_fields validator."
        )

    # Skip validation if object isn't a Django model
    if not isinstance(obj, Model):
        return

    # Get the calling frame to inspect the code that uses the fixture
    frame = inspect.currentframe()
    if frame and frame.f_back and frame.f_back.f_back:
        frame = frame.f_back.f_back
    else:
        return

    # Get the source code of the fixture function
    source_lines, _ = inspect.getsourcelines(frame.f_code)
    source = "".join(source_lines)

    # Find all potential field accesses in the source code
    field_accesses = _extract_model_field_accesses(
        source, obj.__class__.__name__.lower()
    )

    # Validate each field access
    for field_name in field_accesses:
        try:
            # Check if the field exists on the model
            obj._meta.get_field(field_name)  # type: ignore
        except FieldDoesNotExist:
            raise AttributeError(
                f"Field '{field_name}' does not exist on model {obj.__class__.__name__}. "
                "Did the field name change?"
            )


def _extract_model_field_accesses(source_code: str, model_var: str) -> List[str]:
    """
    Extract potential field accesses from fixture source code.

    This is a simple heuristic that looks for model.field patterns. It's not
    perfect but catches common cases.

    Args:
        source_code: The source code of the fixture
        model_var: The variable name of the model (typically the model name lowercase)

    Returns:
        List of potential field names accessed
    """
    import re

    # Look for patterns like model.field_name or model['field_name']
    field_pattern = rf"{model_var}\.(\w+)"
    dict_access_pattern = rf'{model_var}\[\s*[\'"](\w+)[\'"]\s*\]'

    fields = set()

    # Find all field accesses
    for match in re.finditer(field_pattern, source_code):
        field_name = match.group(1)
        # Skip common Python attributes and methods
        if field_name not in (
            "objects",
            "save",
            "delete",
            "_meta",
            "DoesNotExist",
            "id",
        ):
            fields.add(field_name)

    # Find dictionary-style accesses
    for match in re.finditer(dict_access_pattern, source_code):
        fields.add(match.group(1))

    return list(fields)
