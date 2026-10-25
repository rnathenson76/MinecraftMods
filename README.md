# Minecraft Mods

Custom Minecraft Bedrock add-ons, built here on the computer and played on the
iPad. Each mod is a **Behavior Pack** (the rules and stats) plus a **Resource
Pack** (the textures and names), zipped into one `.mcaddon` file.

## The mods

Every mod is its **own separate pack** with its own UUIDs. They install,
update, and uninstall independently — adding one can never disturb another.

| Mod | What it is | File to install |
|---|---|---|
| **Family Mods** | Obsidian Sword, RPG launcher, Emerald Sword + armour | `dist/FamilyMods.mcaddon` |
| **Chopper** | Rideable, flyable helicopter | `dist/Chopper.mcaddon` |
| **Monster Truck** | Driveable truck — nitro, horn, climbs blocks | `dist/MonsterTruck.mcaddon` |
| **Ruby** | Ruby ore, gems, blocks, sword and pickaxe | `dist/Ruby.mcaddon` |
| **Squirrel** | Tameable squirrel that grows 15x and throws nuts | `dist/Squirrel.mcaddon` |
| **Unfun** | Everything nerfed — grind for every stat | `dist/Unfun.mcaddon` |
| **Carrier** | Water Blaster (aircraft carrier coming next) | `dist/Carrier.mcaddon` |

`lego/` isn't a Minecraft mod — it's a buildable LEGO squirrel with a rendered
instruction booklet and a parts list.

## Getting a mod onto the iPad

**The built `.mcaddon` files are committed to this repo, in `dist/`.** You
don't have to build anything to install one — they're ready to go, and the
iPad can download one straight from GitHub without touching the computer.

1. Get the `.mcaddon` onto the iPad — AirDrop is easiest; iCloud Drive,
   Messages or email work too. Or open this repo on GitHub on the iPad and
   download the file directly.
2. Tap the file. Minecraft opens and imports it (both packs at once).
3. In Minecraft: **Play → create or edit a world → Behavior Packs / Resource
   Packs tabs → activate the mod** for that world. **Activate it in both
   tabs** — a mod with only one half switched on is the usual reason a custom
   item or mob turns up invisible or missing.
4. Turn on cheats for that world while testing, so you can `/give` items and
   use spawn eggs without hunting for ingredients.

**Tip:** test in a spare creative world before adding a pack to a main
survival world.

## Building after you change something

```
./scripts/build_all.sh        # every mod, into dist/
./scripts/build_squirrel.sh   # or just one
```

`build_all.sh` runs `tools/check_packs.py` first, which makes sure every mod
still has UUIDs nothing else uses. That matters: if two packs share a UUID,
Minecraft treats them as the same pack and installing one silently replaces
the other, with no error to tell you.

Most changes are one number in one text file — no compiler, no install step
beyond re-running a build script. Each mod's section below says which number
does what.

**Re-installing an update:** bump `version` in that mod's `BP/manifest.json`
and `RP/manifest.json` so re-importing upgrades it in place. If an old copy
seems stuck, delete the pack on the iPad and import the fresh file.

## Minecraft version

Built against **Minecraft Bedrock v26 (the 1.26.x add-on format)**. If a
future update changes the format and items stop appearing, the
`format_version` strings and the manifests' `min_engine_version` are the first
things to update.

## Family Mods — the shared pack (`BP/` + `RP/`)

Three items share one pack here, because they were built before the
one-mod-one-pack habit settled in:

- **Obsidian Sword** (`familymods:obsidian_sword`) — hits as hard as
  Sharpness 20, obsidian-purple blade, huge durability. Craft with 2 obsidian
  + 1 stick. Damage is `"minecraft:damage"` in `BP/items/obsidian_sword.json`.
- **Rocket-Propelled Grenade** (`familymods:rpg`) — fires a rocket that
  explodes on impact. Explosion power 9, breaks blocks, causes fire, rocket
  speed 13. Craft with 6 iron + 2 gunpowder + 1 blaze rod. Tunables are in
  `BP/entities/rpg_rocket.json`.
- **Emerald Sword** — 20-heart hit, plus a Script-API swap: hold it and your
  armour turns to fully-enchanted emerald, put it away and your own armour
  comes back. The swap logic is in `BP/scripts/main.js`; the green look is
  drawn by `scripts/gen_emerald_textures.py`.
  - **Heads-up on the shield:** only the *real* vanilla shield can do the
    block-the-hit crouch. The Emerald Shield is cosmetic — it looks the part
    in the off-hand but adds no blocking move.

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

**Seeing a change without loading Minecraft:**

```
python3 car/tools/render_preview.py    ->  dist/monster_truck_preview.png
```

That draws the truck from the real model and texture files (three angles). It's
handy after editing the shape — and it catches a mistake that's easy to make:
if two parts share an exact face plane, the preview shows a flickery
checkerboard there, and that same overlap flickers in the game too.

**The numbers you'd want to change** are all near the top of one file each:

- speed → `"minecraft:movement"` in `car/BP/entities/monster_truck.json`
- nitro strength, horn pitch, how high it climbs → the `---- Feel ----` block at
  the top of `car/BP/scripts/main.js`
- paint colours and the flame decals → `car/tools/make_textures.py` (re-run
  `./scripts/build_car.sh` and it redraws them for you)
- the shape itself → `car/RP/models/entity/monster_truck.geo.json`
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
BP/  RP/            Family Mods — obsidian sword, RPG, emerald sword + armour
chopper/            SEPARATE mod — the helicopter   (own BP/ + RP/ + UUIDs)
car/                SEPARATE mod — the monster truck
ruby/               SEPARATE mod — ruby ore, gems, blocks, tools
squirrel/           SEPARATE mod — the transforming squirrel
unfun/              SEPARATE mod — everything nerfed
lego/               NOT a Minecraft mod — a buildable LEGO squirrel, with a
                      rendered instruction booklet and parts list

dist/               the built .mcaddon files. These ARE committed, so the iPad
                      can download one straight from GitHub without the
                      computer. Re-run a build script after any change and
                      commit the .mcaddon it produces.

scripts/build_all.sh       every mod, into dist/
scripts/build_mcpack.sh    BP/ + RP/        -> dist/FamilyMods.mcaddon
scripts/build_chopper.sh   chopper/         -> dist/Chopper.mcaddon
scripts/build_car.sh       car/             -> dist/MonsterTruck.mcaddon
scripts/build_ruby.sh      ruby/            -> dist/Ruby.mcaddon
scripts/build_squirrel.sh  squirrel/        -> dist/Squirrel.mcaddon
scripts/build_unfun.sh     unfun/           -> dist/Unfun.mcaddon

tools/check_packs.py       every mod still has its own UUIDs (run by build_all)
tools/check_squirrel.py    the squirrel pack's files all agree with each other
tools/squirrel_model.py    generates the squirrel models, textures and previewer
tools/squirrel_viewer.html open in a browser to look at the squirrel models
car/tools/render_preview.py draws the monster truck without loading Minecraft
```

## Carrier — a SEPARATE mod (its own pack)

Adam's aircraft carrier: a huge ship you place on the ocean and walk all over,
with water guns and a petting zoo. It's being built in phases, and each one
gets tested on the iPad before the next starts. Its ids use the `carrier:`
namespace.

- Build:  `./scripts/build_carrier.sh`  →  `dist/Carrier.mcaddon`
- **Phase 1 (current): the Water Blaster** (`carrier:water_blaster`)
- Next: the ship + Carrier Kit, deck water cannons, then the petting zoo.

**Water Blaster.** Use it to fire water shots. They hurt mobs (2 hearts),
knock them back and splash. They put out burning mobs and fire blocks where
they land, and blazes, endermen and snow golems take extra damage. The
durability bar is the water tank: each shot uses a little, and when it runs
dry you look at water close by and use the blaster to refill it.

It's in the creative inventory under Equipment, or with cheats on:

```
/give @s carrier:water_blaster
```

**Knobs you can turn**

- How hard a shot hits — `"damage"` in `carrier/BP/entities/water_shot.json`
- How many shots a full tank holds — `"max_durability"` in
  `carrier/BP/items/water_blaster.json`
- Shot speed, spray, fire rate, refill reach and the water-hater bonus — the
  `Feel` block at the top of `carrier/BP/scripts/main.js`
- Colours of the icon, the water shot and the pack icon —
  `carrier/tools/make_textures.py`
