# CLAUDE.md

Project guidance for Claude Code sessions in this repo.

This is a Claude Code skill in development for debugging LiteLLM proxy
deployments fronting agentic AI workloads. Read-side and investigative.

## Read first

In order:
1. `dev/intent.md` — what this skill is and isn't.
2. `dev/roadmap.md` — current phase, acceptance criteria, what's next.
3. `dev/decisions.md` — architectural decision log; durable
   principles, not the narrative.

## Core principles

- **Tier model:** Public / User / Admin / Telemetry / Database. Use
  the lowest tier that can answer the question. Never default to the
  highest available.
- **Spec anchoring:** never reference an endpoint or schema column
  without naming the LiteLLM version it applies to. Everything traces
  to `references/litellm/spec/<version>/`.
- **Upstream-only:** spec material derives from the LiteLLM upstream
  repo at the pinned version. No third-party catalogs or curated
  indices.
- **Service-specific in subdirs:** `references/litellm/`,
  `scripts/litellm/`, `tests/litellm/`. Naming the seam early. We are
  not building a multi-service framework yet.
- **Onboarding by tier:** each tier needs exactly one more credential
  than the one below it. Tier tests act as the gate.
- **Multi-version:** two pinned slots, `primary` and `comparison`.
  Both default to latest stable; override via
  `LITELLM_VERSION_PRIMARY` / `LITELLM_VERSION_COMPARISON`.

## Conventions

- Tests are diagnostic. A missing credential should skip with a
  message naming the env var to set, not fail with a stack trace.
- New decisions append to `dev/decisions.md` with a fresh ID and date.
  Don't edit prior entries. Capture durable principles, not the
  narrative.
- Local source clones live outside the repo, at
  `~/.cache/litellm-debug/sources/litellm@<version>/`.
- Comments only when the WHY is non-obvious.
- No abstractions ahead of the second concrete need.

## Test running

Test framework is currently in flight (see "In flight" in
`dev/roadmap.md`). Once chosen, run from repo root; tests are
organized by tier under `tests/litellm/<tier>/`. Markers:
`tier_public`, `tier_user`, `tier_admin`, `tier_telemetry`,
`tier_database`.

## What this skill is not

Not a wrapper around the LiteLLM SDK. Not a management skill — scope
is read-side investigation. Not a hosted service.
