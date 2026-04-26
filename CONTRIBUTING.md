# Contributing

Thanks for your interest. This is a young project; the design is
deliberate and documented in [dev/](dev/). Read those files before
opening a PR.

## Read first

1. [dev/intent.md](dev/intent.md) — what this skill is and isn't.
2. [dev/roadmap.md](dev/roadmap.md) — current phase and acceptance criteria.
3. [dev/decisions.md](dev/decisions.md) — architectural decision log.

## Workflow

1. Pick an open acceptance criterion from `dev/roadmap.md`. If you
   want to work on something not on the roadmap, open an issue first
   to discuss the fit.
2. Open a draft PR with the phase number and acceptance criterion in
   the description.
3. New architectural decisions append a fresh entry to
   `dev/decisions.md` (next free `Dxxx` ID, dated). Don't edit prior
   entries. Capture durable principles, not the narrative of arriving
   at them.
4. Spec anchoring: never reference an endpoint or schema column
   without naming the LiteLLM version. All references must trace to a
   snapshot under `references/litellm/spec/<version>/`.

## Tests

The test suite is the onboarding documentation. Tests for each tier
are runnable standalone with that tier's credentials, and they skip
cleanly when those credentials are absent.

A new tier-specific test must:
- Skip cleanly when its credentials are not in env (not fail).
- Print a diagnostic message naming the env var to set.
- Carry the right marker (`tier_public`, `tier_user`, `tier_admin`,
  `tier_telemetry`, or `tier_database`).

## Style

- Comments only when the WHY is non-obvious.
- No abstractions ahead of the second concrete need.
- Service-specific material lives under named subdirectories
  (currently `litellm/` everywhere). Don't flatten this.
- Match the existing tone in `dev/`: tight, declarative, no marketing
  voice.

## Spec changes

When LiteLLM ships a new version that changes endpoints or schema:
1. Re-pin: `python scripts/litellm/spec_pin.py --version <new>`
   (Phase 1+).
2. The snapshot lands at `references/litellm/spec/<new>/`.
3. Update affected tests, playbooks, and references.
4. Append an entry to `dev/decisions.md` if behaviour changes
   meaningfully (e.g. an endpoint removed, a schema column dropped).

## License of contributions

By opening a PR, you agree to license your contribution under the
project's license (MIT — see [LICENSE](LICENSE)).
