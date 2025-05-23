# Troubleshooting Guide

This guide helps solve common issues with pytest-fixturecheck.

## Common Custom Validator Errors

### Import Errors in Custom Validators

If you're seeing an import error while using a custom validator, it's usually because:

1. **Missing package dependencies**: Your validator imports a package that isn't installed in your environment.
   ```python
   # Example error
   ImportError: No module named 'some_missing_package'
   ```
   
   **Solution**: Install the missing package: `pip install some_missing_package`

2. **Relative import issues**: Your custom validator uses relative imports incorrectly.
   ```python
   # Problematic code
   from .myutils import helper_function
   ```
   
   **Solution**: Make sure your module structure supports relative imports, or use absolute imports.

3. **Circular imports**: Your validator function is part of a circular import chain.
   
   **Solution**: Restructure your imports or move the validator to break the circular dependency.

### Example of a Working Custom Validator

Here's a correctly structured custom validator that avoids common issues:

```python
# In your_project/validators.py

def validate_user_data(obj, is_collection_phase=False):
    """
    Validates that a user object has required fields with valid values.
    
    Args:
        obj: The object to validate
        is_collection_phase: Whether this validation is happening during collection phase
    """
    # Skip validation during collection phase or if obj is a function
    import inspect  # Import locally to avoid potential import issues
    if is_collection_phase or inspect.isfunction(obj):
        return
        
    # Perform actual validation
    if not hasattr(obj, "username"):
        raise AttributeError("User must have a username")
    if obj.username is None:
        raise ValueError("Username cannot be None")
    if not hasattr(obj, "email") or not obj.email:
        raise ValueError("User must have an email")
```

### Best Practices for Custom Validators

1. **Keep imports inside functions** when possible to avoid module-level import issues
2. **Handle collection phase correctly** - always check the `is_collection_phase` parameter
3. **Check if the object is callable** before accessing attributes
4. **Use clear, specific error messages** to make debugging easier
5. **Test your validators independently** before using them with `@fixturecheck`

### Recommended Validator Pattern

Use this pattern for your custom validators to avoid common issues:

```python
def my_validator(obj, is_collection_phase=False):
    # Skip validation during collection or if obj is a function
    import inspect  # Import locally
    if is_collection_phase or inspect.isfunction(obj):
        return
    
    # Rest of validation logic
```

## Django Validator Issues

When using the Django-specific validators, you might encounter:

1. **Django not installed**: 
   ```
   ImportError: Django is not installed
   ```
   
   **Solution**: Install Django: `pip install Django`

2. **Missing model fields**:
   ```
   Field 'xyz' does not exist on model
   ```
   
   **Solution**: Check that you're validating against the correct model and field names

### Django Validator Import Errors

Starting in version 0.4.2, we improved how Django validators are imported. You might have seen this error in earlier versions:

```
ImportError: cannot import name 'FieldDoesNotExist_Export' from 'pytest_fixturecheck.django_validators'
```

This happens when your code imports from the Django validators module but Django is not installed. Django is an optional dependency, so the package should still work without it.

**Solutions:**

1. **Install Django** if you need the Django validators: `pip install Django` or `pip install pytest-fixturecheck[django]`

2. **Update to pytest-fixturecheck 0.4.2 or higher** which handles imports properly without Django installed

3. **Conditionally import** Django validators in your code:
   ```python
   try:
       from pytest_fixturecheck.django_validators import django_model_has_fields
   except ImportError:
       # Handle the case where Django validators are not available
       pass
   ```

## General Troubleshooting Steps

1. **Check your fixture definition** - make sure it's correctly decorated with `@pytest.fixture`
2. **Verify validator syntax** - ensure your validator follows the correct signature
3. **Run with `--verbose`** for more detailed error information
4. **Use the `expect_validation_error=True`** parameter if you're expecting validation to fail

   **Example:**
   ```python
   import pytest
   from pytest_fixturecheck import fixturecheck, has_required_fields
  
   # This fixture is expected to fail validation but the test will still run
   @pytest.fixture
   @fixturecheck(has_required_fields("nonexistent_field"), expect_validation_error=True)
   def fixture_missing_field():
       # This fixture intentionally violates the validator requirements
       return {"name": "test"}  # Missing the 'nonexistent_field'
   
   # Tests using this fixture will run normally, despite the validation error
   def test_with_missing_field(fixture_missing_field):
       assert fixture_missing_field["name"] == "test"
   ```

If you're still having issues, please open an issue on our [GitHub repository](https://github.com/topiaruss/pytest-fixturecheck/issues) with:
1. Your Python and pytest versions
2. The full traceback of the error
3. A minimal example that reproduces the issue 