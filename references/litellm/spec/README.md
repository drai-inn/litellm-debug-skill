# Spec Capture Reference

This directory (`references/litellm/spec/`) contains pinned snapshots of the LiteLLM OpenAPI specification and Database Schema (`schema.prisma`).

## Purpose

These files provide an unchanging, trustworthy reference for the skill. Rather than probing a live proxy that may change its shape or missing an API endpoint because of auth, we snapshot the "source of truth" from upstream LiteLLM.

## How to Refresh

Whenever you need to debug a new proxy version or compare prod vs staging:

1. Update your `.env` with the versions:
```env
LITELLM_VERSION_PRIMARY=v1.55.0
LITELLM_VERSION_COMPARISON=v1.54.0
```

2. Run the spec pin script:
```bash
python scripts/litellm/spec_pin.py
```

This will download `openapi.json` and `schema.prisma` for the specified versions into subdirectories like `references/litellm/spec/v1.55.0/`.
