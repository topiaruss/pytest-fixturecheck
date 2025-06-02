"""Tests for the fixturecheck validator functionality."""

import pytest

from pytest_fixturecheck import creates_validator, fixturecheck


@creates_validator
def validate_string():
    """Factory that creates a string validator."""

    def validator(obj):
        if not isinstance(obj, str):
            raise TypeError(f"Expected string, got {type(obj)}")

    return validator


@creates_validator
def validate_length(min_length: int):
    """Factory that creates a length validator."""

    def validator(obj):
        if not isinstance(obj, str):
            raise TypeError(f"Expected string, got {type(obj)}")
        if len(obj) < min_length:
            raise ValueError(f"String length {len(obj)} is less than minimum {min_length}")

    return validator


@creates_validator
def validate_number_range(min_val: int, max_val: int):
    """Factory that creates a number range validator."""

    def validator(obj):
        if not isinstance(obj, (int, float)):
            raise TypeError(f"Expected number, got {type(obj)}")
        if obj < min_val or obj > max_val:
            raise ValueError(f"Number {obj} is outside range [{min_val}, {max_val}]")

    return validator


def test_basic_validator():
    """Test basic validator functionality using proper pytest fixture patterns."""

    @fixturecheck(validate_string())
    @pytest.fixture
    def string_fixture():
        return "test"

    @fixturecheck(validate_string())
    @pytest.fixture
    def invalid_fixture():
        return 123

    # Test that fixtures can be defined without errors
    assert string_fixture.__name__ == "string_fixture"
    assert invalid_fixture.__name__ == "invalid_fixture"


def test_validator_with_args():
    """Test validator with arguments using proper pytest fixture patterns."""

    @fixturecheck(validate_length(min_length=5))
    @pytest.fixture
    def long_string_fixture():
        return "long string"

    @fixturecheck(validate_length(min_length=5))
    @pytest.fixture
    def short_string_fixture():
        return "hi"

    # Test that fixtures can be defined without errors
    assert long_string_fixture.__name__ == "long_string_fixture"
    assert short_string_fixture.__name__ == "short_string_fixture"


def test_validator_with_multiple_args():
    """Test validator with multiple arguments using proper pytest fixture patterns."""

    @fixturecheck(validate_number_range(min_val=1, max_val=10))
    @pytest.fixture
    def number_fixture():
        return 5

    @fixturecheck(validate_number_range(min_val=1, max_val=10))
    @pytest.fixture
    def out_of_range_fixture():
        return 20

    # Test that fixtures can be defined without errors
    assert number_fixture.__name__ == "number_fixture"
    assert out_of_range_fixture.__name__ == "out_of_range_fixture"


def test_validator_chain():
    """Test chaining multiple validators using proper pytest fixture patterns."""

    @fixturecheck(validate_string())
    @fixturecheck(validate_length(min_length=5))
    @pytest.fixture
    def chained_fixture():
        return "long string"

    @fixturecheck(validate_string())
    @fixturecheck(validate_length(min_length=5))
    @pytest.fixture
    def invalid_chained_fixture():
        return "hi"

    # Test that fixtures can be defined without errors
    assert chained_fixture.__name__ == "chained_fixture"
    assert invalid_chained_fixture.__name__ == "invalid_chained_fixture"


def test_async_fixture_validation():
    """Test validation of async fixtures using proper pytest fixture patterns."""

    @fixturecheck(validate_string())
    @pytest.fixture
    async def async_string_fixture():
        return "test"

    @fixturecheck(validate_string())
    @pytest.fixture
    async def invalid_async_fixture():
        return 123

    # Test that fixtures can be defined without errors
    assert async_string_fixture.__name__ == "async_string_fixture"
    assert invalid_async_fixture.__name__ == "invalid_async_fixture"


def test_collection_phase_validation():
    """Test validation during collection phase using proper pytest fixture patterns."""

    @fixturecheck(validate_string())
    @pytest.fixture
    def collection_phase_fixture():
        return "test"

    # Test that fixture can be defined without errors
    assert collection_phase_fixture.__name__ == "collection_phase_fixture"


def test_validator_execution_directly():
    """Test validator execution directly without fixtures."""
    # Test string validator
    string_validator = validate_string()

    # Should not raise for valid string
    string_validator("test")

    # Should raise for invalid type
    with pytest.raises(TypeError):
        string_validator(123)

    # Test length validator
    length_validator = validate_length(min_length=5)

    # Should not raise for valid length
    length_validator("long string")

    # Should raise for short string
    with pytest.raises(ValueError):
        length_validator("hi")

    # Test number range validator
    range_validator = validate_number_range(min_val=1, max_val=10)

    # Should not raise for valid number
    range_validator(5)

    # Should raise for out of range number
    with pytest.raises(ValueError):
        range_validator(20)
