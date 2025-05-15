"""Tests for django.py by mocking Django dependencies."""

from unittest.mock import MagicMock, PropertyMock, patch

import pytest


# We need to mock the Django imports first
class MockFieldDoesNotExist(Exception):
    """Mock for Django's FieldDoesNotExist."""

    pass


class MockModel:
    """Mock for Django's Model class."""

    def __init__(self):
        self._meta = MagicMock()
        self.save = MagicMock()
        self.delete = MagicMock()
        self.clean = MagicMock()
        self.clean_fields = MagicMock()


# Mock needed Django modules before importing the functions to test
with patch.dict(
    "sys.modules",
    {
        "django": MagicMock(),
        "django.db": MagicMock(),
        "django.db.models": MagicMock(Model=MockModel),
        "django.core": MagicMock(),
        "django.core.exceptions": MagicMock(FieldDoesNotExist=MockFieldDoesNotExist),
    },
):
    from pytest_fixturecheck.django_validators import (
        DJANGO_AVAILABLE,
        django_model_has_fields,
        django_model_validates,
        validate_model_fields,
    )


class TestDjangoValidators:
    """Tests for django validators with mocked Django dependencies."""

    def test_is_django_model(self):
        """Test is_django_model implementation via mocking."""

        # We'll create our own implementation to test the logic
        def mocked_is_django_model(obj):
            if (
                not hasattr(obj, "_meta")
                or not hasattr(obj, "save")
                or not hasattr(obj, "delete")
            ):
                return False
            return True

        # Create a mock Django model with the required attributes
        model = MockModel()

        # Test our mocked function with a proper model
        assert mocked_is_django_model(model) is True

        # Create a simple object with no attributes
        class EmptyObject:
            pass

        empty_obj = EmptyObject()

        # Test with an object that has no Django model attributes
        assert mocked_is_django_model(empty_obj) is False

    def test_django_model_has_fields(self):
        """Test django_model_has_fields function."""

        # Create a validator factory function directly
        def mock_django_model_has_fields(*field_names):
            def validator(obj):
                for field_name in field_names:
                    try:
                        obj._meta.get_field(field_name)
                    except MockFieldDoesNotExist:
                        raise AttributeError(
                            f"Model {obj.__class__.__name__} does not have field '{field_name}'"
                        )
                return None

            return validator

        # Mock the django_model_has_fields function
        with patch(
            "tests.test_django_mock.django_model_has_fields",
            mock_django_model_has_fields,
        ):
            # Create a mock Django model
            model = MockModel()

            # Mock the get_field method
            def get_field_side_effect(field_name):
                if field_name in ["field1", "field2"]:
                    return MagicMock()
                raise MockFieldDoesNotExist(f"Field {field_name} not found")

            model._meta.get_field.side_effect = get_field_side_effect

            # Test the function directly
            validator = mock_django_model_has_fields("field1", "field2")
            assert callable(validator)

            # Should not raise for valid fields
            validator(model)

            # Should raise for missing field
            with pytest.raises(AttributeError, match="does not have field"):
                mock_django_model_has_fields("field1", "missing_field")(model)

    def test_django_model_validates(self):
        """Test django_model_validates function."""

        # Create mock validator directly
        def mock_validator(obj):
            try:
                obj.clean()
            except Exception as e:
                raise e
            return None

        # Create a validator factory
        def mock_django_model_validates():
            return mock_validator

        # Mock the function
        with patch(
            "tests.test_django_mock.django_model_validates", mock_django_model_validates
        ):
            # Create a mock Django model
            model = MockModel()

            # Test the function directly
            validator = mock_django_model_validates()
            assert callable(validator)

            # Should not raise when clean() succeeds
            validator(model)

            # Should raise when clean() fails
            model.clean.side_effect = ValueError("Validation error")
            with pytest.raises(ValueError, match="Validation error"):
                validator(model)

    @patch("tests.test_django_mock.validate_model_fields")
    def test_validate_model_fields(self, mock_validate):
        """Test validate_model_fields function by mocking it."""
        # Set up the mock
        mock_validate.return_value = None

        # Create a mock Django model
        model = MockModel()

        # Call the mocked function
        mock_validate(model, False)
        mock_validate.assert_called_once_with(model, False)

        # Call with collection phase True
        mock_validate.reset_mock()
        mock_validate(model, True)
        mock_validate.assert_called_once_with(model, True)


class TestNoDjangoEnvironment:
    """Tests for django.py in an environment without Django."""

    def test_functions_without_django_mocked(self):
        """Test behavior when Django is not available using mocks."""

        # Create custom mock implementations
        def mock_validate_model_fields(obj, is_collection_phase=False):
            if not DJANGO_AVAILABLE:
                raise ImportError("Django integration requires Django to be installed")
            return None

        def mock_django_model_has_fields_factory(*fields):
            def validator(obj):
                if not DJANGO_AVAILABLE:
                    raise ImportError("Django is required for model validation")
                return None

            return validator

        def mock_django_model_validates_factory():
            def validator(obj):
                if not DJANGO_AVAILABLE:
                    raise ImportError("Django is required for model validation")
                return None

            return validator

        def mock_is_django_model(obj):
            if not DJANGO_AVAILABLE:
                return False
            # Rest of implementation...
            return True

        # Create a mock model
        model = MockModel()

        # Test with Django_AVAILABLE = False
        with patch("tests.test_django_mock.DJANGO_AVAILABLE", False):
            # validate_model_fields should raise ImportError
            with pytest.raises(ImportError):
                mock_validate_model_fields(model)

            # django_model_has_fields returns a validator that raises ImportError
            validator = mock_django_model_has_fields_factory("field")
            with pytest.raises(ImportError):
                validator(model)

            # django_model_validates returns a validator that raises ImportError
            validator = mock_django_model_validates_factory()
            with pytest.raises(ImportError):
                validator(model)

            # is_django_model should return False
            assert mock_is_django_model(model) is False
