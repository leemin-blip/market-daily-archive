#!/usr/bin/env python3
"""Safely replace one proven-invalid inbox draft with a valid candidate."""

from __future__ import annotations

import argparse
import datetime as dt
import os
import stat
import sys
from pathlib import Path

from validate_daily import ValidationFailure, validate_report


class RecoveryFailure(RuntimeError):
    """Raised when a draft conflict cannot be recovered safely."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Preserve and replace a current-Validator-rejected inbox draft"
    )
    parser.add_argument("--repo-root", required=True, type=Path)
    parser.add_argument("--date", required=True)
    parser.add_argument("--candidate", required=True, type=Path)
    return parser.parse_args()


def is_existing_path(path: Path) -> bool:
    return os.path.lexists(path)


def require_regular_file(path: Path, label: str) -> None:
    try:
        metadata = path.lstat()
    except OSError as exc:
        raise RecoveryFailure(f"could not inspect {label}: {exc}") from exc
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        raise RecoveryFailure(f"refusing unsafe {label}: {path}")


def read_utf8(path: Path, label: str) -> str:
    require_regular_file(path, label)
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise RecoveryFailure(f"could not read {label} as UTF-8: {exc}") from exc


def validate_candidate(text: str, date_text: str) -> None:
    try:
        validate_report(text, date_text)
    except ValidationFailure as exc:
        raise RecoveryFailure(
            f"replacement candidate failed the current Validator: {exc}"
        ) from exc
    except Exception as exc:  # Fail closed if Validator execution itself is abnormal.
        raise RecoveryFailure(
            f"could not prove the replacement candidate is valid: {exc}"
        ) from exc


def prove_existing_is_rejected(text: str, date_text: str) -> str:
    try:
        validate_report(text, date_text)
    except ValidationFailure as exc:
        return str(exc)
    except Exception as exc:  # A runtime problem is not proof of validation failure.
        raise RecoveryFailure(
            f"could not prove the existing inbox draft fails Validator: {exc}"
        ) from exc
    raise RecoveryFailure(
        "existing inbox draft still passes the current Validator; "
        "it cannot be treated as a rejected draft"
    )


def reserve_backup_path(rejected_dir: Path, date_text: str, contents: bytes) -> Path:
    try:
        rejected_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
        metadata = rejected_dir.lstat()
    except OSError as exc:
        raise RecoveryFailure(f"could not prepare rejected history: {exc}") from exc
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
        raise RecoveryFailure(f"refusing unsafe rejected history: {rejected_dir}")

    for sequence in range(1, 10_000):
        backup = rejected_dir / f"{date_text}-rejected-{sequence:03d}.md"
        try:
            descriptor = os.open(
                backup,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                0o600,
            )
        except FileExistsError:
            continue
        except OSError as exc:
            raise RecoveryFailure(f"could not preserve rejected draft: {exc}") from exc
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(contents)
                stream.flush()
                os.fsync(stream.fileno())
        except Exception as exc:
            try:
                backup.unlink()
            except OSError:
                pass
            raise RecoveryFailure(f"could not preserve rejected draft: {exc}") from exc
        return backup
    raise RecoveryFailure("rejected history has no available sequence number")


def recover(repo_root: Path, date_text: str, candidate: Path) -> tuple[Path, str]:
    try:
        parsed = dt.date.fromisoformat(date_text)
    except ValueError as exc:
        raise RecoveryFailure(f"invalid ISO date: {date_text}") from exc
    if parsed.isoformat() != date_text:
        raise RecoveryFailure(f"date must use YYYY-MM-DD: {date_text}")

    root = repo_root.resolve()
    existing = root / "inbox" / f"{date_text}.md"
    archive = root / "docs" / date_text[:4] / date_text[5:7] / f"{date_text}.md"
    rejected_dir = root / "inbox" / "rejected"

    candidate_text = read_utf8(candidate, "replacement candidate")
    candidate_bytes = candidate_text.encode("utf-8")
    validate_candidate(candidate_text, date_text)

    if is_existing_path(archive):
        raise RecoveryFailure(
            f"formal archive already exists at docs/{date_text[:4]}/{date_text[5:7]}/"
            f"{date_text}.md; refusing same-date replacement"
        )

    existing_text = read_utf8(existing, "existing inbox draft")
    failure_reason = prove_existing_is_rejected(existing_text, date_text)
    existing_bytes = existing_text.encode("utf-8")
    backup = reserve_backup_path(rejected_dir, date_text, existing_bytes)

    try:
        if read_utf8(existing, "existing inbox draft").encode("utf-8") != existing_bytes:
            raise RecoveryFailure(
                "existing inbox draft changed during recovery; it was not replaced"
            )
        if read_utf8(candidate, "replacement candidate").encode("utf-8") != candidate_bytes:
            raise RecoveryFailure(
                "replacement candidate changed during recovery; the inbox draft was not replaced"
            )
        if is_existing_path(archive):
            raise RecoveryFailure(
                "formal archive appeared during recovery; the inbox draft was not replaced"
            )
        os.replace(candidate, existing)
    except RecoveryFailure:
        raise
    except OSError as exc:
        raise RecoveryFailure(
            f"rejected draft was preserved, but replacement failed: {exc}"
        ) from exc

    return backup, failure_reason


def main() -> int:
    args = parse_args()
    try:
        backup, reason = recover(args.repo_root, args.date, args.candidate)
    except RecoveryFailure as exc:
        print(f"ERROR: {exc}")
        return 2

    try:
        display = backup.resolve().relative_to(args.repo_root.resolve())
    except ValueError:
        display = backup
    print(f"Rejected draft preserved: {display}")
    print(f"Existing draft Validator failure: {reason}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
