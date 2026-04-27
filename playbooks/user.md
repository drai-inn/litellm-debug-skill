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
*   **Model Selection:** Inference costs money and requires specific upstream capabilities. The diagnostic tool will attempt to use `LITELLM_TEST_MODEL` from the `.env` file. If unset, it will pick the first model returned by `/v1/models` and attempt a basic text completion, but will gracefully skip Vision/Tools if the model rejects them.

## Example Output (Level 0)

> **User Tier Diagnosis (Level 0):**
> 
> ▶ IDENTITY & SCOPING
>   🔑 Key Identity: Valid (Alias: `prod-agent-1`)
>   🛡️  Team/User:    Attached to `team_engineering`
>   💰 Budget:       $1.50 / $10.00 spent
>   🚦 Rate Limits:  1000 TPM / 100 RPM
> 
> ▶ MODEL ACCESS
>   🤖 Permitted:    14 models available via this key
>   
> *To investigate a specific failing request, or to view the raw JSON payloads for these permissions, run this script with `--level 1` or `--level 2`.*
