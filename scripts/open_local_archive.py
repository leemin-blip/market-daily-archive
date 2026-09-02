#!/usr/bin/env python3
"""Start or reuse the local Market Daily Archive MkDocs server."""

from __future__ import annotations

import argparse
import fcntl
import os
import signal
import socket
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


HOST = "127.0.0.1"
PORT = 8000
IDENTITY_MARKERS = (
    b'<meta name="description" content="\xe4\xb8\xaa\xe4\xba\xba\xe9\x87\x91\xe8\x9e\x8d\xe5\xb8\x82\xe5\x9c\xba\xe6\x97\xa5\xe6\x8a\xa5\xe6\xa1\xa3\xe6\xa1\x88\xe5\xba\x93">',
    b'<h1 id="market-daily-archive">Market Daily Archive</h1>',
)


class ProbeResult(Enum):
    CLOSED = "closed"
    OPEN_UNREADY = "open-unready"
    ARCHIVE = "archive"
    OTHER = "other"


@dataclass(frozen=True)
class ServiceResult:
    status: str
    url: str
    pid: int | None


class LocalArchiveFailure(RuntimeError):
    """Raised when the local Archive cannot be opened safely."""


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
        return None


def archive_url(port: int) -> str:
    return f"http://{HOST}:{port}/"


def _port_is_open(port: int) -> bool:
    try:
        with socket.create_connection((HOST, port), timeout=0.35):
            return True
    except OSError:
        return False


def probe_archive(port: int) -> ProbeResult:
    if not _port_is_open(port):
        return ProbeResult.CLOSED

    opener = urllib.request.build_opener(
        urllib.request.ProxyHandler({}),
        NoRedirect(),
    )
    url = archive_url(port)
    try:
        try:
            response = opener.open(url, timeout=1.0)
        except urllib.error.HTTPError as exc:
            if exc.code not in {301, 302, 303, 307, 308}:
                return ProbeResult.OTHER
            location = exc.headers.get("Location")
            if not location:
                return ProbeResult.OTHER
            redirected_url = urllib.parse.urljoin(url, location)
            parsed = urllib.parse.urlsplit(redirected_url)
            try:
                redirected_port = parsed.port
            except ValueError:
                return ProbeResult.OTHER
            if (
                parsed.scheme != "http"
                or parsed.hostname != HOST
                or redirected_port != port
            ):
                return ProbeResult.OTHER
            response = opener.open(redirected_url, timeout=1.0)
        with response:
            if response.status != 200:
                return ProbeResult.OTHER
            body = response.read(512 * 1024)
    except urllib.error.HTTPError:
        return ProbeResult.OTHER
    except (OSError, urllib.error.URLError):
        return ProbeResult.OPEN_UNREADY

    return (
        ProbeResult.ARCHIVE
        if all(marker in body for marker in IDENTITY_MARKERS)
        else ProbeResult.OTHER
    )


def _stop_started_process(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        return
    try:
        os.killpg(process.pid, signal.SIGTERM)
        process.wait(timeout=3)
    except (OSError, subprocess.TimeoutExpired):
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except OSError:
            pass


def ensure_archive_server(
    repo_root: Path,
    mkdocs: Path,
    state_dir: Path,
    port: int = PORT,
    timeout: float = 15.0,
) -> ServiceResult:
    repo_root = repo_root.resolve()
    mkdocs = mkdocs.resolve()
    state_dir.mkdir(parents=True, exist_ok=True)
    lock_path = state_dir / ".mkdocs-serve.lock"
    log_path = state_dir / ".mkdocs-serve.log"
    pid_path = state_dir / ".mkdocs-serve.pid"

    with lock_path.open("a+b") as lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        initial = probe_archive(port)
        if initial is ProbeResult.ARCHIVE:
            return ServiceResult("ALREADY_RUNNING", archive_url(port), None)
        if initial in {ProbeResult.OPEN_UNREADY, ProbeResult.OTHER}:
            raise LocalArchiveFailure(
                f"Port {port} is in use by another service; Market Daily Archive was not started."
            )

        if not mkdocs.is_file() or not os.access(mkdocs, os.X_OK):
            raise LocalArchiveFailure(f"MkDocs executable is unavailable: {mkdocs}")
        if not (repo_root / "mkdocs.yml").is_file():
            raise LocalArchiveFailure(f"Market Daily Archive project is unavailable: {repo_root}")

        try:
            log_file = log_path.open("ab", buffering=0)
        except OSError as exc:
            raise LocalArchiveFailure(f"Could not open the local server log: {exc}") from exc

        try:
            process = subprocess.Popen(
                [str(mkdocs), "serve", "--dev-addr", f"{HOST}:{port}"],
                cwd=repo_root,
                stdin=subprocess.DEVNULL,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                start_new_session=True,
                close_fds=True,
            )
        except OSError as exc:
            log_file.close()
            raise LocalArchiveFailure(f"Could not start MkDocs: {exc}") from exc
        finally:
            log_file.close()

        pid_path.write_text(f"{process.pid}\n", encoding="ascii")
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            state = probe_archive(port)
            if state is ProbeResult.ARCHIVE:
                # The verified server intentionally outlives this short launcher process.
                # Mark only the local Popen handle as complete so its destructor does not
                # warn about the deliberately detached child; the server itself continues.
                process.returncode = 0
                return ServiceResult("STARTED", archive_url(port), process.pid)
            if process.poll() is not None:
                raise LocalArchiveFailure(
                    "MkDocs exited before the Archive became available; "
                    "see inbox/.mkdocs-serve.log."
                )
            if state is ProbeResult.OTHER:
                _stop_started_process(process)
                raise LocalArchiveFailure(
                    f"Port {port} was claimed by another service while MkDocs was starting."
                )
            time.sleep(0.2)

        _stop_started_process(process)
        raise LocalArchiveFailure(
            "MkDocs did not become ready within the expected time; "
            "see inbox/.mkdocs-serve.log."
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", required=True, type=Path)
    parser.add_argument("--mkdocs", required=True, type=Path)
    parser.add_argument("--state-dir", required=True, type=Path)
    parser.add_argument("--port", type=int, default=PORT)
    parser.add_argument("--timeout", type=float, default=15.0)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not 1 <= args.port <= 65535:
        print("Service status: FAILED")
        print("Final result: The local port must be between 1 and 65535.")
        return 2
    try:
        result = ensure_archive_server(
            repo_root=args.repo_root,
            mkdocs=args.mkdocs,
            state_dir=args.state_dir,
            port=args.port,
            timeout=args.timeout,
        )
    except LocalArchiveFailure as exc:
        print("Service status: FAILED")
        print(f"Final result: {exc}")
        return 1

    print(f"Service status: {result.status}")
    if result.pid is not None:
        print(f"MkDocs PID: {result.pid}")
    print(f"URL: {result.url}")
    print("Final result: SUCCESS — local Market Daily Archive is ready.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
