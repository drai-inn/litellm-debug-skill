# Public Tier Playbook

This playbook defines how the `litellm-debug` skill investigates the Public tier of a LiteLLM deployment and how it surfaces information back to the developer.

## Design Precedence: Progressive Disclosure & SRE Runbooks

To create a world-class debugging experience, we follow two primary paradigms:
1.  **Progressive Disclosure:** Borrowed from UI/UX design, this prevents overwhelming the developer with raw JSON or stack traces immediately. We start with a high-level summary and provide "drill-down" capabilities.
2.  **SRE Incident Runbooks / CLI Verbosity (`-v`, `-vv`):** Similar to how `pytest` or `curl` handles verbosity, we categorize our output into three distinct levels of detail.

## Verbosity Levels

When investigating the Public tier, the skill should ask the user (or accept a flag) for the desired level of detail.

### Level 0: Summary (The "Traffic Light")
*Goal: Provide a 5-second assessment of the proxy's health and public attack surface.*
*   **Format:** Bullet points with status emojis (✅, ⚠️, ❌, 🔒).
*   **Content:** 
    *   Liveliness (Is it up?)
    *   Readiness (Are dependencies healthy?)
    *   Security/Auth (Are models protected?)
    *   Features (Are metrics/UI exposed?)
*   **Next Step:** Provide a single actionable recommendation (e.g., "Set `LITELLM_USER_KEY` to unlock User tier tests").

### Level 1: Diagnostic (The "Why")
*Goal: Explain the specific reasons for the Level 0 statuses.*
*   **Format:** Structured text with specific HTTP status codes and truncated body excerpts.
*   **Content:**
    *   If Readiness is 503, why? (e.g., "Redis cache connection failed").
    *   If Models are 401, what was the exact message?
*   **Next Step:** Suggest specific configuration changes if an endpoint is unexpectedly exposed or degraded.

### Level 2: Trace (The "Receipts")
*Goal: Provide irrefutable proof of the interaction, enabling the developer to reproduce the issue outside of the skill.*
*   **Format:** Raw HTTP Request/Response pairs, `curl` reproduction commands.
*   **Content:**
    *   Full request headers and payload.
    *   Full response headers and payload (untruncated).
    *   Timing/Latency metrics.

---

## Execution Flow (Public Tier)

When a user asks to "debug the public tier" or "run public tier tests", the skill should follow this loop:

1.  **Verify Environment:** Check if `LITELLM_BASE_URL` is set in `.env`. If not, halt and instruct the user to set it.
2.  **Execute Tests:** Run the `tests/litellm/public/` suite silently via `pytest`.
3.  **Analyze Results:** Parse the test results (Passed, Failed, Skipped).
4.  **Surface Output (Default: Level 0 Summary):** Present the Traffic Light summary.
5.  **Offer Drill-down:** Explicitly ask the user: *"Would you like to see the detailed diagnostics (Level 1) or full HTTP traces (Level 2) for any of these endpoints?"*

## Example Output (Level 0)

> **Public Tier Diagnosis:**
> *   ✅ **Proxy Status:** Reachable and healthy (`/health/liveliness` & `/health/readiness` OK).
> *   🔒 **Security:** Model listing is correctly auth-gated (`/v1/models` returned 401).
> *   ⚠️ **Metrics:** Prometheus metrics are disabled (`/metrics` returned 404).
> *   🌐 **UI & Config:** The Model Hub UI and configuration endpoints are publicly accessible.
> 
> *To investigate why your specific inference requests are failing, provide a `LITELLM_USER_KEY` in your `.env` to unlock the **User tier**.*
> 
> *(Reply with "show diagnostics" or "show traces" for more detail)*
