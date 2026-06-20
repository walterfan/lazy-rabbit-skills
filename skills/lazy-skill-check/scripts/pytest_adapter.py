"""
pytest adapter for lazy-skill-check.

Drop this file next to (or import from) a conftest.py in projects that already
have a pytest harness, and you get three parametrized test families for each
skill directory you register:

    - test_skill_lint        : L1 structural lint
    - test_skill_trigger     : L2 trigger precision eval (needs judge creds)
    - test_skill_behavior    : L3 behavior case assertions on existing runs

Usage (in your project's conftest.py or a test module):

    import sys, pathlib
    sys.path.insert(0, str(pathlib.Path("/path/to/lazy-skill-check/scripts")))
    from pytest_adapter import register_skill

    register_skill(
        skill_dir="skills/my-skill",
        trigger_cases="skills/my-skill/references/trigger-cases.yaml",
        behavior_cases_dir="skills/my-skill/references/behavior",
        runs_dir="tests/.skill-runs/my-skill",   # optional, for L3
        judge_model="claude-haiku-4-5",
    )

We intentionally do NOT spawn real agents during the `pytest` run: L3 relies on
previously captured runs (produced by `lazyskillcheck behavior` in CI before
tests kick in). This keeps `pytest` deterministic, fast, and offline-friendly.
Set LAZY_SKILL_CHECK_SKIP_TRIGGER=1 to skip L2 (useful in offline CI stages).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

HERE = Path(__file__).resolve().parent


@dataclass
class SkillSpec:
    skill_dir: Path
    trigger_cases: Path | None = None
    behavior_cases_dir: Path | None = None
    runs_dir: Path | None = None
    judge_model: str = "claude-haiku-4-5"
    judge_vendor: str | None = None
    f1_threshold: float = 0.85


_REGISTRY: list[SkillSpec] = []


def register_skill(
    skill_dir: str | Path,
    *,
    trigger_cases: str | Path | None = None,
    behavior_cases_dir: str | Path | None = None,
    runs_dir: str | Path | None = None,
    judge_model: str = "claude-haiku-4-5",
    judge_vendor: str | None = None,
    f1_threshold: float = 0.85,
) -> SkillSpec:
    spec = SkillSpec(
        skill_dir=Path(skill_dir).resolve(),
        trigger_cases=Path(trigger_cases).resolve() if trigger_cases else None,
        behavior_cases_dir=Path(behavior_cases_dir).resolve() if behavior_cases_dir else None,
        runs_dir=Path(runs_dir).resolve() if runs_dir else None,
        judge_model=judge_model,
        judge_vendor=judge_vendor,
        f1_threshold=f1_threshold,
    )
    _REGISTRY.append(spec)
    return spec


def registered_skills() -> list[SkillSpec]:
    return list(_REGISTRY)


def _py() -> str:
    return os.environ.get("LAZY_SKILL_CHECK_PYTHON") or sys.executable


# ---------- lint ----------

def run_lint(spec: SkillSpec) -> tuple[int, str]:
    cmd = [_py(), str(HERE / "lint.py"), str(spec.skill_dir)]
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


# ---------- trigger ----------

def run_trigger(spec: SkillSpec) -> dict:
    if spec.trigger_cases is None or not spec.trigger_cases.exists():
        return {"skipped": True, "reason": "no trigger cases"}
    cmd = [
        _py(),
        str(HERE / "trigger_eval.py"),
        "--skill", str(spec.skill_dir),
        "--cases", str(spec.trigger_cases),
        "--judge-model", spec.judge_model,
        "--json",
        "--f1-threshold", str(spec.f1_threshold),
    ]
    if spec.judge_vendor:
        cmd += ["--judge-vendor", spec.judge_vendor]
    p = subprocess.run(cmd, capture_output=True, text=True)
    try:
        payload = json.loads(p.stdout)
    except json.JSONDecodeError:
        payload = {"passed": False, "raw_stdout": p.stdout, "raw_stderr": p.stderr}
    payload["_rc"] = p.returncode
    return payload


# ---------- behavior (from precomputed runs) ----------

def run_behavior_assertions(spec: SkillSpec) -> dict:
    if spec.behavior_cases_dir is None or not spec.behavior_cases_dir.exists():
        return {"skipped": True, "reason": "no behavior cases dir"}
    if spec.runs_dir is None or not spec.runs_dir.exists():
        return {"skipped": True, "reason": f"no runs dir ({spec.runs_dir})"}
    cmd = [
        _py(),
        str(HERE / "evaluate_runs.py"),
        "--cases", str(spec.behavior_cases_dir),
        "--runs", str(spec.runs_dir),
        "--json",
    ]
    p = subprocess.run(cmd, capture_output=True, text=True)
    try:
        payload = json.loads(p.stdout)
    except json.JSONDecodeError:
        payload = {"passed": False, "raw_stdout": p.stdout, "raw_stderr": p.stderr}
    payload["_rc"] = p.returncode
    return payload


# ---------- pytest hooks ----------

def _pytest_params(specs: Iterable[SkillSpec]) -> list:
    import pytest  # type: ignore
    specs = list(specs)
    if not specs:
        pytest.skip("no skills registered via register_skill(...)", allow_module_level=True)
    return [pytest.param(s, id=str(s.skill_dir.name)) for s in specs]


def test_skill_lint(skill_spec: SkillSpec) -> None:  # pragma: no cover - used by pytest
    rc, out = run_lint(skill_spec)
    assert rc == 0, f"L1 lint failed for {skill_spec.skill_dir}:\n{out}"


def test_skill_trigger(skill_spec: SkillSpec) -> None:  # pragma: no cover
    if os.environ.get("LAZY_SKILL_CHECK_SKIP_TRIGGER") == "1":
        import pytest
        pytest.skip("LAZY_SKILL_CHECK_SKIP_TRIGGER=1")
    rep = run_trigger(skill_spec)
    if rep.get("skipped"):
        import pytest
        pytest.skip(rep.get("reason", "skipped"))
    assert rep.get("passed"), (
        f"L2 trigger eval failed (f1<{skill_spec.f1_threshold}): "
        f"metrics={rep.get('metrics')}\nfailures={rep.get('failures')}"
    )


def test_skill_behavior(skill_spec: SkillSpec) -> None:  # pragma: no cover
    rep = run_behavior_assertions(skill_spec)
    if rep.get("skipped"):
        import pytest
        pytest.skip(rep.get("reason", "skipped"))
    assert rep.get("_rc") == 0, (
        f"L3 behavior assertions failed for {skill_spec.skill_dir.name}:\n"
        f"{json.dumps(rep, indent=2, ensure_ascii=False)}"
    )


def pytest_generate_tests(metafunc):  # pragma: no cover - pytest hook
    if "skill_spec" in metafunc.fixturenames:
        metafunc.parametrize(
            "skill_spec", _pytest_params(_REGISTRY), scope="module"
        )
