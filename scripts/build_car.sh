#!/usr/bin/env bash
# Packages the SEPARATE Monster Truck mod (car/BP + car/RP) into its own
# .mcaddon — independent from Family Mods (sword + RPG) and from the Chopper.
#
# Usage:   ./scripts/build_car.sh
# Output:  dist/MonsterTruck.mcaddon   <-- import this on the iPad

set -euo pipefail
cd "$(dirname "$0")/.."

# redraw the textures from car/tools/make_textures.py if python is around
if command -v python3 >/dev/null 2>&1; then
  python3 car/tools/make_textures.py >/dev/null
fi

mkdir -p dist
rm -f dist/MonsterTruck_BP.mcpack dist/MonsterTruck_RP.mcpack dist/MonsterTruck.mcaddon

(cd car/BP && zip -r -q ../../dist/MonsterTruck_BP.mcpack .)
(cd car/RP && zip -r -q ../../dist/MonsterTruck_RP.mcpack .)
(cd dist && zip -q MonsterTruck.mcaddon MonsterTruck_BP.mcpack MonsterTruck_RP.mcpack)

echo "Built dist/MonsterTruck.mcaddon"
echo "This is a separate pack from Family Mods and the Chopper — import it on its own."
