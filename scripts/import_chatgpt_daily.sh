#!/usr/bin/env bash
set -euo pipefail

fail() {
  local layer=$1
  shift
  echo "${layer} status: FAILED" >&2
  echo "Final result: $*" >&2
  exit 1
}

command -v python3 >/dev/null || fail "Input" "python3 is required."

script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
repo_root=$(cd "$script_dir/.." && pwd)
cd "$repo_root"

mkdir -p inbox
temporary_input=$(mktemp "$repo_root/inbox/.chatgpt-import.XXXXXX.md") \
  || fail "Input" "Could not create a temporary inbox file."
normalized_input=""

cleanup() {
  if [[ -n "${temporary_input:-}" && -f "$temporary_input" ]]; then
    rm -f "$temporary_input"
  fi
  if [[ -n "${normalized_input:-}" && -f "$normalized_input" ]]; then
    rm -f "$normalized_input"
  fi
}
trap cleanup EXIT

cat > "$temporary_input"

normalized_input=$(mktemp "$repo_root/inbox/.chatgpt-normalized.XXXXXX.md") \
  || fail "Normalize" "Could not create a temporary normalization file."
if normalization_output=$(python3 scripts/normalize_daily.py \
  --input "$temporary_input" \
  --output "$normalized_input" 2>&1); then
  echo "$normalization_output"
else
  fail "Normalize" "$normalization_output Nothing was imported."
fi
rm -f "$temporary_input"
temporary_input="$normalized_input"
normalized_input=""

if report_date=$(python3 - "$temporary_input" 2>&1 <<'PY'
import datetime as dt
import re
import sys
from pathlib import Path

path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
if not text.strip():
    raise SystemExit("Input is empty or whitespace only.")

exact_h1_dates = re.findall(
    r"^#\s+(\d{4}-\d{2}-\d{2})\s+市场日报\s*$", text, re.MULTILINE
)
if len(exact_h1_dates) > 1:
    raise SystemExit("Found more than one '# YYYY-MM-DD 市场日报' H1.")

front_match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
front_date = None
if front_match:
    title_match = re.search(
        r"^title:\s*[\"']?(\d{4}-\d{2}-\d{2})\s+[^\n]*市场日报[\"']?\s*$",
        front_match.group(1),
        re.MULTILINE,
    )
    if title_match:
        front_date = title_match.group(1)

if exact_h1_dates:
    report_date = exact_h1_dates[0]
    if front_date and front_date != report_date:
        raise SystemExit(
            "Front matter title date does not match the H1 report date: "
            f"{front_date} != {report_date}"
        )
else:
    candidates = []
    if front_date:
        candidates.append(front_date)
    for heading in re.findall(r"^#\s+(.+?)\s*$", text, re.MULTILINE):
        if "市场日报" in heading:
            candidates.extend(re.findall(r"\b\d{4}-\d{2}-\d{2}\b", heading))
    first_line = next((line.strip() for line in text.splitlines() if line.strip()), "")
    if "市场日报" in first_line:
        candidates.extend(re.findall(r"\b\d{4}-\d{2}-\d{2}\b", first_line))
    unique_dates = list(dict.fromkeys(candidates))
    if len(unique_dates) != 1:
        raise SystemExit(
            "No unambiguous report date was found in Markdown front matter or title. "
            "Use the ChatGPT message Copy button so '# YYYY-MM-DD 市场日报' is retained."
        )
    report_date = unique_dates[0]

try:
    parsed = dt.date.fromisoformat(report_date)
except ValueError as exc:
    raise SystemExit(f"Invalid report date: {report_date}") from exc
if parsed.isoformat() != report_date:
    raise SystemExit(f"Report date must use YYYY-MM-DD: {report_date}")

print(report_date)
PY
); then
  :
else
  fail "Input" "$report_date Nothing was imported."
fi

draft_path="$repo_root/inbox/$report_date.md"
draft_status="saved from stdin"

same_markdown() {
  python3 - "$1" "$2" <<'PY'
import sys
from pathlib import Path

def normalized(path: str) -> str:
    text = Path(path).read_text(encoding="utf-8")
    return text.replace("\r\n", "\n").replace("\r", "\n").rstrip() + "\n"

raise SystemExit(0 if normalized(sys.argv[1]) == normalized(sys.argv[2]) else 1)
PY
}

if [[ -e "$draft_path" ]]; then
  if [[ ! -f "$draft_path" || -L "$draft_path" ]]; then
    fail "Draft" "Refusing unsafe inbox target: inbox/$report_date.md"
  fi
  if same_markdown "$temporary_input" "$draft_path"; then
    draft_status="already present with identical content"
    rm -f "$temporary_input"
    temporary_input=""
  else
    fail "Draft" "A different inbox/$report_date.md already exists; it was not overwritten."
  fi
else
  if ! ln "$temporary_input" "$draft_path" 2>/dev/null; then
    if [[ -f "$draft_path" && ! -L "$draft_path" ]] && same_markdown "$temporary_input" "$draft_path"; then
      draft_status="already present with identical content"
    else
      fail "Draft" "Could not safely create inbox/$report_date.md; no existing file was overwritten."
    fi
  fi
  rm -f "$temporary_input"
  temporary_input=""
fi

echo "Report date: $report_date"
echo "Draft status: $draft_status (inbox/$report_date.md)"

if validator_output=$(python3 scripts/validate_daily.py --date "$report_date" --input "$draft_path" 2>&1); then
  echo "$validator_output"
else
  echo "$validator_output" >&2
  validator_reason=${validator_output##*$'\n'}
  validator_reason=${validator_reason#ERROR: }
  if [[ "$validator_reason" == *"YAML front matter"* || "$validator_reason" == *"exactly one H1"* ]]; then
    validator_reason="$validator_reason Use the ChatGPT message Copy button to retain raw Markdown."
  fi
  fail "Validator" "$validator_reason The draft remains in inbox; archive files were not imported."
fi
echo "Validator status: PASSED"

if ! python3 scripts/import_daily.py --date "$report_date" --input "$draft_path"; then
  fail "Import" "The deterministic importer refused the report; no existing report was overwritten."
fi
echo "Import status: PASSED"

if [[ -x .venv/bin/mkdocs ]]; then
  mkdocs_command=(.venv/bin/mkdocs)
elif command -v mkdocs >/dev/null; then
  mkdocs_command=(mkdocs)
else
  fail "Build" "MkDocs is not installed; create .venv and install requirements.txt."
fi

if ! "${mkdocs_command[@]}" build --strict; then
  fail "Build" "Strict MkDocs build failed. Local imported files were not pushed."
fi

echo "Build status: PASSED (mkdocs build --strict)"
echo "GitHub status: NOT RUN (this command never commits or pushes)"
echo "Final result: SUCCESS — $report_date is available in the local archive."
echo "Local preview: run 'mkdocs serve', then open the local address shown by MkDocs."
