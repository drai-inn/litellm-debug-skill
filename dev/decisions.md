# Decisions

Append-only architectural decisions. Each entry: ID, date, decision,
why, alternatives considered. Capture durable principles, not the
narrative of arriving at them.

---

## D001 — Five-tier access model

**Date:** 2026-04-27

Adopt Public / User / Admin / Telemetry / Database as the access tier
model, ordered by privilege ascending. Names plainly convey the security
implication at each tier rather than abstracting it. The skill prefers
the lowest tier that can answer the question, not the highest available.

**Why:** debugging LLM proxy deployments spans wildly different access
situations. Coarser models collapse meaningful distinctions (User vs
Admin, Telemetry vs Database); free-form capability lists give no
ordering to drive "lowest tier first" routing. Plain names matter
because the framing affects who is willing to grant which access.

**Alternatives considered:**
- Three tiers (public / authenticated / privileged) — too coarse.
- Free-form capability list — no ordering.
- Euphemistic names (Privileged / Direct / Root) — hide the security
  implication of bypassing the application's auth model.

---

## D002 — Spec anchoring before tier code

**Date:** 2026-04-27

The skill captures a version-pinned spec snapshot — OpenAPI, schema
definitions, source index — before any tier-specific script is written.
Every subsequent reference to an endpoint, schema column, or source
path traces back to this snapshot.

**Why:** without a pinned spec, probes and parsers ossify against
whichever version was probed at write-time. Endpoints drift, schemas
shift between minor releases, internal modules change. A pinned
snapshot per version is the only way to make diagnostic claims
trustworthy across the deployments the skill encounters.

**Alternatives considered:**
- Live-fetch on every invocation — slow, brittle if the proxy is the
  thing being debugged, hides version drift.
- Reference upstream docs by URL only — fine for a single CRUD
  operation, insufficient for a skill that joins logs and reads
  schemas.

---

## D003 — Service-specific subdirectories from day one

**Date:** 2026-04-27

Service-specific material lives under named subdirectories from the
start: `references/<service>/`, `scripts/<service>/`, `tests/<service>/`.
The portable bones (tier model, probe-route flow, version pinning,
source-axis pattern) sit at the top level.

**Why:** naming the seam early costs nothing. The cost of refactoring
later if a second service is added is real. A plugin loader or service
registry is premature with one service; wait until the third concrete
need before extracting an abstraction.

**Alternatives considered:**
- Flat layout, refactor later — same end state, burns a refactor.
- Plugin loader / service registry now — premature abstraction.

---

## D004 — Test-driven onboarding ladder

**Date:** 2026-04-27

Each tier ships with executable tests. Tests skip cleanly (with a
message naming the missing env var) when their tier's credentials are
not provided. Passing the tests is the gate to using the tier.

**Why:** the first-run experience needs to be useful with the minimum
possible information — typically just a base URL. A test-driven
onboarding ladder gives the user a green light at the lowest privilege
rung, then a clear next step to unlock the next. Tests double as
documentation that is provably true at run time, against the user's
actual deployment — a stronger contract than prose.

**Alternatives considered:**
- Single setup script with prompts — opaque, not re-runnable as a
  verification artifact.
- Documentation-only onboarding — drifts, doesn't catch deployment
  variation.
- Mock-based tests — defeats the point. Tests must run against the
  user's deployment.

---

## D005 — Multi-version pinning, latest by default

**Date:** 2026-04-27

The skill maintains two pinned version slots, `primary` and
`comparison`. Both default to the latest stable release tag. Either
can be overridden via env. Spec snapshots, source clones, and diff
tools all support both slots concurrently.

**Why:** a recurring debugging case is "prod is on version X, test is
on version Y, the same workload behaves differently." A single pinned
slot can't express this; two slots make the comparison a first-class
operation. Defaulting both to latest keeps the simple case simple —
most users never touch the comparison slot until they need it.

**Alternatives considered:**
- One pinned slot with manual re-pinning to compare — loses the
  workflow and any cached comparison artifacts.
- N pinned slots — overkill; two covers prod/test, dev/staging, and
  most version-drift questions.

---

## D006 — Upstream-only spec sources

**Date:** 2026-04-27

All spec material is sourced from the project being debugged, directly
upstream. The skill does not depend on third-party catalogs, curated
collections, or community indices for endpoint shapes, schema
definitions, or source paths.

**Why:** any third-party intermediary introduces a transitive
maintenance dependency we do not control. Such sources can drift, go
stale, or disappear, and the skill's diagnostic claims become harder
to trace. Re-deriving from the upstream project at a pinned version
is the only refresh path that keeps the snapshot honest.

**Alternatives considered:**
- Lift content from third-party catalogs with attribution — speeds up
  initial work but creates a long-tail maintenance issue.
- Maintain our own catalog upstream-of-upstream — overkill; the

---

## D007 — Progressive disclosure & explicit verbosity levels

**Date:** 2026-04-27

The skill surfaces output to the user using progressive disclosure modeled on CLI verbosity levels: Level 0 (Summary/Traffic Light), Level 1 (Diagnostics/The "Why"), and Level 2 (Trace/The "Receipts"). The skill defaults to Level 0 and explicitly offers drill-down.

**Why:** raw JSON and stack traces overwhelm users. A world-class debugging experience respects the user's time by providing actionable business-logic summaries first (like SRE runbooks), while keeping the deepest technical receipts (HTTP traces) readily available for reproduction.

**Alternatives considered:**
- Raw `curl` or `pytest -v` output by default — too noisy, forces the user to parse HTTP headers to find the issue.
- Purely conversational answers — loses the "receipts" that developers need to reproduce issues in other tools (Postman, curl).

