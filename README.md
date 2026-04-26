# litellm-debug

A Claude Code skill for debugging LiteLLM proxy deployments fronting
agentic AI workloads. Read-side and investigative.

**Status:** early development. See [dev/roadmap.md](dev/roadmap.md) for
the current phase.

## What it does

Walks an investigation across five access tiers — Public, User, Admin,
Telemetry, Database — using the least-privileged tier that can answer
the question. Anchored to a version-pinned snapshot of the LiteLLM
OpenAPI and schema, with a local clone of LiteLLM source for deeper
analysis.

Two version slots are tracked concurrently (`primary` and
`comparison`), making prod-vs-test debugging a first-class workflow.

## Onboarding ladder

The skill is designed to be useful at every level of access. Each rung
needs exactly one more credential than the one below.

| Rung | Tier      | Required                                    |
|------|-----------|---------------------------------------------|
| 1    | Public    | `LITELLM_BASE_URL`                          |
| 2    | User      | + `LITELLM_USER_KEY` (any virtual key)      |
| 3    | Admin     | + `LITELLM_MASTER_KEY`                      |
| 4    | Telemetry | + `LANGFUSE_*` (or other backend creds)     |
| 5    | Database  | + `LITELLM_DB_DSN` and `LITELLM_DB_OPTIN=1` |

Run the test suite at any rung. Tiers without credentials skip cleanly
with a message naming the env var that would unlock them.

## Design

- [dev/intent.md](dev/intent.md) — what this is and isn't.
- [dev/roadmap.md](dev/roadmap.md) — phased plan with acceptance criteria.
- [dev/decisions.md](dev/decisions.md) — architectural decision log.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT. See [LICENSE](LICENSE).
