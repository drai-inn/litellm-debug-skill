"""User-tier tests — requires LITELLM_BASE_URL and LITELLM_USER_KEY."""
import pytest
import requests

def test_user_key_info(base_url, user_key):
    """
    Validate the user key via /key/info.
    
    If the proxy restricts `/key/info` to admins only (or if the key is invalid),
    we catch the 401/403 and skip this specific validation test.
    """
    headers = {"Authorization": f"Bearer {user_key}"}
    r = requests.get(f"{base_url}/key/info", headers=headers, timeout=10)
    
    if r.status_code in (401, 403):
        pytest.skip(
            f"LITELLM_USER_KEY could not access /key/info (got {r.status_code}). "
            f"The key might be invalid, or this proxy may restrict /key/info to Admin keys."
        )
        
    assert r.status_code == 200, (
        f"Expected 200 from /key/info, got {r.status_code}. "
        f"Body: {r.text[:200]}"
    )
    
    data = r.json()
    assert isinstance(data, dict), "Expected JSON dictionary from /key/info"

def test_user_info(base_url, user_key):
    """Test retrieving user-level information via /user/info."""
    headers = {"Authorization": f"Bearer {user_key}"}
    r = requests.get(f"{base_url}/user/info", headers=headers, timeout=10)
    
    if r.status_code in (401, 403):
        pytest.skip(
            f"LITELLM_USER_KEY could not access /user/info (got {r.status_code})."
        )
        
    assert r.status_code == 200, f"Expected 200 from /user/info, got {r.status_code}."
    assert "user_info" in r.json() or "user_id" in r.json(), "Expected user metadata in /user/info response"

def test_models_list_with_key(base_url, user_key):
    """Test if we can list permitted models using the user key."""
    headers = {"Authorization": f"Bearer {user_key}"}
    r = requests.get(f"{base_url}/v1/models", headers=headers, timeout=10)
    
    if r.status_code in (401, 403):
        pytest.fail(
            f"LITELLM_USER_KEY is invalid or lacks permissions to list models. "
            f"/v1/models returned {r.status_code}. Body: {r.text[:200]}"
        )
        
    assert r.status_code == 200, (
        f"Expected 200 from /v1/models, got {r.status_code}. "
        f"Body: {r.text[:200]}"
    )
    assert "data" in r.json(), "Expected 'data' key in /v1/models response"
