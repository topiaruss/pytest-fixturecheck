"""Test file that uses fixtures from conftest.py."""

import pytest


def test_valid_user(valid_user):
    """Test that a valid user passes validation."""
    assert valid_user.username == "testuser"


def test_invalid_user(invalid_user):
    """Test that an invalid user still works with expect_validation_error=True."""
    assert invalid_user.username is None


def test_missing_email_user(missing_email_user):
    """Test that a fixture missing an expected field doesn't fail the test when we expect it to fail."""
    assert missing_email_user.username == "testuser"
    assert not hasattr(missing_email_user, "email")
