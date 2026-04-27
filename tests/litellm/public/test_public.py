"""Public-tier smoke tests — only LITELLM_BASE_URL required."""
import pytest
import requests


def test_proxy_liveliness(base_url):
    r = requests.get(f"{base_url}/health/liveliness", timeout=10)
    assert r.status_code == 200, (
        f"Expected 200 from /health/liveliness, got {r.status_code}. "
        f"Body: {r.text[:200]}"
    )


def test_proxy_readiness(base_url):
    # 503 is acceptable: the proxy is up but a dependency (DB, redis)
    # may be degraded. Surface it without failing the smoke test.
    r = requests.get(f"{base_url}/health/readiness", timeout=10)
    assert r.status_code in (200, 503), (
        f"Expected 200 or 503 from /health/readiness, got {r.status_code}. "
        f"Body: {r.text[:200]}"
    )


def test_models_list(base_url):
    # /v1/models is sometimes auth-gated depending on proxy config; treat
    # 401/403 as "deferred to User tier" rather than failure.
    r = requests.get(f"{base_url}/v1/models", timeout=10)
    if r.status_code in (401, 403):
        pytest.skip(
            f"/v1/models requires auth on this deployment "
            f"(got {r.status_code}). Set LITELLM_USER_KEY to test at "
            f"the User tier."
        )
    assert r.status_code == 200, (
        f"Expected 200 from /v1/models, got {r.status_code}. "
        f"Body: {r.text[:200]}"
    )
    assert "data" in r.json(), "Expected 'data' key in /v1/models response"


def test_metrics_endpoint(base_url):
    r = requests.get(f"{base_url}/metrics", timeout=10)
    if r.status_code == 404:
        pytest.skip(
            "/metrics not exposed; Prometheus may be disabled in this "
            "deployment's config."
        )
    assert r.status_code == 200, (
        f"Expected 200 from /metrics, got {r.status_code}."
    )
    body = r.text
    assert "# HELP" in body or "# TYPE" in body, (
        f"Response from /metrics doesn't look like Prometheus exposition "
        f"format. First 200 chars: {body[:200]}"
    )
