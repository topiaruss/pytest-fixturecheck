import ast
import inspect
import traceback
from typing import Any, Dict, List, Optional, Tuple

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
    config.addinivalue_line("markers", "fixturecheck: mark a test as using fixture validation")
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
                fixture_func = current_func  # Use the wrapped function with fixturecheck
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
            fixturedef._fixturecheck_skip = True


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
            fixture_original_func = fixturedef.func  # The func pytest associates with fixturedef

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
                        fixturedef._fixturecheck_skip = True
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
                                failed_fixtures.append((fixturedef, e, traceback.format_exc()))
                                continue
                except Exception as e:
                    # Special handling for pytest-asyncio fixtures and other async-related errors
                    if any(
                        x in str(e).lower() for x in ["asyncio", "coroutine", "awaitable", "async"]
                    ):
                        # Skip asyncio fixtures - they can't be executed during collection
                        fixturedef._fixturecheck_skip = True
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
        try:
            fixture_file = inspect.getfile(fixturedef.func)
            fixture_lineno = inspect.getsourcelines(fixturedef.func)[1]
            location = f"{fixture_file}:{fixture_lineno}"
        except (TypeError, OSError):
            location = "<unknown location>"

        print(f"\nFixture '{fixture_name}' in {location} failed validation:")
        print(f"  {error.__class__.__name__}: {error}")

        # Check if this is likely a user-defined validator error
        error_in_user_code = False
        if isinstance(error, ImportError):
            # For import errors, check if it's from a user-defined module (not pytest_fixturecheck)
            if "pytest_fixturecheck" not in str(error) and tb:
                # Check the traceback to see if the ImportError is coming from user code
                user_paths = [
                    line
                    for line in tb.splitlines()
                    if "site-packages/pytest_fixturecheck" not in line and "File" in line
                ]
                if user_paths:
                    error_in_user_code = True
                    # Extract the path of the file with the import error
                    import_error_file = (
                        user_paths[0].split('"')[1] if '"' in user_paths[0] else "<unknown file>"
                    )
                    print(
                        "\n  POSSIBLE USER CODE ERROR: The import error appears to be in your code."
                    )
                    print(f"  The error occurred in file: {import_error_file}")
                    print(
                        "  Check that all imports in your validator function are correct and the packages are installed."
                    )

        # Print a simplified traceback
        if isinstance(tb, str) and tb.strip():
            # If it's a user code error, print a more helpful message
            if error_in_user_code and isinstance(error, ImportError):
                print("\n  Traceback (most relevant parts):")
                for line in tb.splitlines()[1:]:
                    if "File" in line or "ImportError" in line:
                        print(f"  {line}")
            else:
                # Standard traceback handling
                for line in tb.splitlines()[1:]:
                    if line.strip() and not line.startswith("During"):
                        print(f"  {line}")

    print("\n" + "=" * 80)
    print("Fix these fixture issues before running your tests.")
    if any(isinstance(error, ImportError) for _, error, _ in failed_fixtures):
        print("\nIMPORT ERRORS DETECTED:")
        print(
            "  • If the import error is in your custom validator, ensure all required packages are installed."
        )
        print(
            "  • Custom validators should be defined in your own files, not in the pytest_fixturecheck package."
        )
        print(
            "  • For validator examples, see https://github.com/topiaruss/pytest-fixturecheck#property-validators"
        )
    print("=" * 80)


class FixtureCheckPlugin:
    def __init__(self):
        self.fixture_patterns = [
            "@pytest.fixture",
            "@fixture",
            "@pytest_asyncio.fixture",
        ]

    def count_opportunities(self, content: str) -> int:
        """Count the number of fixtures that could benefit from fixturecheck."""
        opportunities = 0
        tree = ast.parse(content)

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check if this is a fixture
                is_fixture = False
                for decorator in node.decorator_list:
                    if isinstance(decorator, ast.Call):
                        if isinstance(decorator.func, ast.Name):
                            if decorator.func.id in [
                                "fixture",
                                "pytest.fixture",
                                "pytest_asyncio.fixture",
                            ]:
                                is_fixture = True
                                break
                        elif isinstance(decorator.func, ast.Attribute):
                            if decorator.func.attr == "fixture":
                                is_fixture = True
                                break
                    elif isinstance(decorator, ast.Name):
                        if decorator.id in [
                            "fixture",
                            "pytest.fixture",
                            "pytest_asyncio.fixture",
                        ]:
                            is_fixture = True
                            break
                    elif isinstance(decorator, ast.Attribute):
                        if decorator.attr == "fixture":
                            is_fixture = True
                            break

                if is_fixture:
                    # Check if it already has fixturecheck
                    has_fixturecheck = False
                    for decorator in node.decorator_list:
                        if isinstance(decorator, ast.Call):
                            if isinstance(decorator.func, ast.Name):
                                if decorator.func.id == "fixturecheck":
                                    has_fixturecheck = True
                                    break

                    if not has_fixturecheck:
                        opportunities += 1

        return opportunities

    def count_existing_checks(self, content: str) -> int:
        """Count the number of existing fixture checks."""
        existing_checks = 0
        tree = ast.parse(content)

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                for decorator in node.decorator_list:
                    if isinstance(decorator, ast.Call):
                        if isinstance(decorator.func, ast.Name):
                            if decorator.func.id == "fixturecheck":
                                existing_checks += 1
                                break

        return existing_checks

    def get_opportunities_details(self, content: str, filename: str) -> List[Dict[str, Any]]:
        """Get detailed information about fixtures that could benefit from fixturecheck."""
        details = []
        tree = ast.parse(content)

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check if this is a fixture
                is_fixture = False
                fixture_decorator = None

                for decorator in node.decorator_list:
                    if isinstance(decorator, ast.Call):
                        if isinstance(decorator.func, ast.Name):
                            if decorator.func.id in [
                                "fixture",
                                "pytest.fixture",
                                "pytest_asyncio.fixture",
                            ]:
                                is_fixture = True
                                fixture_decorator = decorator
                                break
                        elif isinstance(decorator.func, ast.Attribute):
                            if decorator.func.attr == "fixture":
                                is_fixture = True
                                fixture_decorator = decorator
                                break
                    elif isinstance(decorator, ast.Name):
                        if decorator.id in [
                            "fixture",
                            "pytest.fixture",
                            "pytest_asyncio.fixture",
                        ]:
                            is_fixture = True
                            fixture_decorator = decorator
                            break
                    elif isinstance(decorator, ast.Attribute):
                        if decorator.attr == "fixture":
                            is_fixture = True
                            fixture_decorator = decorator
                            break

                if is_fixture:
                    # Check if it already has fixturecheck
                    has_fixturecheck = False
                    for decorator in node.decorator_list:
                        if isinstance(decorator, ast.Call):
                            if isinstance(decorator.func, ast.Name):
                                if decorator.func.id == "fixturecheck":
                                    has_fixturecheck = True
                                    break

                    if not has_fixturecheck:
                        # Extract function parameters
                        params = [arg.arg for arg in node.args.args]

                        detail = {
                            "name": node.name,
                            "line_number": node.lineno,
                            "params": params,
                            "filename": filename,
                            "validator": None,  # No validator for opportunities
                        }
                        details.append(detail)

        return details

    def get_existing_checks_details(self, content: str, filename: str) -> List[Dict[str, Any]]:
        """Get detailed information about existing fixture checks."""
        details = []
        tree = ast.parse(content)

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check if this function has fixturecheck decorator
                fixturecheck_decorator = None
                for decorator in node.decorator_list:
                    if isinstance(decorator, ast.Call):
                        if isinstance(decorator.func, ast.Name):
                            if decorator.func.id == "fixturecheck":
                                fixturecheck_decorator = decorator
                                break

                if fixturecheck_decorator:
                    # Extract function parameters
                    params = [arg.arg for arg in node.args.args]

                    # Extract validator information
                    validator_info = self._extract_validator_info(fixturecheck_decorator)

                    detail = {
                        "name": node.name,
                        "line_number": node.lineno,
                        "params": params,
                        "filename": filename,
                        "validator": validator_info,
                    }
                    details.append(detail)

        return details

    def _extract_validator_info(self, decorator: ast.Call) -> Optional[str]:
        """Extract validator information from a fixturecheck decorator."""
        if not decorator.args:
            return "Default validator"

        # Get the first argument (the validator)
        validator_arg = decorator.args[0]

        if isinstance(validator_arg, ast.Name):
            return validator_arg.id
        elif isinstance(validator_arg, ast.Attribute):
            return (
                ast.unparse(validator_arg) if hasattr(ast, "unparse") else f"{validator_arg.attr}"
            )
        elif isinstance(validator_arg, ast.Call):
            if hasattr(ast, "unparse"):
                return ast.unparse(validator_arg)
            else:
                # Fallback for older Python versions
                if isinstance(validator_arg.func, ast.Name):
                    return f"{validator_arg.func.id}(...)"
                else:
                    return "Complex validator call"
        else:
            if hasattr(ast, "unparse"):
                return ast.unparse(validator_arg)
            else:
                return "Custom validator"

    def add_fixture_checks(self, content: str) -> str:
        """Add fixturecheck decorators to fixtures that don't have them."""
        tree = ast.parse(content)
        lines = content.splitlines()

        # Track which lines need fixturecheck added
        lines_to_add = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check if this is a fixture and if it already has fixturecheck
                is_fixture = False
                fixture_decorator_line = None
                has_fixturecheck = False

                for decorator in node.decorator_list:
                    # Check for fixturecheck decorators first
                    fixturecheck_found = False
                    if isinstance(decorator, ast.Call):
                        if (
                            isinstance(decorator.func, ast.Name)
                            and decorator.func.id == "fixturecheck"
                        ):
                            fixturecheck_found = True
                        elif (
                            isinstance(decorator.func, ast.Attribute)
                            and decorator.func.attr == "fixturecheck"
                        ):
                            fixturecheck_found = True
                    elif isinstance(decorator, ast.Name) and decorator.id == "fixturecheck":
                        fixturecheck_found = True
                    elif isinstance(decorator, ast.Attribute) and decorator.attr == "fixturecheck":
                        fixturecheck_found = True

                    if fixturecheck_found:
                        has_fixturecheck = True
                        continue

                    # Check for fixture decorators
                    if isinstance(decorator, ast.Call):
                        if isinstance(decorator.func, ast.Name):
                            if decorator.func.id in [
                                "fixture",
                                "pytest.fixture",
                                "pytest_asyncio.fixture",
                            ]:
                                is_fixture = True
                                fixture_decorator_line = decorator.lineno
                        elif isinstance(decorator.func, ast.Attribute):
                            if decorator.func.attr == "fixture":
                                is_fixture = True
                                fixture_decorator_line = decorator.lineno
                    elif isinstance(decorator, ast.Name):
                        if decorator.id in [
                            "fixture",
                            "pytest.fixture",
                            "pytest_asyncio.fixture",
                        ]:
                            is_fixture = True
                            fixture_decorator_line = decorator.lineno
                    elif isinstance(decorator, ast.Attribute):
                        if decorator.attr == "fixture":
                            is_fixture = True
                            fixture_decorator_line = decorator.lineno

                # Only add fixturecheck if it's a fixture and doesn't already have it
                if is_fixture and not has_fixturecheck and fixture_decorator_line is not None:
                    # Insert after the fixture decorator
                    insert_line = fixture_decorator_line
                    lines_to_add.append((insert_line, "@fixturecheck()"))

        # Add the decorators in reverse order to maintain line numbers
        for line_num, decorator in sorted(lines_to_add, reverse=True):
            lines.insert(line_num, decorator)

        return "\n".join(lines)
