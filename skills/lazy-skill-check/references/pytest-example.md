# Using lazy-skill-check inside an existing pytest project

If your repo already has pytest wired up, you don't need a second test runner.
Drop the snippet below into a `conftest.py` or a `test_skills.py` next to your
skills, and your team's familiar `pytest` command will now also grade skills.

## Minimal example

```python
# tests/test_skills.py
import sys, pathlib

LAZY_SKILL_CHECK_SCRIPTS = pathlib.Path(
    "/path/to/lazy-skill-check/scripts"   # vendor or symlink it
).resolve()
sys.path.insert(0, str(LAZY_SKILL_CHECK_SCRIPTS))

from pytest_adapter import register_skill

register_skill(
    skill_dir="skills/pdf-form-filler",
    trigger_cases="skills/pdf-form-filler/references/trigger-cases.yaml",
    behavior_cases_dir="skills/pdf-form-filler/references/behavior",
    runs_dir="tests/.skill-runs/pdf-form-filler",
    judge_model="claude-haiku-4-5",     # or gpt-4o for OpenAI path
)

# adapter also provides: register_skill(...)[2+], three parametrized tests
# pytest hook that fans them out by id.
```

## What you get

- `pytest -k test_skill_lint` runs L1 structural lint. Cheap. Offline.
- `pytest -k test_skill_trigger` runs L2 trigger precision eval. Needs
  `ANTHROPIC_API_KEY` or `OPENAI_API_KEY`. Skip with `LAZY_SKILL_CHECK_SKIP_TRIGGER=1`.
- `pytest -k test_skill_behavior` runs L3 assertions against previously
  recorded runs (typically produced by `lazyskillcheck behavior skills/... --agent claude`
  in a CI step ahead of `pytest`).

Behavior tests never spawn a live agent during `pytest` itself — that keeps
`pytest` deterministic, fast, and offline. Do the expensive spawn upstream,
then have `pytest` grade the captured output.

## Recommended CI layout

```yaml
# .github/workflows/ci.yml (sketch)
jobs:
  skills:
    steps:
      - run: python -m pip install pytest pyyaml
      - run: lazyskillcheck selftest           # lint + judge + parser unit tests
      - run: lazyskillcheck behavior skills/my-skill \
              --output tests/.skill-runs/my-skill
        # runs once, captures Claude/Codex/Cursor output
      - run: pytest tests/test_skills.py
```

## Multi-skill, multi-judge

```python
for skill, cases, judge in [
    ("skills/a", "skills/a/references/trigger-cases.yaml", "claude-haiku-4-5"),
    ("skills/b", "skills/b/references/trigger-cases.yaml", "gpt-4o"),
]:
    register_skill(
        skill_dir=skill,
        trigger_cases=cases,
        judge_model=judge,
    )
```

Each registration becomes a parametrized test node named after
`skill_dir.name`, so `pytest -v` shows:

```
test_skills.py::test_skill_lint[a]       PASSED
test_skills.py::test_skill_lint[b]       PASSED
test_skills.py::test_skill_trigger[a]    PASSED
test_skills.py::test_skill_trigger[b]    SKIPPED (no judge creds)
```
