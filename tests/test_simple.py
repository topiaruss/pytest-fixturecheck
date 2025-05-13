"""Simple test file to verify the basic functionality of the plugin."""

import pytest


def test_plugin_exists():
    """Test that the plugin can be imported."""
    from pytest_fixturecheck import fixturecheck

    assert fixturecheck is not None


def test_validators_exist():
    """Test that the validators can be imported."""
    from pytest_fixturecheck import (
        combines_validators,
        has_property_values,
        has_required_fields,
        has_required_methods,
        is_instance_of,
    )

    assert is_instance_of is not None
    assert has_required_fields is not None
    assert has_required_methods is not None
    assert has_property_values is not None
    assert combines_validators is not None


def test_django_validators_exist():
    """Test that the Django validators can be imported."""
    from pytest_fixturecheck import (
        django_model_has_fields,
        django_model_validates,
        is_django_model,
    )

    assert is_django_model is not None
    assert django_model_has_fields is not None
    assert django_model_validates is not None


def test_creates_validator_exists():
    """Test that the creates_validator decorator can be imported."""
    from pytest_fixturecheck import creates_validator

    assert creates_validator is not None
