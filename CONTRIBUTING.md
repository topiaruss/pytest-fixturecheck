# Contributing to pytest-fixturecheck

Thank you for considering contributing to pytest-fixturecheck! This document outlines the process for contributing to the project.

## Development Setup

1. Fork and clone the repository:

```bash
git clone https://github.com/yourusername/pytest-fixturecheck.git
cd pytest-fixturecheck
```

2. Create a virtual environment and install development dependencies:

```bash
# Using uv (recommended)
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"

# Or using standard pip
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

3. Install pre-commit hooks:

```bash
pip install pre-commit
pre-commit install
```

## Running Tests

Run the tests using pytest:

```bash
# Run all tests
make test-all

# Run a specific test
make test-specific tests/test_plugin.py
```

## Code Style

This project uses:
- Black for code formatting
- isort for import sorting
- flake8 for linting
- mypy for type checking

The pre-commit hooks will run these automatically when you commit changes.

## Pull Request Process

1. Ensure your code passes all tests and pre-commit checks
2. Add or update tests for any new or changed functionality
3. Update documentation if necessary
4. Submit a pull request with a clear description of the changes

## Adding New Features

When adding new features, please follow these guidelines:

1. Start by opening an issue describing the feature
2. Add appropriate tests for new functionality
3. Update the README.md with examples if necessary
4. Add appropriate type hints

## Release Process

The maintainers will handle releases following this process:

1. Update version in pyproject.toml
2. Create and merge a release PR
3. Tag the release on GitHub
4. Build and upload to PyPI

## Django Integration

When working on Django-specific features:

1. Ensure Django-related code gracefully degrades when Django is not installed
2. Add appropriate tests that use Django fixtures
3. Document Django-specific functionality
