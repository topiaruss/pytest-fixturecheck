# Changelog

## 0.6.0 (2025-06-02)

### New Features
- **Added Command-Line Interface (CLI) for fixture analysis and management:**
  - `fixturecheck report` - Analyze test suites to find fixture check opportunities and count existing ones
  - `fixturecheck add` - Automatically add `@fixturecheck()` decorators to fixtures that don't have them
  - `--dry-run` option for `add` command to preview changes without modifying files
  - `--path` option to specify target directory (default: current directory)
  - `--pattern` option to specify file pattern (default: test_*.py)
- **Added verbose reporting options for detailed fixture analysis:**
  - `-v` flag shows detailed fixture information including line numbers, names, and parameters
  - `-vv` flag shows full details including validator information
  - Proper separator blocks between fixture entries for improved readability
- **Enhanced FixtureCheckPlugin with detailed analysis methods:**
  - `get_opportunities_details()` - Extract detailed information about fixtures without checks
  - `get_existing_checks_details()` - Extract detailed information about existing fixture checks
  - `_extract_validator_info()` - Parse validator information from AST decorators
- **Smart path exclusion to prevent analyzing irrelevant directories:**
  - Automatically excludes virtual environments (`.venv`, `venv`, `.env`, `env`, etc.)
  - Excludes package directories (`site-packages`, `dist-packages`, `node_modules`, etc.)
  - Excludes build/cache directories (`.pytest_cache`, `.mypy_cache`, `build`, `dist`, etc.)
  - Prevents CLI from processing hundreds of irrelevant test files in dependencies
- **Comprehensive CLI test suite with 10+ test cases covering all verbose scenarios**
- **Full backward compatibility maintained with existing fixture validation functionality**

### Bug Fixes
- **Fixed Django compatibility issues when Django is not installed:**
  - Resolved ImportError when Django validators are used at import time without Django available
  - Added conditional fixture definitions to prevent import-time failures
  - Ensured graceful fallback behavior when Django is unavailable
- **Improved conftest.py handling:**
  - Clarified in documentation that conftest.py files are always included regardless of pattern
  - Fixed documentation that incorrectly suggested conftest.py was only included when specifically targeted

### Documentation
- **Added comprehensive CLI documentation and examples:**
  - Complete CLI guide with installation, usage, and examples
  - Detailed explanation of verbose options with sample outputs
  - Best practices, workflow examples, and CI/CD integration guidance
  - Added automatic exclusions section explaining which directories are skipped
- **Updated README.md with CLI documentation and examples**
- **Enhanced feature list to highlight CLI capabilities**

## 0.5.0 (2024-05-17)

### Bug Fixes and Improvements
- Fixed flake8 redefinition errors in django_validators.py
- Restructured function definitions to properly handle stub functionality when Django is not available
- Fixed test compatibility in the nodjango environment
- Improved type annotations in __init__.py to avoid mypy redefinition errors
- Enhanced robustness of Django import handling with better fallback mechanisms
- Reformatted code to comply with Black style requirements

## 0.4.3 (2025-05-15)

### Bug Fixes and Improvements
- Fixed formatting issues in django_validators.py to comply with Black style rules
- Added automation for PyPI badge updates during releases
- Enhanced release process with automatic version bumping
- Improved handling of Django import errors

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
