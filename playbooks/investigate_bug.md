# Investigative Discovery Playbook

This playbook defines how the `litellm-debug` skill conducts a deep-dive investigation to determine whether a failing test (revealed in the Level 2 Trace) is caused by a **configuration issue** or an **upstream bug** in the LiteLLM codebase.

## Execution Flow

When a user asks you to "investigate this error", "check if this is a bug", or "validate against the code", follow this loop:

### 1. Extract the Context from Level 2 Trace
Identify the key pieces of information from the failed diagnostic:
*   The exact Error Message or `status` code.
*   The requested capability (e.g., `tools`, `roundtrip`, `vision`).
*   The specific model string and provider (e.g., `gemini/gemini-flash-latest`).
*   The proxy version (from `LITELLM_VERSION_PRIMARY`).

### 2. Search the Local Source Clone
We maintain a local clone of the exact LiteLLM source code that matches the proxy version being debugged at `~/.cache/litellm-debug/sources/litellm@<version>`.
*   **Action:** Use your search tools (`grep` / `glob`) to locate the relevant provider transformation logic (refer to `references/litellm/source_index.md` for routing, usually under `litellm/llms/<provider>/`).
*   Search for the specific error message string or the parameter that triggered it.

### 3. Search the Local Documentation
We also have a local clone of the LiteLLM docs located at `~/.cache/litellm-debug/sources/litellm@<version>/docs/my-website/docs`.
*   **Action:** Search the documentation for instructions on configuring the specific provider, capability, or endpoint (e.g., `pass_through/gemini.md` or `completion/function_calling.md`). Check if there are known limitations or specific `litellm_params` needed to make this work.

### 4. Search Upstream Issues & Pull Requests
If the code appears to be the problem (e.g., missing parameter mapping or dropping a signature like `thoughtSignature`), check if this is a known issue.
*   **Action:** Use the Github CLI via your bash tool (`gh issue list --repo BerriAI/litellm --search "<keywords>"` or `gh pr list`) to search for open or recently merged bug fixes related to your findings.

### 5. Surface the "Bug vs. Config" Report
Synthesize your findings into a structured report.

**Report Format:**
> **Investigative Discovery Report:**
> 
> **Symptom:** The proxy returned `400 Bad Request` during the `roundtrip` capability test on `gemini/gemini-flash-latest`.
> 
> **Source Analysis:** Looking at `litellm/llms/vertex_ai/gemini/vertex_and_google_ai_studio_gemini.py` on tag `v1.82.6-nightly`, the `_transform_parts()` function only parses `thoughtSignature` from the `functionCall` part.
> 
> **Documentation Analysis:** No configuration overrides exist in the docs to bypass this.
> 
> **Upstream Status:** 
> This is a known **Upstream Bug**. 
> It was reported in Issue #25322 and fixed in PR #25357 (which was merged after this proxy version was cut).
> 
> **Recommendation:** Upgrade the proxy to `v1.83.13` or newer to inherit this fix. No local configuration changes can resolve this.
