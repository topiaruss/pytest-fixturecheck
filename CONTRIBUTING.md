# Contributing to pytest-fixturecheck

Thank you for considering contributing to pytest-fixturecheck! This document provides guidelines and steps for contributing to the project.

## Development Setup

1. Fork the repository
2. Clone your forked repository: `git clone https://github.com/yourusername/pytest-fixturecheck.git`
3. Create a virtual environment and activate it:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
4. Install development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```
5. Set up pre-commit hooks:
   ```bash
   pre-commit install
   ```

## Pre-commit Hooks

We use pre-commit hooks to ensure code quality and consistency. The hooks include:

- Code formatting (Black, isort)
- Linting (Flake8, Pylint)
- Type checking (MyPy)
- Security scanning (Bandit)
- Python syntax upgrades (pyupgrade)
- Docstring validation (pydocstyle)
- Various file checks (trailing whitespace, merge conflicts, etc.)

To run all pre-commit hooks manually:

```bash
pre-commit run --all-files
```

To update the pre-commit hooks:

```bash
pre-commit autoupdate
```

## Running Tests

Run the tests using tox:

```bash
tox
```

Or just using pytest:

```bash
pytest
```

## Code Style

We use:
- Black for code formatting
- Flake8 for linting
- MyPy for type checking

You can run these checks with:

```bash
tox -e lint
tox -e mypy
```

## Pull Request Process

1. Create a branch for your feature or bugfix
2. Make your changes
3. Run tests and ensure they pass
4. Update documentation as needed
5. Submit a pull request

## Release Process

To release a new version:

1. Update version in:
   - `src/pytest_fixturecheck/__init__.py`
   - `pyproject.toml`
2. Update `CHANGELOG.md` with the new version and changes
3. Update license format if needed (use `license = {text = "MIT"}` in pyproject.toml for backward compatibility with Python 3.8)
4. Build the package:
   ```bash
   python -m build
   ```
5. Check the built package for issues (warnings, etc.)
6. Tag the release: `git tag v0.x.y`
7. Push the tag: `git push --tags`
8. Upload to PyPI:
   ```bash
   twine upload dist/*0.x.y*
   ```

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive criticism
- Work together to improve the project

## Getting Help

If you have questions about contributing, feel free to:
- Open an issue with your question
- Reach out to the maintainers

Thank you for your contribution!

## Django Integration

When working on Django-specific features:

1. Ensure Django-related code gracefully degrades when Django is not installed
2. Add appropriate tests that use Django fixtures
3. Document Django-specific functionality
