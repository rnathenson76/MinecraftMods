#!/usr/bin/env bash
# Packages the SEPARATE Ruby mod (ruby/BP + ruby/RP) into its own .mcaddon —
# independent from Family Mods (the sword + RPG) and from Chopper.
#
# Usage:   ./scripts/build_ruby.sh
# Output:  dist/Ruby.mcaddon   <-- import this on the iPad

set -euo pipefail
cd "$(dirname "$0")/.."

mkdir -p dist
rm -f dist/Ruby_BP.mcpack dist/Ruby_RP.mcpack dist/Ruby.mcaddon

(cd ruby/BP && zip -r -q ../../dist/Ruby_BP.mcpack .)
(cd ruby/RP && zip -r -q ../../dist/Ruby_RP.mcpack .)
(cd dist && zip -q Ruby.mcaddon Ruby_BP.mcpack Ruby_RP.mcpack)

echo "Built dist/Ruby.mcaddon"
echo "This is a separate pack from Family Mods and Chopper — import it on its own."
