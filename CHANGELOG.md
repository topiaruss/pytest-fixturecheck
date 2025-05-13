# Changelog

## 0.3.0 (Development Version)

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

### Improvements
- Enhanced AsyncIO support for coroutine fixtures
- Improved error reporting with clearer error messages
- Better phase-aware validation (collection vs execution time)
- More robust Django model detection

### API Changes
- All built-in validators now handle `is_collection_phase` parameter
- Old factory functions (`with_required_fields`, etc.) have been preserved for backward compatibility

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