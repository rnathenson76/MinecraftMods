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

## Monster Truck — another SEPARATE mod (its own pack)

The monster truck lives in its own pack under `car/` with its own UUIDs, so it
installs and updates independently of Family Mods (sword + RPG) and the Chopper,
and can't disturb either of them.

- Build:  `./scripts/build_car.sh`  →  `dist/MonsterTruck.mcaddon`
- Entity: `vehicles:monster_truck`; spawn egg reads **"Monster Truck"**
  (black with orange spots)
- Item:   `vehicles:monster_truck_kit` — a craftable "Monster Truck" you tap on
  the ground to place the truck, like a spawn egg

**Driving it:**

- Tap the truck to get in, then steer with the normal move joystick — it's
  faster than the fastest horse.
- **HOLD jump = NITRO** — a burst of speed with flames out the exhaust stacks.
- **TAP jump = HONK** the horn. (Sneak can't be the horn: on Bedrock the sneak
  button is what gets you *out* of a vehicle.)
- Drive into a 1-block step and it **climbs** it instead of stopping.
- It takes no fall damage, can't be shoved around, and drops iron / redstone /
  diamonds if something destroys it.

**Crafting it** (crafting table):

```
iron   iron    iron
wool   redstone  wool      wool = black wool (the tyres)
wool   iron blk  wool      redstone = a redstone BLOCK (the engine)
```

**The numbers you'd want to change** are all near the top of one file each:

- speed → `"minecraft:movement"` in `car/BP/entities/monster_truck.json`
- nitro strength, horn pitch, how high it climbs → the `---- Feel ----` block at
  the top of `car/BP/scripts/main.js`
- paint colours and the flame decals → `car/tools/make_textures.py` (re-run
  `./scripts/build_car.sh` and it redraws them for you)
- the shape itself → `car/RP/models/entity/monster_truck.geo.json`

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
scripts/build_chopper.sh   packages chopper/ into dist/Chopper.mcaddon
scripts/build_car.sh       packages car/ into dist/MonsterTruck.mcaddon
```
