from pytest_fixturecheck.validators_advanced import nested_property_validator

# from pytest_fixturecheck.validators import is_instance_of # Not used in this version of test


class NestedConfig:
    def __init__(self, name_value):
        self.name = name_value


class TopLevelObject:
    def __init__(self, user_name_value):
        self.user = NestedConfig(user_name_value)


# Test nested property validation for a specific value
validator_john = nested_property_validator(user__name="John")
validator_jane = nested_property_validator(user__name="Jane")

# Test cases
obj_john = TopLevelObject("John")
obj_jane = TopLevelObject("Jane")
obj_int_name = TopLevelObject(
    123
)  # For testing a different type that leads to value mismatch

# Successful validation (validator returns None on success)
validator_john(obj_john)

# Failed validations (validator raises ValueError for mismatched values)
error_raised_for_wrong_value = False
try:
    validator_john(obj_jane)
except ValueError:
    error_raised_for_wrong_value = True
assert error_raised_for_wrong_value, "ValueError not raised for wrong value (obj_jane)"

error_raised_for_mismatched_type_value = False
try:
    validator_john(obj_int_name)  # 123 != "John"
except ValueError:
    error_raised_for_mismatched_type_value = True
assert (
    error_raised_for_mismatched_type_value
), "ValueError not raised for mismatched type value (obj_int_name)"

# Test for a different expected value
validator_jane(obj_jane)  # Should pass

error_raised_for_wrong_value_against_jane = False
try:
    validator_jane(obj_john)  # "John" != "Jane"
except ValueError:
    error_raised_for_wrong_value_against_jane = True
assert (
    error_raised_for_wrong_value_against_jane
), "ValueError not raised for wrong value (obj_john vs validator_jane)"

print("test_public_api.py completed successfully.")
