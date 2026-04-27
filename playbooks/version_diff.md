# Version Diff Playbook

This playbook outlines how to use the "Two-version comparison workflow" to debug issues where a workload behaves differently between two deployed environments (e.g., prod vs. test, or pre-upgrade vs. post-upgrade).

## When to Use This Playbook
Use this when you have two proxy environments running different LiteLLM versions, and you need to isolate what structural or code-level change caused a regression.

## Workflow Execution

### 1. Pin the Versions
Update `.env` with the two versions:
```env
LITELLM_VERSION_PRIMARY=v1.55.0  # The broken/new version
LITELLM_VERSION_COMPARISON=v1.54.0  # The working/old version
```

Run the Spec Pin script to snapshot both:
```bash
python scripts/litellm/spec_pin.py
```

### 2. Diff the Schemas (The "What")
If the regression involves DB logging, spend tracking, or proxy configuration, start by diffing the Prisma schemas:
```bash
python scripts/litellm/spec_diff.py
```
*   Look for newly added columns, removed tables, or changed foreign keys.

### 3. Sync the Source (The "Why")
If the schemas match or the issue is with a specific provider's text output, sync the source clones:
```bash
python scripts/litellm/source_sync.py
```

### 4. Focused Source Read
Consult the `references/litellm/source_index.md` to find the relevant file (e.g., `litellm/llms/anthropic/chat/transformation.py`). 

Run a targeted diff directly on the source clones:
```bash
diff -u ~/.cache/litellm-debug/sources/litellm@v1.54.0/litellm/llms/anthropic/chat/transformation.py \
        ~/.cache/litellm-debug/sources/litellm@v1.55.0/litellm/llms/anthropic/chat/transformation.py
```

### 5. Surface the Diagnosis
Present the findings to the developer, linking the observed runtime error back to the specific line of code that changed between the two versions.
