#!/usr/bin/env bash
# Packages the SEPARATE Chopper mod (chopper/BP + chopper/RP) into its own
# .mcaddon — independent from Family Mods (the sword + RPG).
#
# Usage:   ./scripts/build_chopper.sh
# Output:  dist/Chopper.mcaddon   <-- import this on the iPad

set -euo pipefail
cd "$(dirname "$0")/.."

mkdir -p dist
rm -f dist/Chopper_BP.mcpack dist/Chopper_RP.mcpack dist/Chopper.mcaddon

(cd chopper/BP && zip -r -q ../../dist/Chopper_BP.mcpack .)
(cd chopper/RP && zip -r -q ../../dist/Chopper_RP.mcpack .)
(cd dist && zip -q Chopper.mcaddon Chopper_BP.mcpack Chopper_RP.mcpack)

echo "Built dist/Chopper.mcaddon"
echo "This is a separate pack from Family Mods — import it on its own."
