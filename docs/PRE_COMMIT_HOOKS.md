# Pre-commit Hooks for pytest-fixturecheck

This project uses pre-commit hooks to ensure code quality and consistency. This document explains how to use them effectively.

## What is pre-commit?

Pre-commit is a framework for managing and maintaining multi-language pre-commit hooks. It helps you run quality checks before code is committed, ensuring better code quality.

## Installation

The hooks are automatically installed when you run:

```bash
pip install -e ".[dev]"
pre-commit install
```

## Available Hooks

The following hooks are configured:

### Basic Checks

- **trailing-whitespace**: Removes trailing whitespace
- **end-of-file-fixer**: Ensures files end with a newline
- **check-yaml**: Checks YAML files for syntax errors
- **check-toml**: Checks TOML files for syntax errors
- **check-added-large-files**: Prevents giant files from being committed
- **debug-statements**: Checks for debugger imports and py37+ `breakpoint()` calls
- **detect-private-key**: Checks for private keys
- **check-merge-conflict**: Checks for files that contain merge conflict strings
- **mixed-line-ending**: Ensures consistent line endings

### Python Specific

- **isort**: Sorts import statements
- **black**: Formats Python code
- **flake8**: Lints Python code with additional docstring checks
- **mypy**: Type checks Python code
- **pyupgrade**: Automatically upgrades syntax for newer Python versions
- **bandit**: Security checks for Python code
- **pydocstyle**: Checks docstrings for compliance with standards
- **pylint**: Comprehensive Python linting

## Running the Hooks

### Automatically on Commit

Hooks configured with the default stage will run automatically when you commit code. Currently, most hooks are set to the "manual" stage to avoid blocking commits while we improve the codebase.

### Manually

You can run all hooks (including manual ones) with:

```bash
pre-commit run --all-files
pre-commit run --hook-stage manual --all-files
```

Or through tox:

```bash
tox -e pre-commit
```

### Running Individual Hooks

To run a specific hook:

```bash
pre-commit run <hook-id> --all-files
```

For example:

```bash
pre-commit run black --all-files
```

## Skipping Hooks

If you need to skip hooks temporarily:

```bash
git commit -m "Your message" --no-verify
```

However, it's better to fix the issues than to skip the hooks.

## Updating the Hooks

To update the hook versions:

```bash
pre-commit autoupdate
```

## Configuration Files

- **.pre-commit-config.yaml**: Main pre-commit configuration
- **.flake8**: Flake8 configuration
- **.pylintrc**: Pylint configuration
- **.pydocstyle**: Pydocstyle configuration
- **pyproject.toml**: Contains configuration for Black, Bandit, and other tools

## Gradual Adoption Strategy

We've set most hooks to the "manual" stage to avoid blocking commits while we clean up the codebase. The plan is to:

1. Run hooks manually to fix existing issues
2. Gradually move hooks from manual to the default stage as the codebase improves
3. Eventually have all hooks run automatically on commit
