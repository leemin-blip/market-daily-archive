from __future__ import annotations

import unittest

from scripts.validate_daily import ValidationFailure, validate_report


def report_body(report_type: str = "trading_day") -> str:
    filler = "市场变化得到数据和可靠来源支持，并说明资产定价逻辑。" * 12
    common = f"""## 今日市场一句话

{filler}

## 📰 今日重要市场新闻

{filler}

## 🧠 Market Narrative

{filler}

## 👀 What to Watch

{filler}

## 🔗 Sources

- [Federal Reserve](https://www.federalreserve.gov/)
- [U.S. Treasury](https://home.treasury.gov/)
"""
    if report_type == "market_closed":
        sections = f"""## 🏖️ 美国市场休市说明

最近一个美国市场周期休市，因此不重复静态收盘数据。{filler}

## 🌍 全球宏观与利率

个别数据暂不可得，但其余信息已经核实。{filler}

## 🛢️ 商品与汇率

{filler}

## 💻 AI、科技与半导体

{filler}
"""
    else:
        sections = f"""## 市场 Dashboard

2Y Treasury | 10Y Treasury | 2s10s | VIX | VXN | S&P 500 | Nasdaq Composite | Dow | SOX | WTI | Gold

## 🇺🇸 美国国债

{filler}

## 🌡️ 市场波动率

{filler}

## 📈 美国股市

### Major Indices

{filler}

### Magnificent Seven

{filler}

### Semiconductors

{filler}

## 🛢️ 商品

### WTI Crude Oil

{filler}

### Gold

{filler}
"""
        common += "- [BLS](https://www.bls.gov/)\n"
    return f"""---
title: 2026-09-01 市场日报
description: 当日市场主线摘要
report_type: {report_type}
---

# 2026-09-01 市场日报

{sections}
{common}
"""


class ValidateDailyTests(unittest.TestCase):
    def test_accepts_complete_trading_report(self) -> None:
        self.assertEqual(validate_report(report_body(), "2026-09-01"), "trading_day")

    def test_accepts_market_closed_report_with_one_unavailable_item(self) -> None:
        self.assertEqual(
            validate_report(report_body("market_closed"), "2026-09-01"),
            "market_closed",
        )

    def test_rejects_empty_wrong_date_and_missing_structure(self) -> None:
        with self.assertRaises(ValidationFailure):
            validate_report("", "2026-09-01")
        with self.assertRaises(ValidationFailure):
            validate_report(report_body(), "2026-09-02")
        with self.assertRaises(ValidationFailure):
            validate_report(
                report_body().replace("## 🧠 Market Narrative", "## 市场叙事"),
                "2026-09-01",
            )

    def test_rejects_low_source_count_and_truncated_report(self) -> None:
        low_sources = report_body("market_closed").replace(
            "- [U.S. Treasury](https://home.treasury.gov/)\n", ""
        )
        with self.assertRaises(ValidationFailure):
            validate_report(low_sources, "2026-09-01")
        with self.assertRaises(ValidationFailure):
            validate_report(report_body()[:700], "2026-09-01")


if __name__ == "__main__":
    unittest.main()
