#!/usr/bin/env bash
# Packages BP/ and RP/ into a single .mcaddon file that Minecraft (iPad or any
# Bedrock device) can import in one tap.
#
# Usage:
#   ./scripts/build_mcpack.sh
#
# Output:
#   dist/FamilyMods.mcaddon   <-- AirDrop or copy this one file to the iPad

set -euo pipefail
cd "$(dirname "$0")/.."

mkdir -p dist
rm -f dist/FamilyMods_BP.mcpack dist/FamilyMods_RP.mcpack dist/FamilyMods.mcaddon

(cd BP && zip -r -q ../dist/FamilyMods_BP.mcpack .)
(cd RP && zip -r -q ../dist/FamilyMods_RP.mcpack .)
(cd dist && zip -q FamilyMods.mcaddon FamilyMods_BP.mcpack FamilyMods_RP.mcpack)

echo "Built dist/FamilyMods.mcaddon"
echo "Send that one file to the iPad (AirDrop, iCloud Drive, or Messages)"
echo "and tap it there - Minecraft will offer to import it."
