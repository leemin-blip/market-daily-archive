from __future__ import annotations

import unittest

from scripts.extract_chatgpt_daily import ExtractionFailure, extract_report
from scripts.validate_daily import ValidationFailure, validate_report
from tests.test_validate_daily import report_body


REPORT_DATE = "2026-09-01"


class ExtractChatGPTDailyTests(unittest.TestCase):
    def test_chatgpt_preamble_is_removed_without_changing_report_bytes(self) -> None:
        report = report_body().encode("utf-8")
        copied = (
            "已读取最新版 Master Prompt。下面是可直接归档的正式日报。\n\n"
            "生成说明不会进入日报。\n\n"
        ).encode("utf-8") + report

        result = extract_report(copied)

        self.assertEqual(result.strategy, "yaml-title")
        self.assertEqual(result.date, REPORT_DATE)
        self.assertGreater(result.leading_bytes, 0)
        self.assertEqual(result.markdown, report)
        self.assertEqual(validate_report(result.markdown.decode(), REPORT_DATE), "trading_day")

    def test_yaml_title_has_priority_over_an_earlier_exact_h1(self) -> None:
        report = report_body().encode("utf-8")
        copied = b"# 2099-01-01 \xe5\xb8\x82\xe5\x9c\xba\xe6\x97\xa5\xe6\x8a\xa5\n\n" + report

        result = extract_report(copied)

        self.assertEqual(result.strategy, "yaml-title")
        self.assertEqual(result.date, REPORT_DATE)
        self.assertEqual(result.markdown, report)

    def test_unique_exact_h1_is_the_fallback_when_yaml_is_absent(self) -> None:
        markdown = f"# {REPORT_DATE} 市场日报\n\n正文保持原样。\n".encode("utf-8")
        result = extract_report("说明文字\n\n".encode("utf-8") + markdown)

        self.assertEqual(result.strategy, "exact-h1")
        self.assertEqual(result.markdown, markdown)

    def test_ambiguous_or_fenced_candidates_fail_closed(self) -> None:
        report = report_body()
        with self.assertRaises(ExtractionFailure):
            extract_report((report + "\n" + report).encode("utf-8"))
        fenced = f"说明\n\n```markdown\n{report}\n```\n".encode("utf-8")
        with self.assertRaises(ExtractionFailure):
            extract_report(fenced)

    def test_numbered_cross_asset_list_is_not_rewritten_and_validator_rejects_it(self) -> None:
        report = report_body()
        numbered = report.replace(
            "- Treasury 与 DXY 的方向共同反映利率重新定价。",
            "1. Treasury 与 DXY 的方向共同反映利率重新定价。",
        ).replace(
            "- 股票、波动率与商品信号需要放在一起判断。",
            "2. 股票、波动率与商品信号需要放在一起判断。",
        )

        result = extract_report(("说明文字\n\n" + numbered).encode("utf-8"))

        self.assertEqual(result.markdown.decode("utf-8"), numbered)
        with self.assertRaises(ValidationFailure):
            validate_report(result.markdown.decode("utf-8"), REPORT_DATE)


if __name__ == "__main__":
    unittest.main()
