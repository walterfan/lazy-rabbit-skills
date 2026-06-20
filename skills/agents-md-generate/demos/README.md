# agents-md-generate demo

Scripted terminal demo for the `agents-md-generate` skill.

The demo shows Claude Code using the skill to:

- ask for AI tool preferences and symlink intent;
- discover an existing `CLAUDE.md`, `.claude/`, `.cursor/`, and `man/`;
- generate a concise `AGENTS.md` without duplicating the project
  knowledge base;
- add compatibility wiring only when safe;
- verify line count, placeholders, and focused checks.

Regenerate the cast:

```bash
python3 skills/agents-md-generate/demos/gen_agents_md_generate_demo.py \
  skills/agents-md-generate/demos/agents-md-generate-demo.cast
```

Upload to cast-player, if network access is available:

```bash
python3 skills/agents-md-generate/demos/upload_cast.py \
  skills/agents-md-generate/demos/agents-md-generate-demo.cast
```
