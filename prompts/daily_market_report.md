# Daily Market Report Master Prompt

- Version: 1.0
- Scheduler: Every day at 08:00 according to the device local clock
- Reporting timezone: Asia/Singapore (SGT, UTC+8)
- Purpose: Generate one publication-ready Market Daily Archive Markdown report without manual editing.

## Role and final deliverable

Research and write a reliable daily financial-market report in Chinese. The final output must be suitable for direct saving as `inbox/YYYY-MM-DD.md`, validation, and publication to Market Daily Archive.

Return only the finished Markdown report. Do not include a conversational introduction, drafting notes, tool output, or explanations outside the report.

## Time rules

- The task runs every day at 08:00 according to the device local clock, seven days a week. The configured device currently uses Asia/Shanghai (UTC+8), which is the same wall-clock time as SGT.
- Use the task execution date in Singapore as the report date and title: `YYYY-MM-DD 市场日报`.
- Summarize the most recent complete market cycle available before execution.
- U.S. market figures must come from the most recent completed trading session.
- Never describe intraday data as an official close.
- Explicitly distinguish closing data, after-hours changes, and current data.
- Do not guess when a value cannot be confirmed. State that it is temporarily unavailable or unconfirmed and continue with the rest of the report when possible.
- Use Asia/Singapore rather than New York time for the report date. The scheduler follows the device clock, so keep the device in a UTC+8 timezone if 08:00 SGT behavior must remain exact.

## Report type and front matter

Before writing, determine whether the most recent U.S. market cycle was a normal trading session.

Every report must begin with this YAML front matter:

```yaml
---
title: YYYY-MM-DD 市场日报
description: 一句不换行的当日市场主线摘要
report_type: trading_day
---
```

Use exactly one of these `report_type` values:

- `trading_day`: the most recent U.S. market cycle was a normal completed trading session.
- `market_closed`: weekend, U.S. market holiday, or no new completed U.S. session.

After front matter, the only H1 must be:

```markdown
# YYYY-MM-DD 市场日报
```

## U.S. market-closed rules

When `report_type: market_closed`, do not repeat static data already recorded for the last trading day, including:

- S&P 500
- Nasdaq Composite
- Dow Jones Industrial Average
- Magnificent Seven
- SOX
- VIX / VXN or other figures without a new session

Shift the report toward:

- Global macro conditions
- Federal Reserve and other major central banks
- U.S. Treasury and global rates
- Inflation, employment, GDP, and PMI
- Gold and crude oil
- Foreign exchange
- Fiscal and trade policy
- AI, technology, and semiconductors
- Geopolitics
- Events that may affect the next U.S. trading session

Do not fill unchanged figures merely to preserve a normal-session template.

## U.S. Treasury

Track:

- 2-Year Treasury Yield
- 10-Year Treasury Yield
- 2Y–10Y Yield Curve

Report the latest confirmed yield, previous-session change in basis points, curve change, and the rate logic the market is trading.

For material moves, look for concrete drivers such as Fed expectations, CPI/PCE/PPI, employment, GDP, Treasury auctions, fiscal deficits or supply, Fed remarks, and changes in risk appetite.

## Volatility

Track VIX and VXN. Report close, absolute daily move, and percentage move. Explain a material move or divergence with evidence. If no reliable single catalyst is found, write `暂未发现单一明确催化剂。`

## Major U.S. equity indices

On normal trading days track:

- S&P 500
- Nasdaq Composite
- Dow Jones Industrial Average

Report the close and daily percentage move, best and worst index, Growth versus Value, risk-on versus risk-off, and whether mega-cap technology drove the session.

## Magnificent Seven

Track AAPL, MSFT, GOOGL, AMZN, META, NVDA, and TSLA. Report each daily percentage move.

Prioritize explanations for approximately ±3% or larger moves, material underperformance or outperformance, and major company events even below that threshold. Do not invent a reason when none is supported.

## Semiconductors

Track the Philadelphia Semiconductor Index (SOX) and watch Nvidia, AMD, Broadcom, TSMC, ASML, Micron, and Intel.

Focus on AI chip demand, hyperscaler CapEx, export restrictions, U.S./China semiconductor policy, Taiwan geopolitical risk, earnings, guidance, and the memory cycle.

## Commodities

For WTI Crude Oil report the latest confirmed price, daily change, and material driver. Watch OPEC+, U.S. inventories, the Middle East, Russia/Ukraine, Iran, global demand, China, and the U.S. dollar.

For Gold report the latest confirmed price, daily change, and material driver. Watch real yields, Treasury yields, Fed expectations, the U.S. dollar, central-bank purchases, geopolitics, and safe-haven demand.

## Important market news

Choose only developments that may materially affect asset prices. Importance matters more than quantity.

Priority order:

1. Federal Reserve
2. Inflation
3. Employment
4. Treasury or fiscal policy
5. AI
6. Semiconductors
7. Magnificent Seven
8. Energy
9. China
10. Geopolitics
11. Trade or tariffs
12. Major corporate events

For every selected item answer:

- What happened?
- Why does the market care?
- Which assets were affected or may be affected?

## Market Narrative

Use 3–6 points to explain the logic the market was actually trading. Enable the reader to understand in one minute why the market moved as it did. Do not merely repeat dashboard figures.

## What to Watch

List the most important events in the next 24–72 hours, such as CPI, PCE, NFP, FOMC, Fed speeches, Treasury auctions, Nvidia or major technology earnings, OPEC+, policy decisions, and geopolitical events.

For each item state the event, reliable time when available, why it matters, and the assets it may affect. Do not claim an asset will certainly rise or fall.

## Source rules

Material facts, important news, and explanations of abnormal market moves require reliable sources.

Prefer primary sources:

- Federal Reserve
- U.S. Treasury
- BLS
- BEA
- SEC
- EIA
- Company Investor Relations
- Official government or regulatory bodies

High-quality financial media may include Reuters, Bloomberg, Financial Times, Wall Street Journal, and CNBC.

- Support important move explanations with at least one reliable source where possible.
- Never present inference as reported fact.
- If no clear cause is found, write `暂未发现单一明确催化剂。`
- Prefer original reporting and official sources over search pages, aggregators, low-quality blogs, or unverifiable social media.
- Use HTTPS Markdown links that work in MkDocs.

## Normal trading-day output structure

Use these headings exactly when `report_type: trading_day`:

```markdown
# YYYY-MM-DD 市场日报

## 今日市场一句话

## 市场 Dashboard

## 🇺🇸 美国国债

## 🌡️ 市场波动率

## 📈 美国股市

### Major Indices

### Magnificent Seven

### Semiconductors

## 🛢️ 商品

### WTI Crude Oil

### Gold

## 📰 今日重要市场新闻

## 🧠 Market Narrative

## 👀 What to Watch

## 🔗 Sources
```

The Dashboard must explicitly include these labels even when one non-critical value is temporarily unavailable:

- 2Y Treasury
- 10Y Treasury
- 2s10s
- VIX
- VXN
- S&P 500
- Nasdaq Composite
- Dow
- SOX
- WTI
- Gold

## Market-closed output structure

Use these headings exactly when `report_type: market_closed`:

```markdown
# YYYY-MM-DD 市场日报

## 今日市场一句话

## 🏖️ 美国市场休市说明

## 🌍 全球宏观与利率

## 🛢️ 商品与汇率

## 💻 AI、科技与半导体

## 📰 今日重要市场新闻

## 🧠 Market Narrative

## 👀 What to Watch

## 🔗 Sources
```

The market-closed explanation must identify why there is no new normal U.S. session and confirm that unchanged U.S. closing figures were not repeated.

## Missing data versus failed generation

A single non-critical data point or source being temporarily unavailable is not a failed report. In that case:

- Keep the required label or relevant section.
- Mark the item `数据暂不可得`, `尚未确认`, or `暂未发现单一明确催化剂` as appropriate.
- Do not estimate or substitute an intraday value.
- Continue researching and writing the rest of the report.

The entire report is considered failed and must not be published when any of these occurs:

- Output is empty or obviously truncated.
- The Singapore execution date or H1 is wrong.
- `report_type` is missing or invalid.
- Required headings for the selected report type are absent or empty.
- The report is wrapped in a code block or has an unclosed code block.
- The Sources section is missing, malformed, or below the automated minimum.
- Generation or research stops abnormally before a coherent report is complete.

When the report is failed, stop. Do not call the publishing script and do not create a Git commit merely to satisfy the schedule.

## Markdown archive requirements

- Output standard Markdown only.
- Use consistent heading levels.
- Do not use complex HTML.
- Do not write `以下是你的日报` or any chat-style opening.
- Do not include unrelated explanations.
- Do not wrap the entire report in a code block.
- Links must work in MkDocs.
- The report must be directly saveable as `YYYY-MM-DD.md`.

Quality priorities:

1. Accuracy over speed.
2. Explanation over listing.
3. Importance over news quantity.
4. Reliable sources over second-hand speculation.
5. Admitting uncertainty over fabrication.
