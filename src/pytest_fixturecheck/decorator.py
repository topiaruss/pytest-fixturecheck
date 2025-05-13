import functools
import inspect
from typing import Any, Callable, List, Optional, TypeVar, Union, cast

# Create type variables for better typing
F = TypeVar("F", bound=Callable[..., Any])
ValidatorFunc = Callable[[Any, bool], None]


def fixturecheck(
    fixture_or_validator: Union[F, Optional[ValidatorFunc]] = None,
    validator: Optional[ValidatorFunc] = None,
) -> Union[F, Callable[[F], F]]:
    """
    Decorator to validate pytest fixtures before they're used in tests.

    Can be used in two ways:

    1. As a simple decorator:
       @fixturecheck
       @pytest.fixture
       def my_fixture():
           ...

    2. With a validator function:
       @fixturecheck(my_validator_function)
       @pytest.fixture
       def my_fixture():
           ...

    The validator function should accept:
    - The fixture value or fixture function (depending on when it's called)
    - A boolean flag indicating if it's being called during collection phase

    Args:
        fixture_or_validator: Either the fixture function or a validator function
        validator: Optional validator function (not used in the current implementation)

    Returns:
        A decorated fixture function or a decorator function
    """
    # Called as @fixturecheck
    if callable(fixture_or_validator) and validator is None:
        fixture = cast(F, fixture_or_validator)

        @functools.wraps(fixture)
        def wrapped_fixture(*args: Any, **kwargs: Any) -> Any:
            return fixture(*args, **kwargs)

        # Mark this fixture for validation
        wrapped_fixture._fixturecheck = True  # type: ignore
        # Use the default validator (auto-detect Django models)
        wrapped_fixture._validator = _default_validator  # type: ignore
        return cast(F, wrapped_fixture)

    # Called as @fixturecheck(validator_func)
    else:
        validation_func = cast(Optional[ValidatorFunc], fixture_or_validator)

        def decorator(fixture: F) -> F:
            @functools.wraps(fixture)
            def wrapped_fixture(*args: Any, **kwargs: Any) -> Any:
                return fixture(*args, **kwargs)

            # Mark this fixture for validation
            wrapped_fixture._fixturecheck = True  # type: ignore
            wrapped_fixture._validator = validation_func  # type: ignore
            return cast(F, wrapped_fixture)

        return decorator


def _default_validator(obj: Any, is_collection_phase: bool) -> None:
    """
    Default validator that auto-detects Django models.
    
    If the object is a Django model, validate its fields.
    """
    try:
        from .django import validate_model_fields, DJANGO_AVAILABLE, Model
        
        if DJANGO_AVAILABLE:
            # Check if it's a Django model
            if not is_collection_phase and hasattr(obj, '_meta') and isinstance(obj, Model):
                validate_model_fields(obj, is_collection_phase)
    except ImportError:
        pass  # Django not available, skip validation


def with_required_fields(*field_names: str) -> Callable[[F], F]:
    """
    Factory function to create a validator that checks for required fields.
    
    Usage:
    @pytest.fixture
    @fixturecheck.with_required_fields("username", "email")
    def user(db):
        return User.objects.create_user(...)
        
    Args:
        field_names: Names of fields that must be present and non-None
        
    Returns:
        A decorator that can be applied to a fixture
    """
    def validator(obj: Any, is_collection_phase: bool) -> None:
        if is_collection_phase:
            return  # Skip during collection phase
            
        for field in field_names:
            if not hasattr(obj, field):
                raise AttributeError(f"Required field '{field}' missing from {obj.__class__.__name__}")
            if getattr(obj, field) is None:
                raise ValueError(f"Required field '{field}' is None in {obj.__class__.__name__}")
    
    def decorator(fixture: F) -> F:
        return fixturecheck(validator)(fixture)
    
    return decorator


def with_required_methods(*method_names: str) -> Callable[[F], F]:
    """
    Factory function to create a validator that checks for required methods.
    
    Usage:
    @pytest.fixture
    @fixturecheck.with_required_methods("save", "delete")
    def my_object(db):
        return MyObject.objects.create(...)
        
    Args:
        method_names: Names of methods that must be present and callable
        
    Returns:
        A decorator that can be applied to a fixture
    """
    def validator(obj: Any, is_collection_phase: bool) -> None:
        if is_collection_phase:
            return  # Skip during collection phase
            
        for method in method_names:
            if not hasattr(obj, method):
                raise AttributeError(f"Required method '{method}' missing from {obj.__class__.__name__}")
            if not callable(getattr(obj, method)):
                raise TypeError(f"'{method}' is not callable in {obj.__class__.__name__}")
    
    def decorator(fixture: F) -> F:
        return fixturecheck(validator)(fixture)
    
    return decorator


def with_model_validation(*field_names: str) -> Callable[[F], F]:
    """
    Factory function to create a validator that checks for specific Django model fields.
    
    Usage:
    @pytest.fixture
    @fixturecheck.with_model_validation("username", "email")
    def user(db):
        return User.objects.create_user(...)
        
    Args:
        field_names: Names of model fields that must exist
        
    Returns:
        A decorator that can be applied to a fixture
    """
    def validator(obj: Any, is_collection_phase: bool) -> None:
        if is_collection_phase:
            return  # Skip during collection phase
            
        try:
            from .django import DJANGO_AVAILABLE, Model
            from django.core.exceptions import FieldDoesNotExist
            
            if not DJANGO_AVAILABLE:
                raise ImportError("Django is not available")
                
            if not hasattr(obj, '_meta') or not isinstance(obj, Model):
                raise TypeError(f"Object is not a Django model: {type(obj)}")
                
            for field_name in field_names:
                try:
                    obj._meta.get_field(field_name)
                except FieldDoesNotExist:
                    raise AttributeError(f"Field '{field_name}' does not exist on model {obj.__class__.__name__}")
                    
        except ImportError:
            raise ImportError("Django is required for model validation")
    
    def decorator(fixture: F) -> F:
        return fixturecheck(validator)(fixture)
    
    return decorator


def with_property_values(**expected_values: Any) -> Callable[[F], F]:
    """
    Factory function to create a validator that checks for expected property values.
    
    Usage:
    @pytest.fixture
    @fixturecheck.with_property_values(is_active=True, username="testuser")
    def user(db):
        return User.objects.create_user(...)
        
    Args:
        expected_values: Dictionary of property names and their expected values
        
    Returns:
        A decorator that can be applied to a fixture
    """
    def validator(obj: Any, is_collection_phase: bool) -> None:
        if is_collection_phase:
            return  # Skip during collection phase
            
        for prop_name, expected_value in expected_values.items():
            if not hasattr(obj, prop_name):
                raise AttributeError(f"Property '{prop_name}' missing from {obj.__class__.__name__}")
            
            actual_value = getattr(obj, prop_name)
            if actual_value != expected_value:
                raise ValueError(f"Expected {prop_name}={expected_value}, got {actual_value}")
    
    def decorator(fixture: F) -> F:
        return fixturecheck(validator)(fixture)
    
    return decorator


# Add factory functions as methods to the fixturecheck function
fixturecheck.with_required_fields = with_required_fields  # type: ignore
fixturecheck.with_required_methods = with_required_methods  # type: ignore
fixturecheck.with_model_validation = with_model_validation  # type: ignore
fixturecheck.with_property_values = with_property_values  # type: ignore
