import inspect
import sys
import traceback
from typing import Any, Dict, List, Optional, Set, Tuple

import pytest

from .utils import is_async_function, is_coroutine

# Check if pytest-asyncio is installed
PYTEST_ASYNCIO_INSTALLED = False
try:
    import pytest_asyncio

    PYTEST_ASYNCIO_INSTALLED = True
except ImportError:
    pass


def pytest_addoption(parser):
    """Add plugin-specific configuration options."""
    parser.addini(
        "fixturecheck-auto-skip",
        help="Automatically skip tests with invalid fixtures instead of failing",
        default="false",
        type="bool",
    )


def pytest_configure(config: Any) -> None:
    """Register the plugin with pytest."""
    config.addinivalue_line(
        "markers", "fixturecheck: mark a test as using fixture validation"
    )
    # Note: We don't need to call addinivalue_line for fixturecheck-auto-skip
    # since it's already registered as a bool type option in pytest_addoption


def is_async_fixture(fixturedef: Any) -> bool:
    """Check if a fixture is an async fixture."""
    # Check if the fixture function is a coroutine function
    if is_async_function(fixturedef.func):
        return True

    # Check for pytest-asyncio specific attributes
    if hasattr(fixturedef, "unittest") and "async" in str(fixturedef.unittest).lower():
        return True

    # Check fixture name patterns that typically indicate async fixtures
    if fixturedef.argname.startswith("async_"):
        return True

    # Direct check of pytest-asyncio fixture detection if available
    if PYTEST_ASYNCIO_INSTALLED:
        try:
            return hasattr(fixturedef, "_pytest_asyncio_scope")
        except (AttributeError, ImportError):
            pass

    return False


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
                fixture_func = (
                    current_func  # Use the wrapped function with fixturecheck
                )
                break
            current_func = current_func.__wrapped__

    # Check if this fixture has been marked with @fixturecheck
    if getattr(fixture_func, "_fixturecheck", False):
        # Register it to be validated during collection
        if not hasattr(request.config, "_fixturecheck_fixtures"):
            request.config._fixturecheck_fixtures = set()

        request.config._fixturecheck_fixtures.add(fixturedef)

        # Pre-mark async fixtures to skip execution validation
        if is_async_fixture(fixturedef):
            setattr(fixturedef, "_fixturecheck_skip", True)


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
            fixture_original_func = (
                fixturedef.func
            )  # The func pytest associates with fixturedef

            # Default to attributes from this original_func.
            # These will be used if the original_func is not wrapped, or if it is wrapped
            # but the _fixturecheck marker (and thus validator) is on original_func itself,
            # or if the marker is on an inner function that the loop below finds.
            validator = getattr(fixture_original_func, "_validator", None)
            expect_validation_error = getattr(
                fixture_original_func, "_expect_validation_error", False
            )

            # If fixture_original_func is wrapped, we need to search for the actual function
            # in the wrapper chain that has _fixturecheck=True, as that's where
            # _validator and _expect_validation_error will be.
            if hasattr(fixture_original_func, "__wrapped__"):
                current_search_func = fixture_original_func
                while True:  # Loop from outermost to innermost
                    # Check if the current function in the chain has the marker
                    if getattr(current_search_func, "_fixturecheck", False):
                        # Marker found on this current_search_func. Use its attributes.
                        validator = getattr(current_search_func, "_validator", None)
                        expect_validation_error = getattr(
                            current_search_func, "_expect_validation_error", False
                        )
                        break  # Found the true source of attributes, stop searching

                    # If no more wrappers, and we haven't found the marker by break-ing,
                    # the attributes from fixture_original_func (if it had the marker)
                    # or the defaults (None/False) will be used.
                    # The 'validator' and 'expect_validation_error' are already pre-set
                    # using fixture_original_func. If the marker was on fixture_original_func itself,
                    # those are correct. If the marker was on an inner function, this loop
                    # would have updated them and broken. If the marker was *not* on an inner
                    # function reached so far, and this is the innermost, then the pre-set
                    # values (from original_func) remain correct if original_func was marked.
                    if not hasattr(current_search_func, "__wrapped__"):
                        break  # Reached the innermost function

                    current_search_func = current_search_func.__wrapped__

            # At this point, 'validator' and 'expect_validation_error' should be correctly set
            # from the function in the (potential) wrapper chain that has _fixturecheck = True.

            # First, run validator on the fixture function itself if there's a validator
            if validator is not None:
                try:
                    # Pass the function object and True to indicate collection phase
                    validator(fixture_original_func, True)

                    # If we expected validation error but didn't get one
                    if expect_validation_error:
                        failed_fixtures.append(
                            (
                                fixturedef,
                                AssertionError(
                                    "Expected validation error but none occurred during collection phase"
                                ),
                                "No validation error during collection phase",
                            )
                        )
                except Exception as e:
                    # If we were expecting an error, this is good - don't record it as a failure
                    if expect_validation_error:
                        continue
                    else:
                        # Unexpected error - record it
                        failed_fixtures.append((fixturedef, e, traceback.format_exc()))
                        continue

            # Skip validation for unittest fixtures, async fixtures, and other special types
            if (
                hasattr(fixturedef, "unittest")
                or getattr(fixturedef, "_fixturecheck_skip", False)
                or is_async_fixture(fixturedef)
            ):
                continue

            # Create a request context for this fixture
            try:
                request = session._fixturemanager.getfixturerequest(session)

                # Execute the fixture
                try:
                    result = fixturedef.execute(request)

                    # Handle coroutine objects (returned by async fixtures)
                    if is_coroutine(result):
                        # Mark it to skip validation - can't execute coroutines during collection
                        setattr(fixturedef, "_fixturecheck_skip", True)
                        continue

                    # If there's a validator function, run it on the fixture result
                    if validator is not None and result is not None:
                        try:
                            # Pass the result and False to indicate execution phase
                            validator(result, False)

                            # If we expected a validation error but didn't get one
                            if expect_validation_error:
                                failed_fixtures.append(
                                    (
                                        fixturedef,
                                        AssertionError(
                                            "Expected validation error but none occurred during execution phase"
                                        ),
                                        "No validation error during execution phase",
                                    )
                                )
                        except Exception as e:
                            # If we were expecting an error, this is good
                            if expect_validation_error:
                                continue
                            else:
                                # Unexpected error - record it
                                failed_fixtures.append(
                                    (fixturedef, e, traceback.format_exc())
                                )
                                continue
                except Exception as e:
                    # Special handling for pytest-asyncio fixtures and other async-related errors
                    if any(
                        x in str(e).lower()
                        for x in ["asyncio", "coroutine", "awaitable", "async"]
                    ):
                        # Skip asyncio fixtures - they can't be executed during collection
                        setattr(fixturedef, "_fixturecheck_skip", True)
                        continue
                    else:
                        # If we expected a validation error, this might be it
                        if expect_validation_error:
                            continue
                        raise
            except Exception as e:
                # If we were expecting an error during fixture execution, this is fine
                if expect_validation_error:
                    continue
                # Capture and store the error
                failed_fixtures.append((fixturedef, e, traceback.format_exc()))

        except Exception as e:
            # If we were expecting an error, this is fine
            if expect_validation_error:
                continue

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


def _mark_dependent_tests_for_skip(
    session: Any, fixturedef: Any, error: Exception
) -> None:
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
        try:
            fixture_file = inspect.getfile(fixturedef.func)
            fixture_lineno = inspect.getsourcelines(fixturedef.func)[1]
            location = f"{fixture_file}:{fixture_lineno}"
        except (TypeError, OSError):
            location = "<unknown location>"

        print(f"\nFixture '{fixture_name}' in {location} failed validation:")
        print(f"  {error.__class__.__name__}: {error}")

        # Print a simplified traceback
        if isinstance(tb, str) and tb.strip():
            for line in tb.splitlines()[1:]:
                if line.strip() and not line.startswith("During"):
                    print(f"  {line}")

    print("\n" + "=" * 80)
    print("Fix these fixture issues before running your tests.")
    print("=" * 80)
