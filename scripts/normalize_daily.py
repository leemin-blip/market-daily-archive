#!/usr/bin/env python3
"""Normalize narrowly whitelisted Markdown presentation differences."""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path


SECTION_HEADING = "## 跨资产观察"
ORDERED_ITEM_RE = re.compile(r"^(?P<number>[0-9]+)\. (?P<content>\S.*)$")
ORDERED_PREFIX_RE = re.compile(r"^[0-9]+[.)](?:\s|$)")


class NormalizationFailure(RuntimeError):
    """Raised when Markdown cannot be normalized without interpretation."""


@dataclass(frozen=True)
class NormalizationResult:
    markdown: bytes
    changed_markers: tuple[str, ...]


def _line_body(line: str) -> str:
    return line[:-2] if line.endswith("\r\n") else line[:-1] if line.endswith(("\n", "\r")) else line


def normalize_cross_asset_markers(raw: bytes) -> NormalizationResult:
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise NormalizationFailure("input is not valid UTF-8") from exc

    lines = text.splitlines(keepends=True)
    headings = [
        index for index, line in enumerate(lines) if _line_body(line) == SECTION_HEADING
    ]
    if not headings:
        return NormalizationResult(raw, ())
    if len(headings) != 1:
        raise NormalizationFailure(
            "report must contain exactly one '## 跨资产观察' section"
        )

    start = headings[0] + 1
    end = next(
        (
            index
            for index in range(start, len(lines))
            if _line_body(lines[index]).startswith("## ")
        ),
        len(lines),
    )
    section = lines[start:end]
    nonblank = [
        (index, _line_body(line))
        for index, line in enumerate(section, start=start)
        if _line_body(line).strip()
    ]

    ordered_candidates = [
        (index, body)
        for index, body in nonblank
        if ORDERED_PREFIX_RE.match(body.lstrip())
    ]
    if not ordered_candidates:
        return NormalizationResult(raw, ())

    if not 2 <= len(nonblank) <= 5:
        raise NormalizationFailure(
            "numbered 跨资产观察 must contain exactly 2–5 single-line conclusions"
        )

    matches: list[tuple[int, re.Match[str]]] = []
    for index, body in nonblank:
        match = ORDERED_ITEM_RE.fullmatch(body)
        if match is None:
            raise NormalizationFailure(
                "numbered 跨资产观察 must contain only unindented 'N. text' lines"
            )
        matches.append((index, match))

    numbers = [int(match.group("number")) for _, match in matches]
    expected = list(range(1, len(matches) + 1))
    if numbers != expected:
        raise NormalizationFailure(
            "numbered 跨资产观察 must start at 1 and use consecutive numbering"
        )

    changed: list[str] = []
    for index, match in matches:
        line = lines[index]
        body = _line_body(line)
        ending = line[len(body) :]
        marker = f"{match.group('number')}. "
        lines[index] = f"- {match.group('content')}{ending}"
        changed.append(marker)

    normalized = "".join(lines).encode("utf-8")
    return NormalizationResult(normalized, tuple(changed))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Normalize safe Markdown presentation differences before validation"
    )
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        raw = args.input.read_bytes()
        result = normalize_cross_asset_markers(raw)
        args.output.write_bytes(result.markdown)
    except (OSError, NormalizationFailure) as exc:
        print(f"ERROR: {exc}")
        return 2

    if result.changed_markers:
        markers = ", ".join(result.changed_markers)
        print(
            "Normalization passed: converted only 跨资产观察 list marker(s) "
            f"{markers} to '- '."
        )
    else:
        print("Normalization passed: no whitelisted marker change was needed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
