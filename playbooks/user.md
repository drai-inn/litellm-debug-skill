# User Tier Playbook

This playbook defines how the `litellm-debug` skill investigates the User tier of a LiteLLM deployment. The User tier relies on `LITELLM_USER_KEY` to investigate the perspective of a specific client or agent.

## Execution Flow (User Tier)

When a user asks to "debug the user tier" or "check my key", the skill should follow this loop:

1.  **Verify Environment:** Check if `LITELLM_BASE_URL` and `LITELLM_USER_KEY` are set. If not, instruct the user to configure them.
2.  **Execute Tests:** Run the `tests/litellm/user/` suite silently via `pytest`.
3.  **Run Diagnostics:** Run `scripts/litellm/diagnose_user.py --level 0` to fetch and parse the key's scoped permissions.
4.  **Surface Output:** Present the Dashboard summary (Level 0).
5.  **Offer Drill-down:** Explicitly ask if the user wants to see Level 1 (Diagnostics) or Level 2 (HTTP Traces & `curl` commands) for any specific endpoints.

## The Analytical Categories

The User tier diagnostic tool groups endpoints into the following logical sets:

### 1. Identity & Scoping
*Goal: Determine exactly who this key belongs to and what guardrails apply to it.*
*   **Endpoints:** `/key/info`, `/user/info`
*   **Key metrics to extract:**
    *   Key Alias / Token prefix
    *   Associated Team ID or User ID
    *   Spend vs Max Budget
    *   TPM/RPM (Token/Request per minute) limits

### 2. Permitted Model Surface
*Goal: Understand which models this specific key is allowed to route to.*
*   **Endpoints:** `/v1/models` (Auth-gated)
*   **Key metrics to extract:**
    *   Total number of models accessible by *this* key.
    *   (Optional drill down: checking if a specific model the user is failing on is actually in this list).

### 3. Inference Readiness (The "Full Surface")
*Goal: Verify if the proxy will successfully negotiate complex generative requests on behalf of this key.*
*   **Endpoint:** `/v1/chat/completions`
*   **Strategy:** Hitting the proxy with "Hello World" is insufficient for debugging agentic AI workloads. Modern agents use complex modalities. We must test the *fuller surface* of inference capabilities:
    1.  **Standard Text:** A simple `user` message to verify basic connectivity, routing, and budget enforcement.
    2.  **Tool Calling / Functions:** Submitting a payload with `tools` defined and forcing a `tool_choice` to ensure the proxy's parsers (and the upstream provider) properly handle structured schema requests without throwing 400 Bad Request errors.
    3.  **Vision / Media:** Submitting a multi-modal payload containing an `image_url` to verify the proxy correctly proxies or translates rich media requests for the given provider.
    4.  **Round-Trip / Multi-Turn:** Submitting a conversation that has previous `assistant` responses and requires retaining context. This verifies the proxy doesn't corrupt message history from turn to turn.
    5.  **Embeddings:** Submitting a payload to `/v1/embeddings` to verify vectorization support (critical for RAG workflows).
    6.  **Streaming:** Submitting a payload with `stream: true` to verify Server-Sent Events (SSE) stream back cleanly.
    7.  **JSON Mode:** Submitting a payload with `response_format: {"type": "json_object"}` to verify structured output forcing.
*   **Model Selection:** Inference costs money and requires specific upstream capabilities. The target models are configured via the `LITELLM_TEST_MODEL` environment variable:
    *   `all`: Exhaustively tests the full surface on *every* model returned by `/v1/models`.
    *   `first` (or unset): Acts as a quick smoke-test using the first permitted model.
    *   `<model_name>`: Isolates testing to a specific model or comma-separated list of models.
*   **Capabilities Filtering:** You can dynamically filter which capabilities are tested using the `LITELLM_TEST_CAPABILITIES` environment variable:
    *   `all` (default): Runs text, tools, vision, and roundtrip.
    *   `<capability>`: A comma-separated list (e.g., `text,roundtrip`) to isolate specific workloads. The resulting diagnostic matrix will dynamically adapt its columns to match.

    The script degrades gracefully: if a model explicitly rejects tools or vision with a 400 error, it is recorded as a capability limitation (`⚠️`) rather than a hard failure.

## Example Output (Level 0)

> **User Tier Diagnosis (Level 0):**
> 
> ▶ IDENTITY & SCOPING
>   🔑 Key Identity: Valid (Alias: `prod-agent-1`)
>   🛡️  Owner:        User `n.jones@auckland.ac.nz`
>   💰 Budget:       $1.50 / $10.00 spent
>   🚦 Rate Limits:  1000 TPM / 100 RPM
> 
> ▶ MODEL ACCESS
>   🤖 Permitted:    14 models available via this key
>
> ▶ INFERENCE READINESS
>   Model                           | Text | Tools | Vision | Round-Trip | Embed | Stream | JSON Mode |
>   --------------------------------+------+-------+--------+------------+-------+--------+-----------|
>   gpt-oss-20b                     |  ✅  |   ✅   |    ✅   |     ✅      |   ❌   |   ✅    |     ✅     |
>   gemini/gemini-flash-latest      |  ✅  |   ✅   |    ⚠️   |     ⚠️      |   ❌   |   ✅    |     ✅     |
>   
> *To investigate a specific failing request, or to view the raw JSON payloads for these permissions, run this script with `--level 1` or `--level 2`.*
