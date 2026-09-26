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

## Minecraft version

Built and tested against **Minecraft Bedrock v26 (the 1.26.x add-on format)**.
The item files use `"format_version": "1.26.10"`. If a future Minecraft update
changes the item format again and items stop appearing, that version string
(and the manifests' `min_engine_version`) is the first thing to update.

**Re-installing an update:** the pack version is bumped on each fix (see
`version` in `BP/manifest.json` / `RP/manifest.json`), so re-importing the new
`.mcaddon` upgrades it in place. If an old copy ever seems stuck, delete
"Family Mods" from the pack list on the iPad and import the fresh file.

## Roadmap

1. ✅ Obsidian Sword — custom item, damage/durability tuning, crafting recipe
2. 🧪 Rocket-Propelled Grenade — throwable launcher item (`familymods:rpg`)
   that fires a rocket entity (`familymods:rpg_rocket`) which explodes on
   impact. Kid-chosen settings: explosion power 9, breaks blocks, causes
   fire, rocket speed 13. Craft with 6 iron + 2 gunpowder + 1 blaze rod.
   The tunable numbers live in `BP/entities/rpg_rocket.json`
   (`minecraft:explode` power/breaks_blocks/causes_fire, and the projectile
   `power` = flight speed). Currently in testing.
3. Ideas for later: a custom block, a custom mob/pet, a small JavaScript
   script for something interactive.

## Chopper — a SEPARATE mod (its own pack)

The helicopter lives in its own pack under `chopper/` with its own UUIDs, so it
installs and updates independently of Family Mods (sword + RPG) and can't
disturb it.

- Build:  `./scripts/build_chopper.sh`  →  `dist/Chopper.mcaddon`
- Entity: `vehicles:chopper`; spawn-egg reads **"Chopper"** (sky blue, red spots)
- **Stage 1 (current):** rideable helicopter, spinning main + tail rotor, sky-blue
  body with a Minecraft-dog decal on both sides, landing skids. It rests on the
  ground — no flight yet.
- Stage 2 = movement/steering. Stage 3 = real up/down/forward flight (adds a
  little JavaScript via the Script API).

Files: `chopper/BP` (entity, rideable) and `chopper/RP` (model
`chopper.geo.json`, texture, rotor animation, spawn egg). The tunable rotor
speed is `animation_length` in `chopper/RP/animations/chopper.animation.json`.

## Unfun — a SEPARATE mod (its own pack)

A recreation of EightSidedSquare's **"Unfun"** joke mod, living in its own pack
under `unfun/` with its own UUIDs — completely independent of Family Mods and
the Chopper, so it installs and updates on its own and can't disturb them.

**The idea:** the moment you spawn, *everything is nerfed* — you move slow, dig
slow, and hit like a wet noodle. You earn your abilities back by grinding four
skill bars, always shown on screen above the hotbar:

| Bar | Fill it by… | Leveling it up does… |
|-----|-------------|----------------------|
| **Mining**   | breaking blocks (ores give more, leaves/grass give less) | eases **Mining Fatigue**, then grants **Haste** |
| **Building** | placing blocks | eases **Slowness**, then grants **Speed** |
| **Crafting** | crafting items | eases **Weakness**, then grants **Strength** |
| **Smelting** | smelting items in a furnace/blast furnace/smoker | grants **Resistance**, then **Regeneration** |

Each bar fills as you do that activity; fill it and the skill **levels up** (up
to Lv 15), its nerf eases, and past a few levels it flips into a real buff.

- Build:  `./scripts/build_unfun.sh`  →  `dist/Unfun.mcaddon`
- **Turn on scripts:** Unfun runs on the Script API, so in the world's settings
  the **"Additional Modding Capabilities" / Beta APIs** experiment must be ON
  (and both Unfun packs — Behavior + Resource — active for the world).
- **Chat commands** (type in chat): `!unfun help`, `!unfun reset` (start over),
  `!unfun max` (max every skill — handy for testing).

**How each bar is detected** (Bedrock only gives clean events for two of the
four, so the other two use reliable stand-ins — this is the first thing to look
at if a bar isn't filling):

- *Mining* and *Building* use the real `playerBreakBlock` / `playerPlaceBlock`
  events — exact.
- *Crafting* has no Bedrock event, so the script watches your inventory: when
  ingredients go **down** and a product appears **up** in the same instant,
  that's a craft. (It pauses briefly right after mining/placing so a fresh drop
  isn't mistaken for one.)
- *Smelting* has no event either, so the script remembers each furnace you open
  and watches its **output slot** — when the result count climbs, that many
  items just smelted.

**Tuning:** every fun number (XP per action, the leveling curve, and which
effects each skill grants at each level) lives in the `CONFIG` block at the top
of `unfun/BP/scripts/main.js`.

Files: `unfun/BP` (manifest + `scripts/main.js`) and `unfun/RP` (manifest +
pack icon). No custom items or textures — it's all script-driven.

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
