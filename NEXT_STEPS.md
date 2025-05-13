# Next Steps for pytest-fixturecheck v0.3.0

This file outlines the next steps for the pytest-fixturecheck project after implementing the major features for version 0.3.0.

## Implemented Features

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

## Before Release

Before releasing version 0.3.0, the following should be completed:

1. **Additional Tests**
   - Add more tests for edge cases, especially with Django validators
   - Test interactions with other pytest plugins

2. **Documentation**
   - Complete documentation for all new features
   - Add example code for common use cases
   - Update the README with clear examples

3. **Fix Known Issues**
   - There seem to be some issues with test collection when using custom validators
   - Fixture discovery might need improvement

## Future Enhancements for v0.4.0

1. **Enhanced Fixture Discovery**
   - Automatic discovery of fixtures without requiring the decorator
   - Optional auto-validation of all fixtures

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
6. Tag the release in git: `git tag v0.3.0 && git push --tags` 