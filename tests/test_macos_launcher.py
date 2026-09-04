from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "macos" / "archive_today.js"
OPEN_LAUNCHER = ROOT / "macos" / "open_archive.js"
INSTALLER = ROOT / "scripts" / "install_macos_launcher.sh"
PROMPT = ROOT / "prompts" / "daily_market_report.md"


class MacOSLauncherTests(unittest.TestCase):
    def test_launcher_calls_existing_clipboard_import_without_network(self) -> None:
        source = LAUNCHER.read_text(encoding="utf-8")

        self.assertIn('/usr/bin/pbpaste -Prefer txt 2>&1 > "$clipboard_input"', source)
        self.assertIn('LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8 /bin/bash -c ', source)
        self.assertNotIn('/bin/test -x ', source)
        self.assertNotIn('/usr/bin/test', source)
        self.assertIn('/bin/bash -c ', source)
        self.assertIn('__MARKET_DAILY_EXIT__', source)
        self.assertIn('.archive-today-last-run.log', source)
        self.assertIn('PATH=/usr/bin:/bin:/usr/sbin:/sbin', source)
        self.assertIn(r'split(/\r\n|\r|\n/)', source)
        self.assertIn('startsWith("Final result: ")', source)
        self.assertIn('/scripts/import_chatgpt_daily.sh', source)
        self.assertIn('/scripts/extract_chatgpt_daily.py', source)
        self.assertIn('< "$clipboard_input" 2>&1 > "$report_input"', source)
        self.assertIn('< "$report_input" 2>&1', source)
        self.assertIn('cd ', source)
        self.assertIn('__PROJECT_ROOT__', source)
        self.assertIn('今日日报已成功归档', source)
        self.assertIn('归档失败', source)
        for forbidden in (
            "curl ",
            "wget ",
            "gh ",
            "git push",
            "OPENAI_API_KEY",
            "generate_daily.py",
            "dispatch_daily_workflow.sh",
        ):
            self.assertNotIn(forbidden, source)

    def test_master_prompt_requires_unordered_cross_asset_bullets(self) -> None:
        prompt = PROMPT.read_text(encoding="utf-8")

        self.assertIn("Version: 1.6", prompt)
        self.assertIn("unordered Markdown list item beginning exactly with `- `", prompt)
        self.assertIn("Do not use `1.`, `2.`, or any other numbered-list marker", prompt)

    def test_master_prompt_is_cloud_on_demand_with_singapore_date(self) -> None:
        prompt = PROMPT.read_text(encoding="utf-8")

        self.assertIn("Generation mode: Cloud on-demand", prompt)
        self.assertIn("only when an on-demand invocation requests this report", prompt)
        self.assertIn("current calendar date in Asia/Singapore", prompt)
        self.assertNotIn("production generation schedule is every day", prompt)

    def test_master_prompt_requires_real_platform_native_sources(self) -> None:
        prompt = PROMPT.read_text(encoding="utf-8")

        self.assertIn("clickable platform-native source citation", prompt)
        self.assertIn("at least 3 such real, clickable, actually accessed source citations", prompt)
        self.assertIn("does not count without a clickable platform-native citation", prompt)
        self.assertIn("Never invent, guess, reconstruct, or concatenate a URL or citation", prompt)
        self.assertIn("actually accessed during this report's research", prompt)
        self.assertIn("final Market Daily Archive Markdown must still satisfy", prompt)
        self.assertIn("standard HTTPS Markdown links", prompt)
        self.assertIn("generation has failed", prompt)

    def test_installer_builds_ignored_app_next_to_source(self) -> None:
        installer = INSTALLER.read_text(encoding="utf-8")
        gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")

        self.assertIn("osacompile -l JavaScript", installer)
        self.assertIn('macos/归档今日日报.app', installer)
        self.assertIn('macos/打开 Market Daily Archive.app', installer)
        self.assertIn('.venv/bin/python', installer)
        self.assertIn('.venv/bin/mkdocs', installer)
        self.assertIn('lsregister', installer)
        self.assertIn("macos/*.app/", gitignore)

    def test_open_launcher_uses_local_controller_and_default_browser(self) -> None:
        source = OPEN_LAUNCHER.read_text(encoding="utf-8")

        self.assertIn("__PROJECT_ROOT__", source)
        self.assertIn("__PYTHON_BIN__", source)
        self.assertIn("__MKDOCS_BIN__", source)
        self.assertIn("/scripts/open_local_archive.py", source)
        self.assertIn("http://127.0.0.1:8000/", source)
        self.assertIn("app.openLocation(archiveUrl)", source)
        self.assertIn(".open-archive-last-run.log", source)
        self.assertIn("PATH=/usr/bin:/bin:/usr/sbin:/sbin", source)
        self.assertIn("无法打开本地 Archive", source)
        for forbidden in (
            "import_chatgpt_daily.sh",
            "validate_daily.py",
            "git ",
            "gh ",
            "curl ",
            "OPENAI_API_KEY",
        ):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
