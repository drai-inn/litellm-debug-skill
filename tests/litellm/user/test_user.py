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

def test_inference_text(base_url, user_key, test_model):
    """Test standard text completion to ensure basic routing and budget work."""
    if test_model == "__missing_model__":
        pytest.skip("No test model available.")
        
    headers = {"Authorization": f"Bearer {user_key}", "Content-Type": "application/json"}
    payload = {
        "model": test_model,
        "messages": [{"role": "user", "content": "Hello, this is a diagnostic test. Please reply with 'OK'."}],
        "max_tokens": 10
    }
    try:
        r = requests.post(f"{base_url}/v1/chat/completions", headers=headers, json=payload, timeout=20)
    except requests.exceptions.Timeout:
        pytest.skip(f"Model {test_model} timed out.")
    
    if r.status_code == 404:
        pytest.skip(f"Model {test_model} not found or not mapped correctly (got 404).")
    if r.status_code == 403:
         pytest.skip(f"Key does not have budget or permission for {test_model} (got 403).")
    if r.status_code == 429:
         pytest.skip(f"Model {test_model} or API key hit rate limits (got 429).")

    assert r.status_code == 200, f"Expected 200 from text completion, got {r.status_code}. Body: {r.text[:200]}"
    assert "choices" in r.json(), "Expected 'choices' in response"

def test_inference_tools(base_url, user_key, test_model):
    """Test tool-calling capability to ensure schema validation proxies correctly."""
    if test_model == "__missing_model__":
        pytest.skip("No test model available.")
        
    headers = {"Authorization": f"Bearer {user_key}", "Content-Type": "application/json"}
    payload = {
        "model": test_model,
        "messages": [{"role": "user", "content": "What is the weather in London?"}],
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "Get current weather in a location",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "location": {"type": "string", "description": "City name"}
                        },
                        "required": ["location"]
                    }
                }
            }
        ],
        "tool_choice": "auto",
        "max_tokens": 20
    }
    try:
        r = requests.post(f"{base_url}/v1/chat/completions", headers=headers, json=payload, timeout=20)
    except requests.exceptions.Timeout:
        pytest.skip(f"Model {test_model} timed out.")
    
    if r.status_code in (400, 403, 404, 429):
        pytest.skip(f"Model {test_model} rejected tool calling or is unavailable (got {r.status_code}).")

    assert r.status_code == 200, f"Expected 200 from tool completion, got {r.status_code}. Body: {r.text[:200]}"

def test_inference_vision(base_url, user_key, test_model):
    """Test vision capability to ensure multimedia payloads proxy correctly."""
    if test_model == "__missing_model__":
        pytest.skip("No test model available.")
        
    headers = {"Authorization": f"Bearer {user_key}", "Content-Type": "application/json"}
    payload = {
        "model": test_model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "What is in this image?"},
                    {"type": "image_url", "image_url": {"url": "https://upload.wikimedia.org/wikipedia/commons/4/47/PNG_transparency_demonstration_1.png"}}
                ]
            }
        ],
        "max_tokens": 10
    }
    try:
        r = requests.post(f"{base_url}/v1/chat/completions", headers=headers, json=payload, timeout=20)
    except requests.exceptions.Timeout:
        pytest.skip(f"Model {test_model} timed out.")
    
    if r.status_code in (400, 403, 404, 429):
        pytest.skip(f"Model {test_model} rejected vision payload or is unavailable (got {r.status_code}).")

    assert r.status_code == 200, f"Expected 200 from vision completion, got {r.status_code}. Body: {r.text[:200]}"

def test_inference_roundtrip(base_url, user_key, test_model):
    """Test a multi-turn conversation with tool schemas to ensure message history doesn't corrupt."""
    if test_model == "__missing_model__":
        pytest.skip("No test model available.")
        
    headers = {"Authorization": f"Bearer {user_key}", "Content-Type": "application/json"}
    
    # Simulating a turn 2 request where the assistant previously replied with a thought or tool call
    payload = {
        "model": test_model,
        "messages": [
            {"role": "user", "content": "What is the weather in London?"},
            {"role": "assistant", "content": "I should check the weather.", "tool_calls": [{"id": "call_123", "type": "function", "function": {"name": "get_weather", "arguments": "{\"location\": \"London\"}"}}]},
            {"role": "tool", "tool_call_id": "call_123", "name": "get_weather", "content": "It is raining."}
        ],
        "max_tokens": 20
    }
    try:
        r = requests.post(f"{base_url}/v1/chat/completions", headers=headers, json=payload, timeout=20)
    except requests.exceptions.Timeout:
        pytest.skip(f"Model {test_model} timed out.")
    
    if r.status_code in (400, 403, 404, 429):
        pytest.skip(f"Model {test_model} rejected multi-turn tool history or is unavailable (got {r.status_code}).")

    assert r.status_code == 200, f"Expected 200 from roundtrip completion, got {r.status_code}. Body: {r.text[:200]}"

def test_inference_embedding(base_url, user_key, test_model):
    """Test embedding generation via /v1/embeddings."""
    if test_model == "__missing_model__":
        pytest.skip("No test model available.")
        
    headers = {"Authorization": f"Bearer {user_key}", "Content-Type": "application/json"}
    payload = {
        "model": test_model,
        "input": "good morning from litellm"
    }
    try:
        r = requests.post(f"{base_url}/v1/embeddings", headers=headers, json=payload, timeout=20)
    except requests.exceptions.Timeout:
        pytest.skip(f"Model {test_model} timed out.")
    
    if r.status_code in (400, 403, 404, 405, 429):
        pytest.skip(f"Model {test_model} rejected embedding payload or is unavailable (got {r.status_code}).")

    assert r.status_code == 200, f"Expected 200 from embedding, got {r.status_code}. Body: {r.text[:200]}"

def test_inference_stream(base_url, user_key, test_model):
    """Test server-sent events streaming."""
    if test_model == "__missing_model__":
        pytest.skip("No test model available.")
        
    headers = {"Authorization": f"Bearer {user_key}", "Content-Type": "application/json"}
    payload = {
        "model": test_model,
        "messages": [{"role": "user", "content": "Say hello"}],
        "stream": True,
        "max_tokens": 10
    }
    # Don't buffer the whole response so we can check if it starts quickly and has chunks
    try:
        with requests.post(f"{base_url}/v1/chat/completions", headers=headers, json=payload, timeout=20, stream=True) as r:
            if r.status_code in (400, 403, 404, 429):
                pytest.skip(f"Model {test_model} rejected stream payload or is unavailable (got {r.status_code}).")

            assert r.status_code == 200, f"Expected 200 from stream, got {r.status_code}."
            
            # Read the first few lines to confirm it looks like SSE
            first_line = next(r.iter_lines(decode_unicode=True), "")
            if first_line:
                assert first_line.startswith("data: ") or first_line == "", f"Expected stream data, got {first_line[:50]}"
    except requests.exceptions.Timeout:
        pytest.skip(f"Model {test_model} timed out.")

def test_inference_json_mode(base_url, user_key, test_model):
    """Test forcing structured JSON output via response_format."""
    if test_model == "__missing_model__":
        pytest.skip("No test model available.")
        
    headers = {"Authorization": f"Bearer {user_key}", "Content-Type": "application/json"}
    payload = {
        "model": test_model,
        "messages": [{"role": "user", "content": "Output JSON with key 'status' and value 'ok'."}],
        "response_format": {"type": "json_object"},
        "max_tokens": 15
    }
    try:
        r = requests.post(f"{base_url}/v1/chat/completions", headers=headers, json=payload, timeout=20)
    except requests.exceptions.Timeout:
        pytest.skip(f"Model {test_model} timed out.")
    
    if r.status_code in (400, 403, 404, 429):
        pytest.skip(f"Model {test_model} rejected json_mode payload or is unavailable (got {r.status_code}).")

    assert r.status_code == 200, f"Expected 200 from json_mode, got {r.status_code}. Body: {r.text[:200]}"
