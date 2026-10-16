#!/usr/bin/env python3
"""
Checks the Squirrel add-on for the mistakes Minecraft won't tell you about.

A typo in an identifier or a missing texture doesn't produce an error in
Minecraft — the mob just turns up invisible, or doesn't turn up at all, and
you're left guessing. This reads every file and makes sure they agree.

  python3 tools/check_squirrel.py
"""

import json, os, sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BP, RP = os.path.join(HERE, "squirrel", "BP"), os.path.join(HERE, "squirrel", "RP")
problems = []


def fail(msg):
    problems.append(msg)


def load(path):
    try:
        with open(path) as fh:
            return json.load(fh)
    except FileNotFoundError:
        fail(f"missing file: {os.path.relpath(path, HERE)}")
    except json.JSONDecodeError as e:
        fail(f"{os.path.relpath(path, HERE)} is not valid JSON: line {e.lineno}, {e.msg}")
    return None


def walk(root, sub):
    d = os.path.join(root, sub)
    for dirpath, _, names in os.walk(d):
        for n in sorted(names):
            if n.endswith(".json"):
                yield os.path.join(dirpath, n)


# ---- every json file parses -------------------------------------------
for root in (BP, RP):
    for dirpath, _, names in os.walk(root):
        for n in names:
            if n.endswith(".json"):
                load(os.path.join(dirpath, n))

# ---- manifests point at each other ------------------------------------
bp_man, rp_man = load(os.path.join(BP, "manifest.json")), load(os.path.join(RP, "manifest.json"))
if bp_man and rp_man:
    deps = [d.get("uuid") for d in bp_man.get("dependencies", [])]
    if rp_man["header"]["uuid"] not in deps:
        fail("the behaviour pack's dependency UUID doesn't match the resource pack's header UUID")
    seen = {}
    for label, man in (("BP", bp_man), ("RP", rp_man)):
        for uid in [man["header"]["uuid"]] + [m["uuid"] for m in man["modules"]]:
            if uid in seen:
                fail(f"UUID {uid} is used twice ({seen[uid]} and {label}) — every one must be unique")
            seen[uid] = label

# ---- collect what each side defines -----------------------------------
bp_entities, shooters = {}, []
for path in walk(BP, "entities"):
    d = load(path)
    if not d:
        continue
    ent = d["minecraft:entity"]
    bp_entities[ent["description"]["identifier"]] = path
    groups = list(ent.get("component_groups", {}).values()) + [ent.get("components", {})]
    for g in groups:
        if "minecraft:shooter" in g:
            shooters.append((g["minecraft:shooter"]["def"], path))

geometries = set()
for path in walk(RP, "models"):
    d = load(path)
    for g in (d or {}).get("minecraft:geometry", []):
        geometries.add(g["description"]["identifier"])

controllers = set()
for path in walk(RP, "render_controllers"):
    controllers.update((load(path) or {}).get("render_controllers", {}))

anims = set()
for path in walk(RP, "animations"):
    anims.update((load(path) or {}).get("animations", {}))
for path in walk(RP, "animation_controllers"):
    anims.update((load(path) or {}).get("animation_controllers", {}))

sounds = set((load(os.path.join(RP, "sounds", "sound_definitions.json")) or {})
             .get("sound_definitions", {}))

# ---- the resource pack agrees with the behaviour pack ------------------
rp_entities = set()
for path in walk(RP, "entity"):
    d = load(path)
    if not d:
        continue
    desc = d["minecraft:client_entity"]["description"]
    ident = desc["identifier"]
    rp_entities.add(ident)
    rel = os.path.relpath(path, HERE)

    if ident not in bp_entities:
        fail(f"{rel} describes '{ident}' but no behaviour pack entity has that identifier")

    for key, geo in desc.get("geometry", {}).items():
        if geo not in geometries:
            fail(f"{rel}: geometry '{geo}' isn't defined in any .geo.json")

    for key, tex in desc.get("textures", {}).items():
        if not os.path.exists(os.path.join(RP, tex + ".png")):
            fail(f"{rel}: texture '{tex}.png' doesn't exist")

    for c in desc.get("render_controllers", []):
        name = c if isinstance(c, str) else list(c)[0]
        if name.startswith("controller.render.") and name != "controller.render.default" \
           and name not in controllers:
            fail(f"{rel}: render controller '{name}' isn't defined")

    for key, a in desc.get("animations", {}).items():
        if a not in anims:
            fail(f"{rel}: animation '{a}' isn't defined")
    for short in desc.get("scripts", {}).get("animate", []):
        names = [short] if isinstance(short, str) else list(short)
        for n in names:
            if n not in desc.get("animations", {}):
                fail(f"{rel}: scripts/animate runs '{n}', which isn't in this entity's animations list")

for ident, path in bp_entities.items():
    if ident not in rp_entities:
        fail(f"{os.path.relpath(path, HERE)}: '{ident}' has no resource pack entry — it will be invisible")

for ident, path in shooters:
    if ident not in bp_entities:
        fail(f"{os.path.relpath(path, HERE)}: shoots '{ident}', which isn't defined anywhere")

# ---- sound effects referenced by animations exist ----------------------
for path in walk(RP, "animations"):
    for name, a in ((load(path) or {}).get("animations", {})).items():
        for t, ev in (a.get("sound_effects") or {}).items():
            eff = ev.get("effect")
            if eff and eff.startswith("squirrel.") and eff not in sounds:
                fail(f"animation '{name}' plays '{eff}', which isn't in sound_definitions.json")

# ---- spawn rules line up ----------------------------------------------
for path in walk(BP, "spawn_rules"):
    d = load(path)
    ident = (d or {})["minecraft:spawn_rules"]["description"]["identifier"]
    if ident not in bp_entities:
        fail(f"{os.path.relpath(path, HERE)}: spawn rules for '{ident}', which isn't an entity here")

# ---- report ------------------------------------------------------------
if problems:
    print(f"{len(problems)} problem(s) found:\n")
    for p in problems:
        print("  x " + p)
    sys.exit(1)
print(f"Squirrel add-on looks consistent "
      f"({len(bp_entities)} entities, {len(geometries)} models, {len(sounds)} sounds).")
