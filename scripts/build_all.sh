#!/usr/bin/env bash
# Builds every mod in this repo into dist/, and checks first that they're all
# still separate packs.
#
# Usage:   ./scripts/build_all.sh
# Output:  dist/*.mcaddon  — one file per mod, each imported on its own

set -euo pipefail
cd "$(dirname "$0")/.."

python3 tools/check_packs.py
echo

for s in scripts/build_*.sh; do
  [ "$(basename "$s")" = "build_all.sh" ] && continue
  bash "$s" >/dev/null
  echo "built $(basename "$s")"
done

echo
ls -la dist/*.mcaddon
