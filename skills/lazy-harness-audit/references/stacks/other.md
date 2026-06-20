# Other or Unknown Stacks

Maps to `references/universal-rubric.md`. See `references/stack-checklists.md` for the cross-stack heading-to-rubric mapping table.

Use this fallback when no marker file matches a known stack (shell-only repos, C/C++, Lua, mixed-language tooling, custom DSLs, etc.).

**Approach**:
- Document what the project actually is (shell scripts, C/C++, Lua, mixed-language tooling) and what evidence supports that.
- Map the universal rubric categories to whatever build/test surfaces exist: `Makefile`, `meson`, `cmake`, `bazel`, custom CI scripts.
- Be explicit when a category cannot be scored due to missing tooling, and recommend the minimal addition that would make it scorable (e.g., a single `make check` target).

**Priority notes**:
- Do not penalize an unknown stack just because none of the named stack checklists apply. Penalize only when the universal rubric items themselves (e.g., reusable verification path, secrets policy, AGENTS.md) are missing.
- If the project becomes important enough to audit repeatedly, propose promoting it to its own checklist file under `references/stacks/`.
