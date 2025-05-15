"""Minimal test file with a property validator."""

import pytest

from pytest_fixturecheck import fixturecheck


class MinTestObject:
    """Test object with properties."""

    def __init__(self, name="test", value=42):
        self.name = name
        self.value = value


def test_direct_object():
    """Test a direct object without validation."""
    obj = MinTestObject(name="direct")
    assert obj.name == "direct"
    assert obj.value == 42


# Basic validator function
def validate_name_is_test(obj, is_collection_phase=False):
    """Validate that obj.name is 'test'."""
    if is_collection_phase:
        return
    if not hasattr(obj, "name"):
        raise AttributeError("Object has no name attribute")
    if obj.name != "test":
        raise ValueError(f"Expected name='test', got {obj.name}")


@pytest.fixture
def simple_object():
    """A simple fixture without validation."""
    return MinTestObject()


@pytest.fixture
@fixturecheck(validate_name_is_test)
def validated_object():
    """A fixture with validation."""
    return MinTestObject()


def test_simple_object(simple_object):
    """Test using the simple fixture."""
    assert simple_object.name == "test"
    assert simple_object.value == 42


def test_validated_object(validated_object):
    """Test using the validated fixture."""
    assert validated_object.name == "test"
    assert validated_object.value == 42
