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

@pytest.fixture(scope="session")
def user_key():
    key = os.environ.get("LITELLM_USER_KEY")
    if not key:
        pytest.skip(
            "LITELLM_USER_KEY is not set. "
            "Set it in .env to enable User-tier tests."
        )
    return key

@pytest.fixture(scope="session")
def test_model(base_url, user_key):
    model = os.environ.get("LITELLM_TEST_MODEL")
    if model:
        return model
        
    # Attempt to fetch from /v1/models as fallback
    try:
        headers = {"Authorization": f"Bearer {user_key}"}
        r = requests.get(f"{base_url}/v1/models", headers=headers, timeout=5)
        if r.status_code == 200:
            data = r.json()
            models = data.get("data", [])
            if models:
                return models[0].get("id")
    except Exception:
        pass
        
    pytest.skip("No LITELLM_TEST_MODEL provided and could not fetch fallback from /v1/models.")
