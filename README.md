# Family Mods (Minecraft Bedrock Add-On)

Custom items for Minecraft, built here and played on the iPad. This is a
**Bedrock Add-On**: a Behavior Pack (`BP/`, the rules/stats) plus a Resource
Pack (`RP/`, the textures/names), zipped up and imported into Minecraft.

## What's in it so far

- **Obsidian Sword** (`familymods:obsidian_sword`) — hits as hard as
  Sharpness 20, obsidian-purple blade, huge durability. Craft it with
  2 obsidian + 1 stick, same shape as a normal sword recipe.

## How to build it into something Minecraft can open

```
./scripts/build_mcpack.sh
```

This creates `dist/FamilyMods.mcaddon` — **one file** that contains both
packs.

## How to get it onto the iPad and into the world

1. Run the build script above (on the Mac).
2. Get `dist/FamilyMods.mcaddon` onto the iPad — AirDrop is easiest, or
   iCloud Drive / Messages / email also work.
3. On the iPad, tap the `.mcaddon` file. Minecraft should open and say it
   imported an add-on (it installs both packs automatically).
4. In Minecraft: **Play → create or edit a world → Behavior Packs / Resource
   Packs tabs → activate "Family Mods"** for that world.
5. Turn on cheats for that world too (Settings → Cheats → ON) — you don't
   *need* cheats to craft the sword, but it makes it easy to `/give` items
   while testing without needing the exact ingredients.
6. Load the world and either craft the sword normally, or (with cheats on)
   run: `/give @s familymods:obsidian_sword`

**Tip:** test in a spare/creative world first before adding the pack to his
main survival world, in case something needs tweaking.

## How to change something (e.g. make the sword hit even harder)

Open `BP/items/obsidian_sword.json` and change the number next to
`"minecraft:damage"`. Save, re-run the build script, re-send the
`.mcaddon` to the iPad, done. Every change is just editing a number or word
in one of these text files — no compiler, no install step beyond re-running
the script.

## Roadmap

1. ✅ Obsidian Sword — custom item, damage/durability tuning, crafting recipe
2. ⏭️ Rocket-propelled grenade — a throwable item that spawns an explosion.
   This one's a step up (needs a projectile entity + explosion behavior),
   next add-on to build.
3. Ideas for later: a custom block, a custom mob/pet, a small JavaScript
   script for something interactive.

## Project layout

```
BP/                        Behavior Pack — stats, recipes, rules
  manifest.json             pack identity (don't hand-edit the UUIDs)
  items/obsidian_sword.json item definition (damage, durability, etc.)
  recipes/obsidian_sword.json crafting recipe
  texts/en_US.lang           display name
RP/                        Resource Pack — how it looks
  manifest.json
  textures/items/obsidian_sword.png  16x16 icon (placeholder pixel art —
                                       redrawing this is a fun kid project)
  textures/item_texture.json         maps the item id to its texture file
  texts/en_US.lang
scripts/build_mcpack.sh    packages BP/ + RP/ into dist/FamilyMods.mcaddon
```
