"""Test file to verify compatibility with pytest-asyncio."""

import asyncio
import inspect
import sys

import pytest

# Try to import pytest_asyncio, skip tests if not available
try:
    import pytest_asyncio

    PYTEST_ASYNCIO_AVAILABLE = True
except ImportError:
    PYTEST_ASYNCIO_AVAILABLE = False
    pytest.skip("pytest_asyncio not installed, skipping tests", allow_module_level=True)

from pytest_fixturecheck import fixturecheck

# Mark all tests in this module as async
pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture
@fixturecheck
async def async_fixture():
    """An async fixture that returns a string after an await."""
    await asyncio.sleep(0.01)
    return "async result"


@fixturecheck
@pytest_asyncio.fixture
async def async_fixture_order2():
    """An async fixture with different decorator order."""
    await asyncio.sleep(0.01)
    return "another async result"


async def test_async_fixture(async_fixture):
    """Test that async fixtures work with fixturecheck."""
    # Explicitly await the async fixture
    result = (
        await async_fixture if inspect.iscoroutine(async_fixture) else async_fixture
    )
    assert result == "async result"


async def test_async_fixture_order2(async_fixture_order2):
    """Test async fixture with alternative decorator order."""
    # Explicitly await the async fixture
    result = (
        await async_fixture_order2
        if inspect.iscoroutine(async_fixture_order2)
        else async_fixture_order2
    )
    assert result == "another async result"
