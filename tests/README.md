# Test Suite Documentation

This directory contains the test harness that validates the behavior of a LiteLLM proxy deployment. Tests are organized into tiers based on the credentials required to run them.

## The Onboarding Ladder

Our tests act as an onboarding ladder. Each tier builds upon the last. You can run the entire suite at once (`pytest tests/`), and any tests for which you haven't provided credentials will skip gracefully with an informative message.

## Public Tier (`tests/litellm/public/`)
**Requires:** `LITELLM_BASE_URL`

These tests validate the public attack surface and health of the proxy. No authentication is provided.

| Test | Endpoint(s) | Passes when |
|------|-------------|-------------|
| `test_proxy_liveliness` | `/health/liveliness` | Returns 200 |
| `test_proxy_readiness` | `/health/readiness` | Returns 200 (healthy) or 503 (degraded dependencies) |
| `test_metrics_endpoint` | `/metrics` | Returns Prometheus format (skips if 404) |
| `test_models_list` | `/v1/models` | Returns 200 (skips if properly auth-gated with 401/403) |
| `test_identity_endpoints` | `/.well-known/jwks.json`<br>`/.well-known/openid-configuration` | Returns 200 or 404 |
| `test_ui_model_hub` | `/ui/model_hub/` | Returns 200 (skips if 404) |
| `test_ui_configuration_endpoints` | `/.well-known/litellm-ui-config`<br>`/get/ui_settings`<br>`/public/model_hub/info` | Returns 200 |
| `test_service_discovery_endpoints` | `/public/endpoints`<br>`/claude-code/marketplace.json`<br>`/public/agents/fields`<br>`/public/litellm_blog_posts`<br>`/public/providers/fields` | Returns 200 |

## User Tier (`tests/litellm/user/`)
*Coming in Phase 2.*
**Requires:** `LITELLM_BASE_URL` + `LITELLM_USER_KEY`

## Admin Tier (`tests/litellm/admin/`)
*Coming in Phase 3.*
**Requires:** `LITELLM_BASE_URL` + `LITELLM_MASTER_KEY`

## Telemetry Tier (`tests/litellm/telemetry/`)
*Coming in Phase 4.*
**Requires:** `LITELLM_BASE_URL` + Telemetry Backend Credentials

## Database Tier (`tests/litellm/database/`)
*Coming in Phase 5.*
**Requires:** `LITELLM_DB_DSN` + `LITELLM_DB_OPTIN=1`