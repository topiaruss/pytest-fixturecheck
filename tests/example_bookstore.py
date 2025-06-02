"""
Example test file demonstrating pytest-fixturecheck with a bookstore scenario.

This is the example from the README that shows how fixtures can be
validated before tests run.
"""

import pytest

from pytest_fixturecheck import fixturecheck


# Simulate Django models for the example
class Author:
    def __init__(self, name):
        self.name = name


class Publisher:
    def __init__(self, name):
        self.name = name


class Book:
    def __init__(self, title, author, publisher):
        self.title = title
        self.author = author
        self.publisher = publisher


# Define fixtures with fixturecheck validation
@pytest.fixture
@fixturecheck()
def publisher():
    return Publisher(name="Willow House Press")


@pytest.fixture
@fixturecheck()
def author():
    return Author(name="Marian Brook")


@pytest.fixture
@fixturecheck()
def book(author, publisher):
    return Book(
        title="Echoes of the Riverbank",
        author=author,
        publisher=publisher,
    )


@pytest.fixture
@fixturecheck()
def sequel(book):
    return Book(
        title="Whispers in the Willow",
        author=book.author,
        publisher=book.publisher,
    )


# Tests that use the fixtures
def test_book_author(book, author):
    assert book.author == author


def test_sequel_author(sequel, author):
    assert sequel.author == author
