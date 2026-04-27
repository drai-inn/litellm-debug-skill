"""Shared pytest fixtures and tier-marker auto-tagging."""
import os
import pytest

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


_TIERS = ("public", "user", "admin", "telemetry", "database")


def pytest_collection_modifyitems(config, items):
    """Auto-mark tests by tier based on their path under tests/litellm/<tier>/."""
    for item in items:
        path = str(item.fspath)
        for tier in _TIERS:
            if f"/litellm/{tier}/" in path:
                item.add_marker(getattr(pytest.mark, f"tier_{tier}"))
                break


@pytest.fixture(scope="session")
def base_url():
    url = os.environ.get("LITELLM_BASE_URL")
    if not url:
        pytest.skip(
            "LITELLM_BASE_URL is not set. "
            "Copy .env.example to .env and set it to your LiteLLM proxy URL "
            "to enable Public-tier tests."
        )
    return url.rstrip("/")
