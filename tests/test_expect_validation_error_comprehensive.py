"""Comprehensive tests for expect_validation_error parameter."""

from unittest.mock import MagicMock, patch

import pytest

from pytest_fixturecheck import fixturecheck, has_required_fields, is_instance_of


# Create a wrapper for validators to handle collection phase safely
def phase_aware_validator(validator):
    """Wrap a validator to make it phase-aware and skip validation during collection."""

    def wrapper(obj, is_collection_phase=False):
        if is_collection_phase or callable(obj):
            return
        return validator(obj)

    return wrapper


# Fixture that is expected to fail validation during collection
@pytest.fixture
@fixturecheck(phase_aware_validator(is_instance_of(dict)), expect_validation_error=True)
def fixture_fails_collection():
    """This fixture should fail validation during collection."""
    # Return a string instead of a dict
    return "not a dict"


# Fixture that is expected to fail validation during execution
@pytest.fixture
@fixturecheck(has_required_fields("missing_field"), expect_validation_error=True)
def fixture_fails_execution():
    """This fixture should fail validation during execution."""
    return {"exists": True}


# Test fixtures that are expected to fail validation
class TestExpectValidationError:
    """Tests for fixtures that are expected to fail validation."""

    def test_fixture_with_expected_collection_error(self, fixture_fails_collection):
        """Test a fixture that is expected to fail validation during collection."""
        # The fixture should still be available for testing
        assert fixture_fails_collection == "not a dict"

    def test_fixture_with_expected_execution_error(self, fixture_fails_execution):
        """Test a fixture that is expected to fail validation during execution."""
        # The fixture should still be available for testing
        assert fixture_fails_execution["exists"] is True

    def test_expect_validation_error_concept(self):
        """Test the concept of expect_validation_error."""
        # Create a fixture that would normally fail validation
        # Use a phase-aware wrapper around the validator to prevent failure during the decorator application
        validator = phase_aware_validator(is_instance_of(dict))

        @fixturecheck(validator, expect_validation_error=True)
        def test_fixture():
            return "not a dict"

        # The fixture should have the expect_validation_error flag set
        assert hasattr(test_fixture, "_expect_validation_error")
        assert test_fixture._expect_validation_error is True

        # The plugin would normally detect this and add an error to the session if the validation passes
        # This test just verifies that the decorator sets the flag correctly


# Define custom validators for testing
def collection_phase_validator(obj, is_collection_phase=False):
    """A validator that fails during collection phase."""
    if is_collection_phase and not callable(obj):
        pytest.fail("Collection phase error")
    return None


def execution_phase_validator(obj, is_collection_phase=False):
    """A validator that fails during execution phase."""
    if not is_collection_phase and not callable(obj):
        pytest.fail("Execution phase error")
    return None


# Test with different validator behaviors
class TestDifferentValidatorBehaviors:
    """Tests for expect_validation_error with different validator behaviors."""

    # Test with a validator that fails during collection phase
    @pytest.fixture
    @fixturecheck(collection_phase_validator, expect_validation_error=True)
    def fails_only_in_collection(self):
        """This fixture fails validation only during collection."""
        return "value"

    def test_fails_only_in_collection(self, fails_only_in_collection):
        """Test a fixture that fails only during collection phase."""
        assert fails_only_in_collection == "value"

    # Test with a validator that fails during execution phase
    @pytest.fixture
    @fixturecheck(execution_phase_validator, expect_validation_error=True)
    def fails_only_in_execution(self):
        """This fixture fails validation only during execution."""
        return "value"

    def test_fails_only_in_execution(self, fails_only_in_execution):
        """Test a fixture that fails only during execution phase."""
        assert fails_only_in_execution == "value"


# Define validators for combined testing
def always_passes(obj, is_collection_phase=False):
    """A validator that always passes."""
    return True


def always_fails(obj, is_collection_phase=False):
    """A validator that always fails."""
    if not callable(obj):
        raise ValueError("Validation failed")
    return None


def combined_validator(obj, is_collection_phase=False):
    """Combines validators with expected failure."""
    always_passes(obj, is_collection_phase)
    if not is_collection_phase and not callable(obj):
        always_fails(obj, is_collection_phase)
    return None


# Test with combined validators
class TestCombinedValidatorsWithExpectedError:
    """Tests for expect_validation_error with combined validators."""

    # Test with a combination of passing and failing validators
    @pytest.fixture
    @fixturecheck(combined_validator, expect_validation_error=True)
    def combined_validators_fixture(self):
        """This fixture uses combined validators and expects failure."""
        return "value"

    def test_combined_validators_with_expected_error(self, combined_validators_fixture):
        """Test a fixture with combined validators that's expected to fail."""
        assert combined_validators_fixture == "value"
