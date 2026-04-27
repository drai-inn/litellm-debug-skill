# Roadmap

Living document. Revisit at the end of each phase.

The phases double as an onboarding ladder. Each phase requires exactly
one more credential than the one below. New users start at Phase 3
(Public — only needs a base URL) and add credentials as they go. Each
tier ships with executable tests; passing the tests is the gate.

**Current phase:** Phase 3 — Public tier shipped alongside Phase 2 test
harness, to give a working validation flow as early as possible.
**Phase 1 (spec capture) is deferred** until after first end-user
validation; Public-tier liveness/readiness/models/metrics tests do not
depend on a pinned spec.
**Next phase:** Phase 4 — User tier, OR loop back to Phase 1 once the
Public-tier validation has been exercised against a real proxy.

## Phase 0 — Design seed

Capture the tier model, source axis, spec-anchoring principle,
two-version comparison, onboarding-by-tier framing, and the
generalization stance in `dev/intent.md`. Stand up the repo
scaffold (CLAUDE.md, README.md, CONTRIBUTING.md, LICENSE, .gitignore)
and the durable architectural decisions in `dev/decisions.md`.

**Acceptance:** dev/ seeded with intent, roadmap, decisions. Repo
scaffold in place. `git init` complete. First clean commit landed.

## Phase 1 — Spec capture (multi-version, latest-default)

Pin reference LiteLLM versions and snapshot the contracts, sourced
from LiteLLM upstream directly.

Tasks:
1. Two pinned slots: `primary` and `comparison`. Both default to the
   latest stable release tag at pinning time. Either can be overridden
   via `LITELLM_VERSION_PRIMARY` and `LITELLM_VERSION_COMPARISON`.
2. Per-version snapshot artifacts under
   `references/litellm/spec/<version>/`:
   - `openapi.json` — fetched from a running proxy at that version, or
     reconstructed from the source tree if no proxy is available.
   - `schema.prisma` — copied from `litellm/proxy/schema.prisma` in the
     source clone at the pinned tag.
   - `source_index.md` — curated paths into the cloned source for the
     questions that recur (provider transformers, router, callback
     wiring, key auth, spend logging).
3. `scripts/litellm/spec_pin.py` — pins one or both slots, writes the
   snapshot, idempotent and re-runnable.
4. `scripts/litellm/spec_diff.py` — diffs `primary` vs `comparison`
   across all three artifacts. Output is human-readable plus a
   structured form the skill can use to focus an investigation.
5. `references/litellm/spec/README.md` — refresh procedure.

**Required to run:** network access to GitHub. No LiteLLM credentials.

**Acceptance:** from a fresh checkout with zero LiteLLM credentials,
both slots can be pinned and a diff produced between them, all from
local files after the initial fetch. Re-running with the same version
is a no-op.

## Phase 2 — Test harness + skill scaffold

Set up the test runner. Tests are organized by tier and skip cleanly
when their tier's credentials are not in env (with a message
explaining what to set).

Tasks:
1. `pyproject.toml` (or `requirements.txt`) — test runner, requests,
   optional psycopg for the Database tier (only imported when used).
2. `tests/conftest.py` — credential fixtures, env-driven skip logic.
3. `tests/litellm/<tier>/` directories scaffolded for each tier.
4. Test markers for each tier (`tier_public`, `tier_user`, `tier_admin`,
   `tier_telemetry`, `tier_database`).
5. `SKILL.md` — frontmatter (name, description, allowed-tools), workflow
   pointing at the tier playbooks.
6. `scripts/litellm/probe_tiers.py` — given env vars, probes each tier
   and reports which are available. Side-effect-free.
7. `.env.example` — credential template covering all tiers.

**Required to run:** nothing.

**Acceptance:** the test command with no env vars set runs successfully
and skips all tier tests with informative messages saying what to
provide. Adding a credential lights up the corresponding tier's tests.

## Phase 3 — Public tier (LITELLM_BASE_URL only)

The first onboarding rung. The user provides only a base URL.

Tasks:
- `tests/litellm/public/` — liveliness, readiness, `/v1/models`
  reachable, `/metrics` exposed (or warn if not).
- `playbooks/public.md` — health, model surface, Prometheus metrics.

**Required to run:** `LITELLM_BASE_URL`.

**Acceptance:** with `LITELLM_BASE_URL` set, public tier tests pass
against a real proxy. The skill can answer "is the proxy degraded?"
end to end.

## Phase 4 — User tier (+ LITELLM_USER_KEY)

The user provides any virtual key (not necessarily admin).

Tasks:
- `tests/litellm/user/` — `/key/info` self, `/user/info` self,
  completion roundtrip.
- `playbooks/user.md` — self-scoped repro, single-request
  investigation.

**Required to run:** `LITELLM_BASE_URL` + `LITELLM_USER_KEY`.

**Acceptance:** with `LITELLM_USER_KEY` set, user tier tests pass. The
skill can answer "did my last call succeed and why/why not?"

## Phase 5 — Admin tier (+ LITELLM_MASTER_KEY)

The user provides a master key.

Tasks:
- `tests/litellm/admin/` — `/spend/logs`, `/global/spend/logs`,
  `/audit`, `/key/list`, `/user/list`, detailed `/health`.
- `playbooks/admin.md` — cross-user error patterns, audit
  reconstruction, spend correlation.
- `references/litellm/api_endpoints.md` — endpoint catalog derived
  from the pinned `openapi.json` (Phase 1 artifact).
- `scripts/litellm/fetch_spend_logs.py` — paginated fetch, parse,
  summarize.

**Required to run:** `LITELLM_BASE_URL` + `LITELLM_MASTER_KEY`.

**Acceptance:** admin tier tests pass; endpoint catalog reflects the
pinned version and is regenerable from the snapshot.

## Phase 6 — Telemetry tier (+ Langfuse credentials)

Build one backend well first. Langfuse is the most common LiteLLM
telemetry backend.

Tasks:
- `tests/litellm/telemetry/` — Langfuse trace fetch by trace_id, list
  recent traces.
- `playbooks/telemetry.md` — full request/response retrieval,
  tool-call sequence reconstruction, latency breakdown.
- `scripts/litellm/fetch_langfuse.py`.
- `references/litellm/callback_backends.md` — Langfuse first; sections
  for Helicone/Arize/OTel/S3 added as real sessions demand them.

**Required to run:** `LITELLM_BASE_URL` + `LANGFUSE_HOST` +
`LANGFUSE_PUBLIC_KEY` + `LANGFUSE_SECRET_KEY`.

**Acceptance:** given a failing agentic loop, the skill can retrieve
the full tool-call sequence and identify where it diverged.

## Phase 7 — Database tier (+ DSN, opt-in gated)

Last and most invasive. Requires explicit per-session opt-in via
`LITELLM_DB_OPTIN=1` in addition to the DSN, so the credential alone
does not unlock the tier.

Tasks:
- `tests/litellm/database/` — schema-version probe, read-only SELECT
  against `LiteLLM_SpendLogs`. Tests refuse to run without opt-in.
- `playbooks/database.md` — when to use, safe query patterns, schema
  drift handling.
- `references/litellm/database_schema.md` — table-by-table reference,
  generated from the pinned `schema.prisma`.
- `scripts/litellm/query_db.py` — read-only by default, schema-version
  guard before query execution, query templates for recurring
  correlations.

**Required to run:** `LITELLM_DB_DSN` + `LITELLM_DB_OPTIN=1`.

**Acceptance:** skill refuses to use this tier without explicit
opt-in; when invoked, schema-version guard catches drift before query
execution.

## Phase 8 — Source axis tooling

Cross-cutting; can land any time after Phase 1 but is most useful
after Phase 5+.

Tasks:
- `scripts/litellm/source_sync.py` — clone or update LiteLLM source at
  the pinned versions, write to
  `~/.cache/litellm-debug/sources/litellm@<version>/`. Outside the
  repo.
- `references/litellm/source_index.md` — extend the Phase 1 stub with
  recurring grep-targets discovered while building Phases 3–6.
- One worked example: a debugging session that combines a Telemetry
  trace with a `litellm/llms/<provider>/transformation.py` read.

**Acceptance:** a debugging session that requires reading provider
transformation source can be completed without leaving the local
machine.

## Phase 9 — Two-version comparison workflows

Lift the Phase 1 spec diff and Phase 8 source clone into investigative
workflows. The motivating case: prod runs version X, test runs version
Y, the bug appears in Y but not X.

Tasks:
- `playbooks/version_diff.md` — when to use, what to diff first
  (OpenAPI shape changes? Schema changes? Provider transformer
  changes?), how to focus the source read.
- One worked example: a structured diff that produced a one-file
  source read which identified the regression.

**Acceptance:** given two pinned versions exhibiting different
behaviour, the skill can produce a structured diff that drives a
focused source-level investigation rather than a wide search.

## Phase 10 — Generalization probe (vLLM)

Try vLLM. The point is not to ship vLLM support — it is to discover
which assumptions in the skill structure survive contact with a second
service.

Tasks:
- Sketch the same five tiers for vLLM. Note where they map cleanly and
  where they don't (Database tier is empty for vLLM; engine and KV-cache
  state introspection is the natural deepest tier).
- Identify candidate shared bones for extraction.
- Write findings in `dev/generalization_findings.md`.

**Acceptance:** a clear-eyed list of what generalizes, what doesn't,
and whether a second skill (`vllm-debug`) or a refactor (shared
`common/`) is the right move. No code change required.

## In flight (not yet decided)

- Test framework choice. Roadmap currently assumes pytest as the
  default for Python. Alignment with the broader Agent Skills standard
  (https://agentskills.io) is a related open question — the standard
  prescribes file structure and frontmatter but does not opine on test
  framework. Decide before Phase 2 lands.
- Optional `.claude/settings.json` (project-level Claude Code
  settings, MCP server config). Defer until a concrete need surfaces.

## Out of scope (for now)

- Hosting the skill as a service.
- A plugin loader or service registry across multiple OSS services.
- Telemetry backends other than Langfuse, until a real session
  demands one.
