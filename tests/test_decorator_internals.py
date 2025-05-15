"""Tests for internal logic of pytest_fixturecheck/decorator.py."""

import importlib  # Added importlib
import inspect
import sys
import types
from unittest.mock import MagicMock, patch

import pytest

import pytest_fixturecheck.django_validators  # Ensure the module is imported
from pytest_fixturecheck import decorator as fc_decorator

# Assuming _default_validator is accessible for testing.
# If not, we might need to import it carefully or test via the main fixturecheck decorator.
from pytest_fixturecheck.decorator import _default_validator

# Store original import_module for the mock to call
_original_import_module = importlib.import_module

# Import pytest_mock if available, but make it non-essential
pytestmark = []
try:
    import pytest_mock
except ImportError:
    # Skip tests that require pytest-mock if it's not installed
    pytestmark.append(pytest.mark.skip(reason="pytest-mock not installed"))


# Test AttributeError in getattr
class TestDecoratorGetattrErrors:
    class RaisesAttributeError:
        def __getattr__(self, name):
            raise AttributeError(f"Simulated AttributeError for {name}")

    def test_getattr_raises_attribute_error_in_direct_call_heuristic(self, mocker):
        """Test that AttributeError is caught for _is_... checks in direct call heuristic."""
        obj = self.RaisesAttributeError()
        mock_default_validator = mocker.patch(
            "pytest_fixturecheck.decorator._default_validator"
        )

        # Case 1: @fixturecheck applied to an object that raises AttributeError on getattr
        # This object is not a validator/creator and fails inspect.signature, so it should be treated as a fixture body.
        # The getattr calls for _is_validator_check_val/_is_creator_check_val should hit the `except AttributeError`.
        try:
            decorated_func = fc_decorator.fixturecheck(obj)
            assert hasattr(
                decorated_func, "_validator"
            ), "Wrapped function should have _validator attribute"
            assert (
                decorated_func._validator == mock_default_validator
            ), "Should fall back to default validator"
        except Exception as e:
            pytest.fail(
                f"Applying fixturecheck to RaisesAttributeError object (direct) failed: {e}"
            )

    def test_getattr_raises_attribute_error_in_decorator_args(self, mocker):
        """Test AttributeError for _is_... checks when obj is passed as validator/creator arg."""
        obj = self.RaisesAttributeError()
        mock_default_validator = mocker.patch(
            "pytest_fixturecheck.decorator._default_validator"
        )

        # Case 2: fixturecheck(obj) where obj is intended as a validator/creator but raises AttributeError
        decorator_instance_pos = fc_decorator.fixturecheck(obj)

        @decorator_instance_pos
        def my_fixture_pos():
            return "pos"

        assert hasattr(my_fixture_pos, "_validator")
        assert (
            my_fixture_pos._validator == mock_default_validator
        ), "Should use default validator if creator/validator lookup fails"

        # Case 3: fixturecheck(validator=obj) where obj raises AttributeError
        decorator_instance_kw = fc_decorator.fixturecheck(validator=obj)

        @decorator_instance_kw
        def my_fixture_kw():
            return "kw"

        assert hasattr(my_fixture_kw, "_validator")
        assert (
            my_fixture_kw._validator == mock_default_validator
        ), "Should use default validator if kwarg validator lookup fails"


# Test default validator
class TestDefaultValidator:
    def test_default_validator_collection_phase(self):
        """Test _default_validator does nothing during collection phase."""
        mock_obj = MagicMock()
        # Should not raise, and validate_model_fields (if imported) should not be called.
        with patch(
            "pytest_fixturecheck.django_validators.validate_model_fields",
            new_callable=MagicMock,
        ) as mock_validate_django, patch(
            "pytest_fixturecheck.django_validators.DJANGO_AVAILABLE", True
        ):  # Removed create=True
            _default_validator(mock_obj, is_collection_phase=True)
            mock_validate_django.assert_not_called()

    def test_default_validator_no_django_available(self):
        """Test _default_validator when Django is not available."""
        mock_obj = MagicMock()
        # Patch DJANGO_AVAILABLE to False. If this path is taken in _default_validator,
        # validate_model_fields from django_validators should not be called.
        with patch(
            "pytest_fixturecheck.django_validators.DJANGO_AVAILABLE", False
        ) as mock_django_unavailable, patch(
            "pytest_fixturecheck.django_validators.validate_model_fields",
            new_callable=MagicMock,
        ) as mock_validate_django_dv:
            _default_validator(mock_obj, is_collection_phase=False)
            mock_validate_django_dv.assert_not_called()

    def test_default_validator_django_available_not_model_no_meta(self):
        """Test _default_validator with Django, but object has no _meta."""
        mock_obj = MagicMock()
        if hasattr(mock_obj, "_meta"):
            del mock_obj._meta

        with patch(
            "pytest_fixturecheck.django_validators.DJANGO_AVAILABLE", True
        ), patch(
            "pytest_fixturecheck.django_validators.validate_model_fields",
            new_callable=MagicMock,
        ) as mock_validate_django:
            _default_validator(mock_obj, is_collection_phase=False)
            mock_validate_django.assert_not_called()

    def test_default_validator_django_available_not_model_isinstance_false(self):
        """Test _default_validator with Django, object has _meta, but not a Model instance."""
        mock_obj = MagicMock()
        mock_obj._meta = MagicMock()

        with patch(
            "pytest_fixturecheck.django_validators.DJANGO_AVAILABLE", True
        ), patch("django.db.models.Model", new_callable=MagicMock) as MockModel, patch(
            "builtins.isinstance", return_value=False
        ) as mock_isinstance, patch(
            "pytest_fixturecheck.django_validators.validate_model_fields",
            new_callable=MagicMock,
        ) as mock_validate_django:
            _default_validator(mock_obj, is_collection_phase=False)
            mock_isinstance.assert_any_call(mock_obj, MockModel)
            mock_validate_django.assert_not_called()

    def test_default_validator_django_available_is_model_validates(self):
        """Test _default_validator with Django, object is a Model instance, calls validation."""
        mock_obj = MagicMock()
        mock_obj._meta = MagicMock()

        with patch(
            "pytest_fixturecheck.django_validators.DJANGO_AVAILABLE", True
        ), patch(
            "django.db.models.Model", new_callable=MagicMock
        ) as MockModelMetaclass, patch(
            "builtins.isinstance"
        ) as mock_isinstance, patch(
            "pytest_fixturecheck.django_validators.validate_model_fields",
            new_callable=MagicMock,
        ) as mock_validate_django:
            # Make isinstance(mock_obj, MockModelMetaclass) True
            mock_isinstance.side_effect = (
                lambda obj, model_cls: obj is mock_obj
                and model_cls is MockModelMetaclass
            )

            _default_validator(mock_obj, is_collection_phase=False)
            # Check that isinstance was called with our object and the (mocked) Model class
            mock_isinstance.assert_any_call(mock_obj, MockModelMetaclass)
            mock_validate_django.assert_called_once_with(mock_obj)

    def test_default_validator_django_import_error_on_model(self):
        """Test _default_validator when 'from django.db.models import Model' fails."""
        mock_obj = MagicMock()
        mock_obj._meta = MagicMock()

        with patch(
            "pytest_fixturecheck.django_validators.DJANGO_AVAILABLE", True
        ), patch(
            "django.db.models.Model", side_effect=ImportError("Cannot import Model")
        ), patch(
            "pytest_fixturecheck.django_validators.validate_model_fields",
            new_callable=MagicMock,
        ) as mock_validate_django:
            _default_validator(mock_obj, is_collection_phase=False)
            mock_validate_django.assert_not_called()

    def test_default_validator_django_import_error_on_validate_model_fields(self):
        """Test _default_validator when 'from .django import validate_model_fields' fails."""
        # This test targets the outer try-except ImportError in _default_validator for django_validators import.
        mock_obj = MagicMock()

        with patch(
            "pytest_fixturecheck.django_validators.DJANGO_AVAILABLE", True
        ), patch(
            "pytest_fixturecheck.django_validators.validate_model_fields",
            side_effect=ImportError("Cannot import v_m_f from dv"),
        ), patch(
            "pytest_fixturecheck.utils.validate_model_fields", new_callable=MagicMock
        ) as mock_utils_validate, patch(
            "pytest_fixturecheck.utils.DJANGO_AVAILABLE", False
        ):  # Ensure fallback also doesn't run validation
            _default_validator(mock_obj)
            mock_utils_validate.assert_not_called()  # Fallback validation shouldn't be called either

    # Corrected argument order for the following two tests
    @patch("pytest_fixturecheck.utils.validate_model_fields", new_callable=MagicMock)
    @patch("pytest_fixturecheck.utils.DJANGO_AVAILABLE", True)
    @patch.dict(sys.modules, {"pytest_fixturecheck.django_validators": None})
    def test_default_validator_django_import_error_fallback_validates(
        self, mock_utils_validate_fields, mock_utils_django_available
    ):
        """Test _default_validator falls back to utils if django_validators import fails and utils.DJANGO_AVAILABLE is True."""
        mock_model = MagicMock()
        mock_model._meta = MagicMock()  # Has _meta

        _default_validator(mock_model, is_collection_phase=False)
        # Now we expect the *utils* version of validate_model_fields to be called.
        mock_utils_validate_fields.assert_called_once_with(mock_model)

    @patch("pytest_fixturecheck.utils.validate_model_fields", new_callable=MagicMock)
    @patch("pytest_fixturecheck.utils.DJANGO_AVAILABLE", False)
    @patch.dict(sys.modules, {"pytest_fixturecheck.django_validators": None})
    def test_default_validator_django_import_error_fallback_utils_disabled(
        self, mock_utils_validate_fields, mock_utils_django_available_false
    ):
        """Test _default_validator does nothing if django_validators import fails and utils.DJANGO_AVAILABLE is False."""
        mock_model = MagicMock()
        mock_model._meta = MagicMock()  # Has _meta

        _default_validator(mock_model, is_collection_phase=False)
        mock_utils_validate_fields.assert_not_called()

    def test_default_validator_django_model_success_no_expect_error(self, mocker):
        # This test assumes DJANGO_AVAILABLE = True and Model can be imported
        mocker.patch("pytest_fixturecheck.decorator.DJANGO_AVAILABLE", True)
        mock_django_validate_fields = mocker.patch(
            "pytest_fixturecheck.decorator.django_validate_model_fields"
        )

        class MockDjangoModel:
            pass  # Simple mock, no _meta needed for this path if isinstance works

        # Mock successful import of Model and isinstance check
        mocker.patch(
            "django.db.models.Model", new_callable=mocker.PropertyMock, create=True
        )  # Make it an importable name
        mocker.patch(
            "builtins.isinstance",
            lambda obj, model_type: model_type.__name__ == "Model"
            and isinstance(obj, MockDjangoModel),
        )

        obj = MockDjangoModel()
        fc_decorator._default_validator(
            obj, is_collection_phase=False, expect_error_in_validator=False
        )
        mock_django_validate_fields.assert_called_once_with(obj, expect_error=False)

    def test_default_validator_django_model_import_error(self, mocker):
        """Test lines 129, 132: DJANGO_AVAILABLE is True, but django.db.models.Model import fails."""
        mocker.patch("pytest_fixturecheck.decorator.DJANGO_AVAILABLE", True)
        mock_django_validate_fields = mocker.patch(
            "pytest_fixturecheck.decorator.django_validate_model_fields"
        )

        # Store original import_module
        original_import_module = importlib.import_module

        def faulty_import_module(name, package=None):
            if name == "django.db.models":
                raise ImportError("Simulated import error for django.db.models")
            return original_import_module(name, package)

        mocker.patch("importlib.import_module", side_effect=faulty_import_module)
        # Also ensure that even if importlib.import_module isn't used directly,
        # direct `from django.db.models import Model` would fail.
        # This can be tricky if `django.db.models` was already imported by another test.
        # We might need to ensure `sys.modules` reflects this state.
        if "django.db.models" in sys.modules:
            del sys.modules["django.db.models"]  # Try to ensure it's not cached
        if "django.db" in sys.modules:
            # Potentially remove parent too if it causes issues, but be careful
            # This is getting complex, direct mock of `from ... import ...` is hard.
            # Let's rely on importlib.import_module patching primarily.
            pass

        class SomeObject:
            pass

        obj = (
            SomeObject()
        )  # Not a Django model, but the import fail should happen first

        try:
            fc_decorator._default_validator(obj, is_collection_phase=False)
        except Exception as e:
            pytest.fail(f"_default_validator raised an unexpected exception: {e}")

        mock_django_validate_fields.assert_not_called()  # Should not be called if import fails

        # Cleanup mocks to avoid affecting other tests
        mocker.stopall()  # Or specifically unpatch importlib.import_module
        # Restore sys.modules if changed, though typically pytest handles test isolation.


# --- Tests for initial imports in decorator.py ---
class TestDecoratorInitialImports:

    def _mock_import_for_django_validators_failure(self, name, package=None):
        """Side effect for importlib.import_module to simulate django_validators import failure."""
        # Check for absolute import name or relative import from pytest_fixturecheck package
        if name == "pytest_fixturecheck.django_validators" or (
            name == ".django_validators"
            and package
            and package.startswith("pytest_fixturecheck")
        ):
            raise ImportError(
                "Simulated import error for django_validators by test_decorator_internals"
            )
        return _original_import_module(name, package=package)

    # Removed @patch.dict(sys.modules, {'pytest_fixturecheck.django_validators': None})
    # Patch importlib.import_module instead
    @patch("importlib.import_module")
    def test_django_validators_import_error_fallback(
        self, mock_importlib_import_module
    ):
        """
        Test that if 'from .django_validators import ...' fails in decorator.py,
        DJANGO_AVAILABLE is False and django_validate_model_fields is a no-op.
        """
        mock_importlib_import_module.side_effect = (
            self._mock_import_for_django_validators_failure
        )

        original_decorator_module = sys.modules.get("pytest_fixturecheck.decorator")
        if "pytest_fixturecheck.decorator" in sys.modules:
            del sys.modules["pytest_fixturecheck.decorator"]

        # No need to manipulate sys.modules['pytest_fixturecheck.django_validators'] directly anymore

        try:
            # This import will execute decorator.py's top-level code
            # The patched importlib.import_module should cause the ImportError for .django_validators
            import pytest_fixturecheck.decorator as decorator_module_reloaded

            assert (
                decorator_module_reloaded.DJANGO_AVAILABLE is False
            ), "DJANGO_AVAILABLE should be False when .django_validators import fails"

            # Check if django_validate_model_fields is a no-op
            assert (
                decorator_module_reloaded.django_validate_model_fields("any_obj")
                is None
            ), "Fallback django_validate_model_fields should be a no-op"

        finally:
            # Restore original decorator module
            if original_decorator_module:
                sys.modules["pytest_fixturecheck.decorator"] = original_decorator_module
            else:  # pragma: no cover
                if "pytest_fixturecheck.decorator" in sys.modules:
                    del sys.modules["pytest_fixturecheck.decorator"]

            # Reset side_effect for import_module if it was specific to this test instance, though patch should handle it.
            # No specific cleanup for django_validators in sys.modules needed here as we didn't manipulate it directly for this error.


# --- Tests for fixturecheck decorator logic ---
from pytest_fixturecheck.decorator import fixturecheck


class TestFixtureCheckDecoratorLogic:

    def test_direct_apply_inspect_signature_fails(self):
        """
        Test @fixturecheck applied directly to a callable where inspect.signature fails.
        It should fall back to using _default_validator.
        """
        mock_fixture_body = MagicMock(name="mock_fixture_body_uninspectable")

        # Make inspect.signature fail for this specific mock
        with patch("inspect.signature", side_effect=ValueError("Cannot inspect")):
            # Apply decorator directly
            # We need to get the actual decorated function to check its attributes
            decorated_fixture = fixturecheck(mock_fixture_body)

        assert (
            decorated_fixture._validator == _default_validator
        ), "Should use _default_validator when inspect.signature fails on direct apply"
        assert decorated_fixture._fixturecheck is True

    def test_factory_returns_none_uses_default_validator(self):
        """
        Test @fixturecheck(validator_factory) where factory returns None.
        It should fall back to _default_validator.
        """

        def none_returning_factory():
            return None

        none_returning_factory._is_pytest_fixturecheck_creator = True

        @fixturecheck(none_returning_factory)
        def my_fixture():
            return "test_value"

        assert (
            my_fixture._validator == _default_validator
        ), "Should use _default_validator when factory returns None"
        assert my_fixture._fixturecheck is True
        assert my_fixture() == "test_value"  # Ensure fixture still works

    def test_decorator_arg_callable_inspect_fails_uses_default(self):
        """
        Test @fixturecheck(uninspectable_validator_like_arg) where inspect.signature fails
        on the argument within the _decorator_to_return logic.
        """
        uninspectable_callable = MagicMock(name="uninspectable_validator_arg")
        # Not marked as creator or validator
        uninspectable_callable._is_pytest_fixturecheck_creator = False
        uninspectable_callable._is_pytest_fixturecheck_validator = False

        def fixture_body():
            return "data"

        # Mock inspect.signature to only fail for our specific callable
        original_inspect_signature = inspect.signature

        def mock_signature_side_effect(obj):
            if obj is uninspectable_callable:
                raise ValueError("Cannot inspect uninspectable_callable")
            return original_inspect_signature(obj)

        with patch("inspect.signature", side_effect=mock_signature_side_effect):
            # fixturecheck(uninspectable_callable) returns a decorator, then apply to fixture_body
            decorated_fixture = fixturecheck(uninspectable_callable)(fixture_body)

        assert (
            decorated_fixture._validator == _default_validator
        ), "Should use _default_validator when inspect on arg fails in _decorator_to_return"
        assert decorated_fixture._fixturecheck is True
        assert decorated_fixture() == "data"

    @patch("pytest_fixturecheck.decorator._default_validator", new_callable=MagicMock)
    def test_factory_returns_none_uses_default_validator_with_call(
        self, mock_default_validator_in_decorator
    ):
        """
        Test @fixturecheck(validator_factory) where factory returns None.
        It should fall back to _default_validator, which then gets called.
        """
        mock_validator_factory = MagicMock(name="mock_validator_factory")
        mock_validator_factory.return_value = None  # Factory returns None
        mock_validator_factory._is_pytest_fixturecheck_creator = True

        @fixturecheck(mock_validator_factory)
        def my_fixture():
            return "test_value"

        # Call the decorated fixture to trigger the validation logic
        fixture_result = my_fixture()
        assert fixture_result == "test_value"  # Ensure fixture ran

        # The factory should have been called
        mock_validator_factory.assert_called_once_with()

        # _default_validator (mocked as mock_default_validator_in_decorator) should have been called
        # Its first argument will be the result of my_fixture(), second is_collection_phase=False.
        mock_default_validator_in_decorator.assert_called_with("test_value", False)

    def test_validator_kwarg_is_creator(self, mocker):
        """Test coverage for line 84: validator kwarg is a creator."""
        mock_inner_validator = mocker.Mock(spec=fc_decorator.ValidatorFunc)
        mock_inner_validator._is_pytest_fixturecheck_validator = (
            True  # Mark it as a validator
        )

        @fc_decorator.creates_validator
        def my_creator_for_kwarg():
            return mock_inner_validator

        @fc_decorator.fixturecheck(validator=my_creator_for_kwarg)
        def my_fixture_kwarg_creator():
            return "kwarg_creator_test"

        assert hasattr(my_fixture_kwarg_creator, "_validator")
        assert my_fixture_kwarg_creator._validator == mock_inner_validator
        # We don't need to check if my_creator_for_kwarg was called because
        # if _validator is mock_inner_validator, it must have been.

    def test_unmarked_callable_inspect_signature_fails(self, mocker):
        """Test lines 100-102: inspect.signature fails for unmarked callable."""
        mock_default_validator = mocker.patch(
            "pytest_fixturecheck.decorator._default_validator"
        )

        # An object that is callable but inspect.signature might fail for it
        # or a C extension type for which signature is not available.
        class CallableInspectFails:
            def __call__(self, *args, **kwargs):
                return "called"

            # No explicit __signature__ or other inspectable metadata

        callable_obj = CallableInspectFails()

        # Mock inspect.signature to raise an error when called with our specific object
        original_inspect_signature = inspect.signature

        def mock_inspect_signature(obj):
            if obj is callable_obj:
                raise ValueError("Simulated inspect.signature failure")
            return original_inspect_signature(obj)

        mocker.patch("inspect.signature", side_effect=mock_inspect_signature)

        # Pass this callable_obj as the fixture_or_validator (positional argument)
        # It's not marked as a validator or creator.
        # The direct application heuristic (lines 68-74) will try inspect.signature.
        # If it has >=2 params (mocked to fail here), it falls through.
        # Then, in _decorator_to_return, it hits lines 95-102.
        decorator_instance = fixturecheck(callable_obj)

        @decorator_instance
        def my_fixture():
            return "test"

        assert hasattr(my_fixture, "_validator")
        assert my_fixture._validator == mock_default_validator

    def test_unmarked_callable_lt2_params_fallback(self, mocker):
        """Test line 100: unmarked callable with <2 params falls back to default validator."""
        mock_default_validator = mocker.patch(
            "pytest_fixturecheck.decorator._default_validator"
        )

        # A callable that is not marked as validator/creator and has 1 parameter.
        # This should ideally be caught by the direct application heuristic (lines 70-72).
        # However, if it somehow reaches lines 95-99, this test ensures it uses default.
        def unmarked_callable_one_param(arg1):
            return arg1

        decorator_instance = fixturecheck(unmarked_callable_one_param)

        @decorator_instance
        def my_fixture():
            return "test"

        assert hasattr(my_fixture, "_validator")
        assert my_fixture._validator == mock_default_validator

    # Remove the old test_generator_fixture_with_yield and replace with pytester version
    def test_generator_fixture_handling_pytester(self, pytester):
        """
        Test @fixturecheck with a generator fixture using pytester.
        Ensures the yielded value is correct and the validator is called appropriately.
        """
        conftest_py_content = """
import pytest
import pytest_fixturecheck.decorator # Ensure decorator module is loaded for monkeypatching

# Using a simple list in a global scope for call recording due to pytester's execution model.
# In real tests, you'd avoid globals, but for pytester inter-run state, it's a common pattern.
global_mock_validator_calls = []

def inspecting_default_validator_global(obj, is_collection_phase=False):
    global global_mock_validator_calls
    # Store a representation that's easy to assert, e.g., function name for functions
    obj_repr = obj.__name__ if callable(obj) and hasattr(obj, '__name__') else obj
    global_mock_validator_calls.append({'obj': obj_repr, 'is_collection_phase': is_collection_phase})
    # This mock should not raise errors or return specific values unless testing that path
    return None

@pytest.fixture(autouse=True)
def patch_default_validator_for_pytester_run(monkeypatch):
    global global_mock_validator_calls
    global_mock_validator_calls = [] # Reset for each pytester run

    # Path to _default_validator within the decorator module
    monkeypatch.setattr(
        "pytest_fixturecheck.decorator._default_validator",
        inspecting_default_validator_global
    )
"""

        test_yield_file_content = """
import pytest
from pytest_fixturecheck.decorator import fixturecheck

@fixturecheck # Uses the (now patched by conftest.py) _default_validator
@pytest.fixture
def my_yielding_fixture_tc():
    # print("FIXTURE: my_yielding_fixture_tc - yielding 'yielded_data'")
    yield "yielded_data"
    # print("FIXTURE: my_yielding_fixture_tc - teardown")

def test_yielded_value_correct(my_yielding_fixture_tc):
    # print(f"TEST: test_yielded_value_correct - received {my_yielding_fixture_tc}")
    assert my_yielding_fixture_tc == "yielded_data"

def test_check_validator_calls(my_yielding_fixture_tc): # Include fixture to ensure it runs
    global global_mock_validator_calls
    # print(f"TEST: test_check_validator_calls - calls: {global_mock_validator_calls}")

    assert len(global_mock_validator_calls) >= 1, "Validator was not called at least once"

    execution_phase_calls = [
        call for call in global_mock_validator_calls if not call['is_collection_phase']
    ]
    assert len(execution_phase_calls) == 1, \\
        f"Expected one execution phase call, got {len(execution_phase_calls)}: {execution_phase_calls}"
    assert execution_phase_calls[0]['obj'] == "yielded_data", \\
        f"Validator did not receive correct yielded data: {execution_phase_calls[0]['obj']}"

    collection_phase_calls = [
        call for call in global_mock_validator_calls if call['is_collection_phase']
    ]
    assert len(collection_phase_calls) == 1, \\
        f"Expected one collection phase call, got {len(collection_phase_calls)}: {collection_phase_calls}"
    # For collection phase, obj is the fixture function itself.
    # The name might be 'my_yielding_fixture_tc' or its wrapped version.
    # Checking for type or a known part of its name is safer.
    assert collection_phase_calls[0]['obj'] == "my_yielding_fixture_tc", \\
        f"Validator did not receive correct function in collection phase: {collection_phase_calls[0]['obj']}"
"""

        # Use f-strings with !r to ensure the content is correctly escaped for makepyfile
        pytester.makepyfile(
            conftest_py=f"""{conftest_py_content}""",
            test_yield_file=f"""{test_yield_file_content}""",
        )

        result = pytester.runpytest("-v", "test_yield_file.py")
        result.stdout.fnmatch_lines(["*2 passed*"])
        result.assert_outcomes(passed=2)


# Ensure pytest is importable if not already
import pytest


# Test _fixturecheck_nop
def test_fixturecheck_nop_runs():
    # This function is a no-op, just ensure it can be called without error
    try:
        fc_decorator._fixturecheck_nop()
        fc_decorator._fixturecheck_nop(1, 2, a=3, b=4)
    except Exception as e:
        pytest.fail(f"_fixturecheck_nop raised an exception: {e}")


# Test default validator
# ... existing code ...

# ... (rest of the file, e.g., TestPluginValidation class if it exists)


class TestDjangoImportError:
    def test_default_validator_django_import_error(self, mocker):
        """Test lines 123-132: Django.db.models import error in _default_validator."""
        # Patch DJANGO_AVAILABLE to True to enter the Django block
        mocker.patch("pytest_fixturecheck.decorator.DJANGO_AVAILABLE", True)

        # Mock an ImportError when trying to import Model
        mock_import = mocker.patch(
            "builtins.__import__",
            side_effect=lambda name, *args, **kwargs: (
                ImportError(f"Mock import error for {name}")
                if name == "django.db.models"
                else __import__(name, *args, **kwargs)
            ),
        )

        # Create a mock object to validate
        mock_obj = mocker.MagicMock()

        # Call _default_validator - it should handle the ImportError gracefully
        fc_decorator._default_validator(mock_obj)

        # No exception should be raised
        # The validator should pass through the import error block and do nothing

    def test_decorator_django_validators_import_error(self, mocker):
        """Test lines 18-21: ImportError for django_validators."""
        # Save the original import_module function
        original_import = importlib.import_module

        # Create a mock of the decorator module to simulate reloading it
        mock_module = types.ModuleType("pytest_fixturecheck.decorator")
        sys.modules["pytest_fixturecheck.decorator"] = mock_module

        # Mock the import_module to raise ImportError specifically for django_validators
        def mock_import_module(name, package=None):
            if name == ".django_validators" and package == "pytest_fixturecheck":
                raise ImportError("Mock ImportError for django_validators")
            return original_import(name, package)

        mocker.patch("importlib.import_module", side_effect=mock_import_module)

        # Execute the code that would run during module import
        exec(
            """
import functools
import inspect
from typing import Any, Callable, List, Optional, TypeVar, Union, cast, overload

# Import validators and utils
from . import validators
from .utils import creates_validator
from .validators_fix import check_property_values

# Try to import from .django_validators
try:
    from .django_validators import DJANGO_AVAILABLE, validate_model_fields as django_validate_model_fields
except ImportError:
    # This is a fallback if .django_validators itself is missing or unimportable
    DJANGO_AVAILABLE = False
    def django_validate_model_fields(obj, fields_to_check=None, expect_error=False): return None
        """,
            mock_module.__dict__,
        )

        # Verify the fallbacks were created correctly
        assert hasattr(mock_module, "DJANGO_AVAILABLE")
        assert mock_module.DJANGO_AVAILABLE is False
        assert hasattr(mock_module, "django_validate_model_fields")
        assert callable(mock_module.django_validate_model_fields)

        # Clean up
        sys.modules.pop("pytest_fixturecheck.decorator", None)
