"""Test file that demonstrates the phase-aware validation in pytest-fixturecheck."""

import pytest
from typing import Any, Callable

from pytest_fixturecheck import fixturecheck


def phase_aware_validator(obj: Any, is_collection_phase: bool) -> None:
    """A validator that behaves differently based on the phase.
    
    During collection phase, it checks that the function has a docstring.
    During execution phase, it validates the return value.
    """
    if is_collection_phase:
        # This runs during collection - validates the fixture function itself
        if callable(obj):
            if not obj.__doc__:
                raise ValueError("All fixtures must have docstrings")
    else:
        # This runs during execution - validates the fixture return value
        if isinstance(obj, str) and len(obj) < 3:
            raise ValueError("String value must be at least 3 characters long")


@fixturecheck(phase_aware_validator)
@pytest.fixture
def good_fixture():
    """This fixture has a docstring and returns a valid value."""
    return "hello world"


@fixturecheck(phase_aware_validator)
@pytest.fixture
def missing_docstring_fixture():
    # This fixture is missing a docstring, will fail during collection phase
    return "hello world"


@fixturecheck(phase_aware_validator)
@pytest.fixture
def invalid_value_fixture():
    """This fixture has a docstring but returns an invalid value."""
    return "hi"  # Too short, will fail during execution phase


def test_good_fixture(good_fixture):
    """This test uses a valid fixture that passes both collection and execution validation."""
    assert good_fixture == "hello world"


@pytest.mark.xfail(
    reason="This test uses a fixture that fails collection-phase validation"
)
def test_missing_docstring(missing_docstring_fixture):
    """This test uses a fixture that fails during collection phase."""
    assert missing_docstring_fixture == "hello world"


@pytest.mark.xfail(
    reason="This test uses a fixture that fails execution-phase validation"
)
def test_invalid_value(invalid_value_fixture):
    """This test uses a fixture that fails during execution phase."""
    assert len(invalid_value_fixture) > 0 