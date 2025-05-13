"""
Django-specific fixture validators for pytest-fixturecheck.

These validators help identify common issues with Django model fixtures.
"""

import inspect
from typing import Any, List, Optional, Type, Union, Callable

from .utils import creates_validator

try:
    from django.core.exceptions import FieldDoesNotExist, ValidationError
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

    class StubFieldDoesNotExist(Exception):
        """Stub exception for FieldDoesNotExist when Django is not available."""
        pass
        
    class StubValidationError(Exception):
        """Stub exception for ValidationError when Django is not available."""
        pass

    # Alias the stub classes to the expected names
    Model = StubModel  # type: ignore
    Field = StubField  # type: ignore
    FieldDoesNotExist = StubFieldDoesNotExist  # type: ignore
    ValidationError = StubValidationError  # type: ignore


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
        
    # Check basic attributes expected on Django models
    if not hasattr(obj, '_meta') or not hasattr(obj, 'save') or not hasattr(obj, 'delete'):
        return False
        
    # More precise check if django is available
    try:
        return isinstance(obj, Model)
    except (TypeError, ImportError):
        # Fall back to a simple attribute check
        if hasattr(obj, '_meta') and hasattr(obj._meta, 'get_field'):
            return True
    
    return False


def validate_model_fields(obj: Any, is_collection_phase: bool = False) -> None:
    """
    Validate that all fields accessed in a Django model fixture exist.

    This helps catch issues where model fields have been renamed or removed
    but fixture code hasn't been updated.

    Args:
        obj: The object returned by the fixture or the fixture function itself
        is_collection_phase: Whether this is being called during collection phase

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

    # During collection phase, we statically analyze the fixture function
    if is_collection_phase:
        if not callable(obj):
            return
            
        # Get the source code of the fixture function
        try:
            source_lines, _ = inspect.getsourcelines(obj)
            source = "".join(source_lines)
            
            # Try to detect model class names from the source code
            import re
            model_classes = re.findall(r'(\w+)\(\s*[\w=\'",\s]+\)', source)
            for model_name in model_classes:
                # This is just a basic check during collection time
                # We'll do more thorough validation at execution time
                pass
            
            # We don't do actual validation during collection phase
            # just static analysis if needed
        except (TypeError, OSError):
            # Failed to get source lines, which is fine
            pass
        return

    # Skip validation if object isn't a Django model or doesn't have _meta
    if not is_django_model(obj):
        return

    # Get the calling frame to inspect the code that uses the fixture
    frame = inspect.currentframe()
    if frame and frame.f_back and frame.f_back.f_back:
        frame = frame.f_back.f_back
    else:
        return

    # Get the source code of the fixture function
    try:
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
    except (TypeError, OSError):
        # Failed to get source lines, which is fine
        pass


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
            "pk",
            "refresh_from_db",
            "full_clean",
            "clean",
            "clean_fields",
            "validate_unique",
        ):
            fields.add(field_name)

    # Find dictionary-style accesses
    for match in re.finditer(dict_access_pattern, source_code):
        fields.add(match.group(1))

    return list(fields)


@creates_validator
def django_model_has_fields(*field_names: str) -> Callable[[Any], None]:
    """
    Create a validator that checks if a Django model has certain fields.
    
    Args:
        field_names: Names of fields to check for
        
    Returns:
        A validator function
        
    Example:
        @pytest.fixture
        @fixturecheck(django_model_has_fields("username", "email"))
        def user_fixture():
            return User.objects.create(...)
    """
    def validator(obj: Any) -> None:
        if not DJANGO_AVAILABLE:
            raise ImportError("Django is required for model validation")
            
        if not is_django_model(obj):
            raise TypeError(f"Object is not a Django model instance: {type(obj)}")
            
        for field_name in field_names:
            try:
                obj._meta.get_field(field_name)  # type: ignore
            except FieldDoesNotExist:
                raise AttributeError(f"Field '{field_name}' does not exist on model {obj.__class__.__name__}")
    
    return validator


def django_model_validates() -> Callable[[Any, bool], None]:
    """
    Create a validator that performs Django's full_clean validation on a model.
    
    Returns:
        A validator function
        
    Example:
        @pytest.fixture
        @fixturecheck(django_model_validates())
        def user_fixture():
            return User.objects.create(...)
    """
    @creates_validator
    def validator(obj: Any) -> None:
        if not DJANGO_AVAILABLE:
            raise ImportError("Django is required for model validation")
            
        if not is_django_model(obj):
            raise TypeError(f"Object is not a Django model instance: {type(obj)}")
            
        # Call full_clean to run Django's built-in validation
        try:
            obj.full_clean()
        except ValidationError as e:
            raise ValidationError(f"Django model validation failed: {e}")
    
    return validator
