#!/usr/bin/env python3
"""Deterministically import one Markdown market daily into the MkDocs archive."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path


ARCHIVE_BEGIN = "<!-- BEGIN AUTO-GENERATED DAILY ARCHIVE -->"
ARCHIVE_END = "<!-- END AUTO-GENERATED DAILY ARCHIVE -->"
HOME_LATEST_BEGIN = "<!-- BEGIN AUTO-GENERATED LATEST LINK -->"
HOME_LATEST_END = "<!-- END AUTO-GENERATED LATEST LINK -->"
HOME_TABLE_BEGIN = "<!-- BEGIN AUTO-GENERATED DAILY TABLE -->"
HOME_TABLE_END = "<!-- END AUTO-GENERATED DAILY TABLE -->"
YEAR_MONTHS_BEGIN = "<!-- BEGIN AUTO-GENERATED MONTH LIST -->"
YEAR_MONTHS_END = "<!-- END AUTO-GENERATED MONTH LIST -->"
MONTH_DAILIES_BEGIN = "<!-- BEGIN AUTO-GENERATED DAILY LIST -->"
MONTH_DAILIES_END = "<!-- END AUTO-GENERATED DAILY LIST -->"
NAV_BEGIN = "      # BEGIN AUTO-GENERATED DAILY NAV"
NAV_END = "      # END AUTO-GENERATED DAILY NAV"

H1_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)
MARKDOWN_LINK_RE = re.compile(r"\]\(https://[^)]+\)")
REPORT_PATH_RE = re.compile(
    r"^docs/(?P<year>\d{4})/(?P<month>\d{2})/"
    r"(?P<date>\d{4}-\d{2}-\d{2})\.md$"
)


class ImportFailure(RuntimeError):
    """Raised when importing would be unsafe or ambiguous."""


@dataclass(frozen=True)
class DailyEntry:
    date: str
    year: str
    month: str
    relative_path: str
    heading: str
    description: str


def normalize_markdown(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n").rstrip() + "\n"


def validate_date(date_text: str) -> tuple[str, str]:
    try:
        parsed = dt.date.fromisoformat(date_text)
    except ValueError as exc:
        raise ImportFailure(f"Invalid ISO date: {date_text}") from exc
    if parsed.isoformat() != date_text:
        raise ImportFailure(f"Date must use YYYY-MM-DD: {date_text}")
    return f"{parsed.year:04d}", f"{parsed.month:02d}"


def split_front_matter(text: str) -> tuple[str | None, str]:
    if not text.startswith("---\n"):
        return None, text
    closing = text.find("\n---\n", 4)
    if closing == -1:
        raise ImportFailure("Markdown starts with front matter but has no closing ---")
    return text[4:closing], text[closing + 5 :]


def front_matter_value(front_matter: str | None, key: str) -> str | None:
    if front_matter is None:
        return None
    match = re.search(rf"^{re.escape(key)}:\s*(.+?)\s*$", front_matter, re.MULTILINE)
    if not match:
        return None
    value = match.group(1).strip()
    if len(value) >= 2 and value[0] == value[-1] == '"':
        try:
            decoded = json.loads(value)
        except json.JSONDecodeError:
            value = value[1:-1]
        else:
            if isinstance(decoded, str):
                value = decoded
    elif len(value) >= 2 and value[0] == value[-1] == "'":
        value = value[1:-1]
    return value


def extract_heading(body: str) -> str:
    match = H1_RE.search(body)
    if not match:
        raise ImportFailure("Report must contain one level-one Markdown heading")
    return match.group(1).strip()


def prepare_report(raw: str, date_text: str, summary: str | None) -> tuple[str, str, str]:
    normalized = normalize_markdown(raw)
    front_matter, body = split_front_matter(normalized)
    heading = extract_heading(body)

    if date_text not in heading:
        raise ImportFailure(
            f"The first H1 must contain the import date {date_text}; got: {heading}"
        )
    if not MARKDOWN_LINK_RE.search(body):
        raise ImportFailure("Report must retain at least one HTTPS Markdown source link")

    description = (
        summary.strip()
        if summary and summary.strip()
        else front_matter_value(front_matter, "description") or heading
    )
    if "\n" in description:
        raise ImportFailure("Summary must be a single line")

    if front_matter is None:
        generated = (
            "---\n"
            f"title: {json.dumps(date_text, ensure_ascii=False)}\n"
            f"description: {json.dumps(description, ensure_ascii=False)}\n"
            "---\n\n"
        )
        normalized = generated + body.lstrip("\n")

    return normalize_markdown(normalized), heading, description


def entry_from_file(repo_root: Path, path: Path) -> DailyEntry | None:
    relative = path.relative_to(repo_root).as_posix()
    match = REPORT_PATH_RE.match(relative)
    if not match:
        return None
    text = normalize_markdown(path.read_text(encoding="utf-8"))
    front_matter, body = split_front_matter(text)
    heading = extract_heading(body)
    description = front_matter_value(front_matter, "description") or heading
    return DailyEntry(
        date=match.group("date"),
        year=match.group("year"),
        month=match.group("month"),
        relative_path=relative.removeprefix("docs/"),
        heading=heading,
        description=description,
    )


def group_entries(entries: list[DailyEntry]) -> dict[str, dict[str, list[DailyEntry]]]:
    grouped: dict[str, dict[str, list[DailyEntry]]] = {}
    for entry in entries:
        grouped.setdefault(entry.year, {}).setdefault(entry.month, []).append(entry)
    for months in grouped.values():
        for month_entries in months.values():
            month_entries.sort(key=lambda item: item.date, reverse=True)
    return grouped


def replace_generated_block(text: str, begin: str, end: str, body: str, path: Path) -> str:
    begin_index = text.find(begin)
    end_index = text.find(end)
    if begin_index == -1 or end_index == -1 or end_index < begin_index:
        raise ImportFailure(f"Missing or invalid generated markers in {path}")
    prefix_end = begin_index + len(begin)
    return text[:prefix_end] + "\n" + body.rstrip() + "\n" + text[end_index:]


def markdown_label(text: str) -> str:
    return text.replace("\n", " ").replace("|", "\\|").strip()


def render_archive(grouped: dict[str, dict[str, list[DailyEntry]]]) -> str:
    lines: list[str] = []
    for year in sorted(grouped, reverse=True):
        lines.extend([f"## {year}", ""])
        for month in sorted(grouped[year], reverse=True):
            lines.extend([f"### {month} 月", ""])
            for entry in grouped[year][month]:
                lines.append(
                    f"- [{entry.date}]({entry.relative_path}) — "
                    f"{markdown_label(entry.description)}"
                )
            lines.append("")
    return "\n".join(lines).rstrip()


def render_home_table(entries: list[DailyEntry]) -> str:
    lines = ["| 日期 | 状态 | 入口 |", "| --- | --- | --- |"]
    for entry in sorted(entries, key=lambda item: item.date, reverse=True)[:10]:
        lines.append(
            f"| {entry.date} | {markdown_label(entry.description)} | "
            f"[阅读]({entry.relative_path}) |"
        )
    return "\n".join(lines)


def render_nav(grouped: dict[str, dict[str, list[DailyEntry]]]) -> str:
    lines: list[str] = []
    for year in sorted(grouped, reverse=True):
        lines.extend([f'      - "{year}":', f"          - {year}/index.md"])
        for month in sorted(grouped[year], reverse=True):
            lines.extend(
                [
                    f'          - "{month} 月":',
                    f"              - {year}/{month}/index.md",
                ]
            )
            for entry in grouped[year][month]:
                lines.append(
                    f'              - "{entry.date}": {entry.relative_path}'
                )
    return "\n".join(lines)


def year_index_template(year: str) -> str:
    return f"""---
title: {year} 年
---

# {year} 年日报

## 月份

{YEAR_MONTHS_BEGIN}
{YEAR_MONTHS_END}

## 年度状态

年度回顾将在每日自动入库稳定后再开发。当前页面作为 {year} 年各月份的书籍式入口。
"""


def month_index_template(year: str, month: str) -> str:
    return f"""---
title: {year} 年 {month} 月
---

# {year} 年 {month} 月

## 日报

{MONTH_DAILIES_BEGIN}
{MONTH_DAILIES_END}

## 月度回顾

月度回顾属于 V2.3，等待每日自动入库稳定后再开发。
"""


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized = normalize_markdown(text)
    if path.exists() and path.read_text(encoding="utf-8") == normalized:
        return
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=path.parent, delete=False
    ) as handle:
        handle.write(normalized)
        temporary = Path(handle.name)
    os.replace(temporary, path)


def import_daily(
    repo_root: Path, input_path: Path, date_text: str, summary: str | None
) -> list[Path]:
    year, month = validate_date(date_text)
    if not input_path.is_file():
        raise ImportFailure(f"Input Markdown does not exist: {input_path}")

    report_text, heading, description = prepare_report(
        input_path.read_text(encoding="utf-8"), date_text, summary
    )
    target = repo_root / "docs" / year / month / f"{date_text}.md"
    if target.exists():
        existing = normalize_markdown(target.read_text(encoding="utf-8"))
        if existing != report_text:
            raise ImportFailure(
                f"Refusing to overwrite a different report for {date_text}: {target}"
            )

    entries_by_date: dict[str, DailyEntry] = {}
    for path in (repo_root / "docs").glob("[0-9][0-9][0-9][0-9]/[0-9][0-9]/*.md"):
        entry = entry_from_file(repo_root, path)
        if entry:
            entries_by_date[entry.date] = entry
    entries_by_date[date_text] = DailyEntry(
        date=date_text,
        year=year,
        month=month,
        relative_path=f"{year}/{month}/{date_text}.md",
        heading=heading,
        description=description,
    )
    entries = list(entries_by_date.values())
    grouped = group_entries(entries)

    changes: dict[Path, str] = {target: report_text}

    archive_path = repo_root / "docs" / "archive.md"
    archive_text = archive_path.read_text(encoding="utf-8")
    changes[archive_path] = replace_generated_block(
        archive_text,
        ARCHIVE_BEGIN,
        ARCHIVE_END,
        render_archive(grouped),
        archive_path,
    )

    home_path = repo_root / "docs" / "index.md"
    home_text = home_path.read_text(encoding="utf-8")
    latest = max(entries, key=lambda item: item.date)
    home_text = replace_generated_block(
        home_text,
        HOME_LATEST_BEGIN,
        HOME_LATEST_END,
        f"- [查看最新日报]({latest.relative_path})",
        home_path,
    )
    changes[home_path] = replace_generated_block(
        home_text,
        HOME_TABLE_BEGIN,
        HOME_TABLE_END,
        render_home_table(entries),
        home_path,
    )

    for grouped_year, months in grouped.items():
        year_path = repo_root / "docs" / grouped_year / "index.md"
        year_text = (
            year_path.read_text(encoding="utf-8")
            if year_path.exists()
            else year_index_template(grouped_year)
        )
        month_lines = [
            f"- [{grouped_month} 月]({grouped_month}/index.md) — "
            f"{len(month_entries)} 篇日报"
            for grouped_month, month_entries in sorted(months.items(), reverse=True)
        ]
        changes[year_path] = replace_generated_block(
            year_text,
            YEAR_MONTHS_BEGIN,
            YEAR_MONTHS_END,
            "\n".join(month_lines),
            year_path,
        )

        for grouped_month, month_entries in months.items():
            month_path = repo_root / "docs" / grouped_year / grouped_month / "index.md"
            month_text = (
                month_path.read_text(encoding="utf-8")
                if month_path.exists()
                else month_index_template(grouped_year, grouped_month)
            )
            daily_lines = [
                f"- [{entry.date}]({entry.date}.md) — "
                f"{markdown_label(entry.description)}"
                for entry in month_entries
            ]
            changes[month_path] = replace_generated_block(
                month_text,
                MONTH_DAILIES_BEGIN,
                MONTH_DAILIES_END,
                "\n".join(daily_lines),
                month_path,
            )

    mkdocs_path = repo_root / "mkdocs.yml"
    mkdocs_text = mkdocs_path.read_text(encoding="utf-8")
    changes[mkdocs_path] = replace_generated_block(
        mkdocs_text,
        NAV_BEGIN,
        NAV_END,
        render_nav(grouped),
        mkdocs_path,
    )

    changed_paths: list[Path] = []
    for path, text in changes.items():
        before = path.read_text(encoding="utf-8") if path.exists() else None
        normalized = normalize_markdown(text)
        if before != normalized:
            atomic_write(path, normalized)
            changed_paths.append(path)
    return sorted(changed_paths)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Import one Markdown market daily and rebuild date navigation"
    )
    parser.add_argument("--date", required=True, help="Report date in YYYY-MM-DD")
    parser.add_argument("--input", required=True, type=Path, help="Input Markdown file")
    parser.add_argument("--summary", help="Optional one-line description for index pages")
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help=argparse.SUPPRESS,
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    input_path = args.input.expanduser().resolve()
    try:
        changed = import_daily(repo_root, input_path, args.date, args.summary)
    except (ImportFailure, OSError) as exc:
        print(f"ERROR: {exc}")
        return 2

    if changed:
        print(f"Imported {args.date}; changed {len(changed)} file(s):")
        for path in changed:
            print(f"- {path.relative_to(repo_root)}")
    else:
        print(f"Report {args.date} is already imported; no changes needed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
