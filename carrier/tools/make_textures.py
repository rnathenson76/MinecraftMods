#!/usr/bin/env python3
"""
Draws every PNG the Carrier pack needs — no image libraries required.

Run it from the repo root:   python3 carrier/tools/make_textures.py

It writes:
  carrier/RP/textures/items/water_blaster.png   the Water Blaster icon (16x16)
  carrier/RP/textures/entity/water_shot.png     a flying water shot (16x16)
  carrier/RP/pack_icon.png, carrier/BP/pack_icon.png   the pack icons (128x128)

Change a colour below, re-run this, then re-run ./scripts/build_carrier.sh.
"""

import os
import struct
import zlib

# ---- Colours (R, G, B, A) — tweak these! ----
TANK       = (40, 150, 230, 255)    # the see-through water tank
TANK_SHINE = (150, 215, 255, 255)
BODY       = (255, 196, 40, 255)    # the blaster's plastic
BODY_DARK  = (200, 120, 20, 255)
NOZZLE     = (230, 60, 50, 255)
WATER      = (60, 160, 255, 230)
WATER_CORE = (200, 235, 255, 255)
SEA        = (30, 90, 160, 255)
HULL       = (120, 128, 140, 255)
DECK       = (70, 74, 82, 255)
DECK_LINE  = (240, 240, 240, 255)
TOWER      = (150, 158, 170, 255)
CLEAR      = (0, 0, 0, 0)

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


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
        print("wrote", os.path.relpath(path, os.path.dirname(HERE)), f"({self.w}x{self.h})")


def blaster_icon():
    """A chunky super-soaker, nozzle pointing up-right like vanilla tools."""
    c = Canvas(16, 16)
    # barrel running diagonally from the grip up to the nozzle
    for i in range(9):
        c.rect(3 + i, 9 - i, 3, 3, BODY)
    c.rect(12, 0, 4, 4, NOZZLE)
    # water tank sitting on the barrel
    c.rect(3, 2, 6, 5, TANK)
    c.rect(4, 3, 2, 2, TANK_SHINE)
    # grip and trigger
    c.rect(1, 11, 4, 5, BODY_DARK)
    c.rect(6, 12, 1, 2, BODY_DARK)
    return c


def water_shot():
    c = Canvas(16, 16)
    c.disc(7.5, 8.5, 5.5, WATER)
    c.disc(7.5, 6.5, 3.0, (110, 190, 255, 240))
    c.disc(6.0, 5.5, 1.5, WATER_CORE)
    # a pointy drip on top so it reads as a droplet
    for i in range(3):
        c.rect(7 - i // 2, 1 + i, 1 + i, 1, WATER)
    return c


def pack_icon():
    """The carrier from the side, sitting on the sea."""
    c = Canvas(128, 128, (140, 200, 245, 255))      # sky
    c.rect(0, 84, 128, 44, SEA)
    # hull, narrowing at the bow
    for y in range(70, 92):
        inset = (y - 70) // 2
        c.rect(10 + inset, y, 108 - inset * 2, 1, HULL)
    c.rect(4, 64, 120, 6, DECK)                      # flight deck
    for x in range(10, 120, 14):
        c.rect(x, 66, 8, 2, DECK_LINE)              # runway dashes
    c.rect(84, 38, 14, 26, TOWER)                    # island tower
    c.rect(86, 42, 10, 4, (40, 60, 80, 255))         # bridge windows
    c.rect(90, 28, 2, 10, TOWER)                     # mast
    # a water blast arcing off the deck
    for i in range(16):
        c.disc(30 + i * 3, 58 - i * 2 + (i * i) // 12, 2.2, WATER)
    return c


if __name__ == "__main__":
    blaster_icon().write(os.path.join(HERE, "RP/textures/items/water_blaster.png"))
    water_shot().write(os.path.join(HERE, "RP/textures/entity/water_shot.png"))
    icon = pack_icon()
    icon.write(os.path.join(HERE, "RP/pack_icon.png"))
    icon.write(os.path.join(HERE, "BP/pack_icon.png"))
