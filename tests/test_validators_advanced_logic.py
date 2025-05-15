import pytest

from pytest_fixturecheck.validators_advanced import (
    nested_property_validator,
    type_check_properties,
)


class Dummy:
    pass


def test_nested_property_validator_strict_and_non_strict():
    class Inner:
        def __init__(self):
            self.value = 42

    class Outer:
        def __init__(self):
            self.inner = Inner()
            self.name = "outer"

    obj = Outer()

    # Strict: correct value
    validator = nested_property_validator(inner__value=42, name="outer")
    validator(obj, is_collection_phase=False)

    # Strict: wrong value
    validator = nested_property_validator(inner__value=99)
    with pytest.raises(ValueError):
        validator(obj, is_collection_phase=False)

    # Non-strict: wrong value
    validator = nested_property_validator(inner__value=99, strict=False)
    validator(obj, is_collection_phase=False)  # Should only warn, not raise

    # Strict: missing property
    validator = nested_property_validator(inner__missing=1)
    with pytest.raises(AttributeError):
        validator(obj, is_collection_phase=False)

    # Non-strict: missing property
    validator = nested_property_validator(inner__missing=1, strict=False)
    validator(obj, is_collection_phase=False)  # Should only warn, not raise


def test_type_check_properties_union_and_missing():
    class User:
        def __init__(self, name, age, email=None):
            self.name = name
            self.age = age
            self.email = email

    user = User("alice", 30, None)

    # Union type: should pass
    import typing

    validator = type_check_properties(email__type=typing.Union[str, None])
    validator(user, is_collection_phase=False)

    # Wrong type
    validator = type_check_properties(age__type=str)
    with pytest.raises(TypeError):
        validator(user, is_collection_phase=False)

    # Non-strict: wrong type
    validator = type_check_properties(age__type=str, strict=False)
    validator(user, is_collection_phase=False)  # Should only warn, not raise

    # Missing property
    validator = type_check_properties(missing__type=int)
    with pytest.raises(AttributeError):
        validator(user, is_collection_phase=False)

    # Non-strict: missing property
    validator = type_check_properties(missing__type=int, strict=False)
    validator(user, is_collection_phase=False)  # Should only warn, not raise


def test_type_check_properties_value_and_type():
    class Obj:
        def __init__(self):
            self.x = 5

    obj = Obj()
    validator = type_check_properties(x=5, x__type=int)
    validator(obj, is_collection_phase=False)
    # Wrong value
    validator = type_check_properties(x=6, x__type=int)
    with pytest.raises(ValueError):
        validator(obj, is_collection_phase=False)
    # Wrong type
    validator = type_check_properties(x=5, x__type=str)
    with pytest.raises(TypeError):
        validator(obj, is_collection_phase=False)


def test_empty_and_collection_phase():
    validator = nested_property_validator()
    validator(object(), is_collection_phase=True)  # Should not raise
    validator = type_check_properties()
    validator(object(), is_collection_phase=True)  # Should not raise
