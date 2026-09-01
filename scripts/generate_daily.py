#!/usr/bin/env python3
"""Generate one market daily with the OpenAI Responses API.

The caller owns validation and publication. This module only researches and writes
one Markdown draft to a caller-provided, non-repository staging path.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path
import tempfile
from typing import Any, Callable
import urllib.error
import urllib.request


RESPONSES_URL = "https://api.openai.com/v1/responses"
DEFAULT_MODEL = "gpt-5.6-sol"


class GenerationFailure(RuntimeError):
    """Raised when no complete, researched draft can be safely accepted."""


Transport = Callable[[urllib.request.Request, float], dict[str, Any]]


def validate_date(date_text: str) -> str:
    try:
        parsed = dt.date.fromisoformat(date_text)
    except ValueError as exc:
        raise GenerationFailure(f"invalid ISO date: {date_text}") from exc
    if parsed.isoformat() != date_text:
        raise GenerationFailure(f"date must use YYYY-MM-DD: {date_text}")
    return date_text


def default_transport(request: urllib.request.Request, timeout: float) -> dict[str, Any]:
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = response.read()
    except urllib.error.HTTPError as exc:
        # Do not echo response bodies: they may contain request diagnostics or other
        # data that does not belong in a public Actions log.
        raise GenerationFailure(f"OpenAI Responses API returned HTTP {exc.code}") from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise GenerationFailure(
            f"OpenAI Responses API request failed: {type(exc).__name__}"
        ) from exc
    try:
        decoded = json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise GenerationFailure("OpenAI Responses API returned invalid JSON") from exc
    if not isinstance(decoded, dict):
        raise GenerationFailure("OpenAI Responses API returned an unexpected payload")
    return decoded


def response_output_text(response: dict[str, Any]) -> str:
    direct = response.get("output_text")
    if isinstance(direct, str) and direct.strip():
        return direct

    chunks: list[str] = []
    output = response.get("output")
    if not isinstance(output, list):
        return ""
    for item in output:
        if not isinstance(item, dict) or item.get("type") != "message":
            continue
        content = item.get("content")
        if not isinstance(content, list):
            continue
        for block in content:
            if (
                isinstance(block, dict)
                and block.get("type") == "output_text"
                and isinstance(block.get("text"), str)
            ):
                chunks.append(block["text"])
    return "".join(chunks)


def used_web_search(response: dict[str, Any]) -> bool:
    output = response.get("output")
    return isinstance(output, list) and any(
        isinstance(item, dict) and item.get("type") == "web_search_call"
        for item in output
    )


def build_payload(master_prompt: str, date_text: str, model: str) -> dict[str, Any]:
    if not master_prompt.strip():
        raise GenerationFailure("Master Prompt is empty")
    return {
        "model": model,
        "store": False,
        "reasoning": {"effort": "high"},
        "tools": [{"type": "web_search", "search_context_size": "high"}],
        "tool_choice": "required",
        "max_tool_calls": 30,
        "max_output_tokens": 24000,
        "include": ["web_search_call.action.sources"],
        "instructions": (
            "You are the sole AI generation layer for Market Daily Archive. "
            "Use the web_search tool to research current, reliable sources. "
            "Return only the complete publication-ready Markdown report, with no "
            "chat introduction, drafting notes, tool output, or surrounding code fence. "
            "If reliable research or complete generation cannot be finished, fail rather "
            "than returning a partial report."
        ),
        "input": (
            f"Generate the report for {date_text} using Asia/Singapore as the report "
            "date. Follow the complete version-controlled Master Prompt below exactly.\n\n"
            + master_prompt
        ),
    }


def generate_report(
    master_prompt: str,
    date_text: str,
    api_key: str,
    *,
    model: str = DEFAULT_MODEL,
    timeout: float = 1200,
    transport: Transport = default_transport,
) -> tuple[str, dict[str, str]]:
    validate_date(date_text)
    if not api_key:
        raise GenerationFailure("OPENAI_API_KEY is unavailable")
    if not model.strip():
        raise GenerationFailure("OpenAI model is empty")

    payload = build_payload(master_prompt, date_text, model)
    request = urllib.request.Request(
        RESPONSES_URL,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    response = transport(request, timeout)
    status = response.get("status")
    if status != "completed":
        detail = response.get("incomplete_details")
        reason = detail.get("reason") if isinstance(detail, dict) else None
        suffix = f" ({reason})" if isinstance(reason, str) and reason else ""
        raise GenerationFailure(f"OpenAI response did not complete: {status!r}{suffix}")
    if not used_web_search(response):
        raise GenerationFailure("OpenAI response completed without a web search call")

    report = response_output_text(response).replace("\r\n", "\n").replace("\r", "\n")
    if not report.strip():
        raise GenerationFailure("OpenAI response contained no Markdown report")
    report = report.rstrip() + "\n"
    metadata = {
        "response_id": str(response.get("id") or "unknown"),
        "model": str(response.get("model") or model),
        "status": "completed",
    }
    return report, metadata


def atomic_create(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise GenerationFailure(f"refusing to overwrite existing staging output: {path}")
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent, delete=False
        ) as handle:
            handle.write(text)
            temporary = Path(handle.name)
        os.link(temporary, path)
    except FileExistsError as exc:
        raise GenerationFailure(
            f"staging output appeared concurrently; refusing overwrite: {path}"
        ) from exc
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate one researched market daily")
    parser.add_argument("--date", required=True, help="Report date in YYYY-MM-DD")
    parser.add_argument("--prompt", required=True, type=Path, help="Master Prompt path")
    parser.add_argument("--output", required=True, type=Path, help="Temporary Markdown output")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Responses API model")
    parser.add_argument("--timeout", type=float, default=1200, help="API timeout in seconds")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        prompt = args.prompt.read_text(encoding="utf-8")
        report, metadata = generate_report(
            prompt,
            args.date,
            os.environ.get("OPENAI_API_KEY", ""),
            model=args.model,
            timeout=args.timeout,
        )
        atomic_create(args.output, report)
    except (OSError, GenerationFailure) as exc:
        print(f"ERROR: {exc}")
        return 2
    print(
        "Generation completed: "
        f"date={args.date} model={metadata['model']} response_id={metadata['response_id']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
