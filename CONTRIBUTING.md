# Contributing to litellm-debug

First off, thank you for considering contributing to the `litellm-debug` skill! It's community members like you that keep diagnostic tools accurate as upstream projects evolve.

This project follows the [Agent Skills](https://agentskills.io/) open format for giving agents new capabilities. We are building a read-side, investigative tool for LiteLLM deployments.

## Core Philosophy

Before contributing, please read our foundational documents:
1. `dev/intent.md` — What this skill is and isn't.
2. `dev/roadmap.md` — Our phased approach and acceptance criteria.
3. `dev/decisions.md` — Our architectural decisions.
4. `dev/practices.md` — How we build day-to-day (tooling, TUI, etc).

We strictly follow a **Tier Model** (Public, User, Admin, Telemetry, Database). Our goal is always to use the *lowest fidelity tier* that can answer the user's question, and we rely on **Spec Anchoring** to ensure our tests are based on reality, not guesswork.

## Your First Contribution: Validating the Public Tier

A great way to get started and understand how this project works is to validate the completeness of our Public tier tests. LiteLLM frequently adds new configuration and UI endpoints, and it's our job to ensure our smoke tests cover the full public attack surface.

Here is the exact loop you can run to contribute:

### 1. Set up your environment
Clone the repo and install dependencies:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```
Add your proxy URL to `.env`: `LITELLM_BASE_URL=https://your-proxy.com`

### 2. Pin the Specifications
We never guess endpoint paths. We derive them from upstream. Run the spec pin tool to download the `openapi.json` for your LiteLLM version:
```bash
python scripts/litellm/spec_pin.py
```

### 3. Discover Public Endpoints
Run our developer discovery tool. This parses the downloaded OpenAPI spec for any endpoint that does *not* require security, and then dynamically pings your live proxy to see which ones return `200 OK`:
```bash
python scripts/dev/find_public_endpoints.py
```

### 4. Compare and Contribute
Look at the output of the script. Are there endpoints returning `200 OK` that are *not* currently listed in our tests? 
Check `tests/litellm/public/test_public.py` and `scripts/litellm/diagnose_public.py`.

If you find a new public endpoint (e.g., a new `.well-known` config or public `/ui/` path):
1. Add it to `test_public_config_endpoints` in `tests/litellm/public/test_public.py`.
2. Add it to the `ENDPOINTS` dictionary in `scripts/litellm/diagnose_public.py`.
3. Create a Pull Request!

## How to report a bug

When filing an issue, make sure to answer these questions:
1. What version of LiteLLM is your proxy running? (You can check `/health/readiness`)
2. What tier were you trying to debug (Public, User, Admin)?
3. What did you expect the skill to do?
4. What happened instead?

If you find a security vulnerability in how we handle credentials or traces, please do **NOT** open a public issue. Email the maintainers directly.

## Code review process

*   Ensure your tests pass (`pytest tests/litellm/public -v`).
*   Ensure missing credentials cause a test to `skip` gracefully, not `fail`.
*   We review PRs weekly. After feedback, we expect a response within a week or two, or we may close the PR to keep the queue clean.
