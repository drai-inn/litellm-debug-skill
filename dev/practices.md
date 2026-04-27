# Development Practices

This document captures emergent, normative development practices for anyone building or maintaining the `litellm-debug` skill. While `dev/decisions.md` records *architectural* decisions and `CONTRIBUTING.md` provides an external on-ramp, this document outlines *how* we build things day-to-day.

## 1. Tool-Driven Discovery
Never guess the state of upstream LiteLLM.
- **Practice:** Use automated scripts to parse upstream specs (`openapi.json`, `schema.prisma`) against live endpoints. 
- **Example:** `scripts/dev/find_public_endpoints.py` was built to ensure our Public Tier tests remain comprehensive. If you suspect an endpoint is missing or undocumented, write a discovery script to prove it before hardcoding assumptions into the test suite.

## 2. Progressive Disclosure in CLI/TUI Design
Do not overwhelm users with raw JSON or HTML dumps.
- **Practice:** Every diagnostic tool must support verbosity levels (e.g., `--level 0, 1, 2`).
  - **Level 0 (Summary):** High-level TUI dashboard. Status checks, traffic lights.
  - **Level 1 (Diagnostics):** Explanatory excerpts.
  - **Level 2 (Traces):** Raw HTTP traces and exact reproduction commands.
- **Content-Awareness:** Diagnostics must intelligently parse `Content-Type`. Use Python's built-in `html.parser` to extract visible text from HTML responses, and use `json.dumps` to compact or pretty-print JSON. 

## 3. Actionable Drill-Downs ("Receipts")
Always provide an escape hatch from the tool.
- **Practice:** When surfacing an error or a trace, provide the exact `curl` command needed for the user to reproduce the request outside of the Python script.
- **Example:** JSON responses should suggest piping to `jq` (`curl -s ... | jq`), and HTML responses should suggest saving to a file (`curl -s ... -o output.html`).

## 4. Test Suite as Documentation
Tests are the ground truth for proxy behavior.
- **Practice:** If a script or playbook relies on an endpoint existing, there MUST be a corresponding `pytest` check for it.
- **Graceful Degradation:** A missing local `.env` credential or configuration should result in a `pytest.skip` with an actionable message ("Set XYZ variable"), not a hard fail. Failures should be reserved for actual proxy degradation (e.g., expected 200, got 500).

## 5. Agent Skills Alignment
We are building an AI agent skill, not just a CLI tool.
- **Practice:** Always ensure the `SKILL.md` frontmatter (`name`, `description`) is highly optimized for AI intent-matching.
- **Playbook Routing:** Ensure playbooks (`playbooks/*.md`) explicitly define the execution loop the AI should follow when a user requests an investigation.
