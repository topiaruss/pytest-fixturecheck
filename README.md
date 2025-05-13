# pytest-fixturecheck

```
  _____        _            _    _____ _      _                    _____  _               _    
 |  __ \      | |          | |  |  __ (_)    | |                  / ____|| |             | |   
 | |__) |_   _| |_ ___  ___| |_ | |__) _ ____| |_ _   _ _ __ ___ | |     | |__   ___  ___| | __
 |  ___/| | | | __/ _ \/ __| __||  ___/ |_  /| __| | | | '__/ _ \| |     | '_ \ / _ \/ __| |/ /
 | |    | |_| | ||  __/\__ \ |_ | |   | |/ / | |_| |_| | | |  __/| |____ | | | |  __/ (__|   < 
 |_|     \__, |\__\___||___/\__||_|   |_/___(_)__|\__,_|_|  \___| \_____||_| |_|\___|\___|_|\_\
          __/ |                                                                                 
         |___/                                                                                  
```

[![PyPI version](https://badge.fury.io/py/pytest-fixturecheck.svg)](https://badge.fury.io/py/pytest-fixturecheck)
[![Python Versions](https://img.shields.io/pypi/pyversions/pytest-fixturecheck.svg)](https://pypi.org/project/pytest-fixturecheck/)
[![CI](https://github.com/yourusername/pytest-fixturecheck/actions/workflows/ci.yml/badge.svg)](https://github.com/yourusername/pytest-fixturecheck/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/yourusername/pytest-fixturecheck/branch/main/graph/badge.svg)](https://codecov.io/gh/yourusername/pytest-fixturecheck)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A pytest plugin to validate fixtures before they're used in tests. Catch broken fixtures early before they cause confusing test failures.

## The Problem

In complex test suites, particularly when using Django or other ORMs, fixtures can silently break due to model changes. For example:

- A database model field gets renamed, but fixtures that create test data aren't updated
- A fixture depends on another fixture that changes its return structure
- Schema migrations occur but fixture setup code isn't updated

This causes confusing test failures because the error appears in the test using the fixture, not in the fixture itself. It can be hard to diagnose that a broken fixture is the culprit, not the actual test logic.

## Why pytest-fixturecheck?

- **Early Detection**: Identifies fixture issues before tests run
- **Clear Error Messages**: Points directly to the broken fixture, not symptoms
- **Django Integration**: Special validation for Django model fields
- **Simple API**: Just add a decorator to fixtures you want validated
- **Zero Overhead**: Only runs during collection, doesn't slow down normal testing

## Installation

```bash
pip install pytest-fixturecheck
```

## Usage

### Basic Usage

Add the `@fixturecheck` decorator to any fixture you want to validate:

```python
from pytest_fixturecheck import fixturecheck

@fixturecheck
@pytest.fixture
def author():
    return Author.objects.create(name="Marian Brook")
```

This will execute the fixture once during collection time to verify it can run without errors.

### Django Models Example

With Django models, you can use the Django-specific handler to validate model field access:

```python
from pytest_fixturecheck import fixturecheck
from pytest_fixturecheck.django import validate_model_fields

@fixturecheck(validate_model_fields)
@pytest.fixture
def book(author, publisher):
    return Book.objects.create(
        title="Echoes of the Riverbank",
        author=author,
        publisher=publisher,
    )
```

## How It Works

The plugin works by:

1. Discovering fixtures marked with `@fixturecheck`
2. During test collection, executing those fixtures in isolation to verify they work
3. Catching and reporting errors before any tests run
4. Displaying clear error messages pointing directly to fixture issues

## Error Output Example

When a fixture is broken, you'll get a clear error message before any tests run:

```
================================================================================
FIXTURE VALIDATION ERRORS
================================================================================

Fixture 'book' in tests/conftest.py:42 failed validation:
  AttributeError: Field 'title' does not exist on model Book. Did the field name change?
  
================================================================================
Fix these fixture issues before running your tests.
================================================================================
```

## Visual Demo

![pytest-fixturecheck in action](https://github.com/yourusername/pytest-fixturecheck/raw/main/docs/images/fixturecheck-demo.gif)

*The GIF above shows how pytest-fixturecheck catches a broken fixture during test collection, before any tests run.*

## Compatible With

- Python 3.7+
- pytest 6.0.0+
- Django 3.0+ (optional, for Django-specific validation)

## Comparison with Other Tools

| Feature                       | pytest-fixturecheck | pytest-django | factory_boy | standard pytest |
| ----------------------------- | :-----------------: | :-----------: | :---------: | :-------------: |
| Early fixture validation      |          ✅          |       ❌       |      ❌      |        ❌        |
| Django model field validation |          ✅          |       ❌       |      ❌      |        ❌        |
| Clear fixture error reporting |          ✅          |       ❌       |      ❌      |        ❌        |
| Validator extensibility       |          ✅          |       ❌       |      ❌      |        ❌        |
| Simple decorator API          |          ✅          |       ❌       |      ❌      |        ❌        |

While other tools are great for fixture management, pytest-fixturecheck is uniquely focused on validating fixtures *before* tests run, catching issues early in the testing process.

## Contributing

Contributions are welcome! Check out the [Contributing Guidelines](CONTRIBUTING.md) for more information.

To set up the development environment:

```bash
# Clone the repository
git clone https://github.com/yourusername/pytest-fixturecheck.git
cd pytest-fixturecheck

# Install development dependencies
uv pip install -e ".[dev]"

# Run tests
make test-all
```

## License

MIT License
