#!/usr/bin/env python3
"""
Builds the squirrel models and their textures.

There are TWO squirrels in here:
  - "scrawny" : the normal little forest squirrel
  - "buff"    : what he turns into when a monster gets close

Both are described below as a list of boxes. Minecraft measures models in
"units", and 16 units = 1 block, so a 5-unit-wide box is about a third of a
block. Change a number, re-run this script, and the model + texture are
rebuilt together.

  python3 tools/squirrel_model.py
"""

import base64, json, os, struct, zlib

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RP = os.path.join(HERE, "squirrel", "RP")

TEX = 128  # texture is 128x128 pixels

# ---------------------------------------------------------------- colours
# (r, g, b) 0-255.  Tweaking these re-skins the squirrel.
C = {
    "fur":     (150,  86,  44),   # main reddish-brown fur
    "fur_dk":  (112,  62,  30),   # shadow / muscle creases
    "belly":   (226, 202, 166),   # cream belly + chest
    "tail":    (170, 104,  56),   # tail is a touch lighter than the body
    "tail_lt": (214, 176, 134),   # pale underside of the tail
    "snout":   (222, 196, 158),
    "eye":     ( 24,  18,  16),
    "eye_lit": (255, 255, 255),
    "nose":    ( 60,  38,  32),
    "claw":    ( 70,  52,  40),
    "nut":     (198, 150,  92),   # the acorn he throws
    "nut_cap": (104,  70,  40),
}

# ------------------------------------------------------------------ boxes
# Each box: (name, origin[x,y,z], size[w,h,d], colour, belly_colour_or_None)
#   origin = the corner with the smallest x, y and z
#   +Y is up.  -Z is FORWARDS (the squirrel looks that way).
#
# Bones group boxes so they can move together later (head turns, tail sways).
# ("bone name", pivot[x,y,z], rotation[x,y,z] or None, [boxes...])

SCRAWNY = [
    ("body", [0, 4, 0], None, [
        ("torso",   [-2,  3, -4], [4, 4, 8], "fur", "belly"),
    ]),
    ("legs", [0, 0, 0], None, [
        ("leg_bl",  [-2,  0,  2], [1, 3, 1], "fur", None),
        ("leg_br",  [ 1,  0,  2], [1, 3, 1], "fur", None),
        ("leg_fl",  [-2,  0, -3], [1, 3, 1], "fur", None),
        ("leg_fr",  [ 1,  0, -3], [1, 3, 1], "fur", None),
    ]),
    ("head", [0, 7, -4], None, [
        ("head",    [-2,  6, -8], [4, 4, 4], "fur", None),
        ("snout",   [-1,  6, -9], [2, 2, 1], "snout", None),
        ("ear_l",   [-2, 10, -7], [1, 2, 1], "fur", None),
        ("ear_r",   [ 1, 10, -7], [1, 2, 1], "fur", None),
    ]),
    ("tail", [0, 5, 4], [-22, 0, 0], [
        ("tail_lo", [-1,  5,  4], [2, 5, 2], "tail", "tail_lt"),
        ("tail_up", [-2,  9,  3], [4, 6, 3], "tail", "tail_lt"),
    ]),
]

BUFF = [
    ("body", [0, 10, 0], None, [
        ("chest",   [-5,  8, -5], [10, 7, 9], "fur", "belly"),
        ("traps",   [-4, 15, -3], [ 8, 2, 5], "fur", None),
        ("waist",   [-3,  5, -2], [ 6, 4, 6], "fur", "belly"),
    ]),
    # arms splay outwards -- he is too jacked to put them down
    ("arm_l", [-5, 13, 0], [0, 0, -11], [
        ("delt_l",  [ -9, 10, -4], [4, 5, 7], "fur", None),
        ("bicep_l", [ -9,  5, -3], [4, 6, 5], "fur", None),
        ("fore_l",  [-10,  1, -3], [4, 5, 5], "fur", None),
    ]),
    ("arm_r", [5, 13, 0], [0, 0, 11], [
        ("delt_r",  [  5, 10, -4], [4, 5, 7], "fur", None),
        ("bicep_r", [  5,  5, -3], [4, 6, 5], "fur", None),
        ("fore_r",  [  6,  1, -3], [4, 5, 5], "fur", None),
    ]),
    ("legs", [0, 0, 0], None, [
        ("thigh_l", [-4,  2,  0], [4, 4, 5], "fur", None),
        ("thigh_r", [ 0,  2,  0], [4, 4, 5], "fur", None),
        ("calf_l",  [-4,  0,  1], [3, 3, 4], "fur", None),
        ("calf_r",  [ 1,  0,  1], [3, 3, 4], "fur", None),
    ]),
    ("head", [0, 15, -5], None, [
        ("head",    [-3, 14,  -9], [6, 5, 5], "fur", None),
        ("snout",   [-1, 14, -10], [2, 2, 1], "snout", None),
        ("ear_l",   [-3, 19,  -7], [2, 3, 1], "fur", None),
        ("ear_r",   [ 1, 19,  -7], [2, 3, 1], "fur", None),
    ]),
    ("tail", [0, 9, 5], [-28, 0, 0], [
        ("tail_lo", [-2,  9,  4], [4, 7, 4], "tail", "tail_lt"),
        ("tail_up", [-4, 15,  3], [8, 8, 6], "tail", "tail_lt"),
    ]),
]

NUT = [
    ("nut", [0, 0, 0], None, [
        ("shell", [-1, 0, -1], [2, 3, 2], "nut", None),
        ("cap",   [-2, 3, -2], [4, 1, 4], "nut_cap", None),
    ]),
]

# Boxes that get muscle shading drawn on their front face (buff only).
MUSCLE_SPLIT = {"chest", "waist"}
HITBOX = {"squirrel_scrawny": [0.5, 0.5], "squirrel_buff": [1.5, 2.0], "nut": [0.25, 0.25]}

MUSCLE_BULGE = {"bicep_l", "bicep_r", "delt_l", "delt_r", "thigh_l", "thigh_r"}


# ============================================================ texture guts
# Minecraft wraps a box's skin out flat, like a cereal-box net:
#
#          +------+------+
#          | top  |bottom|
#   +------+------+------+------+
#   |right | FRONT| left | back |
#   +------+------+------+------+
#
# so a box w x h x d needs a patch 2*(w+d) wide and (h+d) tall.

def box_faces(u, v, w, h, d):
    """Where each face of a box lands in the texture. Returns name -> (x,y,w,h)."""
    w, h, d = int(round(w)), int(round(h)), int(round(d))
    return {
        "up":    (u + d,         v,     w, d),
        "down":  (u + d + w,     v,     w, d),
        "right": (u,             v + d, d, h),
        "front": (u + d,         v + d, w, h),
        "left":  (u + d + w,     v + d, d, h),
        "back":  (u + d + w + d, v + d, w, h),
    }


def pack(boxes, tex_size=None):
    """Lay every box's patch out on the texture without overlaps (shelf packing)."""
    placed, x, y, shelf = {}, 0, 0, 0
    for name, origin, size, col, belly in boxes:
        w, h, d = (int(round(s)) for s in size)
        pw, ph = 2 * (w + d), h + d
        if x + pw > (tex_size or TEX):
            x, y, shelf = 0, y + shelf, 0
        placed[name] = (x, y)
        x += pw
        shelf = max(shelf, ph)
    if y + shelf > (tex_size or TEX):
        raise SystemExit(f"texture too small: needs {y + shelf}px")
    return placed


class Img:
    def __init__(self, size):
        self.n = size
        self.px = [[(0, 0, 0, 0)] * size for _ in range(size)]

    def rect(self, x, y, w, h, colour):
        for j in range(y, y + h):
            for i in range(x, x + w):
                if 0 <= i < self.n and 0 <= j < self.n:
                    self.px[j][i] = colour + (255,)

    def grain(self, x, y, w, h, amount=12):
        """Speckle a patch so flat fur doesn't look like plastic."""
        for j in range(y, y + h):
            for i in range(x, x + w):
                if not (0 <= i < self.n and 0 <= j < self.n):
                    continue
                r, g, b, a = self.px[j][i]
                if a == 0:
                    continue
                # cheap deterministic hash so the texture is identical every run
                n = ((i * 73856093) ^ (j * 19349663)) & 0xFF
                k = (n % (2 * amount + 1)) - amount
                self.px[j][i] = (clamp(r + k), clamp(g + k), clamp(b + k), a)

    def write(self, path):
        raw = b"".join(
            b"\x00" + b"".join(bytes(p) for p in row) for row in self.px
        )
        def chunk(tag, data):
            return (struct.pack(">I", len(data)) + tag + data
                    + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))
        png = (b"\x89PNG\r\n\x1a\n"
               + chunk(b"IHDR", struct.pack(">IIBBBBB", self.n, self.n, 8, 6, 0, 0, 0))
               + chunk(b"IDAT", zlib.compress(raw, 9))
               + chunk(b"IEND", b""))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        open(path, "wb").write(png)


def clamp(v):
    return 0 if v < 0 else 255 if v > 255 else v


def paint(img, boxes, uvs, buff):
    for name, origin, size, col, belly in boxes:
        u, v = uvs[name]
        w, h, d = (int(round(s)) for s in size)
        f = box_faces(u, v, w, h, d)

        for rect in f.values():
            img.rect(*rect, C[col])
        img.grain(u, v, 2 * (w + d), h + d)

        # pale underside
        if belly:
            img.rect(*f["down"], C[belly])
            fx, fy, fw, fh = f["front"]
            img.rect(fx, fy + fh // 2, fw, fh - fh // 2, C[belly])

        # --- face ---
        if name == "head":
            fx, fy, fw, fh = f["front"]
            ey = fy + max(1, fh // 3)
            for ex in (fx + fw // 5, fx + fw - fw // 5 - 2):
                img.rect(ex, ey, 2, 2, C["eye"])
                img.rect(ex, ey, 1, 1, C["eye_lit"])
        if name == "snout":
            fx, fy, fw, fh = f["front"]
            img.rect(fx + fw // 2 - 1, fy, 2, 1, C["nose"])

        # --- muscles (buff only) ---
        if buff and name in MUSCLE_SPLIT:
            fx, fy, fw, fh = f["front"]
            img.rect(fx + fw // 2, fy, 1, fh, C["fur_dk"])          # centre line
            if name == "chest":
                img.rect(fx, fy + fh - 2, fw, 1, C["fur_dk"])        # under the pecs
        if buff and name in MUSCLE_BULGE:
            for side in ("front", "right", "left"):
                bx, by, bw, bh = f[side]
                img.rect(bx, by + bh // 2, bw, 1, C["fur_dk"])       # bulge crease


def geometry(ident, bones, uvs, size=None):
    out = []
    for bname, pivot, rot, boxes in bones:
        cubes = []
        for name, origin, size, col, belly in boxes:
            cubes.append({"origin": origin, "size": size, "uv": list(uvs[name])})
        bone = {"name": bname, "pivot": pivot, "cubes": cubes}
        if rot:
            bone["rotation"] = rot
        out.append(bone)
    tall = max(o[1] + s[1] for name, _, _, bs in bones if name != "tail"
               for _, o, s, _, _ in bs)
    return {
        "description": {
            "identifier": f"geometry.{ident}",
            "texture_width": size or TEX, "texture_height": size or TEX,
            "visible_bounds_width": 4, "visible_bounds_height": 4,
            "visible_bounds_offset": [0, 1, 0],
        },
        "bones": out,
    }, tall


def build(ident, bones, buff, size=None):
    size = size or TEX
    boxes = [b for _, _, _, bs in bones for b in bs]
    for name, origin, dims, _, _ in boxes:
        if any(float(v) != int(v) for v in dims):
            raise SystemExit(
                f"{ident}: box '{name}' has a fractional size {dims}.\n"
                "Box sizes must be whole units -- Minecraft wraps the texture "
                "using the real size, so a fractional box samples the wrong "
                "pixels and the face disappears in game.")
    uvs = pack(boxes, size)
    img = Img(size)
    img.rect(0, 0, size, size, C["fur"])
    paint(img, boxes, uvs, buff)
    img.write(os.path.join(RP, "textures", "entity", f"{ident}.png"))
    geo, tall = geometry(ident, bones, uvs, size)
    wide = max(o[0] + s[0] for _, o, s, _, _ in boxes) - min(o[0] for _, o, s, _, _ in boxes)
    return geo, tall, wide



def write_viewer(models):
    """Rebuild the browser previewer with the models baked in."""
    tpl = open(os.path.join(HERE, "tools", "viewer_template.html")).read()
    payload = {"texSize": TEX, "models": [], "tex": []}
    for ident, geo, tall, wide, scale in models:
        payload["models"].append({
            "bones": geo["bones"],
            "tallUnits": round(tall, 2),
            "wideUnits": round(wide, 2),
            "fitScale": round(16.0 / tall, 4),
            "trueScale": round(scale, 3),
            "hitbox": HITBOX[ident],
            "cubeCount": sum(len(b["cubes"]) for b in geo["bones"]),
        })
        png = open(os.path.join(RP, "textures", "entity", ident + ".png"), "rb").read()
        payload["tex"].append("data:image/png;base64," + base64.b64encode(png).decode())
    out = os.path.join(HERE, "tools", "squirrel_viewer.html")
    open(out, "w").write(tpl.replace("/*__DATA__*/", json.dumps(payload, separators=(",", ":"))))
    return out


def write_scales(scales):
    """Push the computed scale values into the behaviour pack entity."""
    path = os.path.join(HERE, "squirrel", "BP", "entities", "squirrel.json")
    if not os.path.exists(path):
        return None
    d = json.load(open(path))
    groups = d["minecraft:entity"]["component_groups"]
    for group, ident in (("pets:small", "squirrel_scrawny"), ("pets:giant", "squirrel_buff")):
        groups[group]["minecraft:scale"]["value"] = round(scales[ident], 3)
        w, h = HITBOX[ident]
        groups[group]["minecraft:collision_box"] = {"width": w, "height": h}
    with open(path, "w") as fh:
        json.dump(d, fh, indent=2)
        fh.write("\n")
    return path


def main():
    scrawny, s_tall, s_wide = build("squirrel_scrawny", SCRAWNY, buff=False)
    buff,    b_tall, b_wide = build("squirrel_buff",    BUFF,    buff=True)

    nut, _, _ = build("nut", NUT, buff=False, size=32)
    npath = os.path.join(RP, "models", "entity", "nut.geo.json")
    os.makedirs(os.path.dirname(npath), exist_ok=True)
    with open(npath, "w") as fh:
        json.dump({"format_version": "1.12.0", "minecraft:geometry": [nut]}, fh, indent=2)
        fh.write("\n")

    path = os.path.join(RP, "models", "entity", "squirrel.geo.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        json.dump({"format_version": "1.12.0",
                   "minecraft:geometry": [scrawny, buff]}, fh, indent=2)
        fh.write("\n")

    # What scale each form needs so the giant is exactly 15x the little one.
    # Ignores the tail, which arcs overhead and would flatter the numbers.
    SMALL_BLOCKS = 0.5
    s_scale = SMALL_BLOCKS * 16 / s_tall
    b_scale = s_scale * 15 * s_tall / b_tall
    print(f"scrawny : {s_tall:.1f} units tall, {s_wide:.1f} wide  -> scale {s_scale:.2f} = {SMALL_BLOCKS:.2f} blocks")
    print(f"buff    : {b_tall:.1f} units tall, {b_wide:.1f} wide  -> scale {b_scale:.2f} = {b_tall * b_scale / 16:.2f} blocks tall, {b_wide * b_scale / 16:.2f} wide")
    view = write_viewer([("squirrel_scrawny", scrawny, s_tall, s_wide, s_scale),
                         ("squirrel_buff",    buff,    b_tall, b_wide, b_scale)])
    bp = write_scales({"squirrel_scrawny": s_scale, "squirrel_buff": b_scale})
    print(f"wrote {path}")
    if bp:
        print(f"wrote {bp}   (scale + collision box)")
    print(f"wrote {view}   <-- open this in a browser")


if __name__ == "__main__":
    main()
