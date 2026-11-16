"""Runtime fixtures for generated scenarios (executed by agent_app/services/runner.py)."""
import os

import pytest


@pytest.fixture(scope="session")
def aut_url() -> str:
    return os.environ.get("AUT_URL", "http://localhost:8000")


@pytest.fixture(autouse=True)
def _short_timeouts(page):
    page.set_default_timeout(4000)
