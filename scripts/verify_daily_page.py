#!/usr/bin/env python3
"""Verify that one published Pages URL matches its archived Markdown report."""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path
import urllib.error
import urllib.request

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.recover_daily import verify_page


def fetch(url: str, timeout: float) -> str:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "Market-Daily-Archive-Verifier/1.0"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        if response.status != 200:
            raise RuntimeError(f"published page returned HTTP {response.status}")
        return response.read().decode("utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify one published daily page")
    parser.add_argument("--date", required=True)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--url", required=True)
    parser.add_argument("--attempts", type=int, default=12)
    parser.add_argument("--delay", type=float, default=5)
    parser.add_argument("--timeout", type=float, default=30)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        raw = args.report.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"ERROR: cannot read report: {exc}")
        return 2

    last_error = "published content did not match the report"
    for attempt in range(1, args.attempts + 1):
        try:
            html = fetch(args.url, args.timeout)
            if verify_page(html, raw, args.date):
                print(f"Published page verified: {args.url}")
                return 0
            last_error = "HTTP 200 page did not match title, description, and sources"
        except (OSError, RuntimeError, UnicodeDecodeError, urllib.error.URLError) as exc:
            last_error = f"{type(exc).__name__}: {exc}"
        if attempt < args.attempts:
            time.sleep(args.delay)
    print(f"ERROR: {last_error}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
