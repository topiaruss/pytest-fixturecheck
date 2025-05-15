"""
Tests to demonstrate the 'strict' parameter behavior with actual pytest fixtures.

These tests verify that:
1. By default (strict=True), property validation raises exceptions
2. With strict=False, property validation issues warnings instead
"""

import warnings

import pytest

from pytest_fixturecheck import fixturecheck
from pytest_fixturecheck.validators_fix import (
    check_property_values,
    with_property_values,
)


class StrictFixtureTestObject:
    def __init__(self, name, value):
        self.name = name
        self.value = value


# Fixture with default strict behavior (exceptions)
@pytest.fixture
@with_property_values(name="test", value=42)
def default_fixture():
    """Fixture with default strict behavior (will raise exception)."""
    return StrictFixtureTestObject("wrong", 99)


# Fixture with explicit strict=True behavior (exceptions)
@pytest.fixture
@with_property_values(strict=True, name="test", value=42)
def strict_fixture():
    """Fixture with strict=True (will raise exception)."""
    return StrictFixtureTestObject("wrong", 99)


# Fixture with strict=False behavior (warnings)
@pytest.fixture
@with_property_values(strict=False, name="test", value=42)
def non_strict_fixture():
    """Fixture with strict=False (will issue warnings, not exceptions)."""
    return StrictFixtureTestObject("wrong", 99)


# Test with default strict fixture - should fail
@pytest.mark.xfail(
    reason="This test should fail because the fixture has default strict validation"
)
def test_default_fixture(default_fixture):
    """Test that default strict validation fails the test."""
    # This test should never run because fixture validation fails
    assert default_fixture is not None


# Test with explicit strict=True fixture - should fail
@pytest.mark.xfail(
    reason="This test should fail because the fixture has strict=True validation"
)
def test_strict_fixture(strict_fixture):
    """Test that strict=True validation fails the test."""
    # This test should never run because fixture validation fails
    assert strict_fixture is not None


# Test with non-strict fixture - should pass with warnings
def test_non_strict_fixture(non_strict_fixture):
    """Test that non-strict validation passes the test but issues warnings."""
    # This test should run and pass
    assert non_strict_fixture.name == "wrong"  # Not "test"
    assert non_strict_fixture.value == 99  # Not 42


# Test that warnings are issued with non-strict fixture
def test_non_strict_warnings():
    """Test that non-strict fixture validation issues warnings."""
    warnings_list = []

    # Create a function to record warnings
    def record_warning(message, category, filename, lineno, file=None, line=None):
        warnings_list.append(str(message))

    # Register our warning handler
    original_showwarning = warnings.showwarning
    warnings.showwarning = record_warning

    try:
        # Create and call the fixture directly
        fixture = with_property_values(strict=False, name="test", value=42)(
            lambda: StrictFixtureTestObject("wrong", 99)
        )
        result = fixture()

        # Verify warnings were issued
        assert len(warnings_list) == 2
        assert "Expected name=test, got wrong" in warnings_list[0]
        assert "Expected value=42, got 99" in warnings_list[1]

        # Verify the fixture still returns the result
        assert result.name == "wrong"
        assert result.value == 99
    finally:
        # Restore the original warning handler
        warnings.showwarning = original_showwarning


# Test with fixturecheck and check_property_values
@pytest.fixture
@fixturecheck(check_property_values(strict=False, name="test", value=42))
def non_strict_check_fixture():
    """Fixture with strict=False using check_property_values."""
    return StrictFixtureTestObject("wrong", 99)


def test_non_strict_check_fixture(non_strict_check_fixture):
    """Test that non-strict check_property_values passes the test but issues warnings."""
    # This test should run and pass
    assert non_strict_check_fixture.name == "wrong"  # Not "test"
    assert non_strict_check_fixture.value == 99  # Not 42
