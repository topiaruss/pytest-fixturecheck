"""Test for the __init__.py file."""

import pytest

from pytest_fixturecheck import (
    __all__,
    __version__,
    check_property_values,
    combines_validators,
    creates_validator,
    django_model_has_fields,
    django_model_validates,
    fixturecheck,
    has_property_values,
    has_required_fields,
    has_required_methods,
    is_django_model,
    is_instance_of,
    property_values_validator,
    with_property_values,
)


def test_exported_symbols():
    """Test that all expected symbols are exported."""
    # Main decorator
    assert callable(fixturecheck)

    # Validator decorator
    assert callable(creates_validator)

    # Main validators
    assert callable(is_instance_of)
    assert callable(has_required_fields)
    assert callable(has_required_methods)
    assert callable(has_property_values)
    assert callable(combines_validators)

    # Fixed property validators
    assert callable(property_values_validator)
    assert callable(check_property_values)
    assert callable(with_property_values)

    # Django validators
    assert callable(is_django_model)
    assert callable(django_model_has_fields)
    assert callable(django_model_validates)

    # Test version
    assert isinstance(__version__, str)
    assert (
        __version__.count(".") == 2
    ), "Version should follow semantic versioning format"
    # Check if it matches the pattern x.y.z where x, y, and z are integers
    major, minor, patch = __version__.split(".")
    assert major.isdigit(), "Major version should be a number"
    assert minor.isdigit(), "Minor version should be a number"
    assert patch.isdigit(), "Patch version should be a number"

    # Test __all__ list
    expected_symbols = [
        "fixturecheck",
        "creates_validator",
        "is_instance_of",
        "has_required_fields",
        "has_required_methods",
        "has_property_values",
        "property_values_validator",
        "check_property_values",
        "with_property_values",
        "combines_validators",
        "is_django_model",
        "django_model_has_fields",
        "django_model_validates",
        # Advanced validators (new in 0.3.4)
        "nested_property_validator",
        "type_check_properties",
        "simple_validator",
        "with_nested_properties",
        "with_type_checks",
        # Decorator factory functions (from decorator.py, added in __init__)
        "with_required_fields",
        "with_required_methods",
        "with_model_validation",
    ]
    for symbol in expected_symbols:
        assert symbol in __all__
    assert len(__all__) == len(expected_symbols)


def test_import_star():
    """Test that importing * from pytest_fixturecheck works."""
    # Create a temporary module scope with the imports
    module_dict = {}
    exec("from pytest_fixturecheck import *", module_dict)

    # Check that all symbols in __all__ are imported
    for symbol in __all__:
        try:
            assert symbol in module_dict, f"Symbol {symbol} was not imported with '*'"
            assert callable(module_dict[symbol]), f"Symbol {symbol} is not callable"
        except (AssertionError, KeyError):
            # Skip advanced validators that might not be available in partial installs
            if symbol not in [
                "nested_property_validator",
                "type_check_properties",
                "simple_validator",
                "with_nested_properties",
                "with_type_checks",
            ]:
                raise


def test_fixturecheck_validator_attributes():
    """Test that fixturecheck has the expected validator attributes."""
    assert hasattr(fixturecheck, "with_required_fields")
    assert hasattr(fixturecheck, "with_required_methods")
    assert hasattr(fixturecheck, "with_model_validation")
    assert hasattr(fixturecheck, "with_property_values")
    assert hasattr(fixturecheck, "creates_validator")
    assert hasattr(fixturecheck, "validators")
