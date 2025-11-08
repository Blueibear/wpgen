# tests/conftest.py
from __future__ import annotations
import os
import pytest

REQUIRED_PROVIDER = "mock"

@pytest.fixture(autouse=True, scope="session")
def _force_mock_provider():
    # Force deterministic, offline testing
    os.environ["WPGEN_PROVIDER"] = REQUIRED_PROVIDER
    os.environ.setdefault("WPGEN_CHECK_MODELS", "0")
    os.environ.setdefault("WPGEN_OFFLINE_TESTS", "1")
    os.environ.setdefault("NO_COLOR", "1")

    # Fail fast if something overrides it
    val = os.getenv("WPGEN_PROVIDER", "")
    assert val == REQUIRED_PROVIDER, f"Expected WPGEN_PROVIDER={REQUIRED_PROVIDER}, got {val}"
