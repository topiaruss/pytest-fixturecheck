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


def pytest_fixture_setup(fixturedef: Any, request: Any) -> None:
    """Hook executed when a fixture is about to be setup.

    We use this to track which fixtures have been marked with @fixturecheck.
    """
    fixture_func = fixturedef.func

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

    for fixturedef in fixtures_to_validate:
        try:
            # Create a request context for this fixture
            request = session._fixturemanager.getfixturerequest(session)

            # Execute the fixture
            result = fixturedef.execute(request)

            # If there's a validator function, run it on the fixture result
            validator = getattr(fixturedef.func, "_validator", None)
            if validator is not None and result is not None:
                validator(result)

        except Exception as e:
            # Capture and store the error
            failed_fixtures.append((fixturedef, e, traceback.format_exc()))

    # If any fixtures failed, report the errors
    if failed_fixtures:
        report_fixture_errors(failed_fixtures)
        pytest.exit("Fixture validation failed", 1)


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
