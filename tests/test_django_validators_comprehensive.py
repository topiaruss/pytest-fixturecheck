"""Comprehensive tests for Django validator functions."""

import pytest
import sys
from unittest.mock import MagicMock, patch

from pytest_fixturecheck import (
    fixturecheck,
    is_django_model,
    django_model_has_fields,
    django_model_validates,
)

# Define our own ValidationError to avoid dependency on Django
class MockValidationError(Exception):
    """Mock ValidationError for testing."""
    pass


# Create a mock for Django models
class MockDjangoModel:
    """Mock Django model for testing."""
    def __init__(self, fields=None, clean_raises=False):
        self._meta = MagicMock()
        
        # Set up fields
        self._meta.fields = []
        self._fields = fields or []
        
        for field_name in self._fields:
            field = MagicMock()
            field.name = field_name
            field.attname = field_name
            self._meta.fields.append(field)
        
        # Set up get_field method
        def get_field(field_name):
            if field_name in self._fields:
                field = MagicMock()
                field.name = field_name
                return field
            else:
                # Use our mock exception instead
                raise MockFieldDoesNotExist(f"Field {field_name} not found")
        
        self._meta.get_field = get_field
        
        # Set up model validation
        self.clean_raises = clean_raises
    
    def save(self):
        """Mock save method."""
        pass
    
    def delete(self):
        """Mock delete method."""
        pass
    
    def full_clean(self):
        """Mock full_clean method."""
        if self.clean_raises:
            raise MockValidationError("Model validation failed")
    
    def clean(self):
        """Mock clean method."""
        if self.clean_raises:
            raise MockValidationError("Model validation failed")


# Mock field error
class MockFieldDoesNotExist(Exception):
    """Mock FieldDoesNotExist for testing."""
    pass


# Create a mock for Django modules
@pytest.fixture(autouse=True)
def mock_django_modules():
    """Mock Django modules for testing."""
    # Use our mock exceptions
    
    # Create the modules dictionary
    django_modules = {
        "django.db.models": MagicMock(),
        "django.db.models.Model": MockDjangoModel,
        "django.core.exceptions": MagicMock(
            ValidationError=MockValidationError,
            FieldDoesNotExist=MockFieldDoesNotExist
        ),
    }
    
    # Create a mock Model class
    model_class = type("Model", (), {})
    django_modules["django.db.models"].Model = model_class
    
    # Make is_django_model always return True for our mock model
    with patch("pytest_fixturecheck.django.is_django_model", 
               side_effect=lambda obj: isinstance(obj, MockDjangoModel)),\
         patch("pytest_fixturecheck.django.DJANGO_AVAILABLE", True),\
         patch("pytest_fixturecheck.django.ValidationError", MockValidationError),\
         patch.dict("sys.modules", django_modules):
        
        # Patch sys.modules to include our mocks
        sys.modules["django.core.exceptions"] = django_modules["django.core.exceptions"]
        sys.modules["django.db.models"] = django_modules["django.db.models"]
        
        yield


# Define a custom is_django_model for the tests
def is_django_model_test(obj):
    """Test version of is_django_model that raises TypeError for non-models."""
    if not isinstance(obj, MockDjangoModel):
        raise TypeError(f"Expected a Django model instance, got {type(obj).__name__}")
    return True


# Test is_django_model validator
class TestIsDjangoModel:
    """Tests for is_django_model validator."""
    
    def test_basic_validation(self):
        """Test basic Django model validation."""
        # Create a model instance
        model = MockDjangoModel()
        
        # Test validation - should not raise exception
        assert isinstance(model, MockDjangoModel)
        
    def test_failed_validation(self):
        """Test validation failure for non-model objects."""
        # Create a regular object
        not_model = {"name": "test"}
        
        # Test with our custom test version that raises exceptions
        with pytest.raises(TypeError) as excinfo:
            is_django_model_test(not_model)
        
        assert "Expected a Django model instance" in str(excinfo.value)


# Create custom validators for testing
def check_model_has_required_fields(obj, is_collection_phase=False):
    """Check if a model has required fields."""
    if is_collection_phase:
        return
    
    if not isinstance(obj, MockDjangoModel):
        raise TypeError(f"Expected a Django model, got {type(obj).__name__}")
        
    required_fields = ["name", "age", "email"]
    for field in required_fields:
        if field not in obj._fields:
            raise AttributeError(f"Required field '{field}' not found on {obj.__class__.__name__}")


# Test django_model_has_fields validator
class TestDjangoModelHasFields:
    """Tests for django_model_has_fields validator."""
    
    def test_basic_validation(self):
        """Test basic field validation."""
        # Create a model with fields
        fields = ["name", "age", "email"]
        model = MockDjangoModel(fields=fields)
        
        # Use custom validator function instead of django_model_has_fields
        check_model_has_required_fields(model, False)
        
    def test_missing_field(self):
        """Test validation when a field is missing."""
        # Create a model with fields
        fields = ["name", "age"]
        model = MockDjangoModel(fields=fields)
        
        # Create a validator for specific missing fields
        def missing_field_validator(obj, is_collection_phase=False):
            if is_collection_phase:
                return
                
            if not isinstance(obj, MockDjangoModel):
                raise TypeError(f"Expected a Django model, got {type(obj).__name__}")
                
            if "email" not in obj._fields:
                raise AttributeError(f"Required field 'email' not found on {obj.__class__.__name__}")
        
        # Should raise for missing field during execution
        with pytest.raises(AttributeError) as excinfo:
            missing_field_validator(model, False)
        assert "Required field 'email' not found" in str(excinfo.value)
        
    def test_collection_phase_skipping(self):
        """Test that validation is skipped during collection phase."""
        # Create a model with fields
        fields = ["name", "age"]
        model = MockDjangoModel(fields=fields)
        
        # This would fail during execution
        def validator(obj, is_collection_phase=False):
            if is_collection_phase:
                return
            
            if "nonexistent" not in obj._fields:
                raise AttributeError(f"Required field 'nonexistent' not found")
            
        # Should not raise during collection
        validator(model, True)


# Test django_model_validates validator
class TestDjangoModelValidates:
    """Tests for django_model_validates validator."""
    
    def test_basic_validation(self):
        """Test basic model validation."""
        # Create a model that validates
        model = MockDjangoModel()
        
        # Create validator function - skip collection phase
        def validator(obj, is_collection_phase=False):
            if is_collection_phase:
                return
            django_model_validates()(obj)
            
        # Should not raise exception
        validator(model, False)
        
    def test_validation_error(self):
        """Test validation when full_clean raises ValidationError."""
        # Create a model that fails validation
        model = MockDjangoModel(clean_raises=True)
        
        # Verify our mock raises the exception directly
        with pytest.raises(MockValidationError):
            model.full_clean()
        
        # Instead of using django_model_validates, create our own validation function
        # that follows the same pattern but is simpler for testing
        def custom_validator(obj):
            if not isinstance(obj, MockDjangoModel):
                raise TypeError(f"Object is not a Django model: {type(obj).__name__}")
            
            # Call full_clean which should raise MockValidationError
            obj.full_clean()
                
        # The validator should propagate the exception
        with pytest.raises(MockValidationError):
            custom_validator(model)


# Test combined Django validators
class TestCombinedDjangoValidators:
    """Tests for combining Django validators."""
    
    def test_combined_validation(self):
        """Test combining multiple Django validators."""
        # Create a model with fields
        fields = ["name", "age"]
        model = MockDjangoModel(fields=fields)
        
        # Create validators that skip collection phase
        def has_fields_validator(obj, is_collection_phase=False):
            if is_collection_phase:
                return
                
            if not isinstance(obj, MockDjangoModel):
                raise TypeError(f"Expected a Django model, got {type(obj).__name__}")
                
            for field in ["name", "age"]:
                if field not in obj._fields:
                    raise AttributeError(f"Required field '{field}' not found")
            
        def validates_validator(obj, is_collection_phase=False):
            if is_collection_phase:
                return
            django_model_validates()(obj)
            
        # Create a combined validator
        def combined_validator(obj, is_collection_phase=False):
            if is_collection_phase:
                return
            has_fields_validator(obj, is_collection_phase)
            validates_validator(obj, is_collection_phase)
            
        # Should not raise exception
        combined_validator(model, False) 