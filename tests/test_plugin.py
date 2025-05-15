"""Tests for the pytest-fixturecheck plugin."""

import builtins as real_builtins  # Import with an alias to ensure access to original
import inspect
import unittest.mock as mock  # Import with an alias for unittest.mock
from unittest.mock import MagicMock, patch

import pytest

from pytest_fixturecheck import fixturecheck
from pytest_fixturecheck.plugin import (
    PYTEST_ASYNCIO_INSTALLED,
    is_async_fixture,
    pytest_collection_finish,
    pytest_fixture_setup,
)


def test_fixturecheck_decorator_exists():
    """Test that the fixturecheck decorator exists."""
    assert callable(fixturecheck)


@fixturecheck
@pytest.fixture
def simple_fixture():
    """A simple fixture that returns a string."""
    return "test"


def test_fixture_with_fixturecheck(simple_fixture):
    """Test that a fixture with fixturecheck works."""
    assert simple_fixture == "test"


class TestIsAsyncFixture:
    """Tests for the is_async_fixture utility function."""

    def test_regular_function(self):
        """Test with a regular synchronous function."""
        mock_fixturedef = MagicMock(
            spec=["func", "argname", "unittest", "_pytest_asyncio_scope"]
        )

        def sync_func():
            pass

        mock_fixturedef.func = sync_func
        mock_fixturedef.argname = "sync_fixture"
        if hasattr(mock_fixturedef, "unittest"):
            delattr(mock_fixturedef, "unittest")
        if hasattr(mock_fixturedef, "_pytest_asyncio_scope"):
            delattr(mock_fixturedef, "_pytest_asyncio_scope")
        assert not is_async_fixture(mock_fixturedef)

    async def async_func_for_test(self):  # Helper async function
        pass

    def test_async_def_function(self):
        """Test with an async def function."""
        mock_fixturedef = MagicMock()
        mock_fixturedef.func = self.async_func_for_test
        mock_fixturedef.argname = "some_async_fixture"
        assert is_async_fixture(mock_fixturedef)

    def test_fixture_name_starts_with_async(self):
        """Test with a fixture whose name starts with 'async_'."""
        mock_fixturedef = MagicMock()

        def sync_func():
            pass

        mock_fixturedef.func = sync_func
        mock_fixturedef.argname = "async_named_fixture"
        assert is_async_fixture(mock_fixturedef)

    def test_unittest_async_fixture(self):
        """Test with a simulated unittest async fixture."""
        mock_fixturedef = MagicMock()

        def sync_func():
            pass

        mock_fixturedef.func = sync_func
        mock_fixturedef.argname = "unittest_style_fixture"
        mock_unittest_attr = MagicMock()
        mock_unittest_attr.__str__ = MagicMock(
            return_value="<UnittestAsyncFixture something>"
        )
        mock_fixturedef.unittest = mock_unittest_attr
        assert is_async_fixture(mock_fixturedef)

    def test_unittest_non_async_fixture(self):
        """Test with a simulated unittest non-async fixture."""
        mock_fixturedef = MagicMock(
            spec=["func", "argname", "unittest", "_pytest_asyncio_scope"]
        )

        def sync_func():
            pass

        mock_fixturedef.func = sync_func
        mock_fixturedef.argname = "sync_fixture"
        mock_unittest_attr = MagicMock()
        mock_unittest_attr.__str__ = MagicMock(
            return_value="<UnittestFixture something>"
        )
        mock_fixturedef.unittest = mock_unittest_attr
        if hasattr(mock_fixturedef, "_pytest_asyncio_scope"):
            delattr(mock_fixturedef, "_pytest_asyncio_scope")
        assert not is_async_fixture(mock_fixturedef)

    @patch("pytest_fixturecheck.plugin.PYTEST_ASYNCIO_INSTALLED", True)
    def test_pytest_asyncio_installed_with_scope_attr(self):
        """Test with pytest-asyncio installed and _pytest_asyncio_scope attribute present."""
        mock_fixturedef = MagicMock()

        def sync_func():
            pass

        mock_fixturedef.func = sync_func
        mock_fixturedef.argname = "some_fixture"
        mock_fixturedef._pytest_asyncio_scope = "function"
        assert is_async_fixture(mock_fixturedef)

    @patch("pytest_fixturecheck.plugin.PYTEST_ASYNCIO_INSTALLED", True)
    def test_pytest_asyncio_installed_without_scope_attr(self):
        """Test with pytest-asyncio installed but _pytest_asyncio_scope attribute missing."""
        mock_fixturedef = MagicMock()

        def sync_func():
            pass

        mock_fixturedef.func = sync_func
        mock_fixturedef.argname = "another_fixture"
        if hasattr(mock_fixturedef, "_pytest_asyncio_scope"):
            delattr(mock_fixturedef, "_pytest_asyncio_scope")
        assert not is_async_fixture(mock_fixturedef)

    @patch("pytest_fixturecheck.plugin.PYTEST_ASYNCIO_INSTALLED", False)
    def test_pytest_asyncio_not_installed(self):
        """Test when pytest-asyncio is not installed."""
        mock_fixturedef = MagicMock()

        def sync_func():
            pass

        mock_fixturedef.func = sync_func
        mock_fixturedef.argname = "fixture_when_no_asyncio_plugin"
        mock_fixturedef._pytest_asyncio_scope = "function"
        assert not is_async_fixture(mock_fixturedef)

    # This is the correct and final version of this test
    @patch("pytest_fixturecheck.plugin.PYTEST_ASYNCIO_INSTALLED", True)
    @patch("builtins.hasattr", autospec=True)
    def test_pytest_asyncio_installed_with_scope_attr_error(
        self, mock_autospecced_hasattr
    ):
        """Test a scenario where checking for _pytest_asyncio_scope causes an error."""

        class PlainFixtureDefForTest:
            pass

        test_subject_fixture_def = PlainFixtureDefForTest()

        def _a_sync_function_for_test():
            pass

        test_subject_fixture_def.func = _a_sync_function_for_test
        test_subject_fixture_def.argname = "a_regular_fixture_name_for_test"

        def controlled_hasattr_side_effect(obj, attribute_name):
            if obj is test_subject_fixture_def:
                if attribute_name == "unittest":
                    return False
                if attribute_name == "_pytest_asyncio_scope":
                    raise AttributeError(
                        "Deliberate error checking _pytest_asyncio_scope"
                    )
            return mock.DEFAULT

        mock_autospecced_hasattr.side_effect = controlled_hasattr_side_effect
        assert not is_async_fixture(test_subject_fixture_def)


# New test class for pytest_fixture_setup
class TestPytestFixtureSetup:
    """Tests for the pytest_fixture_setup hook."""

    def test_fixture_not_marked(self):
        """Test that nothing happens if the fixture is not marked with _fixturecheck."""
        mock_fixturedef = MagicMock(spec=["func"])
        mock_fixturedef.func = lambda: None  # Plain function
        # Ensure _fixturecheck is not on func or any wrapped versions
        (
            delattr(mock_fixturedef.func, "_fixturecheck")
            if hasattr(mock_fixturedef.func, "_fixturecheck")
            else None
        )
        if hasattr(mock_fixturedef.func, "__wrapped__"):
            current = mock_fixturedef.func.__wrapped__
            while current:
                (
                    delattr(current, "_fixturecheck")
                    if hasattr(current, "_fixturecheck")
                    else None
                )
                current = getattr(current, "__wrapped__", None)

        mock_request = MagicMock()
        mock_request.config = MagicMock()
        # Ensure _fixturecheck_fixtures is not touched if it doesn't exist
        # or not added to if it does and fixture not marked

        pytest_fixture_setup(mock_fixturedef, mock_request)

        assert (
            not hasattr(mock_request.config, "_fixturecheck_fixtures")
            or mock_fixturedef not in mock_request.config._fixturecheck_fixtures
        )
        assert not hasattr(
            mock_fixturedef, "_fixturecheck_skip"
        )  # Should not be marked for skip

    def test_fixture_marked_directly_non_async(self):
        """Test a non-async fixture marked directly with _fixturecheck."""
        mock_fixturedef = MagicMock(name="direct_non_async_fixturedef", spec=["func"])
        mock_fixturedef.func = lambda: None
        mock_fixturedef.func._fixturecheck = True  # Mark the fixture

        mock_request = MagicMock()
        mock_request.config = MagicMock()
        # Simulate _fixturecheck_fixtures not existing initially
        if hasattr(mock_request.config, "_fixturecheck_fixtures"):
            del mock_request.config._fixturecheck_fixtures

        with patch(
            "pytest_fixturecheck.plugin.is_async_fixture", return_value=False
        ) as mock_is_async:
            pytest_fixture_setup(mock_fixturedef, mock_request)
            mock_is_async.assert_called_once_with(mock_fixturedef)

        assert hasattr(mock_request.config, "_fixturecheck_fixtures")
        assert mock_fixturedef in mock_request.config._fixturecheck_fixtures
        assert not hasattr(mock_fixturedef, "_fixturecheck_skip")

    def test_fixture_marked_directly_async(self):
        """Test an async fixture marked directly with _fixturecheck."""
        mock_fixturedef = MagicMock(name="direct_async_fixturedef")
        mock_fixturedef.func = lambda: None
        mock_fixturedef.func._fixturecheck = True  # Mark the fixture

        mock_request = MagicMock()
        mock_request.config = MagicMock()
        # Simulate _fixturecheck_fixtures existing but empty
        mock_request.config._fixturecheck_fixtures = set()

        with patch(
            "pytest_fixturecheck.plugin.is_async_fixture", return_value=True
        ) as mock_is_async:
            pytest_fixture_setup(mock_fixturedef, mock_request)
            mock_is_async.assert_called_once_with(mock_fixturedef)

        assert mock_fixturedef in mock_request.config._fixturecheck_fixtures
        assert hasattr(mock_fixturedef, "_fixturecheck_skip")
        assert mock_fixturedef._fixturecheck_skip is True

    def test_fixture_marked_on_wrapper(self):
        """Test a non-async fixture marked with _fixturecheck on a wrapper."""
        original_func = lambda: None

        wrapper1 = MagicMock(name="wrapper1")
        wrapper1.__wrapped__ = original_func
        # _fixturecheck is NOT on wrapper1

        wrapper2 = MagicMock(name="wrapper2")
        wrapper2.__wrapped__ = wrapper1
        wrapper2._fixturecheck = True  # Mark is on this wrapper

        mock_fixturedef = MagicMock(name="wrapped_fixturedef", spec=["func"])
        mock_fixturedef.func = wrapper2  # func is the outermost wrapper

        mock_request = MagicMock()
        mock_request.config = MagicMock()
        mock_request.config._fixturecheck_fixtures = set()  # Simulate existing set

        with patch(
            "pytest_fixturecheck.plugin.is_async_fixture", return_value=False
        ) as mock_is_async:
            pytest_fixture_setup(mock_fixturedef, mock_request)
            mock_is_async.assert_called_once_with(mock_fixturedef)

        assert mock_fixturedef in mock_request.config._fixturecheck_fixtures
        assert not hasattr(mock_fixturedef, "_fixturecheck_skip")

    def test_fixture_marked_on_deeply_wrapped_original_func(self):
        """Test when _fixturecheck is on the original, deeply wrapped func, but a wrapper is used."""
        original_func = MagicMock(name="original_deep_func")
        original_func._fixturecheck = True  # Mark is on the innermost original function

        wrapper1 = MagicMock(name="deep_wrapper1")
        wrapper1.__wrapped__ = original_func

        wrapper2 = MagicMock(name="deep_wrapper2")
        wrapper2.__wrapped__ = wrapper1
        # Wrapper2 itself is NOT marked, but it will be the fixture_func initially
        # The loop should find _fixturecheck on original_func if current_func becomes original_func.
        # However, the logic is `if getattr(current_func, "_fixturecheck", False): fixture_func = current_func; break`
        # This means it uses the *wrapper* that has _fixturecheck.
        # If the original func has it, but no wrapper does, it will use the original func after the loop.

        mock_fixturedef = MagicMock(name="deeply_wrapped_fixturedef", spec=["func"])
        # If fixturedef.func is wrapper2, and only original_func has _fixturecheck=True:
        # pytest_fixture_setup will iterate: wrapper2 (no _fc) -> wrapper1 (no _fc) -> original_func (has _fc)
        # Then fixture_func becomes original_func for the final check `if getattr(fixture_func, "_fixturecheck", False):`
        mock_fixturedef.func = wrapper2

        mock_request = MagicMock()
        mock_request.config = MagicMock()
        mock_request.config._fixturecheck_fixtures = set()

        with patch(
            "pytest_fixturecheck.plugin.is_async_fixture", return_value=False
        ) as mock_is_async:
            pytest_fixture_setup(mock_fixturedef, mock_request)

        assert mock_fixturedef in mock_request.config._fixturecheck_fixtures
        assert not hasattr(mock_fixturedef, "_fixturecheck_skip")


# New test class for pytest_collection_finish
class TestPytestCollectionFinish:
    """Tests for the pytest_collection_finish hook."""

    def test_no_fixturecheck_fixtures_attribute(self):
        """Test early exit if session.config has no _fixturecheck_fixtures attribute."""
        mock_session = MagicMock()
        mock_session.config = MagicMock()
        # Ensure _fixturecheck_fixtures attribute does not exist
        if hasattr(mock_session.config, "_fixturecheck_fixtures"):
            delattr(mock_session.config, "_fixturecheck_fixtures")

        # We also need to ensure other parts of the function aren't called, e.g. getini
        # So, if getini were called, it would be an error.
        mock_session.config.getini = MagicMock(
            side_effect=AssertionError("getini should not be called")
        )

        pytest_collection_finish(mock_session)
        mock_session.config.getini.assert_not_called()  # Verifies early exit

    def test_empty_fixtures_to_validate(self):
        """Test early exit if _fixturecheck_fixtures is empty."""
        mock_session = MagicMock()
        mock_session.config = MagicMock()
        mock_session.config._fixturecheck_fixtures = set()  # Empty set
        mock_session.config.getini = MagicMock(
            side_effect=AssertionError("getini should not be called")
        )

        pytest_collection_finish(mock_session)
        mock_session.config.getini.assert_not_called()  # Verifies early exit

    @patch("pytest_fixturecheck.plugin.report_fixture_errors")
    @patch("pytest.exit")  # Patching pytest.exit directly
    def test_auto_skip_false_one_failure(self, mock_pytest_exit, mock_report_errors):
        """Test auto_skip=false: pytest.exit is called on validation failure."""
        mock_session = MagicMock()
        mock_session.config = MagicMock()
        mock_session.config.getini = MagicMock(
            return_value="false"
        )  # auto_skip is false

        failing_validator = MagicMock(side_effect=ValueError("Validation failed"))
        mock_fixture_func = MagicMock(
            _validator=failing_validator, _expect_validation_error=False
        )

        # To handle the wrapper logic in pytest_collection_finish correctly:
        # Ensure func does not have __wrapped__ or if it does, configure it appropriately.
        # For simplicity, assume no wrapping here for the validator finding part.
        (
            delattr(mock_fixture_func, "__wrapped__")
            if hasattr(mock_fixture_func, "__wrapped__")
            else None
        )

        mock_fdef = MagicMock(name="failing_fixturedef")
        mock_fdef.func = mock_fixture_func
        # Ensure it's not skipped by unittest/async/etc. flags for this basic validator test
        mock_fdef.configure_mock(
            **{
                "unittest": None,  # Make hasattr(mock_fdef, 'unittest') true but str() won't match async
                "_fixturecheck_skip": False,
            }
        )
        # We also need to control is_async_fixture for this fixturedef

        mock_session.config._fixturecheck_fixtures = {mock_fdef}

        with patch("pytest_fixturecheck.plugin.is_async_fixture", return_value=False):
            # The collection phase validator(fixture_func, True) will be called
            pytest_collection_finish(mock_session)

        mock_report_errors.assert_called_once()
        mock_pytest_exit.assert_called_once_with("Fixture validation failed", 1)

    @patch("pytest_fixturecheck.plugin.report_fixture_errors")
    @patch("pytest_fixturecheck.plugin._mark_dependent_tests_for_skip")
    @patch("pytest.exit")
    def test_auto_skip_true_one_failure(
        self, mock_pytest_exit, mock_mark_skip, mock_report_errors
    ):
        """Test auto_skip=true: _mark_dependent_tests_for_skip is called."""
        mock_session = MagicMock()
        mock_session.config = MagicMock()
        mock_session.config.getini = MagicMock(return_value="true")  # auto_skip is true

        failing_validator = MagicMock(side_effect=ValueError("Validation failed"))
        mock_fixture_func = MagicMock(
            _validator=failing_validator, _expect_validation_error=False
        )
        (
            delattr(mock_fixture_func, "__wrapped__")
            if hasattr(mock_fixture_func, "__wrapped__")
            else None
        )

        mock_fdef = MagicMock(name="failing_fixturedef_for_skip")
        mock_fdef.func = mock_fixture_func
        mock_fdef.configure_mock(
            **{
                "unittest": None,
                "_fixturecheck_skip": False,
            }
        )

        mock_session.config._fixturecheck_fixtures = {mock_fdef}

        with patch("pytest_fixturecheck.plugin.is_async_fixture", return_value=False):
            pytest_collection_finish(mock_session)

        mock_report_errors.assert_called_once()
        mock_mark_skip.assert_called_once()
        # Check that the first argument to _mark_dependent_tests_for_skip is the session
        # and the second is the fixturedef, and third is the error instance.
        # For now, just assert_called_once is fine, can refine later if needed.
        assert mock_mark_skip.call_args[0][0] == mock_session
        assert mock_mark_skip.call_args[0][1] == mock_fdef
        assert isinstance(mock_mark_skip.call_args[0][2], ValueError)

        mock_pytest_exit.assert_not_called()

    # Tests for collection phase validation (validator(fixture_func, True))
    @patch(
        "pytest_fixturecheck.plugin.report_fixture_errors"
    )  # To prevent printing errors
    @patch("pytest.exit")  # To prevent exit in case of unexpected failures
    def test_collection_validation_passes_not_expected_error(
        self, mock_pytest_exit, mock_report_errors
    ):
        """Collection validation: validator passes, error not expected."""
        mock_session = MagicMock()
        mock_session.config = MagicMock()
        mock_session.config.getini = MagicMock(return_value="false")  # auto_skip false

        mock_validator = MagicMock(return_value=None)  # Validator passes
        mock_fixture_func = MagicMock(
            _validator=mock_validator, _expect_validation_error=False
        )
        (
            delattr(mock_fixture_func, "__wrapped__")
            if hasattr(mock_fixture_func, "__wrapped__")
            else None
        )

        mock_fdef = MagicMock(name="coll_pass_not_expected_fdef")
        mock_fdef.func = mock_fixture_func
        mock_fdef.configure_mock(**{"unittest": None, "_fixturecheck_skip": False})
        mock_session.config._fixturecheck_fixtures = {mock_fdef}

        with patch("pytest_fixturecheck.plugin.is_async_fixture", return_value=False):
            pytest_collection_finish(mock_session)

        mock_validator.assert_called_once_with(mock_fixture_func, True)
        # Assert no errors reported for this fixture (failed_fixtures should be empty or not contain this one)
        # This is indirectly checked by mock_report_errors not being called with this specific error
        # or pytest.exit not being called if this was the only fixture.
        # For simplicity, if report_fixture_errors was called, it means some failure was recorded.
        # If it wasn't called, it implies failed_fixtures was empty.
        if mock_report_errors.call_args_list:
            failed_fixtures_arg = mock_report_errors.call_args_list[0][0][0]
            assert not any(fdef[0] == mock_fdef for fdef in failed_fixtures_arg)
        else:
            pass  # No errors reported, which is correct.
        mock_pytest_exit.assert_not_called()

    @patch("pytest_fixturecheck.plugin.report_fixture_errors")
    @patch("pytest.exit")
    def test_collection_validation_passes_expected_error(
        self, mock_pytest_exit, mock_report_errors
    ):
        """Collection validation: validator passes, error WAS expected (this is a failure)."""
        mock_session = MagicMock()
        mock_session.config = MagicMock()
        mock_session.config.getini = MagicMock(return_value="false")

        mock_validator = MagicMock(return_value=None)
        mock_fixture_func = MagicMock(
            _validator=mock_validator, _expect_validation_error=True
        )  # Error expected
        (
            delattr(mock_fixture_func, "__wrapped__")
            if hasattr(mock_fixture_func, "__wrapped__")
            else None
        )

        mock_fdef = MagicMock(name="coll_pass_expected_fdef")
        mock_fdef.func = mock_fixture_func
        mock_fdef.configure_mock(**{"unittest": None, "_fixturecheck_skip": False})
        mock_session.config._fixturecheck_fixtures = {mock_fdef}

        with patch("pytest_fixturecheck.plugin.is_async_fixture", return_value=False):
            pytest_collection_finish(mock_session)

        mock_validator.assert_called_once_with(mock_fixture_func, True)
        mock_report_errors.assert_called_once()
        failed_fixture_arg = mock_report_errors.call_args[0][0][
            0
        ]  # (fixturedef, error, traceback_str)
        assert failed_fixture_arg[0] == mock_fdef
        assert isinstance(failed_fixture_arg[1], AssertionError)
        assert "Expected validation error but none occurred" in str(
            failed_fixture_arg[1]
        )
        mock_pytest_exit.assert_called_once()  # Because a failure was recorded and auto_skip=false

    @patch("pytest_fixturecheck.plugin.report_fixture_errors")
    @patch("pytest.exit")
    def test_collection_validation_fails_expected_error(
        self, mock_pytest_exit, mock_report_errors
    ):
        """Collection validation: validator fails, error WAS expected (success)."""
        mock_session = MagicMock()
        mock_session.config = MagicMock()
        mock_session.config.getini = MagicMock(return_value="false")

        mock_validator = MagicMock(side_effect=ValueError("Deliberate validation fail"))
        mock_fixture_func = MagicMock(
            _validator=mock_validator, _expect_validation_error=True
        )  # Error expected
        (
            delattr(mock_fixture_func, "__wrapped__")
            if hasattr(mock_fixture_func, "__wrapped__")
            else None
        )

        mock_fdef = MagicMock(name="coll_fail_expected_fdef")
        mock_fdef.func = mock_fixture_func
        mock_fdef.configure_mock(**{"unittest": None, "_fixturecheck_skip": False})
        mock_session.config._fixturecheck_fixtures = {mock_fdef}

        with patch("pytest_fixturecheck.plugin.is_async_fixture", return_value=False):
            pytest_collection_finish(mock_session)

        mock_validator.assert_called_once_with(mock_fixture_func, True)
        # This case is a success, so no error should be reported for this fixture.
        # If mock_report_errors is called, it means some other fixture failed or logic is wrong.
        # Assuming this is the only fixture, mock_report_errors should not be called.
        if mock_report_errors.call_args_list:
            # Check if this specific fixture caused an error report (it shouldn't have)
            errors_for_this_fixture = [
                f_def
                for f_def, err, tb_str in mock_report_errors.call_args_list[0][0][0]
                if f_def == mock_fdef
            ]
            assert (
                not errors_for_this_fixture
            ), "Failure was reported for a fixture that expected an error which occurred."
        else:
            pass  # No errors reported at all, correct.
        mock_pytest_exit.assert_not_called()

    @patch("pytest_fixturecheck.plugin.report_fixture_errors")
    @patch("pytest.exit")
    def test_collection_validation_fails_not_expected_error(
        self, mock_pytest_exit, mock_report_errors
    ):
        """Collection validation: validator fails, error NOT expected (failure)."""
        mock_session = MagicMock()
        mock_session.config = MagicMock()
        mock_session.config.getini = MagicMock(return_value="false")

        original_error = ValueError("Deliberate validation fail")
        mock_validator = MagicMock(side_effect=original_error)
        mock_fixture_func = MagicMock(
            _validator=mock_validator, _expect_validation_error=False
        )  # Error NOT expected
        (
            delattr(mock_fixture_func, "__wrapped__")
            if hasattr(mock_fixture_func, "__wrapped__")
            else None
        )

        mock_fdef = MagicMock(name="coll_fail_not_expected_fdef")
        mock_fdef.func = mock_fixture_func
        mock_fdef.configure_mock(**{"unittest": None, "_fixturecheck_skip": False})
        mock_session.config._fixturecheck_fixtures = {mock_fdef}

        with patch("pytest_fixturecheck.plugin.is_async_fixture", return_value=False):
            pytest_collection_finish(mock_session)

        mock_validator.assert_called_once_with(mock_fixture_func, True)
        mock_report_errors.assert_called_once()
        failed_fixture_arg = mock_report_errors.call_args[0][0][0]
        assert failed_fixture_arg[0] == mock_fdef
        assert (
            failed_fixture_arg[1] is original_error
        )  # Check it's the exact error instance
        mock_pytest_exit.assert_called_once()

    # Tests for skip conditions before fixture execution
    def test_skip_execution_if_unittest_fixture(self):
        """Test that fixture execution is skipped if it's a unittest fixture."""
        mock_session = MagicMock()
        mock_session.config = MagicMock()
        mock_session.config.getini = MagicMock(return_value="false")

        mock_validator = MagicMock()  # Validator exists
        mock_fixture_func = MagicMock(
            _validator=mock_validator, _expect_validation_error=False
        )
        (
            delattr(mock_fixture_func, "__wrapped__")
            if hasattr(mock_fixture_func, "__wrapped__")
            else None
        )

        mock_fdef = MagicMock(name="unittest_fdef")
        mock_fdef.func = mock_fixture_func
        # Configure to be a unittest fixture. str(None) won't contain "async" for is_async_fixture check.
        mock_fdef.configure_mock(unittest=True, _fixturecheck_skip=False)
        mock_fdef.execute = MagicMock(
            side_effect=AssertionError("fixturedef.execute should not be called")
        )

        mock_session.config._fixturecheck_fixtures = {mock_fdef}

        # is_async_fixture should be false for this fixturedef to isolate the unittest check
        with patch("pytest_fixturecheck.plugin.is_async_fixture", return_value=False):
            pytest_collection_finish(mock_session)

        mock_fdef.execute.assert_not_called()
        mock_validator.assert_called_once_with(
            mock_fixture_func, True
        )  # Collection validation still runs

    def test_skip_execution_if_fixturecheck_skip_true(self):
        """Test that fixture execution is skipped if _fixturecheck_skip is True."""
        mock_session = MagicMock()
        mock_session.config = MagicMock()
        mock_session.config.getini = MagicMock(return_value="false")

        mock_validator = MagicMock()
        mock_fixture_func = MagicMock(
            _validator=mock_validator, _expect_validation_error=False
        )
        (
            delattr(mock_fixture_func, "__wrapped__")
            if hasattr(mock_fixture_func, "__wrapped__")
            else None
        )

        mock_fdef = MagicMock(name="skip_true_fdef")
        mock_fdef.func = mock_fixture_func
        mock_fdef.configure_mock(_fixturecheck_skip=True)  # Explicitly set to skip
        # Ensure unittest flag is not the cause of skipping
        delattr(mock_fdef, "unittest") if hasattr(mock_fdef, "unittest") else None
        mock_fdef.execute = MagicMock(
            side_effect=AssertionError("fixturedef.execute should not be called")
        )

        mock_session.config._fixturecheck_fixtures = {mock_fdef}

        with patch("pytest_fixturecheck.plugin.is_async_fixture", return_value=False):
            pytest_collection_finish(mock_session)

        mock_fdef.execute.assert_not_called()
        mock_validator.assert_called_once_with(
            mock_fixture_func, True
        )  # Collection validation still runs

    def test_skip_execution_if_is_async_fixture_true(self):
        """Test that fixture execution is skipped if is_async_fixture is True."""
        mock_session = MagicMock()
        mock_session.config = MagicMock()
        mock_session.config.getini = MagicMock(return_value="false")

        mock_validator = MagicMock()
        mock_fixture_func = MagicMock(
            _validator=mock_validator, _expect_validation_error=False
        )
        (
            delattr(mock_fixture_func, "__wrapped__")
            if hasattr(mock_fixture_func, "__wrapped__")
            else None
        )

        mock_fdef = MagicMock(name="async_fdef_to_skip_execution")
        mock_fdef.func = mock_fixture_func
        # Ensure other skip flags are not the cause
        delattr(mock_fdef, "unittest") if hasattr(mock_fdef, "unittest") else None
        mock_fdef.configure_mock(_fixturecheck_skip=False)
        mock_fdef.execute = MagicMock(
            side_effect=AssertionError("fixturedef.execute should not be called")
        )

        mock_session.config._fixturecheck_fixtures = {mock_fdef}

        with patch(
            "pytest_fixturecheck.plugin.is_async_fixture", return_value=True
        ) as mock_is_async:
            pytest_collection_finish(mock_session)
            mock_is_async.assert_called_with(
                mock_fdef
            )  # Called twice: once in skip check, once in pytest_fixture_setup mock if not careful
            # For this test, it will be called for the skip condition.

        mock_fdef.execute.assert_not_called()
        mock_validator.assert_called_once_with(
            mock_fixture_func, True
        )  # Collection validation still runs

    # Tests for fixture execution and result validation phase
    @patch("pytest_fixturecheck.plugin.report_fixture_errors")
    @patch("pytest.exit")
    @patch("pytest_fixturecheck.plugin.is_coroutine")
    def test_execution_returns_coroutine(
        self, mock_is_coroutine, mock_pytest_exit, mock_report_errors
    ):
        """Test if fixture.execute() returns a coroutine, it's skipped for exec validation."""
        mock_session = MagicMock()
        mock_session.config = MagicMock()
        mock_session.config.getini = MagicMock(return_value="false")
        mock_session._fixturemanager = MagicMock()
        mock_session._fixturemanager.getfixturerequest.return_value = MagicMock(
            name="mock_exec_request"
        )

        mock_validator = MagicMock(name="exec_validator_for_coroutine_test")
        mock_fixture_func = MagicMock(
            _validator=mock_validator, _expect_validation_error=False
        )
        (
            delattr(mock_fixture_func, "__wrapped__")
            if hasattr(mock_fixture_func, "__wrapped__")
            else None
        )

        mock_fdef = MagicMock(name="coroutine_result_fdef")
        mock_fdef.func = mock_fixture_func
        if hasattr(mock_fdef, "unittest"):  # Ensure unittest is not set
            delattr(mock_fdef, "unittest")
        mock_fdef._fixturecheck_skip = False

        coroutine_obj = MagicMock(
            name="coroutine_object"
        )  # Simulate a coroutine object
        mock_fdef.execute = MagicMock(return_value=coroutine_obj)
        mock_is_coroutine.return_value = True

        mock_session.config._fixturecheck_fixtures = {mock_fdef}

        with patch("pytest_fixturecheck.plugin.is_async_fixture", return_value=False):
            pytest_collection_finish(mock_session)

        mock_fdef.execute.assert_called_once()
        mock_is_coroutine.assert_called_once_with(coroutine_obj)
        assert mock_fdef._fixturecheck_skip is True
        # Validator should NOT be called with (result, False) for execution phase
        # It was called with (fixture_func, True) for collection phase.
        mock_validator.assert_called_once_with(mock_fixture_func, True)
        mock_report_errors.assert_not_called()  # No failures expected
        mock_pytest_exit.assert_not_called()

    # Helper method for setting up execution phase tests
    def _setup_execution_phase_test(
        self,
        session_mock,
        validator_behavior,
        expect_error_flag,
        fixture_exec_behavior=None,
        auto_skip_str="false",
    ):
        session_mock.config.getini.return_value = auto_skip_str
        session_mock._fixturemanager = MagicMock()
        session_mock._fixturemanager.getfixturerequest.return_value = MagicMock(
            name="mock_exec_request"
        )
        session_mock._fixturemanager.getfixturerequest.side_effect = None

        validator_mock_for_fdef_attr = None
        returned_validator_mock_for_assertions = MagicMock(
            name="exec_phase_validator_assertion_obj"
        )

        if validator_behavior == "VALIDATOR_IS_NONE":
            validator_mock_for_fdef_attr = None
        elif isinstance(validator_behavior, Exception):
            returned_validator_mock_for_assertions.side_effect = validator_behavior
            validator_mock_for_fdef_attr = returned_validator_mock_for_assertions
        else:
            returned_validator_mock_for_assertions.return_value = validator_behavior
            validator_mock_for_fdef_attr = returned_validator_mock_for_assertions

        fixture_func_mock = MagicMock(
            _validator=validator_mock_for_fdef_attr,
            _expect_validation_error=expect_error_flag,
        )
        (
            delattr(fixture_func_mock, "__wrapped__")
            if hasattr(fixture_func_mock, "__wrapped__")
            else None
        )
        if hasattr(
            fixture_func_mock, "_error_message_match"
        ):  # Ensure clean state for this attr
            delattr(fixture_func_mock, "_error_message_match")

        fdef_mock = MagicMock(name="exec_phase_fdef")
        fdef_mock.func = fixture_func_mock

        if hasattr(
            fdef_mock, "unittest"
        ):  # Ensure unittest attr is not present by default
            delattr(fdef_mock, "unittest")
        fdef_mock._fixturecheck_skip = False

        actual_fixture_result_for_assertion = (
            None  # Default if execute raises or returns None
        )

        if isinstance(fixture_exec_behavior, Exception):
            fdef_mock.execute = MagicMock(side_effect=fixture_exec_behavior)
            # actual_fixture_result_for_assertion remains None
        else:  # Covers fixture_exec_behavior being a value (e.g. string) or None
            fdef_mock.execute = MagicMock(return_value=fixture_exec_behavior)
            actual_fixture_result_for_assertion = fixture_exec_behavior

        session_mock.config._fixturecheck_fixtures = {fdef_mock}
        return (
            fdef_mock,
            returned_validator_mock_for_assertions,
            fixture_func_mock,
            actual_fixture_result_for_assertion,
        )

    @patch("pytest_fixturecheck.plugin.report_fixture_errors")
    @patch("pytest.exit")
    @patch("pytest_fixturecheck.plugin.is_coroutine", return_value=False)
    def test_exec_validation_passes_not_expected(
        self, mock_is_coro, mock_py_exit, mock_rep_err
    ):
        """Exec validation: validator passes, error NOT expected."""
        mock_session = MagicMock()
        mock_session.config = MagicMock()
        # Explicitly pass a non-None fixture_exec_behavior for validator to run on result
        fdef, validator, ff_mock, f_res = self._setup_execution_phase_test(
            mock_session, None, False, fixture_exec_behavior="test_value"
        )

        with patch("pytest_fixturecheck.plugin.is_async_fixture", return_value=False):
            pytest_collection_finish(mock_session)

        validator.assert_any_call(ff_mock, True)  # Collection phase
        validator.assert_any_call(f_res, False)  # Execution phase
        mock_rep_err.assert_not_called()
        mock_py_exit.assert_not_called()

    @patch("pytest_fixturecheck.plugin.report_fixture_errors")
    @patch("pytest.exit")
    @patch("pytest_fixturecheck.plugin.is_coroutine", return_value=False)
    def test_exec_validation_passes_expected_error(
        self, mock_is_coro, mock_py_exit, mock_rep_err
    ):
        """Exec validation: validator passes, error WAS expected (failure)."""
        mock_session = MagicMock()
        mock_session.config = MagicMock()
        fdef, validator, ff_mock, f_res = self._setup_execution_phase_test(
            mock_session, None, True, fixture_exec_behavior="test_value"
        )

        with patch("pytest_fixturecheck.plugin.is_async_fixture", return_value=False):
            pytest_collection_finish(mock_session)

        validator.assert_any_call(ff_mock, True)  # Collection validator (passes)
        validator.assert_any_call(f_res, False)  # Execution validator (passes)

        mock_rep_err.assert_called_once()

        # We expect two errors to be appended because expect_error_flag is True
        # and both collection and execution validators pass.
        # Check that at least one of them is the execution phase error.
        reported_errors_list = mock_rep_err.call_args[0][0]

        found_execution_phase_error = False
        found_collection_phase_error = False
        # Ensure reported_errors_list is not empty before iterating
        assert (
            reported_errors_list
        ), "report_fixture_errors was called with an empty list"
        for reported_fdef, err, tb_str in reported_errors_list:
            if reported_fdef == fdef and isinstance(err, AssertionError):
                if "execution phase" in str(err):
                    found_execution_phase_error = True
                if "collection phase" in str(err):
                    found_collection_phase_error = True

        assert (
            found_execution_phase_error
        ), "Execution phase 'expected error but none occurred' not reported."
        assert (
            found_collection_phase_error
        ), "Collection phase 'expected error but none occurred' not reported."
        mock_py_exit.assert_called_once()  # Because errors were reported and auto_skip=false

    @patch("pytest_fixturecheck.plugin.report_fixture_errors")
    @patch("pytest.exit")
    @patch("pytest_fixturecheck.plugin.is_coroutine", return_value=False)
    def test_exec_validation_fails_expected_error(
        self, mock_is_coro, mock_py_exit, mock_rep_err
    ):
        """Exec validation: validator fails, error WAS expected (success)."""
        mock_session = MagicMock()
        mock_session.config = MagicMock()
        val_error = ValueError("Deliberate exec validation fail")
        # Collection phase validator (from val_error) should also fail, expect_error_flag is True.
        # This means collection phase will pass (expected error occurred), and exec phase validator will run.
        # Correction: If collection phase validator fails & error is expected, plugin continues to *next fixture*.
        # So execution phase for *this* fixture is skipped.
        fdef, validator, ff_mock, f_res = self._setup_execution_phase_test(
            mock_session, val_error, True, fixture_exec_behavior="test_value"
        )

        with patch("pytest_fixturecheck.plugin.is_async_fixture", return_value=False):
            pytest_collection_finish(mock_session)

        validator.assert_called_once_with(
            ff_mock, True
        )  # Collection validator called and raises val_error
        fdef.execute.assert_not_called()  # Execution not reached
        # Execution phase validator not called
        assert validator.call_count == 1

        mock_rep_err.assert_not_called()  # Because the collection error was expected
        mock_py_exit.assert_not_called()

    @patch("pytest_fixturecheck.plugin.report_fixture_errors")
    @patch("pytest.exit")
    @patch("pytest_fixturecheck.plugin.is_coroutine", return_value=False)
    def test_exec_validation_fails_not_expected_error(
        self, mock_is_coro, mock_py_exit, mock_rep_err
    ):
        """Exec validation: validator fails, error NOT expected (failure)."""
        mock_session = MagicMock()
        mock_session.config = MagicMock()
        val_error = ValueError("Deliberate exec validation fail")
        # Collection phase validator (from val_error) will fail. Error is NOT expected.
        # Plugin should record this failure and continue to the next fixture.
        # Execution phase for *this* fixture is skipped.
        fdef, validator, ff_mock, f_res = self._setup_execution_phase_test(
            mock_session, val_error, False, fixture_exec_behavior="test_value"
        )

        with patch("pytest_fixturecheck.plugin.is_async_fixture", return_value=False):
            pytest_collection_finish(mock_session)

        validator.assert_called_once_with(
            ff_mock, True
        )  # Collection validator called and raises val_error
        fdef.execute.assert_not_called()  # Execution not reached
        # Execution phase validator not called
        assert validator.call_count == 1

        mock_rep_err.assert_called_once()
        failed_arg_tuple = mock_rep_err.call_args[0][0][0]
        assert failed_arg_tuple[0] == fdef
        assert failed_arg_tuple[1] is val_error  # The error from collection phase
        mock_py_exit.assert_called_once()  # Because auto_skip=false

        failed_arg = mock_rep_err.call_args[0][0][0]
        assert failed_arg[0] == fdef and failed_arg[1] is val_error
        mock_py_exit.assert_called_once()

    # --- Tests for fixture.execute() failures ---

    @patch("pytest_fixturecheck.plugin.report_fixture_errors")
    @patch("pytest.exit")
    @patch("pytest_fixturecheck.plugin.is_coroutine", return_value=False)
    def test_exec_execute_fails_not_expected(
        self, mock_is_coro, mock_py_exit, mock_rep_err
    ):
        """Test exec phase: fixture.execute() fails, error was NOT expected."""
        mock_session = MagicMock()
        mock_session.config = MagicMock()
        exec_error = RuntimeError("Fixture execution failed")

        fdef, validator_assertion_obj, ff_mock, _ = self._setup_execution_phase_test(
            mock_session,
            None,
            False,
            fixture_exec_behavior=exec_error,
            auto_skip_str="false",
        )

        with patch("pytest_fixturecheck.plugin.is_async_fixture", return_value=False):
            pytest_collection_finish(mock_session)

        validator_assertion_obj.assert_called_once_with(
            ff_mock, True
        )  # Collection validator runs
        fdef.execute.assert_called_once()  # execute was called
        # Execution phase validator should not be called because execute failed before it
        assert validator_assertion_obj.call_count == 1

        mock_rep_err.assert_called_once()
        failed_arg_tuple = mock_rep_err.call_args[0][0][
            0
        ]  # failed_fixtures is a list of (fdef, err, tb_str)
        assert failed_arg_tuple[0] == fdef
        assert failed_arg_tuple[1] is exec_error  # Error from execute()
        mock_py_exit.assert_called_once_with("Fixture validation failed", 1)

    @patch("pytest_fixturecheck.plugin.report_fixture_errors")
    @patch("pytest_fixturecheck.plugin._mark_dependent_tests_for_skip")
    @patch("pytest.exit")
    @patch("pytest_fixturecheck.plugin.is_coroutine", return_value=False)
    def test_exec_execute_fails_not_expected_autoskip(
        self, mock_is_coro, mock_py_exit, mock_mark_skip, mock_rep_err
    ):
        """Test exec phase: fixture.execute() fails, error NOT expected, auto_skip=True."""
        mock_session = MagicMock()
        mock_session.config = MagicMock()
        exec_error = RuntimeError("Fixture execution failed for autoskip")

        fdef, validator_assertion_obj, ff_mock, _ = self._setup_execution_phase_test(
            mock_session,
            None,
            False,
            fixture_exec_behavior=exec_error,
            auto_skip_str="true",
        )

        with patch("pytest_fixturecheck.plugin.is_async_fixture", return_value=False):
            pytest_collection_finish(mock_session)

        validator_assertion_obj.assert_called_once_with(ff_mock, True)
        fdef.execute.assert_called_once()
        assert validator_assertion_obj.call_count == 1

        mock_rep_err.assert_called_once()
        failed_arg_tuple = mock_rep_err.call_args[0][0][0]
        assert failed_arg_tuple[0] == fdef and failed_arg_tuple[1] is exec_error

        mock_mark_skip.assert_called_once()
        assert mock_mark_skip.call_args[0][0] == mock_session
        assert mock_mark_skip.call_args[0][1] == fdef
        assert mock_mark_skip.call_args[0][2] is exec_error
        mock_py_exit.assert_not_called()

    @patch("pytest_fixturecheck.plugin.report_fixture_errors")
    @patch("pytest.exit")
    @patch("pytest_fixturecheck.plugin.is_coroutine", return_value=False)
    def test_exec_execute_fails_expected(
        self, mock_is_coro, mock_py_exit, mock_rep_err
    ):
        """Test exec phase: fixture.execute() fails, error WAS expected."""
        mock_session = MagicMock()
        mock_session.config = MagicMock()
        exec_error = RuntimeError("Fixture execution failed as expected")
        collection_error = ValueError(
            "Collection error also, as expect_error_flag is True"
        )

        fdef, validator_assertion_obj, ff_mock, _ = self._setup_execution_phase_test(
            mock_session,
            validator_behavior=collection_error,  # Collection validator fails
            expect_error_flag=True,  # Error is expected
            fixture_exec_behavior=exec_error,  # Execution also configured to fail
        )

        with patch("pytest_fixturecheck.plugin.is_async_fixture", return_value=False):
            pytest_collection_finish(mock_session)

        # Collection validator runs and fails, expect_error_flag is True, so this is a pass for collection.
        validator_assertion_obj.assert_called_once_with(ff_mock, True)
        # Execution phase (fdef.execute) should not be reached because collection phase failed (as expected) and continued.
        # Actually, the plugin logic is: if collection fails & expected, it `continue`s to *next fixturedef*.
        # So, execute() for *this* fixturedef is not called.
        fdef.execute.assert_not_called()
        assert validator_assertion_obj.call_count == 1

        mock_rep_err.assert_not_called()
        mock_py_exit.assert_not_called()

    @patch("pytest_fixturecheck.plugin.report_fixture_errors")
    @patch("pytest.exit")
    @patch("pytest_fixturecheck.plugin.is_coroutine", return_value=False)
    def test_exec_execute_fails_async_error_type(
        self, mock_is_coro, mock_py_exit, mock_rep_err
    ):
        """Test exec phase: fixture.execute() fails with an async-like error message."""
        mock_session = MagicMock()
        mock_session.config = MagicMock()
        async_exec_error = RuntimeError("Something related to asyncio broke")

        fdef, validator_assertion_obj, ff_mock, _ = self._setup_execution_phase_test(
            mock_session, None, False, fixture_exec_behavior=async_exec_error
        )

        with patch("pytest_fixturecheck.plugin.is_async_fixture", return_value=False):
            pytest_collection_finish(mock_session)

        validator_assertion_obj.assert_called_once_with(
            ff_mock, True
        )  # Collection validator
        fdef.execute.assert_called_once()
        assert validator_assertion_obj.call_count == 1  # Execution validator not called

        assert hasattr(fdef, "_fixturecheck_skip")
        assert (
            fdef._fixturecheck_skip is True
        )  # Should be marked for skip due to async error type

        mock_rep_err.assert_not_called()
        mock_py_exit.assert_not_called()
        mock_is_coro.assert_not_called()  # is_coroutine is on the *result*, execute didn't return a result

    # --- Tests for getfixturerequest() failures ---

    @patch("pytest_fixturecheck.plugin.report_fixture_errors")
    @patch("pytest.exit")
    # No need to patch is_coroutine or is_async_fixture as we fail before execute
    def test_exec_getfixturerequest_fails_not_expected(
        self, mock_py_exit, mock_rep_err
    ):
        """Test exec phase: getfixturerequest() fails, error was NOT expected."""
        mock_session = MagicMock()
        mock_session.config = MagicMock()
        get_request_error = ValueError("Failed to get fixture request")

        # Setup basic mocks using the helper, then override getfixturerequest
        fdef, validator_assertion_obj, ff_mock, _ = self._setup_execution_phase_test(
            mock_session,
            None,
            False,
            auto_skip_str="false",  # validator passes, error not expected
        )
        mock_session._fixturemanager.getfixturerequest.side_effect = get_request_error

        # is_async_fixture will be called for the initial skip checks for execution phase
        with patch("pytest_fixturecheck.plugin.is_async_fixture", return_value=False):
            pytest_collection_finish(mock_session)

        validator_assertion_obj.assert_called_once_with(
            ff_mock, True
        )  # Collection validator runs
        mock_session._fixturemanager.getfixturerequest.assert_called_once_with(
            mock_session
        )
        fdef.execute.assert_not_called()  # Execute should not be reached
        # Validator should only have been called for collection phase
        assert validator_assertion_obj.call_count == 1

        mock_rep_err.assert_called_once()
        failed_arg_tuple = mock_rep_err.call_args[0][0][0]
        assert failed_arg_tuple[0] == fdef
        assert failed_arg_tuple[1] is get_request_error
        mock_py_exit.assert_called_once_with("Fixture validation failed", 1)

    @patch("pytest_fixturecheck.plugin.report_fixture_errors")
    @patch("pytest_fixturecheck.plugin._mark_dependent_tests_for_skip")
    @patch("pytest.exit")
    def test_exec_getfixturerequest_fails_not_expected_autoskip(
        self, mock_py_exit, mock_mark_skip, mock_rep_err
    ):
        """Test exec phase: getfixturerequest() fails, not expected, auto_skip=True."""
        mock_session = MagicMock()
        mock_session.config = MagicMock()
        get_request_error = ValueError("Failed to get fixture request for autoskip")

        fdef, validator_assertion_obj, ff_mock, _ = self._setup_execution_phase_test(
            mock_session, None, False, auto_skip_str="true"
        )
        mock_session._fixturemanager.getfixturerequest.side_effect = get_request_error

        with patch("pytest_fixturecheck.plugin.is_async_fixture", return_value=False):
            pytest_collection_finish(mock_session)

        validator_assertion_obj.assert_called_once_with(ff_mock, True)
        mock_session._fixturemanager.getfixturerequest.assert_called_once_with(
            mock_session
        )
        fdef.execute.assert_not_called()
        assert validator_assertion_obj.call_count == 1

        mock_rep_err.assert_called_once()
        failed_arg_tuple = mock_rep_err.call_args[0][0][0]
        assert failed_arg_tuple[0] == fdef and failed_arg_tuple[1] is get_request_error

        mock_mark_skip.assert_called_once()
        assert mock_mark_skip.call_args[0][0] == mock_session
        assert mock_mark_skip.call_args[0][1] == fdef
        assert mock_mark_skip.call_args[0][2] is get_request_error
        mock_py_exit.assert_not_called()

    @patch("pytest_fixturecheck.plugin.report_fixture_errors")
    @patch("pytest.exit")
    def test_exec_getfixturerequest_fails_expected(self, mock_py_exit, mock_rep_err):
        """Test exec phase: getfixturerequest() fails, error WAS expected."""
        mock_session = MagicMock()
        mock_session.config = MagicMock()
        get_request_error = ValueError("getfixturerequest failed as expected")
        collection_error = ValueError(
            "Collection error also, as expect_error_flag is True"
        )

        fdef, validator_assertion_obj, ff_mock, _ = self._setup_execution_phase_test(
            mock_session,
            validator_behavior=collection_error,  # Collection validator fails
            expect_error_flag=True,  # Error is expected
            auto_skip_str="false",  # auto_skip doesn't matter here as no error reported
        )
        # Execution error (get_request_error) is configured by overriding the mock post-setup:
        mock_session._fixturemanager.getfixturerequest.side_effect = get_request_error

        with patch("pytest_fixturecheck.plugin.is_async_fixture", return_value=False):
            pytest_collection_finish(mock_session)

        validator_assertion_obj.assert_called_once_with(
            ff_mock, True
        )  # Collection validator
        # getfixturerequest is not called because collection phase failed as expected and continued to next fixture.
        mock_session._fixturemanager.getfixturerequest.assert_not_called()
        fdef.execute.assert_not_called()
        assert validator_assertion_obj.call_count == 1

        mock_rep_err.assert_not_called()
        mock_py_exit.assert_not_called()

    # --- Tests for validator is None or result is None during execution phase ---

    @patch("pytest_fixturecheck.plugin.report_fixture_errors")
    @patch("pytest.exit")
    @patch("pytest_fixturecheck.plugin.is_coroutine", return_value=False)
    def test_exec_validator_is_none_not_expected(
        self, mock_is_coro, mock_py_exit, mock_rep_err
    ):
        """Exec phase: fixture_func._validator is None, error NOT expected."""
        mock_session = MagicMock()
        mock_session.config = MagicMock()

        # validator_behavior="VALIDATOR_IS_NONE", expect_error_flag=False
        # fixture_exec_behavior=None means execute() returns "fixture_result_value" (default for non-exception)
        fdef, validator_assertion_obj, ff_mock, f_res = (
            self._setup_execution_phase_test(
                mock_session,
                "VALIDATOR_IS_NONE",
                False,
                fixture_exec_behavior=None,
                auto_skip_str="false",
            )
        )
        # ff_mock._validator should be None due to helper logic

        with patch("pytest_fixturecheck.plugin.is_async_fixture", return_value=False):
            pytest_collection_finish(mock_session)

        fdef.execute.assert_called_once()  # Execute should run
        # Validator should not be called for collection (as ff_mock._validator is None)
        # nor for execution (as validator is None there too)
        validator_assertion_obj.assert_not_called()
        mock_rep_err.assert_not_called()
        mock_py_exit.assert_not_called()

    @patch("pytest_fixturecheck.plugin.report_fixture_errors")
    @patch("pytest.exit")
    @patch("pytest_fixturecheck.plugin.is_coroutine", return_value=False)
    def test_exec_validator_is_none_expected_error(
        self, mock_is_coro, mock_py_exit, mock_rep_err
    ):
        """Exec phase: fixture_func._validator is None, error WAS expected."""
        mock_session = MagicMock()
        mock_session.config = MagicMock()

        fdef, validator_assertion_obj, ff_mock, f_res = (
            self._setup_execution_phase_test(
                mock_session,
                "VALIDATOR_IS_NONE",
                True,
                fixture_exec_behavior=None,
                auto_skip_str="false",
            )
        )

        with patch("pytest_fixturecheck.plugin.is_async_fixture", return_value=False):
            pytest_collection_finish(mock_session)

        fdef.execute.assert_called_once()
        validator_assertion_obj.assert_not_called()
        # Plugin doesn't report "expected error but none occurred" if validator is None for exec phase
        mock_rep_err.assert_not_called()
        mock_py_exit.assert_not_called()

    @patch("pytest_fixturecheck.plugin.report_fixture_errors")
    @patch("pytest.exit")
    @patch("pytest_fixturecheck.plugin.is_coroutine", return_value=False)
    def test_exec_result_is_none_not_expected(
        self, mock_is_coro, mock_py_exit, mock_rep_err
    ):
        """Exec phase: fixture.execute() returns None, error NOT expected."""
        mock_session = MagicMock()
        mock_session.config = MagicMock()

        # fixture_exec_behavior=None results in execute() returning None (explicitly)
        # validator_behavior=None means validator mock passes when called.
        fdef, validator_assertion_obj, ff_mock, f_res = (
            self._setup_execution_phase_test(
                mock_session,
                None,
                False,
                fixture_exec_behavior=None,
                auto_skip_str="false",
            )
        )
        assert f_res is None  # Ensure execute() is configured to return None

        with patch("pytest_fixturecheck.plugin.is_async_fixture", return_value=False):
            pytest_collection_finish(mock_session)

        fdef.execute.assert_called_once()
        validator_assertion_obj.assert_called_once_with(
            ff_mock, True
        )  # Collection validator runs
        # Execution validator not called because result is None
        assert validator_assertion_obj.call_count == 1
        mock_rep_err.assert_not_called()
        mock_py_exit.assert_not_called()

    @patch("pytest_fixturecheck.plugin.report_fixture_errors")
    @patch("pytest.exit")
    @patch("pytest_fixturecheck.plugin.is_coroutine", return_value=False)
    def test_exec_result_is_none_expected_error(
        self, mock_is_coro, mock_py_exit, mock_rep_err
    ):
        """Exec phase: fixture.execute() returns None, error WAS expected."""
        mock_session = MagicMock()
        mock_session.config = MagicMock()

        # If error is expected, and collection validator passes, then an error is reported for collection phase.
        # Execution phase (result is None) will then be skipped for this specific error reporting logic.
        fdef, validator_assertion_obj, ff_mock, f_res = (
            self._setup_execution_phase_test(
                mock_session,
                None,
                True,
                fixture_exec_behavior=None,
                auto_skip_str="false",
            )
        )
        assert f_res is None

        with patch("pytest_fixturecheck.plugin.is_async_fixture", return_value=False):
            pytest_collection_finish(mock_session)

        fdef.execute.assert_called_once()
        validator_assertion_obj.assert_called_once_with(
            ff_mock, True
        )  # Collection validator
        # Execution validator not called as result is None
        assert validator_assertion_obj.call_count == 1

        # Error *is* reported due to collection phase: validator passed, but error was expected.
        mock_rep_err.assert_called_once()
        failed_arg_tuple = mock_rep_err.call_args[0][0][0]
        assert failed_arg_tuple[0] == fdef
        assert isinstance(failed_arg_tuple[1], AssertionError)
        assert (
            "Expected validation error but none occurred during collection phase"
            in str(failed_arg_tuple[1])
        )
        mock_py_exit.assert_called_once()  # Because auto_skip is false and error reported

    # --- Tests for execution phase with wrapped fixtures ---

    @patch("pytest_fixturecheck.plugin.report_fixture_errors")
    @patch("pytest.exit")
    def test_collection_finish_validates_deeply_wrapped_fixture_with_inner_marker(
        self, mock_py_exit, mock_rep_err
    ):
        """Collection phase: validator on an inner wrapper of a deeply wrapped fixture is correctly used."""
        mock_session = MagicMock()
        mock_session.config = MagicMock()
        mock_session.config.getini.return_value = "false"  # auto_skip

        actual_fixture_logic = MagicMock(name="actual_fixture_logic")

        inner_validator_mock = MagicMock(name="inner_validator")
        # Configure collection phase to fail as expected to prevent execution phase attempt
        collection_phase_error = ValueError("Mocked collection validation error")
        inner_validator_mock.side_effect = collection_phase_error

        inner_wrapper = MagicMock(name="inner_wrapper")
        inner_wrapper.__wrapped__ = actual_fixture_logic
        inner_wrapper._fixturecheck = True
        inner_wrapper._validator = inner_validator_mock
        inner_wrapper._expect_validation_error = True  # Error is expected
        (
            delattr(inner_wrapper, "side_effect")
            if hasattr(inner_wrapper, "side_effect")
            else None
        )

        outer_wrapper = MagicMock(name="outer_wrapper")
        outer_wrapper.__wrapped__ = inner_wrapper
        (
            delattr(outer_wrapper, "_fixturecheck")
            if hasattr(outer_wrapper, "_fixturecheck")
            else None
        )
        (
            delattr(outer_wrapper, "_validator")
            if hasattr(outer_wrapper, "_validator")
            else None
        )
        (
            delattr(outer_wrapper, "side_effect")
            if hasattr(outer_wrapper, "side_effect")
            else None
        )

        mock_fdef = MagicMock(name="deeply_wrapped_fdef_inner_marker", spec=["func"])
        mock_fdef.func = outer_wrapper
        mock_session.config._fixturecheck_fixtures = {mock_fdef}

        with patch("pytest_fixturecheck.plugin.is_async_fixture", return_value=False):
            pytest_collection_finish(mock_session)

        inner_validator_mock.assert_called_once_with(outer_wrapper, True)
        mock_rep_err.assert_not_called()
        mock_py_exit.assert_not_called()

    # Removing the duplicated test test_auto_skip_behavior_during_collection_phase
    # Its functionality is covered by existing tests.
    # The following lines were remnants of the faulty deletion and are now removed:
    # @patch('pytest_fixturecheck.plugin._mark_dependent_tests_for_skip')
    # ... extensive comments ...
    # @patch('pytest.exit')


# End of TestPytestCollectionFinish class, or start of next test method if any within this class.
# Based on the previous outline, the class TestPytestCollectionFinish should end here,
# and the next definitions are outside or a new class.
# The next test in the original file structure was TestPluginValidation class.
