#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: scripts/publish_daily.sh YYYY-MM-DD INPUT.md [ONE-LINE-SUMMARY]" >&2
}

fail() {
  echo "ERROR: $*" >&2
  exit 1
}

if [[ $# -lt 2 || $# -gt 3 ]]; then
  usage
  exit 2
fi

report_date=$1
input_path=$2
report_summary=${3:-}

command -v git >/dev/null || fail "git is required"
command -v gh >/dev/null || fail "GitHub CLI (gh) is required"
command -v curl >/dev/null || fail "curl is required"
command -v python3 >/dev/null || fail "python3 is required"

repo_root=$(git rev-parse --show-toplevel 2>/dev/null) || fail "not inside a Git repository"
cd "$repo_root"

current_branch=$(git branch --show-current)
[[ "$current_branch" == "main" ]] || fail "expected branch main, found $current_branch"

if [[ -n "$(git status --porcelain --untracked-files=normal)" ]]; then
  fail "working tree must be clean before automated publishing"
fi

gh auth status --hostname github.com >/dev/null || fail "GitHub CLI authentication is unavailable"

echo "Fetching origin/main before import..."
git fetch origin main
if ! git merge-base --is-ancestor origin/main HEAD; then
  fail "local main is behind or diverged from origin/main; reconcile manually"
fi

import_args=(--date "$report_date" --input "$input_path")
if [[ -n "$report_summary" ]]; then
  import_args+=(--summary "$report_summary")
fi

python3 scripts/import_daily.py "${import_args[@]}"

if [[ -x .venv/bin/mkdocs ]]; then
  mkdocs_command=(.venv/bin/mkdocs)
elif command -v mkdocs >/dev/null; then
  mkdocs_command=(mkdocs)
else
  fail "MkDocs is not installed; create .venv and install requirements.txt"
fi

echo "Running strict site build..."
"${mkdocs_command[@]}" build --strict

git diff --check
git add docs mkdocs.yml
git diff --cached --check

if git diff --cached --quiet; then
  echo "No new archive changes to commit; continuing with remote verification."
else
  git commit -m "Import market daily $report_date"
fi

local_head=$(git rev-parse HEAD)
echo "Pushing $local_head to origin/main..."
git push origin main

remote_head=$(git ls-remote origin refs/heads/main | awk '{print $1}')
[[ -n "$remote_head" ]] || fail "could not read origin/main after push"
[[ "$remote_head" == "$local_head" ]] || fail "remote main does not match local HEAD"
echo "Remote verification passed: $remote_head"

run_id=""
for _attempt in {1..12}; do
  run_id=$(gh run list \
    --workflow deploy-pages.yml \
    --commit "$local_head" \
    --limit 1 \
    --json databaseId \
    --jq '.[0].databaseId // empty')
  if [[ -n "$run_id" ]]; then
    break
  fi
  sleep 5
done

[[ -n "$run_id" ]] || fail "Pages workflow did not appear for commit $local_head"
echo "Waiting for Pages workflow $run_id..."
gh run watch "$run_id" --exit-status --interval 5

IFS=- read -r report_year report_month _report_day <<< "$report_date"
site_url=$(awk '$1 == "site_url:" {print $2; exit}' mkdocs.yml)
[[ -n "$site_url" ]] || fail "site_url is missing from mkdocs.yml"
report_url="${site_url%/}/${report_year}/${report_month}/${report_date}/"

echo "Verifying published page: $report_url"
published_page=$(curl --fail --silent --show-error --location \
  --retry 12 --retry-delay 5 --max-time 30 "$report_url")
grep -F "$report_date" <<< "$published_page" >/dev/null \
  || fail "published page does not contain $report_date"

echo "Publish completed and verified: $report_url"
