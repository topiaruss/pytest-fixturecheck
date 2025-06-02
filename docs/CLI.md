# Command-Line Interface (CLI) Guide

pytest-fixturecheck provides a powerful command-line interface to analyze and manage fixture checks across your codebase. This guide covers all CLI features and usage patterns.

## Installation

The CLI is included when you install pytest-fixturecheck:

```bash
pip install pytest-fixturecheck
```

## Commands Overview

| Command | Description |
|---------|-------------|
| `fixturecheck report` | Analyze test suites to find fixture check opportunities and count existing ones |
| `fixturecheck add` | Automatically add `@fixturecheck()` decorators to fixtures |

## Report Command

The `report` command analyzes your test suite and provides insights about fixture validation coverage.

### Basic Usage

```bash
# Basic report - shows summary counts
fixturecheck report

# Analyze specific directory
fixturecheck report --path tests/

# Use custom file pattern
fixturecheck report --pattern "*_test.py"
```

### Verbose Options

#### Single Verbose (`-v`)

Shows detailed fixture information including line numbers, names, and parameters:

```bash
fixturecheck report -v
```

**Example output:**
```
FIXTURE CHECK REPORT
==================================================

File: tests/test_user.py
----------------------------------------

Opportunities for fixture checks:
  Line 12: user_fixture
    Parameters: db
    ------------------------------
  Line 18: admin_user
    Parameters: user_fixture
    ------------------------------

Existing fixture checks:
  Line 25: validated_user
    Parameters: db
    ------------------------------
  Line 32: checked_admin
    Parameters: validated_user
    ------------------------------

==================================================
Found 2 opportunities for fixture checks
Found 2 existing fixture checks
```

#### Double Verbose (`-vv`)

Shows everything from `-v` plus validator information:

```bash
fixturecheck report -vv
```

**Example output:**
```
FIXTURE CHECK REPORT
==================================================

File: tests/test_user.py
----------------------------------------

Opportunities for fixture checks:
  Line 12: user_fixture
    Parameters: db
    ------------------------------

Existing fixture checks:
  Line 25: validated_user
    Parameters: db
    Validator: Default validator
    ------------------------------
  Line 32: checked_admin
    Parameters: validated_user
    Validator: validate_admin_user
    ------------------------------

==================================================
Found 1 opportunities for fixture checks
Found 2 existing fixture checks
```

### Report Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--path` | `-p` | Path to search for test files | Current directory (`.`) |
| `--pattern` | `-P` | Pattern to match test files | `test_*.py` |
| `--verbose` | `-v` | Verbose output level (use -v or -vv) | None |

### Examples

```bash
# Analyze only unit tests
fixturecheck report --path tests/unit/

# Analyze files with custom pattern
fixturecheck report --pattern "*_tests.py"

# Detailed analysis of integration tests
fixturecheck report -v --path tests/integration/

# Full analysis with validator details
fixturecheck report -vv --path src/tests/
```

## Add Command

The `add` command automatically adds `@fixturecheck()` decorators to fixtures that don't have them.

### Basic Usage

```bash
# Preview changes without modifying files
fixturecheck add --dry-run

# Add decorators to fixtures
fixturecheck add

# Add decorators in specific directory
fixturecheck add --path tests/unit/
```

### Add Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--path` | `-p` | Path to search for test files | Current directory (`.`) |
| `--pattern` | `-P` | Pattern to match test files | `test_*.py` |
| `--dry-run` | `-d` | Show what would be changed without making changes | False |

### Examples

```bash
# Dry run to see what would be modified
fixturecheck add --dry-run
# Output: Would modify tests/test_user.py
#         Would modify tests/test_orders.py

# Actually add the decorators
fixturecheck add
# Output: Modified tests/test_user.py
#         Modified tests/test_orders.py

# Add decorators only to unit tests
fixturecheck add --path tests/unit/

# Add decorators with custom pattern
fixturecheck add --pattern "*_test.py" --dry-run
```

## Workflow Examples

### 1. Initial Assessment

When starting to use pytest-fixturecheck on an existing project:

```bash
# Get overview of your test suite
fixturecheck report

# See detailed breakdown
fixturecheck report -v

# Preview what would be added
fixturecheck add --dry-run
```

### 2. Gradual Adoption

Add fixture checks incrementally:

```bash
# Start with unit tests
fixturecheck add --path tests/unit/

# Check what was added
fixturecheck report -v --path tests/unit/

# Move to integration tests
fixturecheck add --path tests/integration/
```

### 3. Continuous Monitoring

Regular checks during development:

```bash
# Quick check for new opportunities
fixturecheck report

# Detailed analysis for code review
fixturecheck report -vv --path tests/new_feature/

# Add checks to new fixtures
fixturecheck add --path tests/new_feature/
```

### 4. CI/CD Integration

Add to your CI pipeline:

```bash
# Check for fixtures without validation
fixturecheck report > fixture_report.txt

# Ensure all fixtures have checks (exit non-zero if opportunities found)
OPPORTUNITIES=$(fixturecheck report | grep "opportunities" | cut -d' ' -f2)
if [ "$OPPORTUNITIES" -gt 0 ]; then
    echo "Found $OPPORTUNITIES fixtures without checks"
    fixturecheck report -v
    exit 1
fi
```

## Understanding Output

### Opportunities for Fixture Checks

These are fixtures that could benefit from the `@fixturecheck()` decorator:

- **Line number**: Where the fixture is defined
- **Fixture name**: The function name
- **Parameters**: Dependencies (other fixtures, pytest built-ins)

### Existing Fixture Checks

These are fixtures that already have `@fixturecheck()` decorators:

- **Line number**: Where the fixture is defined
- **Fixture name**: The function name  
- **Parameters**: Dependencies
- **Validator** (with `-vv`): The validation function being used
  - `Default validator`: Basic validation (no custom validator)
  - Function name: Custom validator function
  - Complex expressions: Lambda functions or method calls

### Separator Lines

The CLI uses consistent separator patterns:

- `==========================================` - Major section separators
- `----------------------------------------` - File separators
- `------------------------------` - Individual fixture separators

## File Patterns

The CLI supports glob patterns for file matching:

| Pattern | Matches |
|---------|---------|
| `test_*.py` | Files starting with "test_" |
| `*_test.py` | Files ending with "_test.py" |
| `test*.py` | Files starting with "test" |
| `*test*.py` | Files containing "test" |
| `conftest.py` | Specific file name |

## Best Practices

### 1. Start with Dry Run

Always use `--dry-run` first to understand what will change:

```bash
fixturecheck add --dry-run
```

### 2. Use Specific Paths

Target specific directories to control scope:

```bash
# Good: Specific scope
fixturecheck add --path tests/models/

# Avoid: Too broad initially
fixturecheck add  # Entire project
```

### 3. Regular Monitoring

Include fixture check analysis in your development workflow:

```bash
# Add to git hooks or CI
fixturecheck report -v
```

### 4. Combine with grep

Filter output for specific insights:

```bash
# Find fixtures with many parameters
fixturecheck report -v | grep -A1 "Parameters.*,"

# Count validator types
fixturecheck report -vv | grep "Validator:" | sort | uniq -c
```

## Troubleshooting

### Command Not Found

If `fixturecheck` command is not found:

```bash
# Ensure it's installed
pip install pytest-fixturecheck

# Check if it's in PATH
which fixturecheck

# Run directly with Python
python -m pytest_fixturecheck.cli report
```

### No Fixtures Found

If the CLI reports 0 fixtures when you expect more:

1. **Check file pattern**: Use `-P` to specify correct pattern
2. **Check path**: Use `-p` to specify correct directory
3. **Verify syntax**: Ensure fixtures use proper `@pytest.fixture` syntax

```bash
# Debug with verbose output
fixturecheck report -v --path . --pattern "*.py"
```

### Permission Errors

If you get permission errors when using `add`:

```bash
# Check file permissions
ls -la tests/

# Ensure files are writable
chmod +w tests/*.py
```

## Advanced Usage

### Custom Scripts

Create scripts that combine CLI commands:

```bash
#!/bin/bash
# analyze_fixtures.sh

echo "=== Fixture Analysis Report ==="
fixturecheck report

echo -e "\n=== Detailed Breakdown ==="
fixturecheck report -v

echo -e "\n=== Proposed Changes ==="
fixturecheck add --dry-run
```

### Integration with Make

Add to your Makefile:

```makefile
.PHONY: fixture-report fixture-add fixture-check

fixture-report:
	fixturecheck report -v

fixture-add:
	fixturecheck add --dry-run

fixture-check:
	@OPPS=$$(fixturecheck report | grep opportunities | cut -d' ' -f2); \
	if [ "$$OPPS" -gt 0 ]; then \
		echo "❌ Found $$OPPS fixtures without checks"; \
		fixturecheck report -v; \
		exit 1; \
	else \
		echo "✅ All fixtures have validation checks"; \
	fi
```

## See Also

- [Quick Start Guide](QUICKSTART.md) - Basic pytest-fixturecheck usage
- [Property Validators](PROPERTY_VALIDATORS.md) - Built-in validation functions
- [Troubleshooting Guide](TROUBLESHOOTING.md) - Common issues and solutions 