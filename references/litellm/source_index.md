# LiteLLM Source Index

This index provides curated grep-targets for the local clone of the LiteLLM source tree (`~/.cache/litellm-debug/sources/litellm@<version>/`).

When investigating a deeper issue (e.g., during Telemetry or Admin investigations), use this index to know *where* to look in the source without having to search blindly.

## Core Routing
- **Main Proxy Router:** `litellm/proxy/proxy_server.py`
  - Look here for the FastAPI endpoints (`/v1/chat/completions`, etc.).
- **Router Logic (Load Balancing):** `litellm/router.py`
  - Look here for model routing, fallbacks, and load balancing rules.

## Provider Transformations
LiteLLM transforms OpenAI-format requests into provider-specific formats.
- **Provider Transformer Mappings:** `litellm/llms/`
  - Each subfolder (e.g., `anthropic/`, `bedrock/`, `azure/`) contains specific translation logic.
  - Specifically, `litellm/llms/<provider>/chat/transformation.py` handles input/output mappings.

## Callbacks & Telemetry
If a trace is missing or spend isn't logging, check the callback architecture.
- **Callback Manager:** `litellm/utils.py` (Search for `CustomLogger` or `success_callback`)
- **Langfuse Integration:** `litellm/integrations/langfuse.py`

## Auth & Key Scoping
- **Key Validation:** `litellm/proxy/auth/auth_checks.py`
- **User/Team Scoping:** `litellm/proxy/auth/user_api_key_auth.py`

## Spend Logging
- **Cost Calculation:** `litellm/utils.py` (Search for `completion_cost`)
- **DB Logging:** `litellm/proxy/utils/db_logging.py`

---
*Tip: Always ensure you are reading the source clone that matches the `LITELLM_VERSION_PRIMARY` deployed in your environment.*
