from __future__ import annotations

import datetime as dt
import html
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from scripts.import_daily import import_daily, prepare_report
from scripts.recover_daily import COMPLETE, Recovery, RecoveryFailure, singapore_today, verify_page
from test_validate_daily import report_body

DATE = "2026-09-01"
ROOT = Path(__file__).resolve().parent.parent


def rendered_report(raw: str, date: str = DATE) -> str:
    _text, title, description = prepare_report(raw, date, None)
    links = re.findall(r"\[[^\]]+\]\((https://[^)]+)\)", raw)
    return (f'<html><meta name="description" content="{html.escape(description)}">'
            f'<article><h1>{title}<a>¶</a></h1>' + "".join(
                f'<a href="{html.escape(url)}">source</a>' for url in links
            ) + '</article></html>')


class FakeServices(Recovery):
    """Real Git + real validator/importer; only external services are simulated."""
    def __init__(self, root: Path, **kwargs):
        super().__init__(root, DATE, **kwargs)
        self.calls: list[list[str]] = []
        self.push_failure = False
        self.build_failure = False
        self.generation_failure = False
        self.generated = report_body()
        self.generation_input = ""
        self.run_status = "completed"
        self.conclusion = "success"
        self.run_attempt = 1
        self.no_run = False
        self.page_failure = False
        self.pending_polls = 0
        self.retry_fails = False

    def check_repository(self):
        # Production requires the exact GitHub origin; tests use a local bare remote.
        if self.git("branch", "--show-current") != "main":
            raise RecoveryFailure("Commit", "wrong branch")

    def pause(self):
        pass

    def command(self, args, layer, **kwargs):
        self.calls.append(args)
        executable = Path(args[0]).name
        if args[:2] == ["git", "push"] and self.push_failure:
            self.push_failure = False
            raise RecoveryFailure("Push", "simulated network failure")
        if executable == "codex":
            self.generation_input = kwargs["input_text"]
            output = Path(args[args.index("--output-last-message") + 1])
            output.write_text(self.generated, encoding="utf-8")
            if self.generation_failure:
                raise RecoveryFailure("生成", "simulated generation failure")
            return subprocess.CompletedProcess(args, 0, "", "")
        if executable == "mkdocs":
            if self.build_failure:
                raise RecoveryFailure("Build", "simulated strict build failure")
            return subprocess.CompletedProcess(args, 0, "", "")
        if executable == "gh":
            if args[1:3] == ["run", "list"]:
                if self.pending_polls:
                    self.pending_polls -= 1
                    status, conclusion = "in_progress", ""
                else:
                    status, conclusion = self.run_status, self.conclusion
                runs = [] if self.no_run else [{
                    "databaseId": 123, "headSha": args[args.index("--commit") + 1],
                    "status": status, "conclusion": conclusion,
                    "attempt": self.run_attempt, "url": "https://github.com/example/run/123",
                }]
                return subprocess.CompletedProcess(args, 0, json.dumps(runs), "")
            if args[1:3] in (["run", "rerun"], ["workflow", "run"]):
                self.no_run = False
                self.conclusion = "failure" if self.retry_fails else "success"
                self.run_attempt += 1
                return subprocess.CompletedProcess(args, 0, "", "")
            raise AssertionError(args)
        if executable == "curl":
            text = "<html>not this report</html>" if self.page_failure else rendered_report(self.archive.read_text(encoding="utf-8"))
            return subprocess.CompletedProcess(args, 0, text + "\n200", "")
        return super().command(args, layer, **kwargs)


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="market-daily-recovery-test-")
        self.addCleanup(self.temporary.cleanup)
        self.folder = Path(self.temporary.name)
        self.root = self.folder / "repo"
        self.root.mkdir()
        # Keep the fixture date absent even after the real archive reaches that day.
        shutil.copytree(ROOT / "docs", self.root / "docs",
                        ignore=shutil.ignore_patterns(f"{DATE}.md"))
        shutil.copytree(ROOT / "prompts", self.root / "prompts")
        shutil.copytree(ROOT / ".github", self.root / ".github")
        for name in ("mkdocs.yml", "PROJECT.md", ".gitignore"):
            shutil.copyfile(ROOT / name, self.root / name)
        self.git("init", "-b", "main")
        self.git("config", "user.name", "Recovery Test")
        self.git("config", "user.email", "test@example.invalid")
        self.git("config", "commit.gpgsign", "false")
        self.git("config", "core.hooksPath", "/dev/null")
        self.git("add", ".")
        self.git("commit", "-m", "fixture")
        self.remote = self.folder / "remote.git"
        self.git("init", "--bare", str(self.remote))
        self.git("remote", "add", "origin", str(self.remote))
        self.git("push", "-u", "origin", "main")
        self.recovery = FakeServices(self.root)
        self.draft = self.recovery.draft
        self.archive = self.recovery.archive

    def git(self, *args):
        return subprocess.run(["git", *args], cwd=self.root, text=True, check=True,
                              capture_output=True).stdout.strip()

    def draft_report(self):
        self.draft.parent.mkdir(exist_ok=True)
        self.draft.write_text(report_body(), encoding="utf-8")

    def imported(self, *, commit=False, push=False):
        self.draft_report()
        import_daily(self.root, self.draft, DATE, None)
        if commit:
            self.git("add", "docs", "mkdocs.yml")
            self.git("commit", "-m", f"Import market daily {DATE}")
        if push:
            self.git("push", "origin", "main")

    def calls(self, *prefix):
        return [c for c in self.recovery.calls if c[:len(prefix)] == list(prefix)]

    def assert_layer(self, layer):
        with self.assertRaises(RecoveryFailure) as caught:
            self.recovery.run()
        self.assertEqual(caught.exception.layer, layer)

    def test_complete_report_has_no_generation_build_commit_push_or_rerun(self):
        self.imported(commit=True, push=True)
        before = self.git("rev-parse", "HEAD")
        self.recovery.run()
        self.assertEqual(self.recovery.status["Final result"], COMPLETE)
        self.assertEqual(self.recovery.operations, [])
        self.assertEqual(self.git("rev-parse", "HEAD"), before)
        self.assertFalse(self.calls("git", "push"))
        self.assertFalse(self.calls("git", "commit"))
        self.assertFalse(self.calls("git", "fetch"))

    def test_complete_report_leaves_unrelated_work_untouched(self):
        self.imported(commit=True, push=True)
        (self.root / "notes.txt").write_text("personal work", encoding="utf-8")
        self.recovery.run()
        self.assertEqual(self.recovery.status["Final result"], COMPLETE)
        self.assertEqual((self.root / "notes.txt").read_text(), "personal work")

    def test_inbox_is_reused_without_generation(self):
        self.draft_report()
        self.recovery.run()
        self.assertNotIn("生成", self.recovery.operations)
        self.assertTrue(self.archive.is_file())
        self.assertEqual(len(self.calls("git", "commit")), 1)

    def test_archive_without_commit_or_inbox_is_recovered(self):
        self.imported()
        self.draft.unlink()
        before = self.archive.read_bytes()
        self.recovery.run()
        self.assertEqual(self.archive.read_bytes(), before)
        self.assertNotIn("生成", self.recovery.operations)
        self.assertEqual(self.git("status", "--porcelain"), "")

    def test_partial_import_navigation_is_completed(self):
        self.draft_report()
        self.archive.parent.mkdir(parents=True, exist_ok=True)
        self.archive.write_bytes(self.draft.read_bytes())
        self.recovery.run()
        self.assertIn(f'"{DATE}"', (self.root / "mkdocs.yml").read_text())
        self.assertEqual(self.git("status", "--porcelain"), "")

    def test_push_failure_recovers_existing_commit(self):
        self.draft_report()
        self.recovery.push_failure = True
        self.assert_layer("Push")
        committed = self.git("rev-parse", "HEAD")
        self.recovery = FakeServices(self.root)
        self.recovery.run()
        self.assertEqual(self.git("rev-parse", "HEAD"), committed)
        self.assertFalse(self.calls("git", "commit"))
        self.assertNotIn("生成", self.recovery.operations)
        self.assertEqual(self.git("rev-parse", "origin/main"), committed)

    def test_different_same_date_report_refuses_overwrite(self):
        self.imported(commit=True, push=True)
        before = self.archive.read_bytes()
        self.draft.write_text(report_body() + "\n不同来源的新解释。\n", encoding="utf-8")
        self.assert_layer("Import")
        self.assertEqual(self.archive.read_bytes(), before)
        self.assertFalse(self.calls("git", "fetch"))
        self.assertFalse(self.calls("git", "push"))

    def test_validator_failure_stops_before_any_git_operation(self):
        self.draft_report()
        self.draft.write_text("残缺日报", encoding="utf-8")
        self.assert_layer("Validator")
        self.assertFalse(self.calls("git"))
        self.assertFalse(self.archive.exists())

    def test_build_failure_leaves_recoverable_uncommitted_archive(self):
        self.draft_report()
        self.recovery.build_failure = True
        self.assert_layer("Build")
        self.assertTrue(self.archive.is_file())
        self.assertFalse(self.calls("git", "commit"))
        self.recovery = FakeServices(self.root)
        self.recovery.run()
        self.assertEqual(self.git("status", "--porcelain"), "")

    def test_unrelated_dirty_work_is_not_committed(self):
        self.draft_report()
        (self.root / "notes.txt").write_text("do not commit", encoding="utf-8")
        self.assert_layer("Commit")
        self.assertFalse(self.archive.exists())

    def test_manual_navigation_edits_are_not_absorbed(self):
        self.imported()
        with (self.root / "docs/index.md").open("a") as handle:
            handle.write("\nUnrelated manual change\n")
        self.assert_layer("Import")
        self.assertFalse(self.calls("git", "commit"))

    def test_exact_staged_import_is_supported(self):
        self.imported()
        self.git("add", "docs", "mkdocs.yml")
        self.recovery.run()
        self.assertEqual(self.git("status", "--porcelain"), "")

    def test_mixed_staged_content_is_not_committed(self):
        self.imported()
        index = self.root / "docs/index.md"
        original = index.read_text(encoding="utf-8")
        index.write_text(original + "\nUnrelated staged change\n", encoding="utf-8")
        self.git("add", "docs", "mkdocs.yml")
        index.write_text(original, encoding="utf-8")
        self.assert_layer("Commit")
        self.assertFalse(self.calls("git", "commit"))

    def test_symlink_navigation_is_rejected_before_import(self):
        self.draft_report()
        index = self.root / "docs/index.md"
        outside = self.folder / "outside-index.md"
        outside.write_bytes(index.read_bytes())
        index.unlink()
        index.symlink_to(outside)
        original = outside.read_bytes()
        self.assert_layer("Import")
        self.assertEqual(outside.read_bytes(), original)
        self.assertFalse(self.archive.exists())

    def test_remote_ahead_requires_manual_sync_without_push(self):
        self.imported(commit=True, push=True)
        previous = self.git("rev-parse", "HEAD^")
        # Simulate an older checkout without deleting any user's data.
        self.git("checkout", "-b", "older-checkout", previous)
        self.git("branch", "-M", "main")
        self.assert_layer("Push")
        self.assertFalse(self.calls("git", "push"))

    def test_wrong_origin_is_rejected(self):
        production = Recovery(self.root, DATE, no_generate=True)
        with self.assertRaises(RecoveryFailure) as caught:
            production.check_repository()
        self.assertEqual(caught.exception.layer, "Push")

    def test_unrelated_outgoing_commit_is_not_pushed(self):
        self.imported(commit=True)
        (self.root / "notes.txt").write_text("unrelated", encoding="utf-8")
        self.git("add", "notes.txt")
        self.git("commit", "-m", "unrelated")
        self.assert_layer("Push")
        self.assertFalse(self.calls("git", "push"))

    def test_actions_failure_reruns_same_sha_without_commit_or_push(self):
        self.imported(commit=True, push=True)
        self.recovery.conclusion = "failure"
        self.recovery.run()
        self.assertEqual(len(self.calls("gh", "run", "rerun")), 1)
        self.assertFalse(self.calls("git", "commit"))
        self.assertFalse(self.calls("git", "push"))

    def test_pending_actions_are_waited_not_rerun(self):
        self.imported(commit=True, push=True)
        self.recovery.pending_polls = 2
        self.recovery.run()
        self.assertFalse(self.calls("gh", "run", "rerun"))

    def test_repeated_actions_failure_stops_after_one_retry(self):
        self.imported(commit=True, push=True)
        self.recovery.conclusion = "failure"
        self.recovery.retry_fails = True
        self.assert_layer("Actions")
        self.assertEqual(len(self.calls("gh", "run", "rerun")), 1)
        self.assertFalse(self.calls("git", "commit"))
        self.assertFalse(self.calls("git", "push"))

    def test_absent_workflow_dispatches_once(self):
        self.imported(commit=True, push=True)
        self.recovery.no_run = True
        self.recovery.run()
        self.assertEqual(len(self.calls("gh", "workflow", "run")), 1)

    def test_pages_failure_does_not_commit_push_or_redeploy(self):
        self.imported(commit=True, push=True)
        self.recovery.page_failure = True
        self.assert_layer("Pages")
        self.assertFalse(self.calls("git", "push"))
        self.assertFalse(self.calls("gh", "run", "rerun"))

    def test_no_generate_handoff_preserves_repository(self):
        self.recovery.no_generate = True
        with self.assertRaises(RecoveryFailure) as caught:
            self.recovery.run()
        self.assertEqual(caught.exception.code, 3)
        self.assertEqual(caught.exception.layer, "生成")
        self.assertFalse(self.draft.exists())

    @patch("scripts.recover_daily.shutil.which", return_value="codex")
    def test_missing_report_generates_using_current_prompt(self, _which):
        with (self.root / "prompts/daily_market_report.md").open("a") as handle:
            handle.write("\nLatest version marker\n")
        self.git("add", "prompts")
        self.git("commit", "-m", "prompt version")
        self.git("push", "origin", "main")
        self.recovery.run()
        self.assertIn("Latest version marker", self.recovery.generation_input)
        self.assertIn("生成", self.recovery.operations)
        command = next(c for c in self.recovery.calls if c[0] == "codex")
        self.assertIn("read-only", command)
        self.assertNotIn("--dangerously-bypass-approvals-and-sandbox", command)

    @patch("scripts.recover_daily.shutil.which", return_value="codex")
    def test_failed_generator_does_not_adopt_even_complete_output(self, _which):
        self.recovery.generation_failure = True
        self.assert_layer("生成")
        self.assertFalse(self.draft.exists())
        self.assertFalse(self.archive.exists())
        self.assertFalse(self.calls("git", "commit"))

    @patch("scripts.recover_daily.shutil.which", return_value="codex")
    def test_invalid_generated_report_is_not_archived(self, _which):
        self.recovery.generated = "incomplete"
        self.assert_layer("Validator")
        self.assertFalse(self.draft.exists())
        self.assertFalse(self.archive.exists())

    def test_deleted_committed_report_is_not_regenerated(self):
        self.imported(commit=True, push=True)
        self.draft.unlink()
        self.archive.unlink()
        self.assert_layer("Import")
        self.assertNotIn("生成", self.recovery.operations)


class RecoveryUtilityTests(unittest.TestCase):
    def test_invalid_date_returns_usage_error_not_traceback(self):
        result = subprocess.run(
            ["python3", str(ROOT / "scripts/recover_daily.py"), "--date", "2026-02-30"],
            text=True, capture_output=True,
        )
        self.assertEqual(result.returncode, 2)
        self.assertNotIn("Traceback", result.stderr)

    def test_singapore_date_changes_at_utc_16(self):
        before = dt.datetime(2026, 8, 31, 15, 59, tzinfo=dt.timezone.utc)
        after = dt.datetime(2026, 8, 31, 16, 0, tzinfo=dt.timezone.utc)
        self.assertEqual(singapore_today(before), "2026-08-31")
        self.assertEqual(singapore_today(after), "2026-09-01")

    def test_page_requires_article_not_date_in_navigation(self):
        raw = report_body()
        self.assertTrue(verify_page(rendered_report(raw), raw, DATE))
        self.assertFalse(verify_page(f"<nav>{DATE}</nav><h1>Archive</h1>", raw, DATE))
        self.assertFalse(verify_page(rendered_report(raw).replace("https://www.bls.gov/", "https://example.org/"), raw, DATE))


if __name__ == "__main__":
    unittest.main()
