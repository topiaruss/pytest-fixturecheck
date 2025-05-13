"""Tests for factory functions in decorator.py."""

import pytest
from unittest.mock import patch, MagicMock

from pytest_fixturecheck import fixturecheck


class TestFactoryFunctions:
    """Test factory functions from decorator.py."""
    
    def test_with_required_fields(self):
        """Test with_required_fields factory."""
        # Create a mock validator
        with patch("pytest_fixturecheck.validators.has_required_fields") as mock_validator:
            mock_validator.return_value = lambda obj, is_collection_phase=False: None
            
            # Test fixture
            @fixturecheck.with_required_fields("field1", "field2")
            def test_fixture():
                return {"field1": 1, "field2": 2}
                
            # Check fixture is marked correctly
            assert hasattr(test_fixture, "_fixturecheck")
            assert test_fixture._fixturecheck is True
            assert hasattr(test_fixture, "_validator")
            assert callable(test_fixture._validator)
            
            # Check validator was called with correct arguments
            mock_validator.assert_called_once_with("field1", "field2")
    
    def test_with_required_methods(self):
        """Test with_required_methods factory."""
        # Create a mock validator
        with patch("pytest_fixturecheck.validators.has_required_methods") as mock_validator:
            mock_validator.return_value = lambda obj, is_collection_phase=False: None
            
            # Test fixture
            @fixturecheck.with_required_methods("method1", "method2")
            def test_fixture():
                class TestObj:
                    def method1(self): pass
                    def method2(self): pass
                return TestObj()
                
            # Check fixture is marked correctly
            assert hasattr(test_fixture, "_fixturecheck")
            assert test_fixture._fixturecheck is True
            assert hasattr(test_fixture, "_validator")
            assert callable(test_fixture._validator)
            
            # Check validator was called with correct arguments
            mock_validator.assert_called_once_with("method1", "method2")
    
    def test_with_property_values(self):
        """Test with_property_values factory."""
        # Create a mock validator
        with patch("pytest_fixturecheck.validators.has_property_values") as mock_validator:
            mock_validator.return_value = lambda obj, is_collection_phase=False: None
            
            # Test fixture
            @fixturecheck.with_property_values(prop1=1, prop2=2)
            def test_fixture():
                class TestObj:
                    prop1 = 1
                    prop2 = 2
                return TestObj()
                
            # Check fixture is marked correctly
            assert hasattr(test_fixture, "_fixturecheck")
            assert test_fixture._fixturecheck is True
            assert hasattr(test_fixture, "_validator")
            assert callable(test_fixture._validator)
            
            # Check validator was called with correct arguments
            mock_validator.assert_called_once_with(prop1=1, prop2=2)


class TestModelValidation:
    """Test model validation factory."""
    
    @patch("pytest_fixturecheck.decorator.fixturecheck")
    def test_with_model_validation(self, mock_fixturecheck):
        """Test with_model_validation factory."""
        # Mock the fixturecheck function
        mock_fixturecheck.return_value = lambda fixture: fixture
        
        # Test fixture
        @fixturecheck.with_model_validation("field1", "field2")
        def test_fixture():
            return MagicMock()
            
        # Check that fixturecheck was called with a validator
        assert mock_fixturecheck.called
        validator = mock_fixturecheck.call_args[0][0]
        assert callable(validator)


def test_fixturecheck_empty():
    """Test fixturecheck called with empty parentheses."""
    @fixturecheck()
    def test_fixture():
        return "test"
        
    # Check fixture is marked correctly
    assert hasattr(test_fixture, "_fixturecheck")
    assert test_fixture._fixturecheck is True
    assert hasattr(test_fixture, "_validator")
    assert test_fixture._validator is None


def test_fixturecheck_none():
    """Test fixturecheck called with None."""
    @fixturecheck(None)
    def test_fixture():
        return "test"
        
    # Check fixture is marked correctly
    assert hasattr(test_fixture, "_fixturecheck")
    assert test_fixture._fixturecheck is True
    assert hasattr(test_fixture, "_validator")
    assert test_fixture._validator is None 