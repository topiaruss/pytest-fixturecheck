"""Simple tests for the decorator behavior."""

import pytest

from pytest_fixturecheck.decorator import fixturecheck


def test_direct_decorator_application():
    """Test direct application of the decorator."""

    def validator(obj, is_collection_phase=False):
        pass  # Don't return anything (None)

    # Check what's happening when we call fixturecheck(validator)
    decorator = fixturecheck(validator)
    print(f"Type of decorator: {type(decorator)}")

    def test_func():
        return "test"

    # Check if we apply this directly
    result = decorator(test_func)
    print(f"Type of result: {type(result)}")

    # Verify that the result is a function and has _fixturecheck
    assert callable(result)
    assert hasattr(result, "_fixturecheck")
    assert result._fixturecheck is True

    # Make sure it works as a function
    assert result() == "test"


def test_simple_decorator():
    """Test the behavior of fixturecheck when used as a simple decorator."""

    def test_func():
        return "test"

    # Apply the decorator directly
    wrapped = fixturecheck(test_func)
    print(f"Type of wrapped (simple): {type(wrapped)}")

    # Verify that the function is decorated properly
    assert hasattr(wrapped, "_fixturecheck")
    assert wrapped._fixturecheck is True

    # Check that the validator is None or default
    assert hasattr(wrapped, "_validator")

    # Make sure it still works as a function
    assert wrapped() == "test"
