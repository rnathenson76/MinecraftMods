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
3. Ideas for later: a custom mob/pet, a small JavaScript script for
   something interactive. (The "custom block" idea grew into the Ruby mod,
   which lives in its own pack — see below.)

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

## Ruby — another SEPARATE mod (its own pack)

Ruby lives in its own pack under `ruby/` with its own UUIDs, so it installs and
updates independently of Family Mods (sword + RPG) and Chopper, and can't
disturb either one. Its ids use the `gems:` namespace.

- Build:  `./scripts/build_ruby.sh`  →  `dist/Ruby.mcaddon`

**Finding it.** Ruby Ore generates on its own in any Overworld biome,
underground between about **y = -48 and y = 24** — so it turns up around the
same depths as iron and gold. Below y = 0 it appears as **Deepslate Ruby
Ore**, the same way vanilla ores do. Both drop **1-2 rubies** when you break
them, and both can be smelted into a ruby in a furnace or blast furnace.

It only shows up in **newly generated chunks**, so go exploring somewhere you
have never been (or start a new world) — the caves you have already loaded
will not suddenly have ruby in them.

Mining it needs a pickaxe, and it is set to the same tier as diamond ore, so
an **iron pickaxe or better** is the tool for it.

**Making things out of it.**

| What you get | How to craft it |
| --- | --- |
| Block of Ruby | 9 rubies filling the whole 3x3 crafting grid |
| 9 rubies back | 1 Block of Ruby on its own in the grid |
| Ruby Sword | 2 rubies stacked + 1 stick (normal sword shape) |
| Ruby Pickaxe | 3 rubies across the top + 2 sticks down the middle |

The Ruby Sword and Ruby Pickaxe sit between diamond and netherite: 9 damage
on the sword, 1800 durability, and you repair either one with more rubies on
an anvil.

**Testing it quickly** (with cheats on):

```
/give @s gems:ruby 64
/give @s gems:ruby_pickaxe
/setblock ~ ~ ~1 gems:ruby_ore
```

**Knobs you can turn**

- How much ruby the world has — `ruby/BP/feature_rules/ruby_ore_feature_rule.json`:
  `iterations` is how many attempts per chunk (higher = more ruby), and the
  `y` `extent` is the depth range. `count` in
  `ruby/BP/features/ruby_ore_feature.json` is how many blocks are in each vein.
- How many rubies a block drops — the `min`/`max` in
  `ruby/BP/loot_tables/blocks/ruby_ore.json`.
- Sword damage / tool durability — `ruby/BP/items/ruby_sword.json` and
  `ruby/BP/items/ruby_pickaxe.json`.

One difference from vanilla ore worth knowing: the ore drops its rubies no
matter what you break it with, including your bare hand (breaking it by hand
is just very slow). Custom blocks in Bedrock cannot easily require the right
tool for the drop, so this is the simple, always-works version.

Files: `ruby/BP` (blocks, items, recipes, loot tables, ore generation) and
`ruby/RP` (block + item textures, the two texture atlases, names).

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
chopper/                   SEPARATE mod — the helicopter (own BP/ + RP/ + UUIDs)
ruby/                      SEPARATE mod — ruby ore/gem/blocks (own BP/ + RP/ + UUIDs)
scripts/build_mcpack.sh    packages BP/ + RP/ into dist/FamilyMods.mcaddon
scripts/build_chopper.sh   packages chopper/ into dist/Chopper.mcaddon
scripts/build_ruby.sh      packages ruby/ into dist/Ruby.mcaddon
```
