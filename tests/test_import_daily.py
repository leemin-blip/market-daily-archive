from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.import_daily import ImportFailure, import_daily, prepare_report


class ImportDailyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.repo = Path(self.temporary.name)
        (self.repo / "docs" / "2026" / "08").mkdir(parents=True)

        (self.repo / "docs" / "2026" / "08" / "2026-08-30.md").write_text(
            """---
title: 2026-08-30
description: 已有日报
---

# 美股市场日报｜2026-08-30

[来源](https://example.com/existing)
""",
            encoding="utf-8",
        )
        (self.repo / "docs" / "archive.md").write_text(
            """# 日报档案

<!-- BEGIN AUTO-GENERATED DAILY ARCHIVE -->
old
<!-- END AUTO-GENERATED DAILY ARCHIVE -->

## 维护约定
""",
            encoding="utf-8",
        )
        (self.repo / "docs" / "index.md").write_text(
            """# 首页

<!-- BEGIN AUTO-GENERATED LATEST LINK -->
old
<!-- END AUTO-GENERATED LATEST LINK -->

<!-- BEGIN AUTO-GENERATED DAILY TABLE -->
old
<!-- END AUTO-GENERATED DAILY TABLE -->
""",
            encoding="utf-8",
        )
        (self.repo / "docs" / "2026" / "index.md").write_text(
            """# 2026 年日报

<!-- BEGIN AUTO-GENERATED MONTH LIST -->
old
<!-- END AUTO-GENERATED MONTH LIST -->
""",
            encoding="utf-8",
        )
        (self.repo / "docs" / "2026" / "08" / "index.md").write_text(
            """# 2026 年 08 月

<!-- BEGIN AUTO-GENERATED DAILY LIST -->
old
<!-- END AUTO-GENERATED DAILY LIST -->
""",
            encoding="utf-8",
        )
        (self.repo / "mkdocs.yml").write_text(
            """nav:
  - 首页: index.md
  - 日报档案:
      - archive.md
      # BEGIN AUTO-GENERATED DAILY NAV
      old
      # END AUTO-GENERATED DAILY NAV
""",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def input_file(self, name: str, text: str) -> Path:
        path = self.repo / name
        path.write_text(text, encoding="utf-8")
        return path

    def test_import_creates_report_and_all_navigation(self) -> None:
        raw = """# 美股市场日报｜2026-09-01

## 市场摘要

保留原始正文结构。

## Sources

- [Official source](https://example.com/source)
"""
        input_path = self.input_file("incoming.md", raw)

        changed = import_daily(
            self.repo, input_path, "2026-09-01", "九月首篇日报"
        )

        target = self.repo / "docs" / "2026" / "09" / "2026-09-01.md"
        self.assertIn(target, changed)
        report = target.read_text(encoding="utf-8")
        self.assertIn('title: "2026-09-01"', report)
        self.assertIn('description: "九月首篇日报"', report)
        self.assertIn(raw.rstrip(), report)

        archive = (self.repo / "docs" / "archive.md").read_text(encoding="utf-8")
        self.assertIn("[2026-09-01](2026/09/2026-09-01.md)", archive)

        home = (self.repo / "docs" / "index.md").read_text(encoding="utf-8")
        self.assertIn("[查看最新日报](2026/09/2026-09-01.md)", home)
        self.assertIn("| 2026-09-01 | 九月首篇日报 |", home)

        year_index = (self.repo / "docs" / "2026" / "index.md").read_text(
            encoding="utf-8"
        )
        self.assertLess(year_index.index("09 月"), year_index.index("08 月"))

        month_index = (self.repo / "docs" / "2026" / "09" / "index.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("[2026-09-01](2026-09-01.md)", month_index)

        nav = (self.repo / "mkdocs.yml").read_text(encoding="utf-8")
        self.assertIn('          - "09 月":', nav)
        self.assertIn('              - "2026-09-01": 2026/09/2026-09-01.md', nav)

    def test_identical_rerun_is_idempotent(self) -> None:
        raw = """# 美股市场日报｜2026-09-01

[来源](https://example.com/source)
"""
        input_path = self.input_file("incoming.md", raw)
        first = import_daily(self.repo, input_path, "2026-09-01", "日报摘要")
        second = import_daily(self.repo, input_path, "2026-09-01", "日报摘要")
        self.assertTrue(first)
        self.assertEqual(second, [])

    def test_different_duplicate_is_rejected_without_overwrite(self) -> None:
        raw = """# 美股市场日报｜2026-09-01

[来源](https://example.com/source)
"""
        input_path = self.input_file("incoming.md", raw)
        import_daily(self.repo, input_path, "2026-09-01", "日报摘要")
        target = self.repo / "docs" / "2026" / "09" / "2026-09-01.md"
        before = target.read_text(encoding="utf-8")

        input_path.write_text(
            """# 美股市场日报｜2026-09-01

不同内容。[来源](https://example.com/other)
""",
            encoding="utf-8",
        )
        with self.assertRaises(ImportFailure):
            import_daily(self.repo, input_path, "2026-09-01", "日报摘要")
        self.assertEqual(target.read_text(encoding="utf-8"), before)

    def test_rejects_wrong_date_or_missing_source(self) -> None:
        with self.assertRaises(ImportFailure):
            prepare_report(
                "# 美股市场日报｜2026-09-02\n\n[来源](https://example.com)\n",
                "2026-09-01",
                None,
            )
        with self.assertRaises(ImportFailure):
            prepare_report("# 美股市场日报｜2026-09-01\n", "2026-09-01", None)


if __name__ == "__main__":
    unittest.main()
