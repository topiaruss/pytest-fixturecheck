# Changelog

## 0.4.2 (2025-05-15)

### Bug Fixes
- Fixed ImportError when importing `FieldDoesNotExist_Export` or `ValidationError_Export` from `pytest_fixturecheck.django_validators` when Django is not installed
- Improved Django integration layer to ensure graceful imports even when Django is not available
- Enhanced documentation in TROUBLESHOOTING.md with guidance for Django validator import errors
- Updated test suite to ensure compatibility with and without Django installed

## 0.4.1 (2025-05-18)

### Bug Fixes and Improvements
- Enhanced error reporting in plugin.py to better identify when errors come from user code vs. the package
- Created comprehensive TROUBLESHOOTING.md guide with sections on:
  - Import errors and how to resolve them
  - Examples of correctly structured validators
  - Best practices for validator patterns 
- Added examples of:
  - Recommended validator pattern with local imports
  - Using expect_validation_error=True for testing validation failures
- Fixed code formatting issues
- Fixed f-string issues 

## 0.4.0 (2025-05-15)

### Bug Fixes and Improvements
- Fixed `creates_validator` decorator to properly handle different function signatures:
  - Correctly handles functions with a single parameter when called with no arguments
  - Better support for direct validator functions vs factory functions
  - Improved handling of phase-aware validation
- Enhanced Django validators for more robust validation:
  - Improved Django model detection for better test environments compatibility
  - Fixed validation error handling with better error messages
  - Made validators properly respect the `is_collection_phase` parameter
  - Added safety checks for accessing model attributes
- Added exports for `ValidationError` and `FieldDoesNotExist` to simplify testing
- Fixed compatibility issue in Django compatibility layer
- Improved error handling and test stability
- Deeper testing for yield fixture

## 0.3.4 (2024-05-14)

### New Features
- Added advanced validators for more complex validation scenarios:
  - `nested_property_validator` - validates nested object properties using dot notation
  - `type_check_properties` - validates both property values and their types
  - `simple_validator` - simplified API for creating custom validators
- Added factory functions for advanced validators:
  - `with_nested_properties` - validates nested properties with a simple decorator
  - `with_type_checks` - validates property types with a simple decorator
- Added comprehensive documentation in ADVANCED_VALIDATORS.md

### Bug Fixes
- Fixed issues with advanced validators when used directly in test code
- Added documentation about limitations when using validators outside of decorators
- Updated test suite to handle version compatibility issues
- Fixed test cases to avoid direct usage of validator functions

## 0.3.3 (2024-07-21)

### Bug Fixes
- Fixed the `strict` parameter in property validators to correctly control validation behavior
  - When `strict=True` (default): Raises exceptions for mismatched properties
  - When `strict=False`: Issues warnings for mismatched properties instead of raising exceptions
- Added comprehensive tests to verify the strict parameter behavior
- Updated documentation for property validators to include the strict parameter usage

## 0.3.2 (2024-07-14)

### Bug Fixes
- Fixed test suite issues with mock Django validation
- Fixed test cases for custom validators with collection phase handling
- Improved test coverage for utility functions
- Fixed formatting in utils.py to comply with Black style rules
- Updated flake8 configuration to ignore common warnings
- Fixed property validators test case to use direct validator functions

## 0.3.1 (2024-07-13)

### Bug Fixes
- Fixed plugin configuration by properly registering the fixturecheck-auto-skip option with addini
- Added pytest-asyncio as an optional dependency to support async fixtures testing
- Improved handling of fixtures with discovery issues
- Updated documentation with notes about fixture discovery limitations

## 0.3.0 (2024-07-12)

### New Features
- Added `creates_validator` decorator for easier creation of validation functions
- Added factory functions for common validation patterns through `validators` module:
  - `is_instance_of` - validates object is instance of specified type
  - `has_required_fields` - validates object has specified fields
  - `has_required_methods` - validates object has specified methods
  - `has_property_values` - validates object has specified property values
  - `combines_validators` - combines multiple validators into one
- Improved Django model validation with specialized helpers:
  - `is_django_model` - checks if object is a Django model
  - `django_model_has_fields` - validates a Django model has specific fields
  - `django_model_validates` - validates a Django model using Django's validation
- Added `expect_validation_error` parameter for testing validators that are expected to fail
- Added fixed property validators for more reliable property validation:
  - `property_values_validator` - validates using a dictionary of property names and values
  - `check_property_values` - validates using keyword arguments for property names and values
  - `with_property_values` - factory function for property validation with keyword arguments

### Improvements
- Enhanced AsyncIO support for coroutine fixtures
- Improved error reporting with clearer error messages
- Better phase-aware validation (collection vs execution time)
- More robust Django model detection
- Fixed issue with `has_property_values` not accepting keyword arguments
- Added comprehensive documentation for property validators in PROPERTY_VALIDATORS.md

### API Changes
- All built-in validators now handle `is_collection_phase` parameter
- Old factory functions (`with_required_fields`, etc.) have been preserved for backward compatibility
- Added new property validators while maintaining backward compatibility with existing code

## 0.2.1 (2023-06-06)

### Bug Fixes
- Fixed compatability issue with pytest-asyncio
- Fixed handling of fixtures with validation errors
- Moved configuration options (addini) to correct hook
- Made validators backward compatible with optional `is_collection_phase` parameter
- Improved ability to detect fixture functions wrapped in decorators

## 0.2.0 (2023-05-31)

### New Features
- Added Django model field validation
- Support for combining multiple validators
- Improved error messages

## 0.1.0 (2023-05-15)

### Initial Release
- Basic fixture validation
- Auto-fixing of common issues
- Simple validator functions
