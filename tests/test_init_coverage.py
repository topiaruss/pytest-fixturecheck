"""Tests specifically for improving coverage of __init__.py."""

import importlib


def test_import_module():
    """Test importing the module to get coverage for imports."""
    # Import the package - this should execute all of __init__.py
    importlib.import_module("pytest_fixturecheck")

    # Re-import to ensure full coverage
    importlib.reload(importlib.import_module("pytest_fixturecheck"))


def test_package_interface():
    """Test the package's public interface by importing everything."""
    # Import all the exported functions one by one
    # Access the version
    from pytest_fixturecheck import (
        __version__,
    )

    assert __version__

    # Access the __all__ list
    from pytest_fixturecheck import __all__

    assert isinstance(__all__, list)
    assert len(__all__) > 0
