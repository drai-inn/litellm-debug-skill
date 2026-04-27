# Roadmap

The skill is built tier-by-tier as an onboarding ladder: each tier
requires exactly one more credential than the one below, and ships
with executable tests that act as the gate.

Cross-cutting capabilities (spec capture, source axis, version diff)
sit alongside the tier work and feed multiple tiers — they are not on
the linear ladder.

## Tier work

### Test harness

Foundation for every tier-specific test. Gives users a runnable
`pytest` command with sensible skip behaviour before any credentials
are configured.

Tasks:
- `pyproject.toml` — pytest config (markers, testpaths).
- `requirements.txt` — pytest, requests, python-dotenv.
- `tests/conftest.py` — credential fixtures, `.env` loading,
  path-based tier-marker auto-tagging.
- `.env.example` — credential template, rung-by-rung.

**Required:** none.

**Acceptance:** `pytest` with no env vars set runs successfully and
skips all tier tests with messages naming the env var that would
unlock each.

### Public tier — `LITELLM_BASE_URL`

Smoke validation. Verifies the proxy is reachable using only
unauthenticated endpoints.

Tasks:
- `tests/litellm/public/test_public.py` — liveliness, readiness
  (200 or 503), `/v1/models` (skips if auth-gated), `/metrics`
  (skips if Prometheus disabled), `/ui/model_hub/` (skips if UI disabled),
  and public configuration endpoints (`/get/ui_settings`, `/public/endpoints`).
- `playbooks/public.md` — investigative walkthrough.

**Required:** `LITELLM_BASE_URL`.

**Acceptance:** with `LITELLM_BASE_URL` set, the four public tests
pass (or skip with informative messages) against a real proxy. The
skill can answer "is the proxy degraded?" end to end.

### User tier — + `LITELLM_USER_KEY`

Self-scoped investigation: what one virtual key did and why.

Tasks:
- `tests/litellm/user/` — `/key/info` self, `/user/info` self,
  completion roundtrip.
- `playbooks/user.md`.

**Required:** `LITELLM_BASE_URL` + `LITELLM_USER_KEY`.

**Acceptance:** user tier tests pass; the skill can answer "did my
last call succeed and why/why not?"

### Admin tier — + `LITELLM_MASTER_KEY`

Cross-user error patterns, audit reconstruction, spend correlation.

Tasks:
- `tests/litellm/admin/` — `/spend/logs`, `/global/spend/logs`,
  `/audit`, `/key/list`, `/user/list`, detailed `/health`.
- `playbooks/admin.md`.
- `references/litellm/api_endpoints.md` — endpoint catalog derived
  from the pinned `openapi.json` (see Spec capture, below).
- `scripts/litellm/fetch_spend_logs.py`.

**Required:** `LITELLM_BASE_URL` + `LITELLM_MASTER_KEY`.

**Acceptance:** admin tier tests pass; endpoint catalog is
regenerable from the spec snapshot.

**Depends on:** Spec capture (for the endpoint catalog).

### Telemetry tier — + Langfuse credentials

Full request/response retrieval, tool-call sequence reconstruction,
latency breakdown. Langfuse first; other backends added as real
sessions demand.

Tasks:
- `tests/litellm/telemetry/` — Langfuse trace fetch by trace_id,
  list recent traces.
- `playbooks/telemetry.md`.
- `scripts/litellm/fetch_langfuse.py`.
- `references/litellm/callback_backends.md` — Langfuse first.

**Required:** `LITELLM_BASE_URL` + `LANGFUSE_HOST` +
`LANGFUSE_PUBLIC_KEY` + `LANGFUSE_SECRET_KEY`.

**Acceptance:** given a failing agentic loop, the skill can retrieve
the full tool-call sequence and identify where it diverged.

### Database tier — + `LITELLM_DB_DSN` and `LITELLM_DB_OPTIN=1`

Tier of last resort. Direct Postgres access bypasses the proxy's
auth, scoping, and audit log. Requires explicit per-session opt-in
in addition to the DSN.

Tasks:
- `tests/litellm/database/` — schema-version probe, read-only SELECT
  against `LiteLLM_SpendLogs`. Tests refuse to run without opt-in.
- `playbooks/database.md`.
- `references/litellm/database_schema.md` — generated from the
  pinned `schema.prisma`.
- `scripts/litellm/query_db.py` — read-only by default,
  schema-version guard.

**Required:** `LITELLM_DB_DSN` + `LITELLM_DB_OPTIN=1`.

**Acceptance:** the tier refuses to run without explicit opt-in;
with opt-in, schema-version guard catches drift before query
execution.

**Depends on:** Spec capture (for the schema reference).

## Cross-cutting capabilities

### Spec capture — multi-version pinning, latest-default

Pin reference LiteLLM versions and snapshot the contracts (OpenAPI,
Prisma schema, source index). Sourced from LiteLLM upstream directly.
Feeds the Admin and Database tiers' references.

Tasks:
- Two pinned slots, `primary` and `comparison`. Both default to
  latest stable. Override via `LITELLM_VERSION_PRIMARY` and
  `LITELLM_VERSION_COMPARISON`.
- Per-version snapshots under `references/litellm/spec/<version>/`:
  `openapi.json`, `schema.prisma`, `source_index.md`.
- `scripts/litellm/spec_pin.py` — pins one or both slots,
  idempotent.
- `scripts/litellm/spec_diff.py` — diffs primary vs comparison.
- `references/litellm/spec/README.md` — refresh procedure.

**Required:** network access to GitHub.

**Acceptance:** from a fresh checkout with zero LiteLLM credentials,
both slots can be pinned and a diff produced between them.
Re-running with the same version is a no-op.

### Source axis tooling

A local clone of the LiteLLM source at the pinned version, plus a
curated index of where things live. Available at any tier.

Tasks:
- `scripts/litellm/source_sync.py` — clone or update LiteLLM source
  at the pinned versions, write to
  `~/.cache/litellm-debug/sources/litellm@<version>/`. Outside the
  repo.
- `references/litellm/source_index.md` — curated grep-targets:
  provider transformers, the proxy router, callback wiring, key
  auth, spend logging.
- One worked example: a debugging session that combines a Telemetry
  trace with a `litellm/llms/<provider>/transformation.py` read.

**Acceptance:** a debugging session that requires reading provider
transformation source can be completed without leaving the local
machine.

### Two-version comparison workflows

Lift the spec diff and source clone into investigative workflows
for the prod-vs-test debugging case.

Tasks:
- `playbooks/version_diff.md` — when to use, what to diff first
  (OpenAPI shape changes? Schema changes? Provider transformer
  changes?), how to focus the source read.
- One worked example: a structured diff that produced a one-file
  source read which identified the regression.

**Acceptance:** given two pinned versions exhibiting different
behaviour, the skill produces a structured diff that drives a
focused source-level investigation rather than a wide search.

**Depends on:** Spec capture and Source axis tooling.

## Future

### Generalization probe — vLLM

Discover which assumptions in the skill structure survive contact
with a second service. The point is not to ship vLLM support — it is
to inform whether to extract a shared layer or keep two parallel
skills.

Tasks:
- Sketch the same five tiers for vLLM. Note where they map cleanly
  and where they don't (Database tier is empty for vLLM; engine and
  KV-cache state introspection is the natural deepest tier).
- Identify candidate shared bones for extraction.
- Write findings in `dev/generalization_findings.md`.

**Acceptance:** a clear-eyed list of what generalizes, what doesn't,
and whether a second skill (`vllm-debug`) or a refactor (shared
`common/`) is the right move. No code change required at this stage.

## In flight

- Optional `.claude/settings.json` (project-level Claude Code
  settings, MCP server config). Not yet decided whether the skill
  benefits from prescribing any project-level Claude settings.

## Out of scope

- Hosting the skill as a service.
- A plugin loader or service registry across multiple OSS services.
- Telemetry backends beyond Langfuse, until a real session demands
  one.
