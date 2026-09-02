#!/usr/bin/env python3
"""Extract one canonical market daily from a ChatGPT copied response."""

from __future__ import annotations

import datetime as dt
import re
import sys
from dataclasses import dataclass


DELIMITER_RE = re.compile(r"(?m)^---[ \t]*(?:\r?\n|$)")
TITLE_LINE_RE = re.compile(r"(?m)^title:[ \t]*(.*?)[ \t]*\r?$")
EXACT_H1_RE = re.compile(
    r"(?m)^#[ \t]+(\d{4}-\d{2}-\d{2})[ \t]+市场日报[ \t]*\r?$"
)
FENCE_RE = re.compile(r"(?m)^\s*```")


class ExtractionFailure(RuntimeError):
    """Raised when a copied response has no unique safe report boundary."""


@dataclass(frozen=True)
class ExtractionResult:
    markdown: bytes
    date: str
    strategy: str
    leading_bytes: int


def parse_title_date(front_matter: str) -> str | None:
    match = TITLE_LINE_RE.search(front_matter)
    if not match:
        return None
    value = match.group(1).strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"\"", "'"}:
        value = value[1:-1].strip()
    title = re.fullmatch(r"(\d{4}-\d{2}-\d{2})[ \t]+市场日报", value)
    if not title:
        return None
    try:
        parsed = dt.date.fromisoformat(title.group(1))
    except ValueError:
        return None
    return parsed.isoformat() if parsed.isoformat() == title.group(1) else None


def inside_code_fence(text: str, position: int) -> bool:
    return len(FENCE_RE.findall(text, 0, position)) % 2 == 1


def first_nonempty_line(text: str) -> str:
    return next((line.strip() for line in text.splitlines() if line.strip()), "")


def byte_offset(text: str, character_offset: int) -> int:
    return len(text[:character_offset].encode("utf-8"))


def extract_report(raw: bytes) -> ExtractionResult:
    if not raw.strip():
        raise ExtractionFailure("Clipboard text is empty or whitespace only.")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ExtractionFailure(
            f"Clipboard text is not valid UTF-8 at byte {exc.start}."
        ) from exc

    delimiters = list(DELIMITER_RE.finditer(text))
    yaml_candidates: list[tuple[int, str]] = []
    for index, opening in enumerate(delimiters[:-1]):
        closing = delimiters[index + 1]
        if inside_code_fence(text, opening.start()):
            continue
        date = parse_title_date(text[opening.end() : closing.start()])
        if not date:
            continue
        body_start = closing.end()
        if first_nonempty_line(text[body_start:]) != f"# {date} 市场日报":
            continue
        yaml_candidates.append((opening.start(), date))

    if len(yaml_candidates) > 1:
        raise ExtractionFailure(
            "Clipboard contains more than one YAML-titled market daily; "
            "the report boundary is ambiguous."
        )
    if yaml_candidates:
        start, date = yaml_candidates[0]
        start_byte = byte_offset(text, start)
        return ExtractionResult(raw[start_byte:], date, "yaml-title", start_byte)

    h1_candidates = [
        (match.start(), match.group(1))
        for match in EXACT_H1_RE.finditer(text)
        if not inside_code_fence(text, match.start())
    ]
    if len(h1_candidates) > 1:
        raise ExtractionFailure(
            "Clipboard contains more than one exact market-daily H1; "
            "the report boundary is ambiguous."
        )
    if h1_candidates:
        start, date = h1_candidates[0]
        start_byte = byte_offset(text, start)
        return ExtractionResult(raw[start_byte:], date, "exact-h1", start_byte)

    raise ExtractionFailure(
        "Could not uniquely locate 'title: YYYY-MM-DD 市场日报' in YAML "
        "or an exact '# YYYY-MM-DD 市场日报' H1."
    )


def main() -> int:
    try:
        result = extract_report(sys.stdin.buffer.read())
    except ExtractionFailure as exc:
        print("Clipboard status: FAILED", file=sys.stderr)
        print(f"Final result: {exc} Nothing was imported.", file=sys.stderr)
        return 2
    print(
        "Clipboard parser status: PASSED "
        f"(start={result.strategy}, date={result.date}, "
        f"ignored leading bytes={result.leading_bytes})",
        file=sys.stderr,
    )
    sys.stdout.buffer.write(result.markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
