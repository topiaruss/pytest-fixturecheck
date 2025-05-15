"""Tests for the pytest-fixturecheck plugin."""

import pytest
import builtins as real_builtins # Import with an alias to ensure access to original
import unittest.mock as mock # Import with an alias for unittest.mock

from pytest_fixturecheck import fixturecheck
from pytest_fixturecheck.plugin import (
    is_async_fixture, PYTEST_ASYNCIO_INSTALLED, pytest_fixture_setup,
    pytest_collection_finish
)
from unittest.mock import MagicMock, patch


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
        mock_fixturedef = MagicMock(spec=["func", "argname", "unittest", "_pytest_asyncio_scope"])
        def sync_func(): pass
        mock_fixturedef.func = sync_func
        mock_fixturedef.argname = "sync_fixture"
        if hasattr(mock_fixturedef, 'unittest'): delattr(mock_fixturedef, 'unittest')
        if hasattr(mock_fixturedef, '_pytest_asyncio_scope'): delattr(mock_fixturedef, '_pytest_asyncio_scope')
        assert not is_async_fixture(mock_fixturedef)

    async def async_func_for_test(self): # Helper async function
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
        def sync_func(): pass
        mock_fixturedef.func = sync_func
        mock_fixturedef.argname = "async_named_fixture"
        assert is_async_fixture(mock_fixturedef)

    def test_unittest_async_fixture(self):
        """Test with a simulated unittest async fixture."""
        mock_fixturedef = MagicMock()
        def sync_func(): pass
        mock_fixturedef.func = sync_func
        mock_fixturedef.argname = "unittest_style_fixture"
        mock_unittest_attr = MagicMock()
        mock_unittest_attr.__str__ = MagicMock(return_value="<UnittestAsyncFixture something>")
        mock_fixturedef.unittest = mock_unittest_attr
        assert is_async_fixture(mock_fixturedef)

    def test_unittest_non_async_fixture(self):
        """Test with a simulated unittest non-async fixture."""
        mock_fixturedef = MagicMock(spec=["func", "argname", "unittest", "_pytest_asyncio_scope"])
        def sync_func(): pass
        mock_fixturedef.func = sync_func
        mock_fixturedef.argname = "sync_fixture"
        mock_unittest_attr = MagicMock()
        mock_unittest_attr.__str__ = MagicMock(return_value="<UnittestFixture something>")
        mock_fixturedef.unittest = mock_unittest_attr
        if hasattr(mock_fixturedef, '_pytest_asyncio_scope'): delattr(mock_fixturedef, '_pytest_asyncio_scope')
        assert not is_async_fixture(mock_fixturedef)

    @patch('pytest_fixturecheck.plugin.PYTEST_ASYNCIO_INSTALLED', True)
    def test_pytest_asyncio_installed_with_scope_attr(self):
        """Test with pytest-asyncio installed and _pytest_asyncio_scope attribute present."""
        mock_fixturedef = MagicMock()
        def sync_func(): pass
        mock_fixturedef.func = sync_func
        mock_fixturedef.argname = "some_fixture"
        mock_fixturedef._pytest_asyncio_scope = "function"
        assert is_async_fixture(mock_fixturedef)

    @patch('pytest_fixturecheck.plugin.PYTEST_ASYNCIO_INSTALLED', True)
    def test_pytest_asyncio_installed_without_scope_attr(self):
        """Test with pytest-asyncio installed but _pytest_asyncio_scope attribute missing."""
        mock_fixturedef = MagicMock()
        def sync_func(): pass
        mock_fixturedef.func = sync_func
        mock_fixturedef.argname = "another_fixture"
        if hasattr(mock_fixturedef, '_pytest_asyncio_scope'):
            delattr(mock_fixturedef, '_pytest_asyncio_scope')
        assert not is_async_fixture(mock_fixturedef)
        
    @patch('pytest_fixturecheck.plugin.PYTEST_ASYNCIO_INSTALLED', False)
    def test_pytest_asyncio_not_installed(self):
        """Test when pytest-asyncio is not installed."""
        mock_fixturedef = MagicMock()
        def sync_func(): pass
        mock_fixturedef.func = sync_func
        mock_fixturedef.argname = "fixture_when_no_asyncio_plugin"
        mock_fixturedef._pytest_asyncio_scope = "function" 
        assert not is_async_fixture(mock_fixturedef)

    # This is the correct and final version of this test
    @patch('pytest_fixturecheck.plugin.PYTEST_ASYNCIO_INSTALLED', True)
    @patch('builtins.hasattr', autospec=True) 
    def test_pytest_asyncio_installed_with_scope_attr_error(self, mock_autospecced_hasattr):
        """Test a scenario where checking for _pytest_asyncio_scope causes an error."""
        class PlainFixtureDefForTest:
            pass
        test_subject_fixture_def = PlainFixtureDefForTest()
        def _a_sync_function_for_test(): pass
        test_subject_fixture_def.func = _a_sync_function_for_test
        test_subject_fixture_def.argname = "a_regular_fixture_name_for_test"
        def controlled_hasattr_side_effect(obj, attribute_name):
            if obj is test_subject_fixture_def:
                if attribute_name == "unittest":
                    return False
                if attribute_name == "_pytest_asyncio_scope":
                    raise AttributeError("Deliberate error checking _pytest_asyncio_scope")
            return mock.DEFAULT
        mock_autospecced_hasattr.side_effect = controlled_hasattr_side_effect
        assert not is_async_fixture(test_subject_fixture_def)


# New test class for pytest_fixture_setup
class TestPytestFixtureSetup:
    """Tests for the pytest_fixture_setup hook."""

    def test_fixture_not_marked(self):
        """Test that nothing happens if the fixture is not marked with _fixturecheck."""
        mock_fixturedef = MagicMock(spec=['func'])
        mock_fixturedef.func = lambda: None # Plain function
        # Ensure _fixturecheck is not on func or any wrapped versions
        delattr(mock_fixturedef.func, "_fixturecheck") if hasattr(mock_fixturedef.func, "_fixturecheck") else None
        if hasattr(mock_fixturedef.func, "__wrapped__"):
            current = mock_fixturedef.func.__wrapped__
            while current:
                delattr(current, "_fixturecheck") if hasattr(current, "_fixturecheck") else None
                current = getattr(current, "__wrapped__", None)

        mock_request = MagicMock()
        mock_request.config = MagicMock()
        # Ensure _fixturecheck_fixtures is not touched if it doesn't exist
        # or not added to if it does and fixture not marked

        pytest_fixture_setup(mock_fixturedef, mock_request)

        assert not hasattr(mock_request.config, "_fixturecheck_fixtures") or \
               mock_fixturedef not in mock_request.config._fixturecheck_fixtures
        assert not hasattr(mock_fixturedef, "_fixturecheck_skip") # Should not be marked for skip

    def test_fixture_marked_directly_non_async(self):
        """Test a non-async fixture marked directly with _fixturecheck."""
        mock_fixturedef = MagicMock(name="direct_non_async_fixturedef", spec=['func'])
        mock_fixturedef.func = lambda: None
        mock_fixturedef.func._fixturecheck = True # Mark the fixture

        mock_request = MagicMock()
        mock_request.config = MagicMock()
        # Simulate _fixturecheck_fixtures not existing initially
        if hasattr(mock_request.config, "_fixturecheck_fixtures"): 
            del mock_request.config._fixturecheck_fixtures

        with patch('pytest_fixturecheck.plugin.is_async_fixture', return_value=False) as mock_is_async:
            pytest_fixture_setup(mock_fixturedef, mock_request)
            mock_is_async.assert_called_once_with(mock_fixturedef)

        assert hasattr(mock_request.config, "_fixturecheck_fixtures")
        assert mock_fixturedef in mock_request.config._fixturecheck_fixtures
        assert not hasattr(mock_fixturedef, "_fixturecheck_skip")

    def test_fixture_marked_directly_async(self):
        """Test an async fixture marked directly with _fixturecheck."""
        mock_fixturedef = MagicMock(name="direct_async_fixturedef")
        mock_fixturedef.func = lambda: None 
        mock_fixturedef.func._fixturecheck = True # Mark the fixture

        mock_request = MagicMock()
        mock_request.config = MagicMock()
        # Simulate _fixturecheck_fixtures existing but empty
        mock_request.config._fixturecheck_fixtures = set()

        with patch('pytest_fixturecheck.plugin.is_async_fixture', return_value=True) as mock_is_async:
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
        wrapper2._fixturecheck = True # Mark is on this wrapper

        mock_fixturedef = MagicMock(name="wrapped_fixturedef", spec=['func'])
        mock_fixturedef.func = wrapper2 # func is the outermost wrapper

        mock_request = MagicMock()
        mock_request.config = MagicMock()
        mock_request.config._fixturecheck_fixtures = set() # Simulate existing set

        with patch('pytest_fixturecheck.plugin.is_async_fixture', return_value=False) as mock_is_async:
            pytest_fixture_setup(mock_fixturedef, mock_request)
            mock_is_async.assert_called_once_with(mock_fixturedef)

        assert mock_fixturedef in mock_request.config._fixturecheck_fixtures
        assert not hasattr(mock_fixturedef, "_fixturecheck_skip")

    def test_fixture_marked_on_deeply_wrapped_original_func(self):
        """Test when _fixturecheck is on the original, deeply wrapped func, but a wrapper is used."""
        original_func = MagicMock(name="original_deep_func")
        original_func._fixturecheck = True # Mark is on the innermost original function

        wrapper1 = MagicMock(name="deep_wrapper1")
        wrapper1.__wrapped__ = original_func

        wrapper2 = MagicMock(name="deep_wrapper2")
        wrapper2.__wrapped__ = wrapper1
        # Wrapper2 itself is NOT marked, but it will be the fixture_func initially
        # The loop should find _fixturecheck on original_func if current_func becomes original_func.
        # However, the logic is `if getattr(current_func, "_fixturecheck", False): fixture_func = current_func; break`
        # This means it uses the *wrapper* that has _fixturecheck. 
        # If the original func has it, but no wrapper does, it will use the original func after the loop.

        mock_fixturedef = MagicMock(name="deeply_wrapped_fixturedef", spec=['func'])
        # If fixturedef.func is wrapper2, and only original_func has _fixturecheck=True:
        # pytest_fixture_setup will iterate: wrapper2 (no _fc) -> wrapper1 (no _fc) -> original_func (has _fc)
        # Then fixture_func becomes original_func for the final check `if getattr(fixture_func, "_fixturecheck", False):`
        mock_fixturedef.func = wrapper2

        mock_request = MagicMock()
        mock_request.config = MagicMock()
        mock_request.config._fixturecheck_fixtures = set()

        with patch('pytest_fixturecheck.plugin.is_async_fixture', return_value=False) as mock_is_async:
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
        mock_session.config.getini = MagicMock(side_effect=AssertionError("getini should not be called"))

        pytest_collection_finish(mock_session)
        mock_session.config.getini.assert_not_called() # Verifies early exit

    def test_empty_fixtures_to_validate(self):
        """Test early exit if _fixturecheck_fixtures is empty."""
        mock_session = MagicMock()
        mock_session.config = MagicMock()
        mock_session.config._fixturecheck_fixtures = set() # Empty set
        mock_session.config.getini = MagicMock(side_effect=AssertionError("getini should not be called"))

        pytest_collection_finish(mock_session)
        mock_session.config.getini.assert_not_called() # Verifies early exit

    @patch('pytest_fixturecheck.plugin.report_fixture_errors')
    @patch('pytest.exit') # Patching pytest.exit directly
    def test_auto_skip_false_one_failure(self, mock_pytest_exit, mock_report_errors):
        """Test auto_skip=false: pytest.exit is called on validation failure."""
        mock_session = MagicMock()
        mock_session.config = MagicMock()
        mock_session.config.getini = MagicMock(return_value="false") # auto_skip is false

        failing_validator = MagicMock(side_effect=ValueError("Validation failed"))
        mock_fixture_func = MagicMock(_validator=failing_validator, _expect_validation_error=False)
        
        # To handle the wrapper logic in pytest_collection_finish correctly:
        # Ensure func does not have __wrapped__ or if it does, configure it appropriately.
        # For simplicity, assume no wrapping here for the validator finding part.
        delattr(mock_fixture_func, '__wrapped__') if hasattr(mock_fixture_func, '__wrapped__') else None

        mock_fdef = MagicMock(name="failing_fixturedef")
        mock_fdef.func = mock_fixture_func
        # Ensure it's not skipped by unittest/async/etc. flags for this basic validator test
        mock_fdef.configure_mock(**{
            'unittest': None, # Make hasattr(mock_fdef, 'unittest') true but str() won't match async
            '_fixturecheck_skip': False,
        })
        # We also need to control is_async_fixture for this fixturedef

        mock_session.config._fixturecheck_fixtures = {mock_fdef}

        with patch('pytest_fixturecheck.plugin.is_async_fixture', return_value=False):
            # The collection phase validator(fixture_func, True) will be called
            pytest_collection_finish(mock_session)

        mock_report_errors.assert_called_once()
        mock_pytest_exit.assert_called_once_with("Fixture validation failed", 1)

    @patch('pytest_fixturecheck.plugin.report_fixture_errors')
    @patch('pytest_fixturecheck.plugin._mark_dependent_tests_for_skip')
    @patch('pytest.exit')
    def test_auto_skip_true_one_failure(self, mock_pytest_exit, mock_mark_skip, mock_report_errors):
        """Test auto_skip=true: _mark_dependent_tests_for_skip is called."""
        mock_session = MagicMock()
        mock_session.config = MagicMock()
        mock_session.config.getini = MagicMock(return_value="true") # auto_skip is true

        failing_validator = MagicMock(side_effect=ValueError("Validation failed"))
        mock_fixture_func = MagicMock(_validator=failing_validator, _expect_validation_error=False)
        delattr(mock_fixture_func, '__wrapped__') if hasattr(mock_fixture_func, '__wrapped__') else None

        mock_fdef = MagicMock(name="failing_fixturedef_for_skip")
        mock_fdef.func = mock_fixture_func
        mock_fdef.configure_mock(**{
            'unittest': None,
            '_fixturecheck_skip': False,
        })

        mock_session.config._fixturecheck_fixtures = {mock_fdef}

        with patch('pytest_fixturecheck.plugin.is_async_fixture', return_value=False):
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
    @patch('pytest_fixturecheck.plugin.report_fixture_errors') # To prevent printing errors
    @patch('pytest.exit') # To prevent exit in case of unexpected failures
    def test_collection_validation_passes_not_expected_error(self, mock_pytest_exit, mock_report_errors):
        """Collection validation: validator passes, error not expected."""
        mock_session = MagicMock()
        mock_session.config = MagicMock()
        mock_session.config.getini = MagicMock(return_value="false") # auto_skip false

        mock_validator = MagicMock(return_value=None) # Validator passes
        mock_fixture_func = MagicMock(_validator=mock_validator, _expect_validation_error=False)
        delattr(mock_fixture_func, '__wrapped__') if hasattr(mock_fixture_func, '__wrapped__') else None

        mock_fdef = MagicMock(name="coll_pass_not_expected_fdef")
        mock_fdef.func = mock_fixture_func
        mock_fdef.configure_mock(**{'unittest': None, '_fixturecheck_skip': False})
        mock_session.config._fixturecheck_fixtures = {mock_fdef}

        with patch('pytest_fixturecheck.plugin.is_async_fixture', return_value=False):
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
            pass # No errors reported, which is correct.
        mock_pytest_exit.assert_not_called()

    @patch('pytest_fixturecheck.plugin.report_fixture_errors')
    @patch('pytest.exit')
    def test_collection_validation_passes_expected_error(self, mock_pytest_exit, mock_report_errors):
        """Collection validation: validator passes, error WAS expected (this is a failure)."""
        mock_session = MagicMock()
        mock_session.config = MagicMock()
        mock_session.config.getini = MagicMock(return_value="false")

        mock_validator = MagicMock(return_value=None)
        mock_fixture_func = MagicMock(_validator=mock_validator, _expect_validation_error=True) # Error expected
        delattr(mock_fixture_func, '__wrapped__') if hasattr(mock_fixture_func, '__wrapped__') else None

        mock_fdef = MagicMock(name="coll_pass_expected_fdef")
        mock_fdef.func = mock_fixture_func
        mock_fdef.configure_mock(**{'unittest': None, '_fixturecheck_skip': False})
        mock_session.config._fixturecheck_fixtures = {mock_fdef}

        with patch('pytest_fixturecheck.plugin.is_async_fixture', return_value=False):
            pytest_collection_finish(mock_session)

        mock_validator.assert_called_once_with(mock_fixture_func, True)
        mock_report_errors.assert_called_once()
        failed_fixture_arg = mock_report_errors.call_args[0][0][0] # (fixturedef, error, traceback_str)
        assert failed_fixture_arg[0] == mock_fdef
        assert isinstance(failed_fixture_arg[1], AssertionError)
        assert "Expected validation error but none occurred" in str(failed_fixture_arg[1])
        mock_pytest_exit.assert_called_once() # Because a failure was recorded and auto_skip=false

    @patch('pytest_fixturecheck.plugin.report_fixture_errors')
    @patch('pytest.exit')
    def test_collection_validation_fails_expected_error(self, mock_pytest_exit, mock_report_errors):
        """Collection validation: validator fails, error WAS expected (success)."""
        mock_session = MagicMock()
        mock_session.config = MagicMock()
        mock_session.config.getini = MagicMock(return_value="false")

        mock_validator = MagicMock(side_effect=ValueError("Deliberate validation fail"))
        mock_fixture_func = MagicMock(_validator=mock_validator, _expect_validation_error=True) # Error expected
        delattr(mock_fixture_func, '__wrapped__') if hasattr(mock_fixture_func, '__wrapped__') else None
        
        mock_fdef = MagicMock(name="coll_fail_expected_fdef")
        mock_fdef.func = mock_fixture_func
        mock_fdef.configure_mock(**{'unittest': None, '_fixturecheck_skip': False})
        mock_session.config._fixturecheck_fixtures = {mock_fdef}

        with patch('pytest_fixturecheck.plugin.is_async_fixture', return_value=False):
            pytest_collection_finish(mock_session)
        
        mock_validator.assert_called_once_with(mock_fixture_func, True)
        # This case is a success, so no error should be reported for this fixture.
        # If mock_report_errors is called, it means some other fixture failed or logic is wrong.
        # Assuming this is the only fixture, mock_report_errors should not be called.
        if mock_report_errors.call_args_list:
            # Check if this specific fixture caused an error report (it shouldn't have)
            errors_for_this_fixture = [
                f_def for f_def, err, tb_str in mock_report_errors.call_args_list[0][0][0]
                if f_def == mock_fdef
            ]
            assert not errors_for_this_fixture, "Failure was reported for a fixture that expected an error which occurred."
        else:
            pass # No errors reported at all, correct.
        mock_pytest_exit.assert_not_called()

    @patch('pytest_fixturecheck.plugin.report_fixture_errors')
    @patch('pytest.exit')
    def test_collection_validation_fails_not_expected_error(self, mock_pytest_exit, mock_report_errors):
        """Collection validation: validator fails, error NOT expected (failure)."""
        mock_session = MagicMock()
        mock_session.config = MagicMock()
        mock_session.config.getini = MagicMock(return_value="false")

        original_error = ValueError("Deliberate validation fail")
        mock_validator = MagicMock(side_effect=original_error)
        mock_fixture_func = MagicMock(_validator=mock_validator, _expect_validation_error=False) # Error NOT expected
        delattr(mock_fixture_func, '__wrapped__') if hasattr(mock_fixture_func, '__wrapped__') else None

        mock_fdef = MagicMock(name="coll_fail_not_expected_fdef")
        mock_fdef.func = mock_fixture_func
        mock_fdef.configure_mock(**{'unittest': None, '_fixturecheck_skip': False})
        mock_session.config._fixturecheck_fixtures = {mock_fdef}

        with patch('pytest_fixturecheck.plugin.is_async_fixture', return_value=False):
            pytest_collection_finish(mock_session)

        mock_validator.assert_called_once_with(mock_fixture_func, True)
        mock_report_errors.assert_called_once()
        failed_fixture_arg = mock_report_errors.call_args[0][0][0]
        assert failed_fixture_arg[0] == mock_fdef
        assert failed_fixture_arg[1] is original_error # Check it's the exact error instance
        mock_pytest_exit.assert_called_once()
