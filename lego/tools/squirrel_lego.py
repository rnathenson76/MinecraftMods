#!/usr/bin/env python3
"""
Turns the Minecraft squirrel (tools/squirrel_model.py on the squirrel branch)
into two real LEGO builds: the scrawny squirrel and the buff squirrel.

How it works
  1. The Minecraft boxes are scaled onto a LEGO grid.
       x, z : 1 cell = 1 stud   (8 mm)
       y    : 1 cell = 1 plate  (3.2 mm, a brick is 3 plates)
  2. Every cell on the outside gets the colour the Minecraft texture paints
     there (fur, belly, eyes, nose, muscle creases...). Cells hidden inside
     are "any colour" -- use whatever you have.
  3. The joints (click hinges for tails and arms) are placed first.
  4. Each layer is filled with bricks, plates and tiles. The filler tries lots
     of layouts per layer and keeps the one whose seams overlap the layer below
     best, so the model holds together.
  5. Checks: every part connects to the rest of its sub-model, the posable
     parts don't hit the body, and the model stands up (centre of mass).
  6. Writes LDraw files (open in BrickLink Studio / LDCad), a BrickLink wanted
     list, and steps.json for the instruction booklet renderer.

  python3 lego/tools/squirrel_lego.py
"""

import collections, json, math, os, random, sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # lego/

# ======================================================== Minecraft source
# Copied from tools/squirrel_model.py (branch claude/optimistic-pascal-67pxxb).
# (bone, pivot, rotation, [(box, origin, size, colour, belly_colour)])
SCRAWNY_MC = [
    ("body", [0, 4, 0], None, [("torso", [-2, 3, -4], [4, 4, 8], "fur", "belly")]),
    ("legs", [0, 0, 0], None, [
        ("leg_bl", [-2, 0, 2], [1, 3, 1], "fur", None), ("leg_br", [1, 0, 2], [1, 3, 1], "fur", None),
        ("leg_fl", [-2, 0, -3], [1, 3, 1], "fur", None), ("leg_fr", [1, 0, -3], [1, 3, 1], "fur", None)]),
    ("head", [0, 7, -4], None, [
        ("head", [-2, 6, -8], [4, 4, 4], "fur", None), ("snout", [-1, 6, -9], [2, 2, 1], "snout", None),
        ("ear_l", [-2, 10, -7], [1, 2, 1], "fur", None), ("ear_r", [1, 10, -7], [1, 2, 1], "fur", None)]),
    ("tail", [0, 5, 4], [-22, 0, 0], [
        ("tail_lo", [-1, 5, 4], [2, 5, 2], "tail", "tail_lt"), ("tail_up", [-2, 9, 3], [4, 6, 3], "tail", "tail_lt")]),
]
BUFF_MC = [
    ("body", [0, 10, 0], None, [
        ("chest", [-5, 8, -5], [10, 7, 9], "fur", "belly"), ("traps", [-4, 15, -3], [8, 2, 5], "fur", None),
        ("waist", [-3, 5, -2], [6, 4, 6], "fur", "belly")]),
    ("arm_l", [-5, 13, 0], [0, 0, -11], [
        ("delt_l", [-9, 10, -4], [4, 5, 7], "fur", None), ("bicep_l", [-9, 5, -3], [4, 6, 5], "fur", None),
        ("fore_l", [-10, 1, -3], [4, 5, 5], "fur", None)]),
    ("arm_r", [5, 13, 0], [0, 0, 11], [
        ("delt_r", [5, 10, -4], [4, 5, 7], "fur", None), ("bicep_r", [5, 5, -3], [4, 6, 5], "fur", None),
        ("fore_r", [6, 1, -3], [4, 5, 5], "fur", None)]),
    ("legs", [0, 0, 0], None, [
        ("thigh_l", [-4, 2, 0], [4, 4, 5], "fur", None), ("thigh_r", [0, 2, 0], [4, 4, 5], "fur", None),
        ("calf_l", [-4, 0, 1], [3, 3, 4], "fur", None), ("calf_r", [1, 0, 1], [3, 3, 4], "fur", None)]),
    ("head", [0, 15, -5], None, [
        ("head", [-3, 14, -9], [6, 5, 5], "fur", None), ("snout", [-1, 14, -10], [2, 2, 1], "snout", None),
        ("ear_l", [-3, 19, -7], [2, 3, 1], "fur", None), ("ear_r", [1, 19, -7], [2, 3, 1], "fur", None)]),
    ("tail", [0, 9, 5], [-28, 0, 0], [
        ("tail_lo", [-2, 9, 4], [4, 7, 4], "tail", "tail_lt"), ("tail_up", [-4, 15, 3], [8, 8, 6], "tail", "tail_lt")]),
]
MUSCLE_SPLIT = {"chest", "waist"}
MUSCLE_BULGE = {"bicep_l", "bicep_r", "delt_l", "delt_r", "thigh_l", "thigh_r"}

# ================================================================ colours
# Minecraft colour name -> LDraw colour code
MC2LEGO = {"fur": 70, "fur_dk": 308, "belly": 19, "tail": 84, "tail_lt": 19,
           "snout": 19, "eye": 0, "eye_lit": 15, "nose": 308}
ANY = -1          # hidden inside: any colour will do (drawn light bluish grey)
COLORS = {        # ldraw: (name, hex, bricklink id)
    70: ("Reddish Brown", "#582A12", 88), 308: ("Dark Brown", "#352100", 120),
    19: ("Tan", "#E4CD9E", 2), 84: ("Medium Nougat", "#AA7D55", 150),
    0: ("Black", "#1B2A34", 11), 15: ("White", "#FFFFFF", 1),
    71: ("Light Bluish Gray", "#A0A5A9", 86), 72: ("Dark Bluish Gray", "#6C6E68", 85),
    ANY: ("Any colour (hidden)", "#A0A5A9", None),
}
RENDER_ANY = 71

# ================================================================== parts
# key: (ldraw id, bricklink id, name, x-length, z-width, height in plates, kind)
# All in current LEGO production; hidden parts may be any colour.
PARTS = {}
def _p(ld, bl, name, w, d, h, kind):
    PARTS[ld] = dict(ld=ld, bl=bl, name=name, w=w, d=d, h=h, kind=kind)
for ld, w, d in [("3005", 1, 1), ("3004", 2, 1), ("3622", 3, 1), ("3010", 4, 1), ("3009", 6, 1),
                 ("3008", 8, 1), ("3003", 2, 2), ("3002", 3, 2), ("3001", 4, 2), ("2456", 6, 2)]:
    _p(ld, ld, f"Brick {d} x {w}", w, d, 3, "brick")
for ld, w, d in [("3024", 1, 1), ("3023", 2, 1), ("3623", 3, 1), ("3710", 4, 1), ("3666", 6, 1),
                 ("3460", 8, 1), ("3022", 2, 2), ("3021", 3, 2), ("3020", 4, 2), ("3795", 6, 2),
                 ("3034", 8, 2), ("3031", 4, 4), ("3032", 6, 4), ("3035", 8, 4)]:
    _p(ld, ld, f"Plate {d} x {w}", w, d, 1, "plate")
for ld, bl, w, d in [("3070b", "3070b", 1, 1), ("3069b", "3069b", 2, 1), ("63864", "63864", 3, 1),
                     ("2431", "2431", 4, 1), ("6636", "6636", 6, 1), ("3068b", "3068b", 2, 2)]:
    _p(ld, bl, f"Tile {d} x {w}", w, d, 1, "tile")
_p("44301", "44301b", "Hinge Plate 1 x 2 Locking, 1 Finger on End", 2, 1, 1, "hinge")
_p("44302", "44302b", "Hinge Plate 1 x 2 Locking, 2 Fingers on End", 2, 1, 1, "hinge")
_p("30364", "30364", "Hinge Brick 1 x 2 Locking, 1 Finger Vertical End", 2, 1, 3, "hinge")
_p("30365", "30365", "Hinge Brick 1 x 2 Locking, 2 Fingers Vertical End", 2, 1, 3, "hinge")

# Which (part, colour) combos to use for visible surfaces. Conservative on
# purpose: sizes that LEGO makes (and has recently made) in each colour.
COMMON = {"3005", "3004", "3622", "3010", "3003", "3001", "3024", "3023", "3710", "3666",
          "3022", "3021", "3020", "3795", "3070b", "3069b", "2431", "3068b"}
AVAIL = {
    70: COMMON | {"3009", "3008", "3002", "2456", "3623", "3460", "3034", "3031", "3032", "63864", "6636"},
    19: COMMON | {"3009", "3008", "3002", "2456", "3623", "3460", "3034", "3031", "3032", "63864", "6636"},
    308: COMMON - {"3622"},
    84: {"3005", "3004", "3010", "3003", "3001", "3024", "3023", "3710", "3666", "3022", "3021",
         "3020", "3070b", "3069b", "2431", "3068b"},
    0: set(PARTS), 15: set(PARTS), ANY: set(PARTS),
}
BRICKS = [k for k, p in PARTS.items() if p["kind"] == "brick"]
PLATES = [k for k, p in PARTS.items() if p["kind"] == "plate"]
TILES = [k for k, p in PARTS.items() if p["kind"] == "tile"]

LDU_STUD, LDU_PLATE = 20, 8
ROT_Y90 = [[0, 0, 1], [0, 1, 0], [-1, 0, 0]]
ID = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
ROT_Y180 = [[-1, 0, 0], [0, 1, 0], [0, 0, -1]]
FINGER_PZ = [[0, 0, -1], [0, 1, 0], [1, 0, 0]]    # part +X -> world +Z
FINGER_MZ = [[0, 0, 1], [0, 1, 0], [-1, 0, 0]]    # part +X -> world -Z


# ================================================================== grid
def edge(v, s, sym=False):
    """Scale a Minecraft coordinate onto the grid. x is rounded half towards 0
    so left and right stay mirror images; y/z round half up."""
    x = v * s
    if sym and abs(abs(x) % 1 - 0.5) < 1e-9:
        return int(math.copysign(math.floor(abs(x)), x))
    return math.floor(x + 0.5 + 1e-9)


class Box:
    def __init__(self, name, o, sz, col, belly, H, V, dx=0, dy=0, dz=0):
        self.name, self.col, self.belly, self.mc = name, col, belly, sz
        self.x0, self.x1 = edge(o[0], H, True) + dx, edge(o[0] + sz[0], H, True) + dx
        self.y0, self.y1 = edge(o[1], V) + dy, edge(o[1] + sz[1], V) + dy
        self.z0, self.z1 = edge(o[2], H) + dz, edge(o[2] + sz[2], H) + dz

    def cells(self):
        return {(x, y, z) for x in range(self.x0, self.x1) for y in range(self.y0, self.y1)
                for z in range(self.z0, self.z1)}

    def has(self, c):
        return self.x0 <= c[0] < self.x1 and self.y0 <= c[1] < self.y1 and self.z0 <= c[2] < self.z1


N6 = [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)]
FACE = {(0, 0, -1): "front", (0, 0, 1): "back", (-1, 0, 0): "left", (1, 0, 0): "right",
        (0, 1, 0): "up", (0, -1, 0): "down"}
FACE_PRIORITY = ["front", "left", "right", "back", "up", "down"]


def face_colour(b, face, c, buff):
    """Colour Minecraft paints on box b's `face` at cell c (see paint() in squirrel_model.py)."""
    x, y, z = c
    w, h, d = b.mc
    col = b.col
    row = math.floor((b.y1 - (y + 0.5)) / (b.y1 - b.y0) * h)
    if face in ("front", "back"):
        u = math.floor((b.x1 - (x + 0.5)) / (b.x1 - b.x0) * w); fw = w
    elif face in ("left", "right"):
        u = math.floor(((z + 0.5) - b.z0) / (b.z1 - b.z0) * d); fw = d
    else:
        u, fw = 0, w
    if b.belly:
        if face == "down":
            col = b.belly
        if face == "front" and row >= h // 2:
            col = b.belly
    if face == "front" and b.name == "head":
        ey = max(1, h // 3)
        for ex in (fw // 5, fw - fw // 5 - 2):
            if ex <= u < ex + 2 and ey <= row < ey + 2:
                col = "eye_lit" if (u, row) == (ex, ey) else "eye"
    if face == "front" and b.name == "snout" and row == 0 and fw // 2 - 1 <= u <= fw // 2:
        col = "nose"
    if buff and b.name in MUSCLE_SPLIT and face == "front":
        if -1 <= x <= 0:                                   # centre line, kept symmetric
            col = "fur_dk"
        if b.name == "chest" and row == h - 2:
            col = "fur_dk"
    if buff and b.name in MUSCLE_BULGE and face in ("front", "left", "right") and row == h // 2:
        col = "fur_dk"
    return col


# ================================================================ parts in the model
class Placed:
    _n = 0

    def __init__(self, part, color, cells, asm, y0, pos=None, mat=None, note=None):
        Placed._n += 1
        self.uid = Placed._n
        self.part, self.color, self.cells, self.asm, self.y0 = part, color, cells, asm, y0
        self.h = PARTS[part]["h"]
        self.pos, self.mat, self.note = pos, mat, note
        if pos is None:
            xs = [c[0] for c in cells]; zs = [c[2] for c in cells]
            x0, x1, z0, z1 = min(xs), max(xs) + 1, min(zs), max(zs) + 1
            self.pos = (10 * (x0 + x1), -LDU_PLATE * (y0 + self.h), 10 * (z0 + z1))
            self.mat = ID if (x1 - x0) == PARTS[part]["w"] else ROT_Y90
        self.foot = {(c[0], c[2]) for c in cells}
        self.top = y0 + self.h - 1
        self.step = None

    def ldraw(self, color=None, M=None, T=None):
        m, p = self.mat, self.pos
        if M is not None:
            p = [sum(M[i][k] * (p[k] - T[k]) for k in range(3)) + T[k2] for i, k2 in zip(range(3), range(3))]
            m = [[sum(M[i][k] * self.mat[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
        c = color if color is not None else (RENDER_ANY if self.color == ANY else self.color)
        f = lambda v: ("%.4f" % v).rstrip("0").rstrip(".")
        return "1 %d %s %s %s %s %s.dat" % (c, f(p[0]), f(p[1]), f(p[2]),
                                            " ".join(f(v) for r in m for v in r), self.part)


class Assembly:
    def __init__(self, name, title, boxes, buff, hollow=0):
        self.name, self.title, self.buff = name, title, buff
        self.boxes = boxes
        self.cells = set()
        for b in boxes:
            self.cells |= b.cells()
        if hollow:
            self.cells = hollowed(self.cells, hollow)
        self.specials = []     # Placed joint parts
        self.parts = []
        self.joint = None      # dict(axis, point, angle, parent) -- how this hangs on its parent

    def paint(self):
        self.color = {}
        for c in self.cells:
            best = None
            for d in N6:
                n = (c[0] + d[0], c[1] + d[1], c[2] + d[2])
                if n in self.cells:
                    continue
                face = FACE[d]
                for b in self.boxes:
                    if b.has(c) and not b.has(n):
                        cand = (FACE_PRIORITY.index(face), face_colour(b, face, c, self.buff))
                        if best is None or cand[0] < best[0]:
                            best = cand
            self.color[c] = MC2LEGO[best[1]] if best else ANY


def hollowed(cells, wall):
    """Keep only cells within `wall` studs (or 3*wall plates) of the outside."""
    keep = set()
    for c in cells:
        x, y, z = c
        near = any((x + d, y, z) not in cells or (x - d, y, z) not in cells or
                   (x, y, z + d) not in cells or (x, y, z - d) not in cells for d in range(1, wall + 1))
        near = near or any((x, y + d, z) not in cells or (x, y - d, z) not in cells
                           for d in range(1, 3 * wall + 1))
        if near:
            keep.add(c)
    return keep


# ================================================================ tiler
def fits(asm, occ, x0, z0, w, d, y, h, need_color):
    col = None
    cells = []
    for dy in range(h):
        for x in range(x0, x0 + w):
            for z in range(z0, z0 + d):
                c = (x, y + dy, z)
                if c not in asm.cells or c in occ:
                    return None
                cc = asm.color[c]
                if cc != ANY:
                    if col is None:
                        col = cc
                    elif cc != col:
                        return None
                cells.append(c)
    return cells, (col if col is not None else ANY)


def top_exposed(asm, c):
    return (c[0], c[1] + 1, c[2]) not in asm.cells


def tile_layer(asm, occ, y, below, rng, style):
    """One candidate tiling of layer y. Returns list of (part, color, cells)."""
    layer = sorted(c for c in asm.cells if c[1] == y and c not in occ)
    free = set(layer)
    out = []
    order = layer[:]
    if style["scan"] == 1:
        order.sort(key=lambda c: (c[0], c[2]))
    elif style["scan"] == 2:
        order.sort(key=lambda c: (-c[2], -c[0]))
    elif style["scan"] == 3:
        order.sort(key=lambda c: (-c[0], c[2]))
    else:
        order.sort(key=lambda c: (c[2], c[0]))

    def shapes(kinds):
        s = []
        for k in kinds:
            p = PARTS[k]
            for rot in (0, 1):
                w, d = (p["w"], p["d"]) if rot == 0 else (p["d"], p["w"])
                if rot == 1 and p["w"] == p["d"]:
                    continue
                pref = 0 if (w >= d) == (style["long_x"]) else 1
                s.append((-(w * d), pref, rng.random() * style["jitter"], k, w, d))
        s.sort()
        return s

    tiles_first = [c for c in order if top_exposed(asm, c)]
    rest = [c for c in order if not top_exposed(asm, c)]

    def place(cands, kinds, h):
        for _, _, _, k, w, d in shapes(kinds):
            for c in cands:
                if c not in free:
                    continue
                x0, z0 = c[0], c[2]
                r = fits(asm, occ, x0, z0, w, d, y, h, True)
                if not r:
                    continue
                cells, col = r
                if any(cc[1] == y and cc not in free for cc in cells):
                    continue
                if col not in AVAIL or k not in AVAIL[col]:
                    continue
                if PARTS[k]["kind"] == "tile" and not all(top_exposed(asm, cc) for cc in cells):
                    continue
                if PARTS[k]["kind"] != "tile" and any(top_exposed(asm, cc) for cc in cells if cc[1] == y + h - 1):
                    continue
                if h > 1 and any(top_exposed(asm, cc) for cc in cells if cc[1] < y + h - 1):
                    continue
                if h > 1 and any(cc in occ for cc in cells):
                    continue
                for cc in cells:
                    if cc[1] == y:
                        free.discard(cc)
                out.append((k, col, cells))
    place(tiles_first, TILES, 1)
    if style["bricks"]:
        place(rest, BRICKS, 3)
    place(rest, PLATES, 1)
    if free:
        return None
    return out


def score_layer(tiling, below_owner, y):
    """Lower is better: part count, seams stacked on seams, unsupported parts."""
    owner = {}
    for i, (k, col, cells) in enumerate(tiling):
        for c in cells:
            if c[1] == y:
                owner[(c[0], c[2])] = i
    s = len(tiling) * 1.0
    for (x, z), i in owner.items():
        for dx, dz in ((1, 0), (0, 1)):
            n = (x + dx, z + dz)
            if n in owner and owner[n] != i:
                a, b = below_owner.get((x, z)), below_owner.get(n)
                if a is not None and b is not None and a != b:
                    s += 1.5                               # seam right on top of a seam
    for i, (k, col, cells) in enumerate(tiling):
        foot = {(c[0], c[2]) for c in cells if c[1] == y}
        sup = {below_owner[f] for f in foot if f in below_owner}
        if not sup:
            s += 6 if any(f in below_owner for f in []) else 4
        elif len(sup) == 1 and len(foot) > 1:
            s += 0.6
        # bonus for tying two parts together
        s -= 0.4 * min(len(sup), 3)
    return s


def tile_assembly(asm, seed=1, tries=40):
    rng = random.Random(seed)
    occ = {}
    for sp in asm.specials:
        for c in sp.cells:
            occ[c] = sp
    parts = list(asm.specials)
    ys = sorted({c[1] for c in asm.cells})
    for y in ys:
        below_owner = {}
        for c, p in occ.items():
            if c[1] == y - 1 and PARTS[p.part]["kind"] != "tile":
                below_owner[(c[0], c[2])] = p.uid
        best = None
        for t in range(tries):
            style = dict(scan=t % 4, long_x=((y // 3 + t) % 2 == 0), jitter=0.0 if t < 4 else 1.0,
                         bricks=(t % 8) != 7)
            til = tile_layer(asm, occ, y, below_owner, rng, style)
            if til is None:
                continue
            sc = score_layer(til, below_owner, y)
            if best is None or sc < best[0]:
                best = (sc, til)
        if best is None:
            raise SystemExit(f"{asm.name}: could not fill layer {y}")
        for k, col, cells in best[1]:
            p = Placed(k, col, cells, asm.name, y)
            parts.append(p)
            for c in cells:
                occ[c] = p
    asm.parts = parts
    asm.occ = occ
    return parts


# ============================================================== checks
def links(asm):
    """Stud connections inside one assembly: part -> set of parts."""
    g = collections.defaultdict(set)
    occ = asm.occ
    for p in asm.parts:
        if PARTS[p.part]["kind"] == "tile":
            continue
        for (x, z) in p.foot:
            q = occ.get((x, p.top + 1, z))
            if q is not None and q is not p:
                g[p.uid].add(q.uid); g[q.uid].add(p.uid)
    return g


def components(asm):
    g = links(asm)
    seen, comps = set(), []
    for p in asm.parts:
        if p.uid in seen:
            continue
        stack, comp = [p.uid], set()
        while stack:
            u = stack.pop()
            if u in seen:
                continue
            seen.add(u); comp.add(u)
            stack.extend(g[u] - seen)
        comps.append(comp)
    return comps


def weak_parts(asm):
    """Parts held by a single stud and nothing else (wobbly)."""
    g = links(asm)
    return [p for p in asm.parts if len(g[p.uid]) <= 1 and len(p.foot) >= 4]


# ============================================================== joints
def rot_matrix(axis, deg):
    a = math.radians(deg); c, s = math.cos(a), math.sin(a)
    if axis == "x":
        return [[1, 0, 0], [0, c, -s], [0, s, c]]
    if axis == "z":
        return [[c, -s, 0], [s, c, 0], [0, 0, 1]]
    return [[c, 0, s], [0, 1, 0], [-s, 0, c]]


def apply(M, T, p):
    return [sum(M[i][k] * (p[k] - T[k]) for k in range(3)) + T[i] for i in range(3)]


def cell_center_ldu(c):
    return (20 * c[0] + 10, -8 * c[1] - 4, 20 * c[2] + 10)


def ldu_to_cell(p):
    return (math.floor(p[0] / 20), math.floor(-p[1] / 8), math.floor(p[2] / 20))


def collisions(moving, fixed, deg):
    """Cells of `moving` (posed at `deg`) that land inside `fixed`'s cells."""
    j = moving.joint
    M = rot_matrix(j["axis"], deg)
    hit = set()
    hinge_cells = {c for sp in moving.specials for c in sp.cells}
    for c in moving.cells:
        if c in hinge_cells:
            continue
        cx, cy, cz = cell_center_ldu(c)
        for ox in (-7, 7):
            for oy in (-3, 3):
                for oz in (-7, 7):
                    q = ldu_to_cell(apply(M, j["point"], (cx + ox, cy + oy, cz + oz)))
                    if q in fixed.cells:
                        hit.add(q)
    return hit


# ============================================================== models
def make_scrawny(H=1.5):
    V = H * 2.5
    boxes = lambda bone, **kw: [Box(n, o, s, c, b, H, V, **kw) for (bn, _, _, bs) in SCRAWNY_MC
                               if bn in bone for (n, o, s, c, b) in bs]
    main = Assembly("scrawny_body", "Body", boxes({"body", "legs", "head"}), buff=False)
    torso = [b for b in main.boxes if b.name == "torso"][0]
    zb = torso.z1                                  # back face of the torso
    tail_lo = Box(*SCRAWNY_MC[3][3][0], H, V)
    ly = tail_lo.y0 - 1                            # hinge plate layer (pivot sits just below its top)
    tail = Assembly("scrawny_tail", "Tail", boxes({"tail"}, dz=1, dy=(ly - tail_lo.y0)), buff=False)
    tail.cells = tail.cells | {(x, ly, z) for x in range(tail_lo.x0, tail_lo.x1) for z in (zb + 1, zb + 2)}
    for x in range(tail_lo.x0, tail_lo.x1):
        cx = 20 * x + 10
        main.specials.append(Placed("44302", 0, {(x, ly, zb - 2), (x, ly, zb - 1)}, main.name, ly,
                                    pos=(cx, -8 * (ly + 1), 20 * (zb - 1)), mat=FINGER_PZ, note="tail hinge"))
        tail.specials.append(Placed("44301", 0, {(x, ly, zb + 1), (x, ly, zb + 2)}, tail.name, ly,
                                    pos=(cx, -8 * (ly + 1), 20 * (zb + 2)), mat=FINGER_MZ, note="tail hinge"))
    tail.joint = dict(axis="x", point=(0, -8 * (ly + 1) + 2, 20 * zb + 10), angle=-22.5,
                      range=(-45, 10), parent=main.name, label="tail")
    return [main, tail]


def make_buff(H=1.5):
    V = H * 2.5
    def boxes(bone, **kw):
        return [Box(n, o, s, c, b, H, V, **kw) for (bn, _, _, bs) in BUFF_MC
                if bn in bone for (n, o, s, c, b) in bs]
    main = Assembly("buff_body", "Body", boxes({"body", "legs", "head"}), buff=True)
    chest = [b for b in main.boxes if b.name == "chest"][0]
    asms = [main]

    # ---- arms: click-hinge bricks at the shoulder, arms pushed out 1 stud to make room
    pivot_y = 13 * V                                # plates
    top = round(pivot_y + 1.25)                     # hinge brick top (axis is 1.25 plates below)
    ly = top - 3
    arm_z = [-4, -2, 0, 2]
    for side, bone, sx in (("l", "arm_l", -1), ("r", "arm_r", 1)):
        arm = Assembly(f"buff_arm_{side}", "Left arm" if side == "l" else "Right arm",
                       boxes({bone}, dx=sx), buff=True, hollow=2)
        inner = chest.x0 if sx < 0 else chest.x1 - 1          # chest wall cell on this side
        a_cells = [inner, inner - sx]                          # two cells into the chest
        b_cells = [inner + 2 * sx, inner + 3 * sx]              # arm side, after 1-stud gap
        for z in arm_z:
            ca = 10 * (min(a_cells) + max(a_cells) + 1)
            cb = 10 * (min(b_cells) + max(b_cells) + 1)
            main.specials.append(Placed("30365", 0, {(x, ly + k, z) for x in a_cells for k in range(3)},
                                        main.name, ly, pos=(ca, -8 * top, 20 * z + 10),
                                        mat=ROT_Y180 if sx < 0 else ID, note="shoulder hinge"))
            arm.specials.append(Placed("30364", 0, {(x, ly + k, z) for x in b_cells for k in range(3)},
                                       arm.name, ly, pos=(cb, -8 * top, 20 * z + 10),
                                       mat=ID if sx < 0 else ROT_Y180, note="shoulder hinge"))
            arm.cells |= {(x, ly + k, z) for x in b_cells for k in range(3)}
        axis_x = 20 * (inner + 2 * sx) + 10
        arm.joint = dict(axis="z", point=(axis_x, -8 * top + 10, 0), angle=11.25 * (-sx),
                         range=(-90, 0) if sx > 0 else (0, 90), parent=main.name,
                         label="left arm" if sx < 0 else "right arm")
        asms.append(arm)

    # ---- tail: six click-hinge bricks across the back
    tl = Box(*BUFF_MC[5][3][0], H, V)
    zb = chest.z1
    top = round(9 * V + 1.25)
    ly = top - 3
    tail = Assembly("buff_tail", "Tail", boxes({"tail"}, dz=1, dy=ly - tl.y0), buff=True, hollow=2)
    for x in range(tl.x0, tl.x1):
        cx = 20 * x + 10
        main.specials.append(Placed("30365", 0, {(x, ly + k, z) for z in (zb - 2, zb - 1) for k in range(3)},
                                    main.name, ly, pos=(cx, -8 * top, 20 * (zb - 1)), mat=FINGER_PZ,
                                    note="tail hinge"))
        tail.specials.append(Placed("30364", 0, {(x, ly + k, z) for z in (zb + 1, zb + 2) for k in range(3)},
                                    tail.name, ly, pos=(cx, -8 * top, 20 * (zb + 2)), mat=FINGER_MZ,
                                    note="tail hinge"))
        tail.cells |= {(x, ly + k, z) for z in (zb + 1, zb + 2) for k in range(3)}
    tail.joint = dict(axis="x", point=(0, -8 * top + 10, 20 * zb + 10), angle=-28,
                      range=(-60, 5), parent=main.name, label="tail")
    asms.append(tail)
    return asms


# ============================================================== reporting
def mass_and_com(asms):
    """Rough centre of mass: every filled cell weighs the same."""
    tot, acc = 0, [0.0, 0.0, 0.0]
    for a in asms:
        M = rot_matrix(a.joint["axis"], a.joint["angle"]) if a.joint else ID
        T = a.joint["point"] if a.joint else (0, 0, 0)
        for c in a.cells:
            p = apply(M, T, cell_center_ldu(c))
            tot += 1
            for i in range(3):
                acc[i] += p[i]
    return tot, [v / tot for v in acc]


def footprint(asm):
    ymin = min(c[1] for c in asm.cells)
    return {(c[0], c[2]) for c in asm.cells if c[1] == ymin}


def summary(model, asms):
    print(f"== {model}")
    allp = [p for a in asms for p in a.parts]
    print(f"   parts: {len(allp)}")
    for a in asms:
        comps = components(a)
        extra = "" if len(comps) == 1 else f"  !! {len(comps)} separate pieces: sizes {sorted(len(c) for c in comps)}"
        print(f"   {a.name:16s} {len(a.parts):4d} parts, {len(a.cells):5d} cells{extra}")
        if a.joint:
            parent = [b for b in asms if b.name == a.joint["parent"]][0]
            for deg in sorted({a.joint["angle"], *a.joint["range"]}):
                hit = collisions(a, parent, deg)
                print(f"      pose {deg:+6.1f} deg: {'clear' if not hit else f'HITS body in {len(hit)} cells'}")
    n, com = mass_and_com(asms)
    fp = footprint(asms[0])
    xs = [f[0] for f in fp]; zs = [f[1] for f in fp]
    cx, cz = com[0] / 20, com[2] / 20
    print(f"   weight ~{n * 0.096:.0f} g   centre of mass x={cx:.1f} z={cz:.1f} studs;"
          f" feet span x {min(xs)}..{max(xs) + 1}, z {min(zs)}..{max(zs) + 1}")
    return dict(com=(cx, cz), feet=((min(xs), max(xs) + 1), (min(zs), max(zs) + 1)))


def build_model(model, asms, seed):
    for a in asms:
        a.paint()
        tile_assembly(a, seed=seed)
    return asms


if __name__ == "__main__":
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    s = build_model("scrawny", make_scrawny(), seed)
    summary("scrawny", s)
    b = build_model("buff", make_buff(), seed)
    summary("buff", b)
