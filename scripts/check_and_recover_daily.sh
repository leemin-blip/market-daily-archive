#!/usr/bin/env bash
set -euo pipefail
recovery_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
export PATH="/Users/lantolee/.local/bin:$PATH"
if [[ -z "${GH_CONFIG_DIR:-}" && -d /Users/lantolee/.local/config/gh ]]; then
  export GH_CONFIG_DIR=/Users/lantolee/.local/config/gh
fi
exec python3 "$recovery_root/scripts/recover_daily.py" "$@"
