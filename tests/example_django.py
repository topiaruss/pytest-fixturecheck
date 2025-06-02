"""Example file showing the Django integration of pytest-fixturecheck.

NOTE: This is a non-runnable example since it requires Django,
but it demonstrates the intended usage.
"""

import pytest
from pytest_fixturecheck import fixturecheck
from pytest_fixturecheck.django import validate_model_fields

# This code would be in a real Django project
"""
# models.py
from django.db import models

class Author(models.Model):
    name = models.CharField(max_length=255)

class Publisher(models.Model):
    name = models.CharField(max_length=255)

class Book(models.Model):
    title = models.CharField(max_length=255)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    publisher = models.ForeignKey(Publisher, on_delete=models.CASCADE)
"""

# This would be in conftest.py or a test file


# Standard fixture - no validation
@pytest.fixture
def publisher():
    # This would work with real Django models
    # return Publisher.objects.create(name="Willow House Press")
    pass


# Using fixturecheck without model validation
@pytest.fixture
@fixturecheck()
def author():
    # This would work with real Django models
    # return Author.objects.create(name="Marian Brook")
    pass


# Using fixturecheck with Django model field validation
@fixturecheck(validate_model_fields)
@pytest.fixture
def book(author, publisher):
    # This would work with real Django models
    # return Book.objects.create(
    #     title="Echoes of the Riverbank",
    #     author=author,
    #     publisher=publisher,
    # )
    pass


# If the Book model changed, for example 'title' was renamed to 'book_title',
# the validator would detect this during collection and report:
#
# FIXTURE VALIDATION ERRORS
# ========================
#
# Fixture 'book' in tests/conftest.py:25 failed validation:
#   AttributeError: Field 'title' does not exist on model Book. Did the field name change?
