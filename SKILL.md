---
name: litellm-debug
description: Investigates and debugs LiteLLM proxy deployments across Public, User, Admin, Telemetry, and Database tiers. Use this to diagnose degraded proxies, authentication issues, and trace tool-call sequences.
---
# LiteLLM Debug Skill

Project guidance for AI agents interacting with this repository.

This project implements the [Agent Skills](https://agentskills.io/) open format. It is a skill for debugging LiteLLM proxy deployments fronting agentic AI workloads. Read-side and investigative.

## Read first

In order:
1. `dev/intent.md` — what this skill is and isn't.
2. `dev/roadmap.md` — work plan with acceptance criteria.
3. `dev/decisions.md` — architectural decision log; durable principles.
4. `dev/practices.md` — normative development and tooling practices.

## Core principles

- **Tier model:** Public / User / Admin / Telemetry / Database. Use the lowest tier that can answer the question. Never default to the highest available.
- **Playbook Routing:** When a user asks you to investigate or debug a specific tier, ALWAYS read the corresponding playbook in `playbooks/` (e.g., `playbooks/public.md`) first to understand the execution flow and required output format.
- **Spec anchoring:** never reference an endpoint or schema column without naming the LiteLLM version it applies to. Everything traces to `references/litellm/spec/<version>/`.
- **Upstream-only:** spec material derives from the LiteLLM upstream repo at the pinned version. No third-party catalogs or curated indices.
- **Service-specific in subdirs:** `references/litellm/`, `scripts/litellm/`, `tests/litellm/`. Naming the seam early. We are not building a multi-service framework yet.
- **Onboarding by tier:** each tier needs exactly one more credential than the one below it. Tier tests act as the gate.
- **Multi-version:** two pinned slots, `primary` and `comparison`. Both default to latest stable; override via `LITELLM_VERSION_PRIMARY` / `LITELLM_VERSION_COMPARISON`.
- **Targeted Testing:** Filter inference tests via `LITELLM_TEST_MODEL` (`all`, `first`, or specific model ID) and `LITELLM_TEST_CAPABILITIES` (e.g., `text,roundtrip`).

## Conventions

- Tests are diagnostic. A missing credential should skip with a message naming the env var to set, not fail with a stack trace.
- New decisions append to `dev/decisions.md` with a fresh ID and date.
- Local source clones live outside the repo, at `~/.cache/litellm-debug/sources/litellm@<version>/`.
- Comments only when the WHY is non-obvious.
- No abstractions ahead of the second concrete need.

## Test running

```
pip install -r requirements.txt
pytest                              # all tiers; skip those without creds
pytest tests/litellm/public -v      # Public tier only (just LITELLM_BASE_URL)
pytest -m tier_admin                # by marker
```

Tier markers are auto-applied based on the test's path under `tests/litellm/<tier>/`.

## What this skill is not

Not a wrapper around the LiteLLM SDK. Not a management skill — scope is read-side investigation. Not a hosted service.
