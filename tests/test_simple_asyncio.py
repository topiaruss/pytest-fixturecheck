"""Simple test for asyncio compatibility."""

import pytest
import asyncio
from pytest_fixturecheck import fixturecheck

# Skip all tests if asyncio mark is not available
asyncio_mark = getattr(pytest.mark, "asyncio", None)
if asyncio_mark is None:
    pytest.skip("pytest.mark.asyncio not available, skipping tests", allow_module_level=True)

# Simplified async test with direct fixture usage (no verification)
@pytest.fixture
async def simple_async_fixture():
    """A simple async fixture."""
    await asyncio.sleep(0.01)
    return "async value"

# Test using a fixture with @fixturecheck
@pytest.fixture
@fixturecheck
def normal_fixture():
    """A regular fixture that works with fixturecheck."""
    return "normal value"

# Run tests with different combinations of fixtures
def test_simple_normal(normal_fixture):
    """Test that our normal fixture with fixturecheck works."""
    assert normal_fixture == "normal value"

@pytest.mark.asyncio
async def test_simple_async(simple_async_fixture):
    """Test that a regular async fixture works."""
    assert await simple_async_fixture == "async value" 