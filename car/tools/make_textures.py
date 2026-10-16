#!/usr/bin/env python3
"""
Draws every PNG the Monster Truck pack needs — no image libraries required.

Run it from the repo root:   python3 car/tools/make_textures.py

It writes:
  car/RP/textures/entity/monster_truck.png   the truck's paint (1024x1024)
  car/RP/textures/items/monster_truck.png    the item icon (32x32)
  car/RP/pack_icon.png, car/BP/pack_icon.png the pack icons (128x128)

The entity texture is mostly big blocks of flat colour. The model
(monster_truck.geo.json) points each cube at the colour zone it wants:

    uv [0,   0]    black paint          uv [300, 0]    orange trim
    uv [0, 300]    tinted glass         uv [300, 300]  steel / chrome
    uv [0, 512]    tyre rubber          uv [600, 0]    headlight glow
    uv [600, 300]  left flame decal     uv [600, 380]  right flame decal

Change a colour below, re-run this, then re-run ./scripts/build_car.sh.
"""

import math
import os
import struct
import zlib

# ---- Paint colours (R, G, B, A) — tweak these! ----
BLACK_PAINT = (20, 20, 23, 255)
ORANGE      = (232, 110, 20, 255)
YELLOW      = (255, 214, 74, 255)
DEEP_RED    = (150, 30, 8, 255)
GLASS       = (150, 205, 228, 70)
TYRE        = (38, 38, 41, 255)
STEEL       = (150, 156, 166, 255)
HEADLIGHT   = (255, 244, 190, 255)
CLEAR       = (0, 0, 0, 0)


class Canvas:
    def __init__(self, w, h, fill=CLEAR):
        self.w, self.h = w, h
        self.px = bytearray(bytes(fill) * (w * h))

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            o = (y * self.w + x) * 4
            self.px[o:o + 4] = bytes(c)

    def rect(self, x, y, w, h, c):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.set(xx, yy, c)

    def disc(self, cx, cy, r, c):
        r2 = r * r
        for yy in range(int(cy - r) - 1, int(cy + r) + 2):
            for xx in range(int(cx - r) - 1, int(cx + r) + 2):
                if (xx - cx) ** 2 + (yy - cy) ** 2 <= r2:
                    self.set(xx, yy, c)

    def blit(self, src, x0, y0, mirror=False):
        for y in range(src.h):
            for x in range(src.w):
                o = (y * src.w + x) * 4
                c = src.px[o:o + 4]
                if c[3]:
                    self.set(x0 + (src.w - 1 - x if mirror else x), y0 + y, c)

    def write(self, path):
        raw = bytearray()
        for y in range(self.h):
            raw.append(0)  # filter type 0
            raw += self.px[y * self.w * 4:(y + 1) * self.w * 4]

        def chunk(tag, data):
            return (struct.pack(">I", len(data)) + tag + data
                    + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

        png = (b"\x89PNG\r\n\x1a\n"
               + chunk(b"IHDR", struct.pack(">IIBBBBB", self.w, self.h, 8, 6, 0, 0, 0))
               + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
               + chunk(b"IEND", b""))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(png)
        print("wrote", path, f"({self.w}x{self.h})")


def flame_panel(w, h, background=BLACK_PAINT):
    """Hot-rod flames licking backwards along a panel."""
    c = Canvas(w, h, background)

    # (where it starts, how long, how high it licks, how fat) — as fractions
    tongues = [(0.00, 0.30, 0.42, 1.00), (0.11, 0.46, 0.72, 0.85),
               (0.24, 0.28, 0.36, 0.95), (0.33, 0.52, 0.80, 1.05),
               (0.48, 0.32, 0.46, 0.80), (0.58, 0.44, 0.66, 1.00),
               (0.72, 0.26, 0.34, 0.90), (0.80, 0.38, 0.58, 0.85)]

    # three passes: dark outline, orange body, yellow core — a whole pass at a
    # time, so a later stroke can never paint over an earlier flame's colour
    for colour, grow, taper in ((DEEP_RED, 1.8, 0.75),
                                (ORANGE, 1.0, 0.70),
                                (YELLOW, 0.38, 0.55)):
        # the wavy pool of fire the tongues grow out of
        for x in range(w):
            band = 5 + 2.5 * math.sin(x / 19.0) + 2.0 * math.sin(x / 7.0 + 1.3)
            band *= (1.55 if colour is DEEP_RED else
                     1.10 if colour is ORANGE else 0.45)
            for y in range(h - int(band), h):
                c.set(x, y, colour)

        for start, length, rise, fat in tongues:
            x0 = start * w
            span = max(6.0, length * w)
            thick = h * 0.10 * grow * fat
            for step in range(int(span)):
                t = step / span
                # licks up and flicks over: fast rise early, curling at the tip
                x = x0 + step + 2.0 * t * t * span * 0.12
                y = h - (5 + rise * h * (t ** 0.65))
                r = thick * (1.0 - t) ** taper
                if r < 0.45:
                    break
                c.disc(x, y, r, colour)
    return c


def entity_texture():
    c = Canvas(1024, 1024, BLACK_PAINT)
    c.rect(0, 0, 256, 256, BLACK_PAINT)      # body paint
    c.rect(0, 300, 256, 200, GLASS)          # windows
    c.rect(0, 512, 256, 256, TYRE)           # tyres
    c.rect(300, 0, 256, 256, ORANGE)         # trim, cage, hubs
    c.rect(300, 300, 256, 256, STEEL)        # frame, bumpers, exhaust
    c.rect(600, 0, 128, 128, HEADLIGHT)      # headlights

    panel = flame_panel(290, 60)
    c.blit(panel, 600, 300)                  # left side
    c.blit(panel, 600, 380, mirror=True)     # right side (mirrored)
    c.write("car/RP/textures/entity/monster_truck.png")


def item_icon():
    """Tiny side-on monster truck for the crafted item."""
    c = Canvas(32, 32)
    c.rect(4, 12, 24, 7, BLACK_PAINT)        # body
    c.rect(9, 6, 12, 6, BLACK_PAINT)         # cab
    c.rect(10, 7, 10, 4, GLASS)              # window
    c.rect(3, 15, 26, 2, STEEL)              # frame
    c.rect(4, 17, 24, 2, ORANGE)             # flame stripe
    c.rect(6, 16, 4, 1, YELLOW)
    c.rect(15, 16, 5, 1, YELLOW)
    for cx in (9, 23):                       # big wheels
        c.disc(cx, 23, 6, TYRE)
        c.disc(cx, 23, 2, ORANGE)
    c.rect(27, 11, 2, 2, HEADLIGHT)          # headlight
    c.write("car/RP/textures/items/monster_truck.png")


def pack_icon():
    c = Canvas(128, 128, BLACK_PAINT)
    c.blit(flame_panel(128, 44), 0, 84)
    c.rect(18, 40, 92, 24, BLACK_PAINT)
    c.rect(34, 22, 44, 20, BLACK_PAINT)
    c.rect(38, 26, 36, 12, GLASS)
    c.rect(16, 58, 96, 6, STEEL)
    for cx in (36, 92):
        c.disc(cx, 74, 20, TYRE)
        c.disc(cx, 74, 7, ORANGE)
    c.rect(106, 44, 8, 8, HEADLIGHT)
    c.write("car/RP/pack_icon.png")
    c.write("car/BP/pack_icon.png")


if __name__ == "__main__":
    entity_texture()
    item_icon()
    pack_icon()
