# litellm-debug

A Claude Code skill for debugging LiteLLM proxy deployments fronting
agentic AI workloads. Read-side and investigative.

**Status:** early development. See [dev/roadmap.md](dev/roadmap.md) for
the current phase.

## Quickstart — Public tier (no LiteLLM credentials required)

The lowest rung of the onboarding ladder needs only the base URL of
your LiteLLM proxy.

```bash
git clone https://github.com/drai-inn/litellm-debug-skill.git
cd litellm-debug-skill

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env and set LITELLM_BASE_URL to your proxy URL

pytest tests/litellm/public -v
```

You should see four tests:

| Test                       | Passes when                                  |
|----------------------------|----------------------------------------------|
| `test_proxy_liveliness`    | `/health/liveliness` returns 200             |
| `test_proxy_readiness`     | `/health/readiness` returns 200 or 503       |
| `test_models_list`         | `/v1/models` returns 200 (skips if auth-gated) |
| `test_metrics_endpoint`    | `/metrics` returns Prometheus format (skips if 404) |

If `LITELLM_BASE_URL` is unset, all four skip cleanly with a message
telling you what to set.

To unlock the next rung, add the next credential to `.env` and run the
corresponding test directory.

## What it does

Walks an investigation across five access tiers — Public, User, Admin,
Telemetry, Database — using the least-privileged tier that can answer
the question. Anchored to a version-pinned snapshot of the LiteLLM
OpenAPI and schema (Phase 1, upcoming), with a local clone of LiteLLM
source for deeper analysis.

Two version slots are tracked concurrently (`primary` and
`comparison`), making prod-vs-test debugging a first-class workflow.

## Onboarding ladder

The skill is designed to be useful at every level of access. Each rung
needs exactly one more credential than the one below.

| Rung | Tier      | Required                                    | Tests                          |
|------|-----------|---------------------------------------------|--------------------------------|
| 1    | Public    | `LITELLM_BASE_URL`                          | `tests/litellm/public/`        |
| 2    | User      | + `LITELLM_USER_KEY` (any virtual key)      | `tests/litellm/user/` (TBD)    |
| 3    | Admin     | + `LITELLM_MASTER_KEY`                      | `tests/litellm/admin/` (TBD)   |
| 4    | Telemetry | + `LANGFUSE_*` (or other backend creds)     | `tests/litellm/telemetry/` (TBD) |
| 5    | Database  | + `LITELLM_DB_DSN` and `LITELLM_DB_OPTIN=1` | `tests/litellm/database/` (TBD) |

Run the full suite with `pytest`. Tiers without credentials skip
cleanly with a message naming the env var that would unlock them.

## Design

- [dev/intent.md](dev/intent.md) — what this is and isn't.
- [dev/roadmap.md](dev/roadmap.md) — phased plan with acceptance criteria.
- [dev/decisions.md](dev/decisions.md) — architectural decision log.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT. See [LICENSE](LICENSE).
