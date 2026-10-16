#!/usr/bin/env python3
"""
Draws a picture of the monster truck straight from the pack files — so you can
see a model change without rebuilding the add-on and loading Minecraft.

Run it from anywhere:   python3 car/tools/render_preview.py
Output:                 dist/monster_truck_preview.png   (three views)

It reads the real files the game reads:

    car/RP/models/entity/monster_truck.geo.json    the shape
    car/RP/textures/entity/monster_truck.png       the paint

and draws them the way Minecraft does — box UV mapping, nearest-neighbour
texture sampling, a depth buffer so near parts cover far ones, back faces
skipped, and the tinted glass blended on top at the end.

It is a PREVIEW, not the game: no shadows between parts, no sky light, and the
wheels are drawn parked (the spin animation isn't applied). Its real use is
spotting modelling mistakes — two parts sharing an exact face plane show up
here as a flickery checkerboard, and that same overlap flickers in game.

Want a different angle? Edit VIEWS at the bottom: (yaw, pitch) in degrees,
yaw 0 looks at the back of the truck, 180 at the front.
"""

import json
import math
import os
import struct
import sys
import zlib

from make_textures import Canvas  # sits next to this file

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MODEL = os.path.join(ROOT, "car/RP/models/entity/monster_truck.geo.json")
TEXTURE = os.path.join(ROOT, "car/RP/textures/entity/monster_truck.png")
OUTPUT = os.path.join(ROOT, "dist/monster_truck_preview.png")

SUPERSAMPLE = 3       # draw this many times bigger, then shrink = smooth edges
LIGHT = (0.35, 0.86, -0.37)   # which way the sun comes from
SKY_TOP, SKY_BOTTOM = (198, 209, 224), (150, 163, 180)
PAPER_TOP, PAPER_BOTTOM = (243, 245, 249), (226, 230, 237)


# ---------------------------------------------------------------- texture ---

def load_png(path):
    """Minimal PNG reader (8-bit RGBA) so this needs no image library."""
    data = open(path, "rb").read()
    pos, idat, width, height = 8, b"", 0, 0
    while pos < len(data):
        length = struct.unpack(">I", data[pos:pos + 4])[0]
        kind = data[pos + 4:pos + 8]
        chunk = data[pos + 8:pos + 8 + length]
        if kind == b"IHDR":
            width, height = struct.unpack(">II", chunk[:8])
        elif kind == b"IDAT":
            idat += chunk
        pos += 12 + length

    raw = zlib.decompress(idat)
    stride = width * 4
    out, prev, i = bytearray(), bytearray(stride), 0
    for _ in range(height):
        filt = raw[i]; i += 1
        line = bytearray(raw[i:i + stride]); i += stride
        for x in range(stride):                      # undo the row filters
            a = line[x - 4] if x >= 4 else 0
            b = prev[x]
            c = prev[x - 4] if x >= 4 else 0
            if filt == 1:
                line[x] = (line[x] + a) & 255
            elif filt == 2:
                line[x] = (line[x] + b) & 255
            elif filt == 3:
                line[x] = (line[x] + (a + b) // 2) & 255
            elif filt == 4:
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                line[x] = (line[x] + (a if (pa <= pb and pa <= pc)
                                      else (b if pb <= pc else c))) & 255
        out += line
        prev = line
    return width, height, out


TEX_W, TEX_H, TEX = load_png(TEXTURE)


def texel(u, v):
    x = min(TEX_W - 1, max(0, int(u)))
    y = min(TEX_H - 1, max(0, int(v)))
    o = (y * TEX_W + x) * 4
    return TEX[o], TEX[o + 1], TEX[o + 2], TEX[o + 3]


# ------------------------------------------------------------------ model ---

def rotate_x(point, degrees, pivot):
    a = math.radians(degrees)
    x, y, z = point
    _, py, pz = pivot
    y -= py
    z -= pz
    return (x, py + y * math.cos(a) - z * math.sin(a),
            pz + y * math.sin(a) + z * math.cos(a))


def build_faces():
    """Every cube face as (corners, texture corner, texture size, normal)."""
    geo = json.load(open(MODEL))["minecraft:geometry"][0]
    faces = []
    for bone in geo["bones"]:
        bone_rot = bone.get("rotation")
        bone_pivot = bone.get("pivot", [0, 0, 0])
        for cube in bone.get("cubes", []):
            ox, oy, oz = cube["origin"]
            w, h, d = cube["size"]
            x0, y0, z0, x1, y1, z1 = ox, oy, oz, ox + w, oy + h, oz + d
            uv = cube["uv"]

            # corner the texture starts at, edge along texture-u, edge along
            # texture-v, outward normal, and the face's size in texture pixels
            plan = {
                "north": ((x1, y1, z0), (-w, 0, 0), (0, -h, 0), (0, 0, -1), (w, h)),
                "south": ((x0, y1, z1), (w, 0, 0), (0, -h, 0), (0, 0, 1), (w, h)),
                "west":  ((x0, y1, z0), (0, 0, d), (0, -h, 0), (-1, 0, 0), (d, h)),
                "east":  ((x1, y1, z1), (0, 0, -d), (0, -h, 0), (1, 0, 0), (d, h)),
                "up":    ((x0, y1, z0), (w, 0, 0), (0, 0, d), (0, 1, 0), (w, d)),
                "down":  ((x0, y0, z0), (w, 0, 0), (0, 0, d), (0, -1, 0), (w, d)),
            }
            # the standard Minecraft box-UV unwrap, when the cube just says
            # "uv": [u, v] instead of naming each face
            box = None
            if not isinstance(uv, dict):
                u, v = uv
                box = {"up": (u + d, v), "down": (u + d + w, v),
                       "east": (u, v + d), "north": (u + d, v + d),
                       "west": (u + d + w, v + d), "south": (u + 2 * d + w, v + d)}

            for name, (start, edge_u, edge_v, normal, size) in plan.items():
                if isinstance(uv, dict):
                    if name not in uv:
                        continue
                    uv_at, uv_size = uv[name]["uv"], uv[name]["uv_size"]
                else:
                    uv_at, uv_size = box[name], size

                corners = [
                    start,
                    tuple(start[i] + edge_u[i] for i in range(3)),
                    tuple(start[i] + edge_u[i] + edge_v[i] for i in range(3)),
                    tuple(start[i] + edge_v[i] for i in range(3)),
                ]
                # a cube can be turned inside its bone, and the bone can be
                # turned too (the windshield and the tyres both do this)
                for turn, pivot in ((cube.get("rotation"), cube.get("pivot", bone_pivot)),
                                    (bone_rot, bone_pivot)):
                    if turn:
                        corners = [rotate_x(p, turn[0], pivot) for p in corners]
                        normal = rotate_x(normal, turn[0], (0, 0, 0))
                faces.append((corners, uv_at, uv_size, normal))
    return faces


FACES = build_faces()


# ----------------------------------------------------------------- render ---

def render(yaw_deg, pitch_deg, width, height):
    """One view of the truck, drawn SUPERSAMPLE times too big."""
    W, H = width * SUPERSAMPLE, height * SUPERSAMPLE
    yaw, pitch = math.radians(yaw_deg), math.radians(pitch_deg)

    def view(p):
        """Spin the world around the truck. Bigger depth = nearer the camera."""
        x, y, z = p
        xr = x * math.cos(yaw) - z * math.sin(yaw)
        zr = x * math.sin(yaw) + z * math.cos(yaw)
        yr = y * math.cos(pitch) - zr * math.sin(pitch)
        return xr, yr, y * math.sin(pitch) + zr * math.cos(pitch)

    # frame the truck automatically, whatever angle it is seen from
    seen = [view(p) for face in FACES for p in face[0]]
    x0 = min(p[0] for p in seen); x1 = max(p[0] for p in seen)
    y0 = min(p[1] for p in seen); y1 = max(p[1] for p in seen)
    scale = min(W * 0.88 / (x1 - x0), H * 0.88 / (y1 - y0))
    mid_x, mid_y = (x0 + x1) / 2, (y0 + y1) / 2

    def screen(p):
        xr, yr, depth = view(p)
        return (W / 2 + (xr - mid_x) * scale, H / 2 - (yr - mid_y) * scale, depth)

    canvas = Canvas(W, H)
    sky(canvas, SKY_TOP, SKY_BOTTOM)
    ground_shadow(canvas, screen)
    depth_buffer = [-1e9] * (W * H)

    def brightness(normal):
        length = math.sqrt(sum(c * c for c in normal)) or 1.0
        lit = sum(normal[i] * LIGHT[i] for i in range(3)) / length
        return 0.52 + 0.48 * max(0.0, lit)

    def triangle(a, b, c, shade, blend):
        """Each corner is (x, y, depth, texture u, texture v)."""
        min_x = max(0, int(min(a[0], b[0], c[0])))
        max_x = min(W - 1, int(max(a[0], b[0], c[0])) + 1)
        min_y = max(0, int(min(a[1], b[1], c[1])))
        max_y = min(H - 1, int(max(a[1], b[1], c[1])) + 1)
        area = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(area) < 1e-9 or min_x > max_x:
            return
        for yi in range(min_y, max_y + 1):
            py = yi + 0.5
            row = yi * W
            for xi in range(min_x, max_x + 1):
                px = xi + 0.5
                wa = ((b[1] - c[1]) * (px - c[0]) + (c[0] - b[0]) * (py - c[1])) / area
                if wa < 0 or wa > 1:
                    continue
                wb = ((c[1] - a[1]) * (px - c[0]) + (a[0] - c[0]) * (py - c[1])) / area
                if wb < 0:
                    continue
                wc = 1.0 - wa - wb
                if wc < 0:
                    continue
                depth = wa * a[2] + wb * b[2] + wc * c[2]
                idx = row + xi
                if depth <= depth_buffer[idx]:
                    continue
                r, g, bl, alpha = texel(wa * a[3] + wb * b[3] + wc * c[3],
                                        wa * a[4] + wb * b[4] + wc * c[4])
                if alpha == 0:
                    continue
                col = (min(255, int(r * shade)), min(255, int(g * shade)),
                       min(255, int(bl * shade)))
                if blend:                      # glass: see the truck through it
                    o = idx * 4
                    f = alpha / 255.0
                    col = tuple(int(col[i] * f + canvas.px[o + i] * (1 - f))
                                for i in range(3))
                else:
                    depth_buffer[idx] = depth
                canvas.set(xi, yi, col + (255,))

    def draw(face, blend):
        corners, uv_at, uv_size, normal = face
        if view(normal)[2] <= 0.0:             # face is pointing away from us
            return
        uv_corners = [(uv_at[0], uv_at[1]),
                      (uv_at[0] + uv_size[0], uv_at[1]),
                      (uv_at[0] + uv_size[0], uv_at[1] + uv_size[1]),
                      (uv_at[0], uv_at[1] + uv_size[1])]
        pts = []
        for p, t in zip(corners, uv_corners):
            sx, sy, depth = screen(p)
            pts.append((sx, sy, depth, t[0], t[1]))
        shade = brightness(normal)
        triangle(pts[0], pts[1], pts[2], shade, blend)
        triangle(pts[0], pts[2], pts[3], shade, blend)

    see_through = [f for f in FACES if texel(f[1][0] + 1, f[1][1] + 1)[3] != 255]
    solid = [f for f in FACES if texel(f[1][0] + 1, f[1][1] + 1)[3] == 255]
    for face in solid:
        draw(face, False)
    see_through.sort(key=lambda f: sum(view(p)[2] for p in f[0]))  # far ones first
    for face in see_through:
        draw(face, True)

    return shrink(canvas, SUPERSAMPLE)


def sky(canvas, top, bottom):
    for y in range(canvas.h):
        t = y / canvas.h
        col = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3)) + (255,)
        for x in range(canvas.w):
            canvas.set(x, y, col)


def ground_shadow(canvas, screen):
    """A soft dark blob under the truck so it doesn't look like it's floating."""
    pts = [screen(p)[:2] for p in
           ((-30, 0, -42), (30, 0, -42), (30, 0, 44), (-30, 0, 44))]
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    cx, cy = sum(xs) / 4, sum(ys) / 4
    rx, ry = (max(xs) - min(xs)) / 2 * 0.95, (max(ys) - min(ys)) / 2 * 0.95
    for y in range(int(cy - ry - 8), int(cy + ry + 9)):
        for x in range(int(cx - rx - 8), int(cx + rx + 9)):
            if not (0 <= x < canvas.w and 0 <= y < canvas.h):
                continue
            d = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
            if d > 1.7:
                continue
            f = 0.40 * max(0.0, min(1.0, (1.7 - d)))
            o = (y * canvas.w + x) * 4
            canvas.set(x, y, (int(canvas.px[o] * (1 - f)),
                              int(canvas.px[o + 1] * (1 - f)),
                              int(canvas.px[o + 2] * (1 - f)), 255))


def shrink(src, factor):
    out = Canvas(src.w // factor, src.h // factor)
    for y in range(out.h):
        for x in range(out.w):
            r = g = b = 0
            for dy in range(factor):
                for dx in range(factor):
                    o = ((y * factor + dy) * src.w + (x * factor + dx)) * 4
                    r += src.px[o]; g += src.px[o + 1]; b += src.px[o + 2]
            n = factor * factor
            out.set(x, y, (r // n, g // n, b // n, 255))
    return out


# (yaw, pitch) in degrees — yaw 0 is behind the truck, 180 is in front of it
VIEWS = [(216, 20), (272, 5), (38, 20)]


def main():
    print("rendering (takes a few seconds — it's all pure Python)...")
    hero = render(VIEWS[0][0], VIEWS[0][1], 660, 560)
    side = render(VIEWS[1][0], VIEWS[1][1], 400, 270)
    rear = render(VIEWS[2][0], VIEWS[2][1], 400, 270)

    sheet = Canvas(1104, 600)
    sky(sheet, PAPER_TOP, PAPER_BOTTOM)
    sheet.blit(hero, 14, 20)
    sheet.blit(side, 690, 20)
    sheet.blit(rear, 690, 310)
    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    sheet.write(OUTPUT)


if __name__ == "__main__":
    sys.exit(main())
