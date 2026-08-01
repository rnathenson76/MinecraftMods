#!/usr/bin/env bash
# Packages the SEPARATE Unfun mod (unfun/BP + unfun/RP) into its own
# .mcaddon — independent from Family Mods (sword + RPG) and from the Chopper.
#
# Usage:   ./scripts/build_unfun.sh
# Output:  dist/Unfun.mcaddon   <-- import this on the iPad

set -euo pipefail
cd "$(dirname "$0")/.."

mkdir -p dist
rm -f dist/Unfun_BP.mcpack dist/Unfun_RP.mcpack dist/Unfun.mcaddon

(cd unfun/BP && zip -r -q ../../dist/Unfun_BP.mcpack .)
(cd unfun/RP && zip -r -q ../../dist/Unfun_RP.mcpack .)
(cd dist && zip -q Unfun.mcaddon Unfun_BP.mcpack Unfun_RP.mcpack)

echo "Built dist/Unfun.mcaddon"
echo "This is a separate pack — import it on its own (it needs BOTH its packs"
echo "active in the world: the Behavior Pack runs the scripts, and you must"
echo "turn on 'Additional Modding Capabilities'/Beta APIs for the scripts to run)."
