# Intent

A Claude Code skill that supports debugging a LiteLLM proxy deployment
when it is fronting agentic AI workloads. Read-side and investigative.

## What this skill is

- A single skill, `litellm-debug`, that walks an investigation: detect
  what access is available, pick the lowest-fidelity tier that can
  answer the question, fetch and parse, and surface a diagnosis.
- A spec-anchored reference layer pinned to a specific LiteLLM version,
  so endpoint shapes, schema columns, and source paths are trustworthy
  rather than aspirational.
- A cross-cutting Source axis: a local clone of the LiteLLM repo at the
  pinned version, indexed enough to grep call sites and read provider
  transformers without round-tripping to GitHub.
- An onboarding ladder. Each tier requires exactly one more credential
  than the one below it. New users start at Public (only needs a base
  URL) and add credentials only as needed. Tier-specific tests act as
  the gate: a tier becomes "available" when its tests pass.

## What this skill is not

- Not a management skill. Scope is read-side investigation; managing
  proxy resources (users, keys, models) is out of scope.
- Not a wrapper around the LiteLLM SDK for using LiteLLM in app code.
- Not a hosted service. Everything runs locally; the only network
  calls are to the user's own LiteLLM proxy and (optionally) their
  telemetry backend and the LiteLLM upstream repo on GitHub.

## Access tier model

Five tiers, ordered by privilege ascending. The skill prefers the
lowest tier that can answer the question, not the highest available.

| Tier        | What it is                                       | Boundary respected? |
|-------------|--------------------------------------------------|---------------------|
| Public      | Unauthenticated health, metrics, model surface   | yes                 |
| User        | Virtual key, self-scoped                         | yes                 |
| Admin       | Master key, cross-user admin API                 | yes                 |
| Telemetry   | OTel / Langfuse / Helicone / Arize / S3 export   | yes (sanctioned)    |
| Database    | Direct Postgres access                           | no — escapes proxy  |

Telemetry sits above Admin in fidelity because traces include full
prompt/response payloads that the Admin API redacts. It still respects
the proxy's security model: the operator chose to export to a backend
with its own auth.

Database is last because it bypasses key scoping, per-team isolation,
and audit-log integrity. Tier of last resort, opt-in only.

## Source axis (cross-cutting)

Available at any tier. Two artifacts:

- A local clone of the LiteLLM upstream repo
  (`github.com/BerriAI/litellm`) checked out at the version matching
  the user's deployed proxy, kept under
  `~/.cache/litellm-debug/sources/litellm@<version>/`.
- A curated `references/litellm/source_index.md` that maps "where to
  grep" for the recurring questions: provider transformers, the proxy
  router, callback wiring, key auth, spend logging.

Indexing tools, in order of how often they pay off:
1. ripgrep — text search, fast enough that no index is needed.
2. ast-grep — structural queries when text isn't enough.
3. pyright/jedi — call graphs and type-aware navigation, only when (1)
   and (2) fail.

Version pinning is non-negotiable: a transformer fixed in v1.55 is
still buggy in a v1.52 deployment, and the Source axis is only
trustworthy when checked out at the version actually running.

## Spec anchoring

Before the first script runs, the skill captures a version-pinned spec
snapshot. This is the contract that everything else references.

Captured artifacts (per pinned LiteLLM version):

- `references/litellm/spec/<version>/openapi.json` — fetched from the
  proxy's `/openapi.json` endpoint, or from the source tree if
  unavailable.
- `references/litellm/spec/<version>/schema.prisma` — copied from the
  cloned source at the pinned tag. Authoritative for the Database tier.
- `references/litellm/spec/<version>/source_index.md` — curated paths
  into the cloned source for the questions that recur.

Refresh policy: re-pin when the user's deployed version differs from
the captured snapshot. The skill probes `/health` (or equivalent) on
each run and warns when drift is detected.

Multi-version: the skill maintains two pinned slots, `primary` and
`comparison`. Both default to the latest stable LiteLLM release;
either can be overridden via env (`LITELLM_VERSION_PRIMARY`,
`LITELLM_VERSION_COMPARISON`). This supports the prod-vs-test
debugging case directly: when the same workload behaves differently
across two deployed versions, the skill diffs the relevant pieces of
the OpenAPI, schema, and source tree to focus the investigation.

Source: spec material is sourced from the LiteLLM upstream repo
directly. The skill does not depend on third-party catalogs,
intermediaries, or curated collections for endpoint shapes, schema
definitions, or source paths.

## Generalization stance

About 60% of this skill is portable to any OSS service with deployed
instances; 40% is LiteLLM-specific.

Portable bones:
- The five-tier model
- The probe-then-route flow
- "Use the lowest tier that can answer the question"
- Version pinning + local source clone + curated source index
- Source-axis-as-cross-cutting

Service-specific:
- Endpoint paths and shapes
- DB schemas (some services have no DB; vLLM's equivalent is engine
  and KV-cache state introspection — different shape)
- Telemetry backends
- Provider/internals quirks index

Service-specific material is segregated under named subdirectories
(`references/litellm/`, `scripts/litellm/`, `tests/litellm/`) from day
one. This costs nothing now and makes a future `references/vllm/` an
obvious move.

We do **not** build a plugin loader, service registry, or shared
abstraction layer yet. Two services is the predecessor of the rule of
three; the real abstraction will emerge from the second concrete
implementation, not from upfront design.
