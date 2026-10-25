#!/usr/bin/env bash
# Packages the SEPARATE Carrier mod (carrier/BP + carrier/RP) into its own
# .mcaddon — independent from every other mod.
#
# Usage:   ./scripts/build_carrier.sh
# Output:  dist/Carrier.mcaddon   <-- import this on the iPad

set -euo pipefail
cd "$(dirname "$0")/.."

# redraw the textures from carrier/tools/make_textures.py if python is around
if command -v python3 >/dev/null 2>&1; then
  python3 carrier/tools/make_textures.py >/dev/null
fi

mkdir -p dist
rm -f dist/Carrier_BP.mcpack dist/Carrier_RP.mcpack dist/Carrier.mcaddon

(cd carrier/BP && zip -r -q ../../dist/Carrier_BP.mcpack .)
(cd carrier/RP && zip -r -q ../../dist/Carrier_RP.mcpack .)
(cd dist && zip -q Carrier.mcaddon Carrier_BP.mcpack Carrier_RP.mcpack)

echo "Built dist/Carrier.mcaddon"
echo "This is a separate pack from every other mod — import it on its own."
