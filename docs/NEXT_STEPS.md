# Next Steps for pytest-fixturecheck v0.4.1+

This file outlines the next steps for the pytest-fixturecheck project after releasing version 0.4.1.

## Progress in v0.4.1

1. **Improved Error Reporting**
   - Enhanced error detection in plugin.py to better identify when errors come from user code vs. the package
   - Added more helpful error messages for import errors 
   - Improved traceback formatting for better readability

2. **Documentation Enhancements**
   - Created comprehensive TROUBLESHOOTING.md guide with:
     - Sections on import errors and how to resolve them
     - Examples of correctly structured validators
     - Best practices for validator patterns
     - Recommended validator pattern with local imports
     - Django validator troubleshooting
     - General troubleshooting steps
   - Added examples of using `expect_validation_error=True` for testing validation failures
   - Updated README.md to reference the troubleshooting guide

3. **Code Quality Improvements**
   - Fixed f-string issues where f-strings were used without variable substitutions
   - Applied Black formatting to plugin.py
   - Ensured code passes tox -e lint and tox -e py313 tests

## Completed in Version 0.4.0

1. **Bug Fixes and Improvements**
   - Fixed `creates_validator` decorator to properly handle different function signatures
   - Enhanced Django validators for more robust validation
   - Added exports for `ValidationError` and `FieldDoesNotExist` to simplify testing
   - Fixed compatibility issue in Django compatibility layer
   - Improved error handling and test stability
   - Added deeper testing for yield fixtures

## Completed in Previous Versions (0.3.x)

1. **Enhanced Validator Framework**
   - Added `creates_validator` decorator for easy validator creation
   - Added factory functions for common validation patterns
   - Implemented a rich set of built-in validators

2. **Advanced Validators**
   - Added `nested_property_validator` for validating nested object properties
   - Added `type_check_properties` for validating both property values and their types
   - Added `simple_validator` for a simplified API to create custom validators
   - Added factory functions for advanced validators:
     - `with_nested_properties` for validating nested properties
     - `with_type_checks` for validating property types

3. **Improved Django Integration**
   - Enhanced Django model detection with the `is_django_model` function
   - Added specialized Django validators:
     - `django_model_has_fields`
     - `django_model_validates`

4. **Testing Validators**
   - Added `expect_validation_error` parameter for testing validators
   - This allows for creating fixtures that are expected to fail validation

5. **Better AsyncIO Support**
   - Improved detection and handling of async fixtures
   - Better compatibility with pytest-asyncio

6. **Fixed Property Value Validators**
   - Added three new validators for property validation:
     - `property_values_validator` - Takes a dictionary of property names and values
     - `check_property_values` - Takes keyword arguments for property names and values
     - `with_property_values` - A factory function for property validation

## Future Enhancements for v0.4.2 and Beyond

1. **Enhanced Fixture Discovery**
   - Automatic discovery of fixtures without requiring the decorator
   - Optional auto-validation of all fixtures
   - Investigate and fix fixture discovery issues where fixtures decorated with @fixturecheck are not properly discovered

2. **More Validation Patterns**
   - Add validators for common patterns like JSONSchema validation
   - Add more ORM-specific validators beyond Django (SQLAlchemy, etc.)
   - Support for data class validation

3. **Performance Improvements**
   - Optimize fixture validation during collection phase
   - Add caching for previously validated fixtures
   - Profile and optimize validation functions

4. **Configuration Options**
   - More granular configuration options
   - Project-wide validation rules
   - Support for validation groups

5. **Advanced Error Handling**
   - Provide more context in error messages
   - Add option to generate fix suggestions for common errors
   - Improve how dependent tests are marked for skipping

6. **Deeper AsyncIO Integration**
   - Better support for complex async fixture scenarios
   - Improved validation for coroutine objects
   - Address any remaining compatibility issues with pytest-asyncio

7. **Add Integration Tests**
   - Test the plugin with real-world fixture scenarios
   - Test performance with many fixtures
   - Create complex fixture dependency trees for testing

## Contribution Opportunities

Below are specific areas where contributions would be valuable:

1. **Improve Coverage for django.py (needs better coverage)**
   - Add tests for Django model validation functions
   - Create proper test fixtures with Django model mocks

2. **Increase Coverage for plugin.py**
   - Test pytest plugin hooks
   - Cover the fixture collection and execution phases

3. **Add Tests for Edge Cases**
   - Test validation with more complex nested fixtures
   - Test error handling and reporting
   - Test with large fixture dependency chains

4. **Improve AsyncIO Support Testing**
   - Add more comprehensive tests for async fixtures
   - Test concurrent validation scenarios

5. **Enhance Documentation**
   - Add more examples in docstrings
   - Create usage examples for common scenarios
   - Create video tutorials or interactive examples

6. **Create Integration Examples**
   - Show integration with popular testing frameworks
   - Demonstrate usage in real-world projects

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
   - `pyproject.toml`
2. Update `CHANGELOG.md`
3. Build the package: `python -m build`
4. Test the built package in a fresh environment
5. Upload to PyPI: `twine upload dist/*`
6. Tag the release in git: `git tag v0.4.2 && git push --tags`
