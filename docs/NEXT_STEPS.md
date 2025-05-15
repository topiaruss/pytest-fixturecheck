# Next Steps for pytest-fixturecheck v0.4.0

This file outlines the next steps for the pytest-fixturecheck project after releasing version 0.3.2.

## Progress in v0.3.2

1. **Test Suite Improvements**
   - Fixed mock Django validation in test_django_validators_comprehensive.py
   - Improved test coverage for utility functions in test_utils_comprehensive.py
   - Created workarounds for property validators tests with direct validator functions

2. **Configuration and Code Quality**
   - Enhanced flake8 configuration with more comprehensive ignore rules
   - Fixed formatting issues in utils.py and other files
   - Improved CI pipeline stability

## Completed in Version 0.3.0

1. **Enhanced Validator Framework**
   - Added `creates_validator` decorator for easy validator creation
   - Added factory functions for common validation patterns
   - Implemented a rich set of built-in validators

2. **Improved Django Integration**
   - Enhanced Django model detection with the `is_django_model` function
   - Added specialized Django validators:
     - `django_model_has_fields`
     - `django_model_validates`

3. **Testing Validators**
   - Added `expect_validation_error` parameter for testing validators
   - This allows for creating fixtures that are expected to fail validation

4. **Better AsyncIO Support**
   - Improved detection and handling of async fixtures
   - Better compatibility with pytest-asyncio

5. **Improved API**
   - Simplified API for common validation tasks
   - Maintained backward compatibility with existing validators

6. **Fixed Property Value Validators**
   - Fixed issues with `has_property_values` not accepting keyword arguments
   - Added three new validators for property validation:
     - `property_values_validator` - Takes a dictionary of property names and values
     - `check_property_values` - Takes keyword arguments for property names and values
     - `with_property_values` - A factory function to replace `fixturecheck.with_property_values`
   - Comprehensive test coverage for property validators (72%)

## Future Enhancements for v0.4.0

1. **Enhanced Fixture Discovery**
   - Automatic discovery of fixtures without requiring the decorator
   - Optional auto-validation of all fixtures
   - Investigate and fix the fixture discovery issue in tests/test_property_values_fix.py where fixtures
     decorated with @fixturecheck are not being properly discovered by pytest

2. **Type Checking**
   - Add validators for type annotations
   - Integration with mypy or other type checkers

3. **More Validation Patterns**
   - Add validators for common patterns like JSONSchema validation
   - Add more ORM-specific validators (SQLAlchemy, etc.)

4. **Performance Improvements**
   - Optimize fixture validation during collection phase
   - Add caching for previously validated fixtures

5. **Configuration Options**
   - More granular configuration options
   - Project-wide validation rules

6. **Property Validators Enhancements**
   - Add support for nested property validation
   - Support for complex property validation logic (e.g., range validation, custom patterns)
   - Add validators for property types

7. **Fix Python 3.12 AsyncIO Compatibility**
   - Investigate and fix issues with pytest-asyncio tests on Python 3.12
   - Currently, asyncio tests are skipped in CI for Python 3.12 due to import errors
   - This may require updates to how pytest-asyncio is integrated or conditional test skipping
   - Initial workarounds implemented in v0.3.1-0.3.2, but a more comprehensive solution is needed

## Contribution Opportunities

Below are specific areas where contributions would be valuable:

1. **Improve Coverage for django.py (currently at 12%)**
   - Add tests for Django model validation functions
   - Create proper test fixtures with Django model mocks

2. **Increase Coverage for plugin.py (currently at 35%)**
   - Test pytest plugin hooks
   - Cover the fixture collection and execution phases

3. **Add Tests for Edge Cases in decorator.py**
   - Test validation with more complex nested fixtures
   - Test error handling and reporting

4. **Improve AsyncIO Support Testing**
   - Add more comprehensive tests for async fixtures
   - Test concurrent validation scenarios

5. **Add Integration Tests**
   - Test the plugin with real-world fixture scenarios
   - Test performance with many fixtures

6. **Enhance Documentation**
   - Add more examples in docstrings
   - Create usage examples for common scenarios
   - Document best practices for using the property validators

## Development Workflow

The recommended workflow for contributing to the project:

1. Fork the repository
2. Create a branch for your feature or bugfix
3. Add tests for your changes
4. Make your changes and ensure all tests pass
5. Update documentation
6. Submit a pull request

## Release Process

To release a new version:

1. Update version number in:
   - `src/pytest_fixturecheck/__init__.py`
   - `pyproject.toml`
2. Update `CHANGELOG.md`
3. Build the package: `python -m build`
4. Test the built package in a fresh environment
5. Upload to PyPI: `twine upload dist/*`
6. Tag the release in git: `git tag v0.4.0 && git push --tags`
