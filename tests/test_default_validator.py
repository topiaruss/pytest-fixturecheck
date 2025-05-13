"""Tests for the default validator in decorator.py."""

from unittest.mock import MagicMock, patch

import pytest

from pytest_fixturecheck.decorator import _default_validator


class TestDefaultValidator:
    """Tests for the default validator function."""

    def test_default_validator_non_django(self):
        """Test default validator with a non-Django object."""
        # Should not raise any exception
        _default_validator({"test": "value"})
        _default_validator(["test"])
        _default_validator("test")
        _default_validator(123)

    def test_default_validator_collection_phase(self):
        """Test default validator during collection phase."""
        # Create a mock object
        obj = MagicMock()

        # Test with collection phase - should not raise any exceptions
        _default_validator(obj, is_collection_phase=True)

    def test_default_validator_django_not_available(self):
        """Test default validator when Django is not available."""
        # Force import to fail to simulate Django not being available
        with patch(
            "builtins.__import__",
            side_effect=lambda name, *args, **kwargs: (
                ImportError("No module named django")
                if name == "django"
                else __import__(name, *args, **kwargs)
            ),
        ):
            # Should not raise any exception
            _default_validator(MagicMock())
