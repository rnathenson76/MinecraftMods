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

## Squirrel — a SEPARATE mod (its own pack)

A tameable squirrel that **grows 15x and throws nuts** when a monster gets
close. Its own pack under `squirrel/` with its own UUIDs, so it installs and
updates independently of Family Mods and the Chopper.

- Build:  `./scripts/build_squirrel.sh`  →  `dist/Squirrel.mcaddon`
- Entity: `pets:squirrel`; projectile `pets:nut`; spawn egg reads **"Squirrel"**
- **Where do you find one?** In the woods — oak/birch forests and taigas, on
  grass, in daylight, in groups of 1–3. Only in chunks you haven't visited yet;
  already-generated terrain won't grow squirrels. Or use the spawn egg.
- **Taming:** feed it wheat seeds (1 in 3 chance, like a wolf). A tamed squirrel
  follows you and sits when you tap it. Feed it seeds again to heal it.

### How the transformation works

No JavaScript — it's all component groups, the same mechanism a baby zombie
uses to grow up. The squirrel carries two of them and swaps between them:

| | `pets:small` | `pets:giant` |
|---|---|---|
| Looks like | scrawny model | buff model |
| Height | 0.5 blocks | **7.5 blocks** |
| Collision box | 0.5 × 0.5 | 1.5 × 2.0 |
| Can attack | no | nuts + a melee swipe |

`minecraft:target_nearby_sensor` does the switching: a monster inside **8
blocks** fires `pets:go_giant`, and once everything is past **12 blocks** it
fires `pets:go_small`. The two different distances stop it flickering between
sizes when a mob paces the boundary.

The giant form looks 15x bigger but only *occupies* 1.5 × 2 blocks, which is
why a 7½-block squirrel still fits through the world instead of suffocating in
caves. That gap is deliberate — `minecraft:scale` is visual, `collision_box` is
physical, and they're set separately.

Wild squirrels transform too, so the forest is genuinely dangerous.

### Tuning it

Everything is one number in `squirrel/BP/entities/squirrel.json`:

| What | Where |
|---|---|
| How close a monster has to get | `target_nearby_sensor` → `inside_range` |
| How far before he shrinks | `target_nearby_sensor` → `outside_range` |
| Melee swipe damage | `pets:giant` → `minecraft:attack` → `damage` |
| How tough he is | `minecraft:health` (100) |
| Damage resistance when giant | `pets:giant` → `damage_sensor` → `damage_multiplier` |
| How fast he throws | `behavior.ranged_attack` → `attack_interval_min/max` |
| Nut damage / speed | `squirrel/BP/entities/nut.json` → `impact_damage`, `power` |

Which monsters set him off is the filter list in
`behavior.nearest_attackable_target` — currently the `monster` family plus
piglins and hoglins, so cows, villagers and iron golems are safe.

### The models

Both squirrels are generated, not hand-edited:

```
python3 tools/squirrel_model.py     # models + textures + the previewer
python3 tools/check_squirrel.py     # catches typos Minecraft won't report
```

`tools/squirrel_model.py` describes both squirrels as a list of boxes near the
top of the file (16 units = 1 block). Change a number, re-run, and the
geometry, both textures and the previewer are all rebuilt together.

**`tools/squirrel_viewer.html` — open this in a browser on the computer.** Drag
to turn either squirrel, toggle **True scale** to see the 15x next to a player
silhouette, and **Hitbox** to see the collision box. Much faster than building
an `.mcaddon` and loading it on the iPad to look at a model.

`tools/check_squirrel.py` cross-checks every identifier, texture path, geometry
name, animation and sound reference between the two packs. A typo in an
add-on doesn't produce an error in Minecraft — the mob just turns up invisible
or not at all — so this runs automatically as part of the build.


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
