#!/usr/bin/env bash
set -euo pipefail

fail() {
  echo "ERROR: $*" >&2
  exit 1
}

command -v gh >/dev/null || fail "GitHub CLI (gh) is required"
command -v python3 >/dev/null || fail "python3 is required"

dispatch_root=$(git rev-parse --show-toplevel 2>/dev/null) || fail "not inside the project repository"
cd "$dispatch_root"

report_date=${1:-$(TZ=Asia/Singapore date +%F)}
python3 -c 'import datetime,sys; value=sys.argv[1]; assert datetime.date.fromisoformat(value).isoformat() == value' "$report_date" \
  || fail "report date must use YYYY-MM-DD"

repository="leemin-blip/market-daily-archive"
workflow="generate-daily.yml"

previous_id=$(gh run list \
  --repo "$repository" \
  --workflow "$workflow" \
  --event workflow_dispatch \
  --limit 1 \
  --json databaseId \
  --jq '.[0].databaseId // empty')

gh workflow run "$workflow" \
  --repo "$repository" \
  --ref main \
  -f "report_date=$report_date"

run_id=""
for _attempt in {1..24}; do
  candidate=$(gh run list \
    --repo "$repository" \
    --workflow "$workflow" \
    --event workflow_dispatch \
    --limit 1 \
    --json databaseId \
    --jq '.[0].databaseId // empty')
  if [[ -n "$candidate" && "$candidate" != "$previous_id" ]]; then
    run_id=$candidate
    break
  fi
  sleep 5
done

[[ -n "$run_id" ]] || fail "workflow_dispatch was accepted but no new run appeared"
run_url=$(gh run view "$run_id" --repo "$repository" --json url --jq .url)
echo "Workflow run: $run_url"
gh run watch "$run_id" --repo "$repository" --exit-status --interval 5
echo "Workflow completed successfully: $run_url"
