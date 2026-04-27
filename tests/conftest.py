"""Shared pytest fixtures and tier-marker auto-tagging."""
import os
import pytest
import requests

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

def pytest_generate_tests(metafunc):
    if "test_model" in metafunc.fixturenames:
        base_url = os.environ.get("LITELLM_BASE_URL", "").rstrip("/")
        user_key = os.environ.get("LITELLM_USER_KEY")
        test_model_env = os.environ.get("LITELLM_TEST_MODEL", "first")
        
        models_to_test = []
        if test_model_env not in ("all", "first"):
            # Comma-separated list or single model
            models_to_test = [m.strip() for m in test_model_env.split(",") if m.strip()]
        else:
            if base_url and user_key:
                try:
                    r = requests.get(f"{base_url}/v1/models", headers={"Authorization": f"Bearer {user_key}"}, timeout=5)
                    if r.status_code == 200:
                        data = r.json().get("data", [])
                        if data:
                            if test_model_env == "first":
                                models_to_test = [data[0]["id"]]
                            elif test_model_env == "all":
                                models_to_test = [m["id"] for m in data]
                except Exception:
                    pass
        
        if not models_to_test:
            # Dummy to ensure tests run and skip rather than fail collection
            models_to_test = ["__missing_model__"]
            
        metafunc.parametrize("test_model", models_to_test)
