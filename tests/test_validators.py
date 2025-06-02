"""Tests for the fixturecheck validator functionality."""

import pytest
from pytest_fixturecheck import fixturecheck, creates_validator


@creates_validator
def validate_string(obj):
    """Validate that the object is a string."""
    if not isinstance(obj, str):
        raise TypeError(f"Expected string, got {type(obj)}")


@creates_validator
def validate_length(obj, min_length: int):
    """Validate that the string has a minimum length."""
    if not isinstance(obj, str):
        raise TypeError(f"Expected string, got {type(obj)}")
    if len(obj) < min_length:
        raise ValueError(f"String length {len(obj)} is less than minimum {min_length}")


@creates_validator
def validate_number_range(obj, min_val: int, max_val: int):
    """Validate that the number is within a range."""
    if not isinstance(obj, (int, float)):
        raise TypeError(f"Expected number, got {type(obj)}")
    if obj < min_val or obj > max_val:
        raise ValueError(f"Number {obj} is outside range [{min_val}, {max_val}]")


def test_basic_validator():
    """Test basic validator functionality."""
    @fixturecheck(validate_string())
    @pytest.fixture
    def string_fixture():
        return "test"
    
    # Should pass
    assert string_fixture() == "test"
    
    @fixturecheck(validate_string())
    @pytest.fixture
    def invalid_fixture():
        return 123
    
    # Should fail
    with pytest.raises(TypeError):
        invalid_fixture()


def test_validator_with_args():
    """Test validator with arguments."""
    @fixturecheck(validate_length(min_length=5))
    @pytest.fixture
    def long_string_fixture():
        return "long string"
    
    # Should pass
    assert long_string_fixture() == "long string"
    
    @fixturecheck(validate_length(min_length=5))
    @pytest.fixture
    def short_string_fixture():
        return "hi"
    
    # Should fail
    with pytest.raises(ValueError):
        short_string_fixture()


def test_validator_with_multiple_args():
    """Test validator with multiple arguments."""
    @fixturecheck(validate_number_range(min_val=1, max_val=10))
    @pytest.fixture
    def number_fixture():
        return 5
    
    # Should pass
    assert number_fixture() == 5
    
    @fixturecheck(validate_number_range(min_val=1, max_val=10))
    @pytest.fixture
    def out_of_range_fixture():
        return 20
    
    # Should fail
    with pytest.raises(ValueError):
        out_of_range_fixture()


def test_validator_chain():
    """Test chaining multiple validators."""
    @fixturecheck(validate_string())
    @fixturecheck(validate_length(min_length=5))
    @pytest.fixture
    def chained_fixture():
        return "long string"
    
    # Should pass
    assert chained_fixture() == "long string"
    
    @fixturecheck(validate_string())
    @fixturecheck(validate_length(min_length=5))
    @pytest.fixture
    def invalid_chained_fixture():
        return "hi"
    
    # Should fail
    with pytest.raises(ValueError):
        invalid_chained_fixture()


def test_async_fixture_validation():
    """Test validation of async fixtures."""
    @fixturecheck(validate_string())
    @pytest.fixture
    async def async_string_fixture():
        return "test"
    
    # Should pass
    assert async_string_fixture() == "test"
    
    @fixturecheck(validate_string())
    @pytest.fixture
    async def invalid_async_fixture():
        return 123
    
    # Should fail
    with pytest.raises(TypeError):
        invalid_async_fixture()


def test_collection_phase_validation():
    """Test validation during collection phase."""
    @fixturecheck(validate_string())
    @pytest.fixture
    def collection_phase_fixture():
        return "test"
    
    # During collection phase, validation should be skipped
    assert collection_phase_fixture() == "test" 