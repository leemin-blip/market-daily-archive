from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests.test_validate_daily import report_body


SOURCE_ROOT = Path(__file__).resolve().parents[1]
REPORT_DATE = "2099-09-01"


def valid_report() -> str:
    return report_body().replace("2026-09-01", REPORT_DATE)


class ImportChatGPTDailyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.repo = Path(self.temporary.name)
        shutil.copytree(SOURCE_ROOT / "docs", self.repo / "docs")
        (self.repo / "scripts").mkdir()
        for name in (
            "import_chatgpt_daily.sh",
            "import_daily.py",
            "normalize_daily.py",
            "recover_rejected_draft.py",
            "validate_daily.py",
        ):
            shutil.copy2(SOURCE_ROOT / "scripts" / name, self.repo / "scripts" / name)
        shutil.copy2(SOURCE_ROOT / "mkdocs.yml", self.repo / "mkdocs.yml")

        bin_dir = self.repo / ".venv" / "bin"
        bin_dir.mkdir(parents=True)
        fake_mkdocs = bin_dir / "mkdocs"
        fake_mkdocs.write_text(
            "#!/bin/sh\nprintf '%s\\n' \"$@\" > mkdocs.args\n"
            "exit \"${FAKE_MKDOCS_EXIT:-0}\"\n",
            encoding="utf-8",
        )
        fake_mkdocs.chmod(0o755)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def run_import(self, markdown: str, **environment: str) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env.update(environment)
        return subprocess.run(
            [str(self.repo / "scripts" / "import_chatgpt_daily.sh")],
            cwd=self.repo,
            input=markdown,
            text=True,
            capture_output=True,
            env=env,
            check=False,
        )

    @property
    def draft(self) -> Path:
        return self.repo / "inbox" / f"{REPORT_DATE}.md"

    @property
    def archived(self) -> Path:
        return self.repo / "docs" / "2099" / "09" / f"{REPORT_DATE}.md"

    def test_imports_valid_stdin_and_runs_strict_build(self) -> None:
        result = self.run_import(valid_report())

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.draft.read_text(encoding="utf-8"), valid_report())
        self.assertEqual(
            self.archived.read_text(encoding="utf-8"), valid_report().rstrip() + "\n"
        )
        self.assertEqual(
            (self.repo / "mkdocs.args").read_text(encoding="utf-8"),
            "build\n--strict\n",
        )
        self.assertIn(f"Report date: {REPORT_DATE}", result.stdout)
        self.assertIn("Validator status: PASSED", result.stdout)
        self.assertIn("Import status: PASSED", result.stdout)
        self.assertIn("GitHub status: NOT RUN", result.stdout)
        self.assertIn("Final result: SUCCESS", result.stdout)

    def test_empty_input_stops_before_draft_and_build(self) -> None:
        result = self.run_import(" \n\t\n")

        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.draft.exists())
        self.assertFalse(self.archived.exists())
        self.assertFalse((self.repo / "mkdocs.args").exists())
        self.assertIn("Input status: FAILED", result.stderr)

    def test_identical_rerun_is_idempotent(self) -> None:
        first = self.run_import(valid_report())
        before = self.archived.read_bytes()
        nav_before = (self.repo / "mkdocs.yml").read_text(encoding="utf-8")
        second = self.run_import(valid_report())

        self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
        self.assertEqual(second.returncode, 0, second.stdout + second.stderr)
        self.assertEqual(self.archived.read_bytes(), before)
        self.assertIn("already present with identical content", second.stdout)
        self.assertEqual(
            (self.repo / "mkdocs.yml").read_text(encoding="utf-8"), nav_before
        )

    def test_different_existing_inbox_is_not_overwritten(self) -> None:
        self.draft.parent.mkdir(parents=True)
        self.draft.write_text(valid_report(), encoding="utf-8")
        different = valid_report().replace("当日市场主线摘要", "另一份市场主线摘要")

        result = self.run_import(different)

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.draft.read_text(encoding="utf-8"), valid_report())
        self.assertFalse(self.archived.exists())
        self.assertFalse((self.repo / "mkdocs.args").exists())
        self.assertIn("Draft status: FAILED", result.stderr)
        self.assertIn("still passes the current Validator", result.stderr)
        self.assertFalse((self.repo / "inbox" / "rejected").exists())

    def test_replaces_only_proven_invalid_draft_after_new_candidate_passes(self) -> None:
        invalid = valid_report().replace("## 🧠 Market Narrative", "## 市场叙事")
        self.draft.parent.mkdir(parents=True)
        self.draft.write_text(invalid, encoding="utf-8")

        result = self.run_import(valid_report())

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.draft.read_text(encoding="utf-8"), valid_report())
        self.assertEqual(
            self.archived.read_text(encoding="utf-8"), valid_report().rstrip() + "\n"
        )
        rejected = self.repo / "inbox" / "rejected" / f"{REPORT_DATE}-rejected-001.md"
        self.assertEqual(rejected.read_text(encoding="utf-8"), invalid)
        self.assertIn("Replacement candidate Validator status: PASSED", result.stdout)
        self.assertIn("Rejected draft preserved:", result.stdout)

    def test_invalid_replacement_does_not_overwrite_invalid_draft(self) -> None:
        old_invalid = valid_report().replace(
            "## 🧠 Market Narrative", "## 旧的市场叙事"
        )
        new_invalid = valid_report().replace(
            "## 👀 What to Watch", "## 新的观察列表"
        )
        self.draft.parent.mkdir(parents=True)
        self.draft.write_text(old_invalid, encoding="utf-8")

        result = self.run_import(new_invalid)

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.draft.read_text(encoding="utf-8"), old_invalid)
        self.assertFalse(self.archived.exists())
        self.assertFalse((self.repo / "inbox" / "rejected").exists())
        self.assertIn("Validator status: FAILED", result.stderr)
        self.assertIn("existing inbox draft was not changed", result.stderr)

    def test_archived_date_blocks_recovery_and_preserves_everything(self) -> None:
        first = self.run_import(valid_report())
        old_draft = self.draft.read_bytes()
        old_archive = self.archived.read_bytes()
        different = valid_report().replace("当日市场主线摘要", "另一份市场主线摘要")

        second = self.run_import(different)

        self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
        self.assertNotEqual(second.returncode, 0)
        self.assertEqual(self.draft.read_bytes(), old_draft)
        self.assertEqual(self.archived.read_bytes(), old_archive)
        self.assertFalse((self.repo / "inbox" / "rejected").exists())
        self.assertIn("formal archive already exists", second.stderr)

    def test_rejected_history_collision_uses_next_available_name(self) -> None:
        invalid = valid_report().replace("## 🧠 Market Narrative", "## 市场叙事")
        rejected_dir = self.repo / "inbox" / "rejected"
        rejected_dir.mkdir(parents=True)
        collision = rejected_dir / f"{REPORT_DATE}-rejected-001.md"
        collision.write_text("existing audit record\n", encoding="utf-8")
        self.draft.write_text(invalid, encoding="utf-8")

        result = self.run_import(valid_report())

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(collision.read_text(encoding="utf-8"), "existing audit record\n")
        next_backup = rejected_dir / f"{REPORT_DATE}-rejected-002.md"
        self.assertEqual(next_backup.read_text(encoding="utf-8"), invalid)
        self.assertIn(str(next_backup.relative_to(self.repo)), result.stdout)

    def test_validator_failure_leaves_draft_but_does_not_import(self) -> None:
        invalid = valid_report().replace("## 🧠 Market Narrative", "## 市场叙事")

        result = self.run_import(invalid)

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.draft.read_text(encoding="utf-8"), invalid)
        self.assertFalse(self.archived.exists())
        self.assertFalse((self.repo / "mkdocs.args").exists())
        self.assertIn("Validator status: FAILED", result.stderr)

    def test_numbered_cross_asset_is_normalized_before_validation(self) -> None:
        numbered = valid_report().replace(
            "- Treasury 与 DXY 的方向共同反映利率重新定价。",
            "1. Treasury 与 DXY 的方向共同反映利率重新定价。",
        ).replace(
            "- 股票、波动率与商品信号需要放在一起判断。",
            "2. 股票、波动率与商品信号需要放在一起判断。",
        )

        result = self.run_import(numbered)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.draft.read_text(encoding="utf-8"), valid_report())
        self.assertEqual(
            self.archived.read_text(encoding="utf-8"), valid_report().rstrip() + "\n"
        )
        self.assertIn("converted only 跨资产观察 list marker(s)", result.stdout)

    def test_unsafe_numbered_cross_asset_stops_before_draft(self) -> None:
        unsafe = valid_report().replace(
            "- Treasury 与 DXY 的方向共同反映利率重新定价。",
            "1. Treasury 与 DXY 的方向共同反映利率重新定价。",
        ).replace(
            "- 股票、波动率与商品信号需要放在一起判断。",
            "3. 股票、波动率与商品信号需要放在一起判断。",
        )

        result = self.run_import(unsafe)

        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.draft.exists())
        self.assertFalse(self.archived.exists())
        self.assertIn("Normalize status: FAILED", result.stderr)

    def test_different_existing_archive_is_not_overwritten(self) -> None:
        first = self.run_import(valid_report())
        existing = self.archived.read_text(encoding="utf-8")
        self.draft.unlink()
        different = valid_report().replace("市场变化得到数据", "资产变化得到数据")

        second = self.run_import(different)

        self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
        self.assertNotEqual(second.returncode, 0)
        self.assertEqual(self.archived.read_text(encoding="utf-8"), existing)
        self.assertIn("Import status: FAILED", second.stderr)

    def test_front_matter_and_h1_dates_must_match(self) -> None:
        mismatch = valid_report().replace(
            f"title: {REPORT_DATE} 市场日报", "title: 2099-09-02 市场日报"
        )

        result = self.run_import(mismatch)

        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.draft.exists())
        self.assertFalse(self.archived.exists())
        self.assertIn("Input status: FAILED", result.stderr)

    def test_relaxed_report_title_reaches_validator_with_specific_reason(self) -> None:
        invalid = valid_report().replace(
            f"# {REPORT_DATE} 市场日报", f"# {REPORT_DATE} 美股市场日报"
        )

        result = self.run_import(invalid)

        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(self.draft.exists())
        self.assertFalse(self.archived.exists())
        self.assertIn("Validator status: FAILED", result.stderr)
        self.assertIn("exactly one H1", result.stderr)
        self.assertIn("ChatGPT message Copy button", result.stderr)

    def test_missing_date_explains_how_to_preserve_markdown(self) -> None:
        result = self.run_import("市场日报\n\n没有可识别日期。\n")

        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.archived.exists())
        self.assertIn("Input status: FAILED", result.stderr)
        self.assertIn("ChatGPT message Copy button", result.stderr)

    def test_build_failure_is_reported_and_never_pushes(self) -> None:
        result = self.run_import(valid_report(), FAKE_MKDOCS_EXIT="7")

        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(self.archived.exists())
        self.assertIn("Build status: FAILED", result.stderr)
        script = (self.repo / "scripts" / "import_chatgpt_daily.sh").read_text(
            encoding="utf-8"
        )
        for forbidden in ("git push", "gh ", "curl ", "OPENAI_API_KEY", "generate_daily.py"):
            self.assertNotIn(forbidden, script)


if __name__ == "__main__":
    unittest.main()
