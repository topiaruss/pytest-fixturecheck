"""Tests specifically for improving coverage of __init__.py."""

import importlib
import pytest


def test_import_module():
    """Test importing the module to get coverage for imports."""
    # Import the package - this should execute all of __init__.py
    importlib.import_module('pytest_fixturecheck')
    
    # Re-import to ensure full coverage
    importlib.reload(importlib.import_module('pytest_fixturecheck'))


def test_package_interface():
    """Test the package's public interface by importing everything."""
    # Import all the exported functions one by one
    from pytest_fixturecheck import fixturecheck
    from pytest_fixturecheck import creates_validator
    from pytest_fixturecheck import is_instance_of
    from pytest_fixturecheck import has_required_fields
    from pytest_fixturecheck import has_required_methods
    from pytest_fixturecheck import has_property_values
    from pytest_fixturecheck import combines_validators
    from pytest_fixturecheck import is_django_model
    from pytest_fixturecheck import django_model_has_fields
    from pytest_fixturecheck import django_model_validates
    
    # Access the version
    from pytest_fixturecheck import __version__
    assert __version__
    
    # Access the __all__ list
    from pytest_fixturecheck import __all__
    assert isinstance(__all__, list)
    assert len(__all__) > 0 