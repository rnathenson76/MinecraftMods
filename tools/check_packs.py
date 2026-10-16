#!/usr/bin/env python3
"""
Checks that every mod in this repo is still its OWN separate pack.

Each mod has to have UUIDs nothing else uses. If two packs share one,
Minecraft treats them as the same pack — installing one silently replaces
the other, and there's no error message to tell you that's what happened.
Easy to cause by copying a manifest from another mod as a starting point.

  python3 tools/check_packs.py
"""

import collections, json, os, sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
mods, seen = collections.defaultdict(dict), collections.defaultdict(list)
problems = []

for dirpath, dirs, names in os.walk(HERE):
    dirs[:] = [d for d in dirs if d not in (".git", "dist", "__pycache__")]
    if "manifest.json" not in names:
        continue
    path = os.path.join(dirpath, "manifest.json")
    rel = os.path.relpath(path, HERE)
    try:
        m = json.load(open(path))
    except json.JSONDecodeError as e:
        problems.append(f"{rel} is not valid JSON: line {e.lineno}, {e.msg}")
        continue
    parts = rel.split(os.sep)
    mod = "Family Mods" if len(parts) == 2 else parts[0]
    mods[mod][parts[-2]] = (rel, m)
    for label, uuid in ([("header", m["header"]["uuid"])] +
                        [(f"module {i}", x["uuid"]) for i, x in enumerate(m.get("modules", []))]):
        seen[uuid].append(f"{mod}/{parts[-2]} {label}")

print(f"{'mod':16s} {'pack':5s} {'version':9s} name")
print("-" * 64)
for mod in sorted(mods):
    for kind in sorted(mods[mod]):
        rel, m = mods[mod][kind]
        h = m["header"]
        print(f"{mod:16s} {kind:5s} {'.'.join(map(str, h['version'])):9s} {h['name']}")

    # a behaviour pack has to point at its own resource pack, not another mod's
    if "BP" in mods[mod] and "RP" in mods[mod]:
        bp, rp = mods[mod]["BP"][1], mods[mod]["RP"][1]
        deps = [d.get("uuid") for d in bp.get("dependencies", []) if "uuid" in d]
        if deps and rp["header"]["uuid"] not in deps:
            problems.append(f"{mod}: the behaviour pack's dependency doesn't point at "
                            f"{mod}'s own resource pack")

for uuid, where in seen.items():
    if len(where) > 1:
        problems.append("UUID " + uuid + " is shared by: " + ", ".join(where)
                        + " — these packs would overwrite each other in Minecraft")

print()
if problems:
    print(f"{len(problems)} problem(s):\n")
    for p in problems:
        print("  x " + p)
    sys.exit(1)
print(f"OK: {len(mods)} mods, {len(seen)} UUIDs, all unique — every mod is its own pack.")
