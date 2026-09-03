from __future__ import annotations

import unittest

from scripts.validate_daily import ValidationFailure, validate_report


def report_body(report_type: str = "trading_day") -> str:
    filler = "市场变化得到数据和可靠来源支持，并说明资产定价逻辑。" * 12
    common = f"""## 今日市场一句话

{filler}

## 📰 今日重要市场新闻

{filler}

## 跨资产观察

- Treasury 与 DXY 的方向共同反映利率重新定价。{filler}
- 股票、波动率与商品信号需要放在一起判断。{filler}

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

### 利率

2Y Treasury | 10Y Treasury | 30Y Treasury | 2Y–10Y 美债利差

### Fed

Fed Rate Expectations

### 风险

VIX | VXN | 市场风险状态：中等

### 股票

S&P 500 | Nasdaq Composite | Dow Jones Industrial Average | Russell 2000 | SOX

### 美元

DXY

### 商品

WTI | Gold

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

    def test_rejects_source_names_and_titles_without_urls(self) -> None:
        names_only = report_body().replace(
            "- [Federal Reserve](https://www.federalreserve.gov/)\n"
            "- [U.S. Treasury](https://home.treasury.gov/)\n"
            "- [BLS](https://www.bls.gov/)\n",
            "- Federal Reserve\n"
            "- Reuters — Markets close higher after economic data\n"
            "- BLS — Employment Situation\n",
        )

        with self.assertRaisesRegex(
            ValidationFailure,
            r"Sources has 0 HTTPS Markdown link\(s\); minimum is 3 for trading_day",
        ):
            validate_report(names_only, "2026-09-01")

    def test_rejects_old_spread_label_and_missing_new_dashboard_core(self) -> None:
        with self.assertRaises(ValidationFailure):
            validate_report(
                report_body().replace("2Y–10Y 美债利差", "2s10s"),
                "2026-09-01",
            )
        for label in (
            "30Y Treasury",
            "Fed Rate Expectations",
            "Russell 2000",
            "DXY",
        ):
            with self.subTest(label=label), self.assertRaises(ValidationFailure):
                validate_report(
                    report_body().replace(label, "REMOVED CORE LABEL"),
                    "2026-09-01",
                )

    def test_rejects_risk_state_without_approved_text_level(self) -> None:
        with self.assertRaises(ValidationFailure):
            validate_report(
                report_body().replace("市场风险状态：中等", "市场风险状态：🟡"),
                "2026-09-01",
            )

    def test_rejects_cross_asset_section_without_two_to_five_points(self) -> None:
        with self.assertRaises(ValidationFailure):
            validate_report(
                report_body().replace(
                    "- 股票、波动率与商品信号需要放在一起判断。" +
                    "市场变化得到数据和可靠来源支持，并说明资产定价逻辑。" * 12,
                    "",
                ),
                "2026-09-01",
            )

    def test_rejects_section_between_cross_asset_and_market_narrative(self) -> None:
        with self.assertRaises(ValidationFailure):
            validate_report(
                report_body().replace(
                    "## 🧠 Market Narrative",
                    "## 额外章节\n\n不应夹在跨资产观察与 Market Narrative 之间。\n\n"
                    "## 🧠 Market Narrative",
                ),
                "2026-09-01",
            )


if __name__ == "__main__":
    unittest.main()
