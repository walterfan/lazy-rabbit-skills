# Python Stack Checklist

Maps to `references/universal-rubric.md`. See `references/stack-checklists.md` for the cross-stack heading-to-rubric mapping table.

**Markers**: `pyproject.toml`, `setup.py`, `setup.cfg`, `requirements*.txt`, `Pipfile`, `tox.ini`, `pytest.ini`, `noxfile.py`, `poetry.lock`.

**Verification surfaces** (rubric §2):
- Test: `pytest`, `tox`, `nox`, `python -m unittest`.
- Lint/format: `ruff check`, `ruff format`, `flake8`, `black`, `isort`.
- Type: `mypy`, `pyright`, `pyre`.
- Pre-commit: `.pre-commit-config.yaml` with hooks actually installed in CI.

**Architecture fitness** (rubric §3):
- `import-linter` contracts, `pydeps`, custom AST checks for layering.
- Public API: typed stubs, `__all__` discipline, semver-aware release notes.

**Behavior harness** (rubric §4):
- Fixtures under `tests/fixtures`, `conftest.py`-driven setup, snapshot tests (`syrupy`).
- Integration tests using `testcontainers-python`, `pytest-docker`, or hermetic fakes.

**Safety tooling** (rubric §5):
- `pip-audit`, `safety`, `bandit`, `semgrep`, secret scanners.
- Lockfile usage (`poetry.lock`, `requirements.lock`, `pip-tools`).

**Priority notes**:
- A `pyproject.toml` alone is not a harness — confirm tools are configured under `[tool.*]` and actually invoked by a script or CI step.
