# Optional: alternative modern stacks (use only when requested)

**Default for `lazy-python-dev`:** follow [python-library.md](python-library.md) — **Poetry** for dependencies and lockfile, **Ruff** for lint/format, **pytest** for tests.

This file summarizes **optional** ideas from external guides (e.g. [Trail of Bits `modern-python`](https://github.com/trailofbits/skills/tree/main/plugins/modern-python/skills/modern-python)) such as **uv** or **ty**. Use them **only** when the user explicitly wants migration or a greenfield stack *without* Poetry, or is comparing tools. **Do not** replace an existing repo’s Poetry workflow without an ADR or explicit user request.

## When to mention uv / ty

- User asks "should we use uv instead of pip/poetry" — answer with tradeoffs; **if the project already uses Poetry, recommend staying on Poetry** unless they are starting fresh and have team approval to switch.
- User is bootstrapping a *new* repo and names Astral/uv/ty — then summarizing the ToB-style flow is fine; still offer Poetry + Ruff + pytest as the first-class alternative for library-aligned work.

## Quick mapping (same ideas, different defaults)

| Concern | Preferred in this skill | Optional alternative (explicit opt-in) |
|---------|---------------------------|----------------------------------------|
| Lockfile + installs | `poetry.lock` + `poetry install` | `uv` lock and sync in greenfield or approved migration |
| Format / lint | Ruff via Poetry dev deps | Same; tool is Ruff either way |
| Type checking | Project choice (e.g. mypy/pyright) or follow repo | `ty` if user and repo agree |

## Upstream

Full `uv`/`ty` command examples and cookiecutter live in the [Trail of Bits modern-python skill](https://github.com/trailofbits/skills/tree/main/plugins/modern-python/skills/modern-python). Treat as reference material, not a mandate to remove Poetry.
