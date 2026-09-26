# Squirrel Power Suit (LEGO)

The Minecraft squirrel from the squirrel mod (branch `claude/optimistic-pascal-67pxxb`,
`tools/squirrel_model.py`) turned into two real LEGO builds:

| | Scrawny squirrel | Buff squirrel |
|---|---|---|
| Scale | 1 stud per Minecraft unit | 2 studs per Minecraft unit |
| Parts | ~112 | ~2,000 |
| Size | 4 studs wide, ~4.5 in tall with tail up | ~14 in tall, ~6 lb |
| Moves | tail clicks up/back | arms click out sideways (0–90°), tail clicks back |

The buff squirrel is hollow and splits at the chest. The scrawny squirrel stands in
the bottom half with his tail clicked straight up; the top half drops on as a lid,
held by four 2x2 stud patches (the rest of the rim is tiled so it lifts off easily).

## Files

- `booklet/index.html` – the instruction booklet (steps, parts callouts, parts lists).
- `models/scrawny_squirrel.mpd`, `models/buff_squirrel.mpd` – LDraw models with build
  steps. Open in BrickLink Studio or LDCad. Parts drawn Light Bluish Gray are hidden
  inside and can be any colour.
- `bricklink/*_wanted.xml` – BrickLink wanted lists (hidden parts have no colour set).
- `tools/squirrel_lego.py` – the designer: scales the Minecraft boxes onto a stud/plate
  grid, paints the outside from the texture rules (belly, eyes, nose, muscle lines),
  places the click hinges, fills each layer with common bricks/plates/tiles (trying many
  layouts per layer and keeping the one whose seams overlap best), then checks that every
  part is connected, the arms and tails clear the body across their range, and that the
  buff squirrel's centre of mass is over his feet.
- `tools/render/` – renders every booklet picture with three.js' LDrawLoader in headless
  Chromium.
- `tools/make_booklet.py` – assembles the booklet HTML.

## Rebuilding

```sh
python3 lego/tools/squirrel_lego.py          # design + models + steps.json
# ROOT needs node_modules/three (npm install three) and lib/ = the LDraw parts
# library (https://library.ldraw.org, parts/ and p/ folders)
ROOT=/path/to/root node lego/tools/render/render.mjs
python3 lego/tools/make_booklet.py
```

## Design notes

- LEGO bricks are 1.2 studs tall, so heights are scaled at 2.5 plates per stud to keep
  the Minecraft proportions. Odd widths round toward the middle so left and right match.
- Changes from the Minecraft model: the arms sit 1 stud out from the chest to make room
  for the shoulder hinges, the shoulder hinge is at the top of the arm (so the arm can
  swing up without hitting the chest), tails sit 1 stud back for their hinges, and the
  buff squirrel got big feet. Without them his chest and head tip him onto his face.
- The buff arms and tail are 85% of Minecraft size, shrunk toward their joints. That
  roughly halves the load on the click hinges (arm ~295 g, tail ~350 g). Arms keep
  2-stud hollow walls (they get grabbed); the tail has 1-stud walls.
- The power-suit fit was found by searching every position, rotation and tail angle of
  the scrawny squirrel against the buff body with walls at least 1 stud thick. At the
  11 in size (1.5 studs/unit) the scrawny squirrel only fit if shrunk to 3 studs wide, so
  the buff squirrel was scaled up to 2 studs/unit instead.
- Only parts LEGO currently makes are used. Visible surfaces stick to sizes that are
  common in each colour; Medium Nougat (the tail) is the scarcest colour.
