# litellm-debug

An [Agent Skill](https://agentskills.io/) for debugging LiteLLM proxy deployments fronting
agentic AI workloads. Read-side and investigative.

This repository implements the open Agent Skills standard. The `SKILL.md` file at the root acts as the entry point and instructions for AI agents (like Claude Code) when they interact with this repository.

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

# 1. Run the raw test suite
pytest tests/litellm/public -v

# 2. Generate a progressive diagnostic report
python3 scripts/litellm/diagnose_public.py --level 0
```

This will produce a traffic-light dashboard view of your proxy's public surface area:

```text
┌───────────────────────────────────────────────────────────┐
│              LITELLM PUBLIC TIER DASHBOARD                │
└───────────────────────────────────────────────────────────┘

▶ HEALTH & PERFORMANCE
  ✅ Proxy Core:   Reachable & Responsive
  ✅ Dependencies: Healthy
  盲 Observability: Metrics disabled (404)

▶ SECURITY & IDENTITY SURFACE
  🔒 Core API:     Auth-gated (Safe)
  🔑 Identity:     SSO/OIDC configuration exposed

▶ UI & CLIENT CONFIGURATION
  🖥️  Web UI:       Exposed (Model Hub)
  ⚙️  Config Data:  3 frontend settings endpoints exposed

▶ SERVICE DISCOVERY CAPABILITIES
  📡 Discovery:    5/5 provider and capability endpoints exposed

───────────────────────────────────────────────────────────
💡 Next Step: To investigate why specific inference requests
   are failing, provide LITELLM_USER_KEY in your .env to
   unlock the USER TIER.
```

You should see eight tests pass or skip gracefully. (For a full breakdown of the test suite and what each test validates, see [tests/README.md](tests/README.md)).

If `LITELLM_BASE_URL` is unset, all tests will skip cleanly with a message
telling you what to set.

To unlock the next rung, add the next credential to `.env` and run the
corresponding test directory.

## What it does

Walks an investigation across five access tiers — Public, User, Admin,
Telemetry, Database — using the least-privileged tier that can answer
the question. Anchored to a version-pinned snapshot of the LiteLLM
OpenAPI and schema (Phase 1 completed), with a local clone of LiteLLM
source for deeper analysis.

Two version slots are tracked concurrently (`primary` and
`comparison`), making prod-vs-test debugging a first-class workflow.

## Onboarding ladder

The skill is designed to be useful at every level of access. Each rung
needs exactly one more credential than the one below.

To respect your time and avoid overwhelming you with raw logs, the skill uses **Progressive Disclosure** (similar to SRE runbooks and CLI verbosity):
- **Level 0 (Summary):** A fast, traffic-light assessment of the tier's health and security.
- **Level 1 (Diagnostics):** The "Why" behind a degraded status (e.g., parsing a 503 error to identify a Redis failure).
- **Level 2 (Traces):** Full HTTP request/response pairs and `curl` reproduction commands.

The skill defaults to Level 0 and will ask if you want to drill down.

| Rung | Tier      | Required                                    | Tests                          |
|------|-----------|---------------------------------------------|--------------------------------|
| 1    | Public    | `LITELLM_BASE_URL`                          | `tests/litellm/public/`        |
| 2    | User      | + `LITELLM_USER_KEY` (any virtual key)      | `tests/litellm/user/`          |
| 3    | Admin     | + `LITELLM_MASTER_KEY`                      | `tests/litellm/admin/` (TBD)   |
| 4    | Telemetry | + `LANGFUSE_*` (or other backend creds)     | `tests/litellm/telemetry/` (TBD) |
| 5    | Database  | + `LITELLM_DB_DSN` and `LITELLM_DB_OPTIN=1` | `tests/litellm/database/` (TBD) |

Run the full suite with `pytest`. Tiers without credentials skip
cleanly with a message naming the env var that would unlock them.

### Inference Readiness Testing

For the User Tier, the skill evaluates actual inference capabilities across different modalities. We test **7 distinct inference gateway dimensions** to ensure full agentic readiness:
1. **Text**: Standard `/v1/chat/completions` text routing.
2. **Tools**: Function calling and structured tool schema routing.
3. **Vision**: Multimodal image processing.
4. **Round-Trip**: Multi-turn conversation context preservation (crucial for agent loops).
5. **Embeddings**: `/v1/embeddings` vectorization routing.
6. **Streaming**: Server-Sent Events (SSE) stream delivery.
7. **JSON Mode**: Structured output forcing via `response_format`.

You can customize what is tested using environment variables:

- `LITELLM_TEST_MODEL`: Set to `all`, `first`, or a specific model like `gpt-4o`.
- `LITELLM_TEST_CAPABILITIES`: Comma-separated list of capabilities to test (e.g., `text,roundtrip` or `all`).

## Investigative Discovery

When the skill uncovers a failure (e.g., a specific capability like Round-Trip failing on a specific model), it doesn't just stop at the error. It uses the `playbooks/investigate_bug.md` workflow to:
1. Grep the local LiteLLM source clone (`~/.cache/litellm-debug/sources/...`) for the failing code.
2. Cross-reference the local LiteLLM documentation clone (`.../docs/my-website/docs`).
3. Query the upstream GitHub repository for known issues or pull requests.
4. Synthesize a definitive "Bug vs. Config" report.

## Design

- [dev/intent.md](dev/intent.md) — what this is and isn't.
- [dev/roadmap.md](dev/roadmap.md) — phased plan with acceptance criteria.
- [dev/decisions.md](dev/decisions.md) — architectural decision log.
- [dev/practices.md](dev/practices.md) — normative development practices.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT. See [LICENSE](LICENSE).
