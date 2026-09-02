#!/usr/bin/env bash
set -euo pipefail

fail() {
  echo "ERROR: $*" >&2
  exit 1
}

command -v osacompile >/dev/null || fail "osacompile is required (macOS only)."

script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
repo_root=$(cd "$script_dir/.." && pwd)
source_file="$repo_root/macos/archive_today.js"
launcher_path="$repo_root/macos/归档今日日报.app"
open_source_file="$repo_root/macos/open_archive.js"
open_launcher_path="$repo_root/macos/打开 Market Daily Archive.app"

[[ -f "$source_file" ]] || fail "Launcher source is missing: $source_file"
[[ -f "$open_source_file" ]] || fail "Launcher source is missing: $open_source_file"

if [[ -x "$repo_root/.venv/bin/python" ]]; then
  python_bin="$repo_root/.venv/bin/python"
elif command -v python3 >/dev/null; then
  python_bin=$(command -v python3)
else
  fail "python3 is required."
fi

if [[ -x "$repo_root/.venv/bin/mkdocs" ]]; then
  mkdocs_bin="$repo_root/.venv/bin/mkdocs"
elif command -v mkdocs >/dev/null; then
  mkdocs_bin=$(command -v mkdocs)
else
  fail "MkDocs is required. Create .venv and install requirements.txt first."
fi

temporary_dir=$(mktemp -d "${TMPDIR:-/tmp}/market-daily-launcher.XXXXXX") \
  || fail "Could not create a temporary build directory."
cleanup() {
  rm -rf "$temporary_dir"
}
trap cleanup EXIT

rendered_source="$temporary_dir/archive_today.js"
rendered_open_source="$temporary_dir/open_archive.js"
escaped_root=${repo_root//\\/\\\\}
escaped_root=${escaped_root//&/\\&}
escaped_root=${escaped_root//|/\\|}
escaped_python=${python_bin//\\/\\\\}
escaped_python=${escaped_python//&/\\&}
escaped_python=${escaped_python//|/\\|}
escaped_mkdocs=${mkdocs_bin//\\/\\\\}
escaped_mkdocs=${escaped_mkdocs//&/\\&}
escaped_mkdocs=${escaped_mkdocs//|/\\|}
sed "s|__PROJECT_ROOT__|$escaped_root|g" "$source_file" > "$rendered_source"
sed \
  -e "s|__PROJECT_ROOT__|$escaped_root|g" \
  -e "s|__PYTHON_BIN__|$escaped_python|g" \
  -e "s|__MKDOCS_BIN__|$escaped_mkdocs|g" \
  "$open_source_file" > "$rendered_open_source"

compiled_launcher="$temporary_dir/归档今日日报.app"
compiled_open_launcher="$temporary_dir/打开 Market Daily Archive.app"
osacompile -l JavaScript -o "$compiled_launcher" "$rendered_source"
osacompile -l JavaScript -o "$compiled_open_launcher" "$rendered_open_source"

previous_launcher=""
if [[ -e "$launcher_path" ]]; then
  previous_launcher="$temporary_dir/previous-launcher.app"
  mv "$launcher_path" "$previous_launcher"
fi

if ! mv "$compiled_launcher" "$launcher_path"; then
  if [[ -n "$previous_launcher" && -e "$previous_launcher" ]]; then
    mv "$previous_launcher" "$launcher_path"
  fi
  fail "Could not install the compiled launcher."
fi

previous_open_launcher=""
if [[ -e "$open_launcher_path" ]]; then
  previous_open_launcher="$temporary_dir/previous-open-launcher.app"
  mv "$open_launcher_path" "$previous_open_launcher"
fi

if ! mv "$compiled_open_launcher" "$open_launcher_path"; then
  if [[ -n "$previous_open_launcher" && -e "$previous_open_launcher" ]]; then
    mv "$previous_open_launcher" "$open_launcher_path"
  fi
  fail "Could not install the compiled local Archive launcher."
fi

launch_services_register="/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister"
if [[ -x "$launch_services_register" ]]; then
  if ! "$launch_services_register" -f "$launcher_path" >/dev/null 2>&1; then
    echo "Warning: Launch Services refresh was unavailable; the App was still rebuilt in place." >&2
  fi
  if ! "$launch_services_register" -f "$open_launcher_path" >/dev/null 2>&1; then
    echo "Warning: Launch Services refresh was unavailable for the local Archive App." >&2
  fi
fi

echo "Installed: $launcher_path"
echo "Installed: $open_launcher_path"
echo "Daily use: copy the complete report, then click 归档今日日报.app."
echo "Local reading: click 打开 Market Daily Archive.app."
echo "Optional: drag the app to the Dock for one-click access."
