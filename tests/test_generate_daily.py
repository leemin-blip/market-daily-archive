from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest
import urllib.request

from scripts.generate_daily import (
    GenerationFailure,
    atomic_create,
    generate_report,
)
from scripts.validate_daily import ValidationFailure, validate_report
from test_validate_daily import report_body


DATE = "2026-09-01"
KEY = "test-key-never-log"


def completed_response(text: str) -> dict:
    return {
        "id": "resp_test",
        "model": "gpt-5.6-sol-2026-08-01",
        "status": "completed",
        "output": [
            {"type": "web_search_call", "id": "ws_test", "status": "completed"},
            {
                "type": "message",
                "content": [{"type": "output_text", "text": text}],
            },
        ],
    }


class RecordingTransport:
    def __init__(self, response: dict):
        self.response = response
        self.request: urllib.request.Request | None = None
        self.timeout = 0.0

    def __call__(self, request: urllib.request.Request, timeout: float) -> dict:
        self.request = request
        self.timeout = timeout
        return self.response


class GenerateDailyTests(unittest.TestCase):
    def test_responses_api_uses_master_prompt_and_web_search(self) -> None:
        transport = RecordingTransport(completed_response(report_body()))
        report, metadata = generate_report(
            "MASTER PROMPT UNIQUE MARKER",
            DATE,
            KEY,
            transport=transport,
        )
        self.assertEqual(validate_report(report, DATE), "trading_day")
        self.assertEqual(metadata["response_id"], "resp_test")
        self.assertIsNotNone(transport.request)
        assert transport.request is not None
        payload = json.loads(transport.request.data or b"{}")
        self.assertEqual(payload["model"], "gpt-5.6-sol")
        self.assertEqual(payload["tools"], [{"type": "web_search", "search_context_size": "high"}])
        self.assertEqual(payload["tool_choice"], "required")
        self.assertIn("MASTER PROMPT UNIQUE MARKER", payload["input"])
        self.assertIn(DATE, payload["input"])
        self.assertEqual(transport.request.get_header("Authorization"), f"Bearer {KEY}")

    def test_empty_api_output_fails_closed(self) -> None:
        with self.assertRaises(GenerationFailure):
            generate_report(
                "prompt", DATE, KEY,
                transport=RecordingTransport(completed_response("   ")),
            )

    def test_incomplete_api_response_fails_closed(self) -> None:
        response = {
            "id": "resp_incomplete",
            "status": "incomplete",
            "incomplete_details": {"reason": "max_output_tokens"},
            "output": [],
        }
        with self.assertRaisesRegex(GenerationFailure, "max_output_tokens"):
            generate_report("prompt", DATE, KEY, transport=RecordingTransport(response))

    def test_missing_web_search_call_fails_closed(self) -> None:
        response = completed_response(report_body())
        response["output"] = response["output"][1:]
        with self.assertRaisesRegex(GenerationFailure, "without a web search"):
            generate_report("prompt", DATE, KEY, transport=RecordingTransport(response))

    def test_api_failure_does_not_create_staging_file(self) -> None:
        class FailingTransport:
            def __call__(self, _request, _timeout):
                raise GenerationFailure("OpenAI Responses API returned HTTP 500")

        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "report.md"
            with self.assertRaises(GenerationFailure) as caught:
                report, _metadata = generate_report(
                    "prompt", DATE, KEY, transport=FailingTransport()
                )
                atomic_create(output, report)
            self.assertFalse(output.exists())
            self.assertNotIn(KEY, str(caught.exception))

    def test_truncated_markdown_is_rejected_by_existing_validator(self) -> None:
        transport = RecordingTransport(completed_response(report_body()[:700]))
        report, _metadata = generate_report("prompt", DATE, KEY, transport=transport)
        with self.assertRaises(ValidationFailure):
            validate_report(report, DATE)

    def test_atomic_staging_never_overwrites(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "report.md"
            atomic_create(output, "first\n")
            with self.assertRaises(GenerationFailure):
                atomic_create(output, "second\n")
            self.assertEqual(output.read_text(encoding="utf-8"), "first\n")

    def test_missing_api_key_fails_before_transport(self) -> None:
        transport = RecordingTransport(completed_response(report_body()))
        with self.assertRaisesRegex(GenerationFailure, "OPENAI_API_KEY"):
            generate_report("prompt", DATE, "", transport=transport)
        self.assertIsNone(transport.request)


if __name__ == "__main__":
    unittest.main()
