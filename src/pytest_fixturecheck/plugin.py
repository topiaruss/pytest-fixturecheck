import inspect
import sys
import traceback
from typing import Any, Dict, List, Optional, Set, Tuple

import pytest


def pytest_configure(config: Any) -> None:
    """Register the plugin with pytest."""
    config.addinivalue_line(
        "markers", "fixturecheck: mark a test as using fixture validation"
    )
    # Add configuration option for auto-skip
    config.addini(
        "fixturecheck-auto-skip",
        help="Automatically skip tests with invalid fixtures instead of failing",
        default="false",
        type="bool",
    )


def pytest_fixture_setup(fixturedef: Any, request: Any) -> None:
    """Hook executed when a fixture is about to be setup.

    We use this to track which fixtures have been marked with @fixturecheck.
    """
    fixture_func = fixturedef.func

    # Support different decorator orders - check original fixture if wrapped
    if hasattr(fixture_func, "__wrapped__"):
        # Check if any wrapper in the chain has _fixturecheck
        current_func = fixture_func
        while hasattr(current_func, "__wrapped__"):
            if getattr(current_func, "_fixturecheck", False):
                fixture_func = current_func  # Use the wrapped function with fixturecheck
                break
            current_func = current_func.__wrapped__

    # Check if this fixture has been marked with @fixturecheck
    if getattr(fixture_func, "_fixturecheck", False):
        # Register it to be validated during collection
        if not hasattr(request.config, "_fixturecheck_fixtures"):
            request.config._fixturecheck_fixtures = set()

        request.config._fixturecheck_fixtures.add(fixturedef)


def pytest_collection_finish(session: Any) -> None:
    """After collection is complete, validate all fixtures marked with @fixturecheck.

    This runs before any tests execute, so we can catch fixture errors early.
    """
    if not hasattr(session.config, "_fixturecheck_fixtures"):
        return

    fixtures_to_validate = session.config._fixturecheck_fixtures
    if not fixtures_to_validate:
        return

    failed_fixtures = []
    auto_skip = session.config.getini("fixturecheck-auto-skip") == "true"

    for fixturedef in fixtures_to_validate:
        try:
            # Get the fixture function and validator
            fixture_func = fixturedef.func
            # Support different decorator orders - check original fixture if wrapped
            if hasattr(fixture_func, "__wrapped__"):
                # Check if any wrapper in the chain has _fixturecheck
                current_func = fixture_func
                while hasattr(current_func, "__wrapped__"):
                    if getattr(current_func, "_fixturecheck", False):
                        # Found the wrapper with fixturecheck
                        validator = getattr(current_func, "_validator", None)
                        break
                    current_func = current_func.__wrapped__
                else:
                    # No wrapper had _fixturecheck
                    validator = getattr(fixture_func, "_validator", None)
            else:
                validator = getattr(fixture_func, "_validator", None)

            # First, run validator on the fixture function itself if there's a validator
            if validator is not None:
                # Pass the function object and True to indicate collection phase
                validator(fixture_func, True)
                
            # Create a request context for this fixture
            request = session._fixturemanager.getfixturerequest(session)

            # Execute the fixture
            result = fixturedef.execute(request)

            # If there's a validator function, run it on the fixture result
            if validator is not None and result is not None:
                # Pass the result and False to indicate execution phase
                validator(result, False)

        except Exception as e:
            # Capture and store the error
            failed_fixtures.append((fixturedef, e, traceback.format_exc()))

    # If any fixtures failed, report the errors
    if failed_fixtures:
        report_fixture_errors(failed_fixtures)
        if not auto_skip:
            pytest.exit("Fixture validation failed", 1)
        else:
            # Mark the failing tests for skipping
            for fixturedef, error, _ in failed_fixtures:
                _mark_dependent_tests_for_skip(session, fixturedef, error)


def _mark_dependent_tests_for_skip(session: Any, fixturedef: Any, error: Exception) -> None:
    """Mark tests that depend on the failing fixture for skipping."""
    fixture_name = fixturedef.argname
    
    # Create a skip marker with the error message
    skip_marker = pytest.mark.skip(
        reason=f"Fixture '{fixture_name}' failed validation: {error.__class__.__name__}: {error}"
    )
    
    # Apply the marker to tests that use this fixture
    for item in session.items:
        if fixture_name in item.fixturenames:
            item.add_marker(skip_marker)


def report_fixture_errors(failed_fixtures: List[Tuple]) -> None:
    """Format and print errors for any fixtures that failed validation."""
    print("\n" + "=" * 80)
    print("FIXTURE VALIDATION ERRORS")
    print("=" * 80)

    for fixturedef, error, tb in failed_fixtures:
        fixture_name = fixturedef.argname
        fixture_file = inspect.getfile(fixturedef.func)
        fixture_lineno = inspect.getsourcelines(fixturedef.func)[1]

        print(
            f"\nFixture '{fixture_name}' in {fixture_file}:{fixture_lineno} failed validation:"
        )
        print(f"  {error.__class__.__name__}: {error}")

        # Print a simplified traceback
        for line in tb.splitlines()[1:]:
            if line.strip() and not line.startswith("During"):
                print(f"  {line}")

    print("\n" + "=" * 80)
    print("Fix these fixture issues before running your tests.")
    print("=" * 80)
