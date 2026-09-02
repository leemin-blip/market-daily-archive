from __future__ import annotations

import http.server
import os
import signal
import socket
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest import mock

from scripts.open_local_archive import (
    IDENTITY_MARKERS,
    LocalArchiveFailure,
    ProbeResult,
    ensure_archive_server,
    probe_archive,
)


def free_port() -> int:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return listener.getsockname()[1]


class StaticHandler(http.server.BaseHTTPRequestHandler):
    body = b""

    def do_GET(self) -> None:  # noqa: N802
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(self.body)

    def log_message(self, format: str, *args: object) -> None:
        pass


class OpenLocalArchiveTests(unittest.TestCase):
    def serve(self, body: bytes) -> tuple[http.server.HTTPServer, int]:
        port = free_port()
        handler = type("TestHandler", (StaticHandler,), {"body": body})
        server = http.server.HTTPServer(("127.0.0.1", port), handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        return server, port

    def test_existing_archive_is_reused_without_needing_mkdocs(self) -> None:
        server, port = self.serve(b"<html>" + b"\n".join(IDENTITY_MARKERS) + b"</html>")
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result = ensure_archive_server(
                root,
                root / "missing-mkdocs",
                root / "state",
                port=port,
            )

        self.assertEqual(result.status, "ALREADY_RUNNING")
        self.assertIsNone(result.pid)
        self.assertEqual(probe_archive(port), ProbeResult.ARCHIVE)

    def test_unrelated_service_on_port_is_rejected(self) -> None:
        server, port = self.serve(b"<html><h1>Another local app</h1></html>")
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaisesRegex(LocalArchiveFailure, "another service"):
                ensure_archive_server(
                    root,
                    root / "missing-mkdocs",
                    root / "state",
                    port=port,
                )

    def test_same_origin_redirect_to_archive_is_accepted(self) -> None:
        port = free_port()
        body = b"<html>" + b"\n".join(IDENTITY_MARKERS) + b"</html>"

        class RedirectHandler(StaticHandler):
            def do_GET(self) -> None:  # noqa: N802
                if self.path == "/":
                    self.send_response(302)
                    self.send_header("Location", "/market-daily-archive/")
                    self.end_headers()
                    return
                self.send_response(200)
                self.end_headers()
                self.wfile.write(body)

        server = http.server.HTTPServer(("127.0.0.1", port), RedirectHandler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)

        self.assertEqual(probe_archive(port), ProbeResult.ARCHIVE)

    def test_external_redirect_is_rejected_without_following_it(self) -> None:
        port = free_port()

        class ExternalRedirectHandler(StaticHandler):
            def do_GET(self) -> None:  # noqa: N802
                self.send_response(302)
                self.send_header("Location", "https://example.com/not-allowed")
                self.end_headers()

        server = http.server.HTTPServer(("127.0.0.1", port), ExternalRedirectHandler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)

        self.assertEqual(probe_archive(port), ProbeResult.OTHER)

    def test_start_then_rerun_keeps_one_server(self) -> None:
        port = free_port()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            state = root / "state"
            state.mkdir()
            (root / "mkdocs.yml").write_text("site_name: test\n", encoding="utf-8")
            launches = state / "launches.log"
            fake_mkdocs = root / "fake-mkdocs"
            body = repr(b"<html>" + b"\n".join(IDENTITY_MARKERS) + b"</html>")
            fake_mkdocs.write_text(
                "#!/usr/bin/env python3\n"
                "import http.server, os, sys\n"
                "from pathlib import Path\n"
                f"Path({str(launches)!r}).open('a').write(f'{{os.getpid()}}\\n')\n"
                "address = sys.argv[sys.argv.index('--dev-addr') + 1]\n"
                "host, port = address.rsplit(':', 1)\n"
                f"BODY = {body}\n"
                "class Handler(http.server.BaseHTTPRequestHandler):\n"
                "    def do_GET(self):\n"
                "        self.send_response(200)\n"
                "        self.end_headers()\n"
                "        self.wfile.write(BODY)\n"
                "    def log_message(self, format, *args):\n"
                "        pass\n"
                "http.server.HTTPServer((host, int(port)), Handler).serve_forever()\n",
                encoding="utf-8",
            )
            fake_mkdocs.chmod(0o755)

            first = ensure_archive_server(
                root,
                fake_mkdocs,
                state,
                port=port,
                timeout=5,
            )
            try:
                second = ensure_archive_server(
                    root,
                    fake_mkdocs,
                    state,
                    port=port,
                    timeout=5,
                )

                self.assertEqual(first.status, "STARTED")
                self.assertEqual(second.status, "ALREADY_RUNNING")
                self.assertEqual(len(launches.read_text(encoding="utf-8").splitlines()), 1)
                self.assertEqual(probe_archive(port), ProbeResult.ARCHIVE)
            finally:
                if first.pid is not None:
                    try:
                        os.killpg(first.pid, signal.SIGTERM)
                        os.waitpid(first.pid, 0)
                    except (ChildProcessError, ProcessLookupError):
                        pass
                    deadline = time.monotonic() + 2
                    while probe_archive(port) is not ProbeResult.CLOSED and time.monotonic() < deadline:
                        time.sleep(0.05)

    @mock.patch("scripts.open_local_archive.time.sleep", return_value=None)
    @mock.patch(
        "scripts.open_local_archive.probe_archive",
        side_effect=[ProbeResult.CLOSED, ProbeResult.OPEN_UNREADY, ProbeResult.ARCHIVE],
    )
    @mock.patch("scripts.open_local_archive.subprocess.Popen")
    def test_new_server_may_bind_before_its_page_is_ready(
        self,
        popen: mock.Mock,
        _probe: mock.Mock,
        _sleep: mock.Mock,
    ) -> None:
        process = popen.return_value
        process.pid = 4242
        process.poll.return_value = None
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "mkdocs.yml").write_text("site_name: test\n", encoding="utf-8")
            mkdocs = root / "mkdocs"
            mkdocs.write_text("#!/bin/sh\n", encoding="utf-8")
            mkdocs.chmod(0o755)

            result = ensure_archive_server(
                root,
                mkdocs,
                root / "state",
                port=free_port(),
                timeout=2,
            )

        self.assertEqual(result.status, "STARTED")
        self.assertEqual(result.pid, 4242)


if __name__ == "__main__":
    unittest.main()
