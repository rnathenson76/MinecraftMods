#!/usr/bin/env bash
# Packages the SEPARATE Squirrel mod (squirrel/BP + squirrel/RP) into its own
# .mcaddon — independent from Family Mods and from the Chopper.
#
# Usage:   ./scripts/build_squirrel.sh
# Output:  dist/Squirrel.mcaddon   <-- import this on the iPad

set -euo pipefail
cd "$(dirname "$0")/.."

python3 tools/squirrel_model.py            # models + textures + previewer
python3 tools/check_squirrel.py            # catch typos before Minecraft does

mkdir -p dist
rm -f dist/Squirrel_BP.mcpack dist/Squirrel_RP.mcpack dist/Squirrel.mcaddon

(cd squirrel/BP && zip -r -q ../../dist/Squirrel_BP.mcpack .)
(cd squirrel/RP && zip -r -q ../../dist/Squirrel_RP.mcpack .)
(cd dist && zip -q Squirrel.mcaddon Squirrel_BP.mcpack Squirrel_RP.mcpack)

echo "Built dist/Squirrel.mcaddon"
echo "This is a separate pack from Family Mods and the Chopper — import it on its own."
