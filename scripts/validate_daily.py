#!/usr/bin/env python3
"""Fail-closed quality gate for generated Market Daily Archive reports."""

from __future__ import annotations

import argparse
import datetime as dt
import re
from pathlib import Path


HEADING_RE = re.compile(r"^(#{1,3})\s+(.+?)\s*$", re.MULTILINE)
HTTPS_LINK_RE = re.compile(r"\[[^\]]+\]\(https://[^)]+\)")

COMMON_HEADINGS = (
    (2, "今日市场一句话"),
    (2, "📰 今日重要市场新闻"),
    (2, "🧠 Market Narrative"),
    (2, "👀 What to Watch"),
    (2, "🔗 Sources"),
)
TRADING_HEADINGS = COMMON_HEADINGS + (
    (2, "市场 Dashboard"),
    (2, "🇺🇸 美国国债"),
    (2, "🌡️ 市场波动率"),
    (2, "📈 美国股市"),
    (2, "🛢️ 商品"),
    (3, "Major Indices"),
    (3, "Magnificent Seven"),
    (3, "Semiconductors"),
    (3, "WTI Crude Oil"),
    (3, "Gold"),
)
CLOSED_HEADINGS = COMMON_HEADINGS + (
    (2, "🏖️ 美国市场休市说明"),
    (2, "🌍 全球宏观与利率"),
    (2, "🛢️ 商品与汇率"),
    (2, "💻 AI、科技与半导体"),
)
DASHBOARD_LABELS = (
    "2Y Treasury",
    "10Y Treasury",
    "2s10s",
    "VIX",
    "VXN",
    "S&P 500",
    "Nasdaq Composite",
    "Dow",
    "SOX",
    "WTI",
    "Gold",
)


class ValidationFailure(RuntimeError):
    """Raised when a generated report is unsafe to publish."""


def normalize(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def split_front_matter(text: str) -> tuple[str, str]:
    if not text.startswith("---\n"):
        raise ValidationFailure("generated report must include YAML front matter")
    closing = text.find("\n---\n", 4)
    if closing == -1:
        raise ValidationFailure("front matter has no closing ---")
    return text[4:closing], text[closing + 5 :]


def front_matter_value(front_matter: str, key: str) -> str | None:
    match = re.search(rf"^{re.escape(key)}:\s*(.+?)\s*$", front_matter, re.MULTILINE)
    if not match:
        return None
    return match.group(1).strip().strip("\"'")


def section_text(body: str, title: str) -> str:
    matches = list(HEADING_RE.finditer(body))
    for index, match in enumerate(matches):
        if match.group(2).strip().rstrip("#").strip() != title:
            continue
        level = len(match.group(1))
        end = len(body)
        for later in matches[index + 1 :]:
            if len(later.group(1)) <= level:
                end = later.start()
                break
        return body[match.end() : end].strip()
    return ""


def validate_report(raw: str, date_text: str) -> str:
    try:
        parsed = dt.date.fromisoformat(date_text)
    except ValueError as exc:
        raise ValidationFailure(f"invalid ISO date: {date_text}") from exc
    if parsed.isoformat() != date_text:
        raise ValidationFailure(f"date must use YYYY-MM-DD: {date_text}")

    text = normalize(raw)
    if not text.strip():
        raise ValidationFailure("generated report is empty")
    front_matter, body = split_front_matter(text)
    report_type = front_matter_value(front_matter, "report_type")
    if report_type not in {"trading_day", "market_closed"}:
        raise ValidationFailure(
            "front matter report_type must be trading_day or market_closed"
        )
    description = front_matter_value(front_matter, "description")
    if not description:
        raise ValidationFailure("front matter description must be a non-empty line")
    expected_title = f"{date_text} 市场日报"
    if front_matter_value(front_matter, "title") != expected_title:
        raise ValidationFailure(f"front matter title must be: {expected_title}")

    stripped_body = body.lstrip()
    if stripped_body.startswith("```"):
        raise ValidationFailure("the full report must not be wrapped in a code fence")
    if body.count("```") % 2:
        raise ValidationFailure("report contains an unclosed code fence")

    headings = [
        (len(match.group(1)), match.group(2).strip().rstrip("#").strip())
        for match in HEADING_RE.finditer(body)
    ]
    h1s = [title for level, title in headings if level == 1]
    if h1s != [expected_title]:
        raise ValidationFailure(
            f"report must contain exactly one H1: # {expected_title}"
        )

    required = TRADING_HEADINGS if report_type == "trading_day" else CLOSED_HEADINGS
    heading_set = set(headings)
    missing = [f"{'#' * level} {title}" for level, title in required if (level, title) not in heading_set]
    if missing:
        raise ValidationFailure("missing required heading(s): " + ", ".join(missing))

    for _level, title in COMMON_HEADINGS:
        content = section_text(body, title)
        minimum = 20 if title == "🔗 Sources" else 40
        if len(re.sub(r"\s+", "", content)) < minimum:
            raise ValidationFailure(f"required section is empty or incomplete: {title}")

    compact_length = len(re.sub(r"\s+", "", body))
    minimum_length = 1200 if report_type == "trading_day" else 800
    if compact_length < minimum_length:
        raise ValidationFailure(
            f"report appears incomplete: {compact_length} content characters; "
            f"minimum is {minimum_length} for {report_type}"
        )

    sources = section_text(body, "🔗 Sources")
    source_count = len(HTTPS_LINK_RE.findall(sources))
    minimum_sources = 3 if report_type == "trading_day" else 2
    if source_count < minimum_sources:
        raise ValidationFailure(
            f"Sources has {source_count} HTTPS Markdown link(s); "
            f"minimum is {minimum_sources} for {report_type}"
        )

    if report_type == "trading_day":
        dashboard = section_text(body, "市场 Dashboard")
        missing_labels = [label for label in DASHBOARD_LABELS if label not in dashboard]
        if missing_labels:
            raise ValidationFailure(
                "Dashboard is missing required label(s): " + ", ".join(missing_labels)
            )

    return report_type


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate one generated market daily")
    parser.add_argument("--date", required=True, help="Report date in YYYY-MM-DD")
    parser.add_argument("--input", required=True, type=Path, help="Generated Markdown")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        raw = args.input.read_text(encoding="utf-8")
        report_type = validate_report(raw, args.date)
    except (OSError, ValidationFailure) as exc:
        print(f"ERROR: {exc}")
        return 2
    print(f"Validation passed for {args.date} ({report_type}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
