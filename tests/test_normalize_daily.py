from __future__ import annotations

import unittest

from scripts.normalize_daily import NormalizationFailure, normalize_cross_asset_markers
from scripts.validate_daily import ValidationFailure, validate_report
from tests.test_validate_daily import report_body


REPORT_DATE = "2026-09-01"


def numbered_report() -> bytes:
    return (
        report_body()
        .replace(
            "- Treasury 与 DXY 的方向共同反映利率重新定价。",
            "1. Treasury 与 DXY 的方向共同反映利率重新定价。",
        )
        .replace(
            "- 股票、波动率与商品信号需要放在一起判断。",
            "2. 股票、波动率与商品信号需要放在一起判断。",
        )
        .encode("utf-8")
    )


class NormalizeDailyTests(unittest.TestCase):
    def test_converts_only_consecutive_ordered_markers(self) -> None:
        before = numbered_report()
        expected = report_body().encode("utf-8")

        result = normalize_cross_asset_markers(before)

        self.assertEqual(result.changed_markers, ("1. ", "2. "))
        self.assertEqual(result.markdown, expected)
        self.assertEqual(
            before.replace(b"1. Treasury", b"- Treasury").replace(
                b"2. \xe8\x82\xa1\xe7\xa5\xa8", b"- \xe8\x82\xa1\xe7\xa5\xa8"
            ),
            result.markdown,
        )

    def test_already_valid_bullets_are_byte_identical(self) -> None:
        before = report_body().encode("utf-8")
        result = normalize_cross_asset_markers(before)

        self.assertEqual(result.changed_markers, ())
        self.assertIs(result.markdown, before)

    def test_validator_rejects_before_and_passes_after(self) -> None:
        before = numbered_report()
        with self.assertRaises(ValidationFailure):
            validate_report(before.decode("utf-8"), REPORT_DATE)

        after = normalize_cross_asset_markers(before).markdown
        self.assertEqual(validate_report(after.decode("utf-8"), REPORT_DATE), "trading_day")

    def test_mixed_or_nonconsecutive_numbering_fails_closed(self) -> None:
        mixed = numbered_report().replace(
            b"2. \xe8\x82\xa1\xe7\xa5\xa8", b"- \xe8\x82\xa1\xe7\xa5\xa8"
        )
        skipped = numbered_report().replace(b"2. ", b"3. ")

        with self.assertRaises(NormalizationFailure):
            normalize_cross_asset_markers(mixed)
        with self.assertRaises(NormalizationFailure):
            normalize_cross_asset_markers(skipped)

    def test_indented_or_continued_numbering_fails_closed(self) -> None:
        indented = numbered_report().replace(b"1. Treasury", b"  1. Treasury")
        continued = numbered_report().replace(
            b"1. Treasury", b"1. Treasury\ncontinued detail"
        )

        with self.assertRaises(NormalizationFailure):
            normalize_cross_asset_markers(indented)
        with self.assertRaises(NormalizationFailure):
            normalize_cross_asset_markers(continued)

    def test_out_of_range_numbering_fails_closed(self) -> None:
        one = b"".join(
            line for line in numbered_report().splitlines(keepends=True)
            if not line.startswith(b"2. ")
        )
        with self.assertRaises(NormalizationFailure):
            normalize_cross_asset_markers(one)


if __name__ == "__main__":
    unittest.main()
