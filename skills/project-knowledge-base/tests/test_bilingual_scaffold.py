import re
import subprocess
import tempfile
import unittest
from pathlib import Path
import importlib.util


class BilingualScaffoldTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.skill_root = Path(__file__).resolve().parents[1]

    def test_template_sphinx_scaffold_includes_bilingual_files_and_targets(self) -> None:
        layout_template = self.skill_root / "templates" / "sphinx" / "_templates" / "layout.html"
        makefile_path = self.skill_root / "templates" / "sphinx" / "Makefile"
        conf_path = self.skill_root / "templates" / "sphinx" / "conf.py"

        self.assertTrue(layout_template.exists(), "layout.html template is missing")

        makefile = makefile_path.read_text(encoding="utf-8")
        for target in ("html-en", "html-zh", "html-all", "gettext", "intl-update", "strip-confidential"):
            self.assertRegex(makefile, rf"(?m)^{re.escape(target)}:", f"missing target {target}")

        conf = conf_path.read_text(encoding="utf-8")
        self.assertIn('language = os.environ.get("SPHINX_LANGUAGE", "en")', conf)
        self.assertIn("locale_dirs = ['locale/']", conf)
        self.assertIn("gettext_compact = False", conf)
        self.assertIn("available_languages", conf)

    def test_init_pkb_supports_bilingual_flag_and_copies_publish_artifacts(self) -> None:
        init_script = self.skill_root / "scripts" / "init_pkb.sh"

        with tempfile.TemporaryDirectory() as temp_dir:
            pkb_root = Path(temp_dir) / "demo-pkb" / "man"
            result = subprocess.run(
                [
                    "bash",
                    str(init_script),
                    "--pkb-root",
                    str(pkb_root),
                    "--sphinx",
                    "--bilingual=zh_CN",
                    "--project-name",
                    "Demo SDK",
                    "--force",
                ],
                cwd=self.skill_root,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            self.assertTrue((pkb_root / "_templates" / "layout.html").exists())
            self.assertTrue((pkb_root / "scripts" / "translate_po.py").exists())
            self.assertTrue((pkb_root / "scripts" / "render_landing.py").exists())

            conf = (pkb_root / "conf.py").read_text(encoding="utf-8")
            self.assertIn("available_languages", conf)
            self.assertIn("locale_dirs = ['locale/']", conf)

            makefile = (pkb_root / "Makefile").read_text(encoding="utf-8")
            self.assertRegex(makefile, r"(?m)^html-all:")
            self.assertRegex(makefile, r"(?m)^strip-confidential:")


if __name__ == "__main__":
    unittest.main()
