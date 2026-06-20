import importlib.util
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from textwrap import dedent


SKILL_ROOT = Path(__file__).resolve().parents[1]


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _make_doc(level: str | None) -> str:
    meta_lines = [
        "<!-- PKB-metadata",
        "last_updated: 2026-05-06",
        "commit: abc1234",
        "updated_by: human+ai",
    ]
    if level is not None:
        meta_lines.append(f"confidentiality: {level}")
    meta_lines.append("-->")
    return "# Title\n\nbody\n\n---\n" + "\n".join(meta_lines) + "\n"


class TemplateConfidentialityFieldTests(unittest.TestCase):
    """Every shipped template must declare confidentiality (default L1)."""

    def _gather_templates(self) -> list[Path]:
        roots = [
            SKILL_ROOT / "templates" / "docs",
            SKILL_ROOT / "templates" / "sphinx",
            SKILL_ROOT / "templates" / "adr",
            SKILL_ROOT / "templates" / "changes" / "_template",
        ]
        out: list[Path] = []
        for r in roots:
            if r.exists():
                out.extend(sorted(r.rglob("*.md")))
        return out

    def test_every_template_with_metadata_declares_confidentiality(self) -> None:
        templates = self._gather_templates()
        self.assertGreater(len(templates), 0, "no templates discovered")
        meta_re = re.compile(r"<!--\s*PKB-metadata\s*\n(.*?)-->", re.DOTALL)

        missing: list[str] = []
        wrong_default: list[str] = []
        for tpl in templates:
            text = tpl.read_text(encoding="utf-8")
            m = meta_re.search(text)
            if not m:
                continue
            block = m.group(1)
            if "confidentiality:" not in block:
                missing.append(str(tpl.relative_to(SKILL_ROOT)))
                continue
            level_match = re.search(r"^confidentiality:\s*(\S+)\s*$", block, re.MULTILINE)
            self.assertIsNotNone(level_match, f"unparseable confidentiality line in {tpl}")
            assert level_match is not None
            if level_match.group(1) != "L1":
                wrong_default.append(f"{tpl.relative_to(SKILL_ROOT)}={level_match.group(1)}")

        self.assertEqual(missing, [], f"templates missing confidentiality field: {missing}")
        self.assertEqual(
            wrong_default, [],
            f"templates must default to L1: {wrong_default}",
        )


class StripConfidentialTests(unittest.TestCase):
    """strip_confidential.py removes the right artifacts and keeps the rest."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.module = _load_module(
            "strip_confidential",
            SKILL_ROOT / "scripts" / "strip_confidential.py",
        )

    def _build_fixture(self, root: Path) -> tuple[Path, Path]:
        doc_dir = root / "doc"
        site_dir = root / "doc" / "_build" / "site"
        doc_dir.mkdir(parents=True)

        cases = {
            "00-overview.md": "L1",
            "01-quick-start.md": None,        # missing field => L1 default
            "02-architecture.md": "L2",
            "05-secret.md": "L3",
            "06-very-secret.md": "L5",
            "07-typo-level.md": "L9",         # unknown => fallback L5 (stripped)
        }
        for name, level in cases.items():
            (doc_dir / name).write_text(_make_doc(level), encoding="utf-8")

        for lang in ("en", "zh"):
            (site_dir / lang).mkdir(parents=True)
            (site_dir / lang / "_sources").mkdir()
            for name in cases:
                stem = name[:-3]
                (site_dir / lang / f"{stem}.html").write_text(
                    f"<html>{stem}</html>", encoding="utf-8",
                )
                (site_dir / lang / "_sources" / f"{stem}.txt").write_text(
                    "src", encoding="utf-8",
                )

        return doc_dir, site_dir

    def test_default_threshold_strips_l3_and_above(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            doc_dir, site_dir = self._build_fixture(Path(tmp))
            results = self.module.strip(site_dir, doc_dir, "L3", dry_run=False)
            stripped = {r.docname for r in results}
            self.assertEqual(stripped, {"05-secret", "06-very-secret", "07-typo-level"})

            for stem in ("00-overview", "01-quick-start", "02-architecture"):
                for lang in ("en", "zh"):
                    self.assertTrue(
                        (site_dir / lang / f"{stem}.html").exists(),
                        f"public page {stem} unexpectedly removed",
                    )

            for stem in ("05-secret", "06-very-secret", "07-typo-level"):
                for lang in ("en", "zh"):
                    self.assertFalse(
                        (site_dir / lang / f"{stem}.html").exists(),
                        f"confidential page {stem} should be stripped",
                    )
                    self.assertFalse(
                        (site_dir / lang / "_sources" / f"{stem}.txt").exists(),
                        f"source {stem}.txt should be stripped",
                    )

    def test_dry_run_does_not_delete_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            doc_dir, site_dir = self._build_fixture(Path(tmp))
            results = self.module.strip(site_dir, doc_dir, "L3", dry_run=True)
            self.assertGreater(len(results), 0)
            for stem in ("05-secret", "06-very-secret"):
                for lang in ("en", "zh"):
                    self.assertTrue(
                        (site_dir / lang / f"{stem}.html").exists(),
                        f"dry-run must not delete {stem}.html",
                    )

    def test_min_level_l2_strips_more_aggressively(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            doc_dir, site_dir = self._build_fixture(Path(tmp))
            results = self.module.strip(site_dir, doc_dir, "L2", dry_run=False)
            stripped = {r.docname for r in results}
            self.assertIn("02-architecture", stripped)
            self.assertNotIn("00-overview", stripped)

    def test_parse_level_defaults_and_fallbacks(self) -> None:
        self.assertEqual(self.module.parse_level(_make_doc("L1")), "L1")
        self.assertEqual(self.module.parse_level(_make_doc("l4")), "L4")
        self.assertEqual(self.module.parse_level(_make_doc(None)), "L1")
        self.assertEqual(self.module.parse_level(_make_doc("L9")), "L5")
        self.assertEqual(self.module.parse_level("no metadata at all"), "L1")

    def test_cli_dry_run_emits_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            doc_dir, site_dir = self._build_fixture(Path(tmp))
            result = subprocess.run(
                [
                    sys.executable,
                    str(SKILL_ROOT / "scripts" / "strip_confidential.py"),
                    "--site-dir", str(site_dir),
                    "--doc-dir", str(doc_dir),
                    "--dry-run",
                    "--json",
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            payload = json.loads(result.stdout)
            self.assertTrue(any(item["docname"] == "05-secret" for item in payload))
            self.assertTrue(
                (site_dir / "en" / "05-secret.html").exists(),
                "JSON dry-run must not delete files",
            )


class ReviewStatusConfidentialityTests(unittest.TestCase):
    """pkb_review_status parses and renders the confidentiality column."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.module = _load_module(
            "pkb_review_status",
            SKILL_ROOT / "scripts" / "pkb_review_status.py",
        )

    def test_scan_reports_confidentiality_with_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            doc_dir = Path(tmp)
            (doc_dir / "00-overview.md").write_text(_make_doc("L2"), encoding="utf-8")
            (doc_dir / "04-repo-map.md").write_text(_make_doc(None), encoding="utf-8")
            (doc_dir / "10-runbook.md").write_text(_make_doc("L4"), encoding="utf-8")

            docs = {d.file: d for d in self.module.scan_docs(str(doc_dir))}
            self.assertEqual(docs["00-overview.md"].confidentiality, "L2")
            self.assertEqual(docs["04-repo-map.md"].confidentiality, "L1")
            self.assertEqual(docs["10-runbook.md"].confidentiality, "L4")

    def test_invalid_level_falls_back_to_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            doc_dir = Path(tmp)
            (doc_dir / "00-overview.md").write_text(_make_doc("L42"), encoding="utf-8")
            docs = self.module.scan_docs(str(doc_dir))
            self.assertEqual(docs[0].confidentiality, "L1")

    def test_cli_table_includes_level_column_and_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            doc_dir = Path(tmp)
            (doc_dir / "00-overview.md").write_text(
                dedent(
                    """\
                    # Title

                    body

                    ---
                    <!-- PKB-metadata
                    last_updated: 2026-05-06
                    commit: abc1234
                    updated_by: ai
                    review_status: pending
                    review_score: 0
                    reviewed_by:
                    confidentiality: L3
                    -->
                    """
                ),
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    sys.executable,
                    str(SKILL_ROOT / "scripts" / "pkb_review_status.py"),
                    "--doc-dir", str(doc_dir),
                ],
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            self.assertIn("Level", result.stdout)
            self.assertIn("L3", result.stdout)
            self.assertIn("Restricted (L3+): 1", result.stdout)


class SkillDocumentationTests(unittest.TestCase):
    """SKILL.md documents the confidentiality contract and toolkit entry."""

    def test_skill_md_mentions_levels_and_strip_script(self) -> None:
        text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        for needle in (
            "Confidentiality & Publish Policy",
            "L1",
            "L2",
            "L3",
            "L4",
            "L5",
            "scripts/strip_confidential.py",
            "confidentiality: L1",
        ):
            self.assertIn(needle, text, f"SKILL.md missing reference: {needle}")


class SphinxConfBadgeTests(unittest.TestCase):
    """conf.py and custom.css carry the visible badge for confidentiality."""

    def test_conf_renders_confidentiality_label(self) -> None:
        conf_text = (SKILL_ROOT / "templates" / "sphinx" / "conf.py").read_text(encoding="utf-8")
        self.assertIn("'confidentiality'", conf_text)
        self.assertIn("pkb-level", conf_text)
        self.assertIn("L1 \u00b7 Public", conf_text)
        self.assertIn("L5 \u00b7 \u7edd\u5bc6", conf_text)

    def test_custom_css_defines_level_badges(self) -> None:
        css_text = (SKILL_ROOT / "templates" / "sphinx" / "_static" / "custom.css").read_text(encoding="utf-8")
        for cls in ("pkb-level-l1", "pkb-level-l2", "pkb-level-l3", "pkb-level-l4", "pkb-level-l5"):
            self.assertIn(cls, css_text, f"custom.css missing class .{cls}")


class PublishFlowWiringTests(unittest.TestCase):
    """The Sphinx Makefile must build the site before stripping confidential pages."""

    def test_makefile_strip_target_runs_after_html_all(self) -> None:
        mk = (SKILL_ROOT / "templates" / "sphinx" / "Makefile").read_text(encoding="utf-8")
        self.assertIn("strip-confidential:", mk)
        self.assertIn("CONF_MIN_LEVEL", mk)
        self.assertRegex(mk, r"(?m)^strip-confidential:.*html-all")


if __name__ == "__main__":
    unittest.main()
