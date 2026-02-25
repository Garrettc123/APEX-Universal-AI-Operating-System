"""Pytest configuration and shared fixtures for the APEX test suite."""
import pytest


@pytest.fixture(scope="session")
def anyio_backend():
    """Use asyncio as the anyio backend (required by pytest-asyncio)."""
    return "asyncio"
