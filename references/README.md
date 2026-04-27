# References

This directory contains domain-specific reference material and documentation that the agent can read when needed.

As per the Agent Skills specification and our `dev/intent.md` roadmap, this directory will house:
- `references/litellm/spec/<version>/openapi.json` — Pinned OpenAPI specifications.
- `references/litellm/spec/<version>/schema.prisma` — Pinned Prisma schema files.
- `references/litellm/source_index.md` — Curated grep-targets for the LiteLLM source tree (e.g., provider transformers, proxy router, callback wiring).

Agents will load these files on demand to avoid consuming context unnecessarily.
