#!/usr/bin/env python3
"""
Generates all the emerald-set textures for the Emerald Sword mod.

Everything green in this mod (the sword icon, the four armor-slot icons, the
shield icon, and the two armor "layer" textures that get painted onto the
player's body) is drawn here in plain Python -- no image editor needed. Re-run
this any time you want to tweak a colour or a shape:

    python3 scripts/gen_emerald_textures.py

Then re-run ./scripts/build_mcpack.sh to repackage. Redrawing these into nicer
pixel art (in any paint program, keeping the same file names/sizes) is a great
kid project.
"""

import os
import struct
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
RP = os.path.join(HERE, "..", "RP")
ITEMS_DIR = os.path.join(RP, "textures", "items")
ARMOR_DIR = os.path.join(RP, "textures", "models", "armor")

# ---- emerald palette (r, g, b, a) -----------------------------------------
T = (0, 0, 0, 0)            # transparent
O = (5, 46, 22, 255)        # near-black outline
D = (11, 122, 54, 255)      # dark green
M = (18, 184, 77, 255)      # mid green
G = (23, 221, 98, 255)      # bright emerald
L = (124, 240, 166, 255)    # light highlight
W = (234, 255, 242, 255)    # sparkle / glint
B = (107, 74, 43, 255)      # handle brown
K = (63, 42, 23, 255)       # dark brown


def write_png(path, pixels):
    """pixels = list of rows; each row = list of (r,g,b,a). Writes RGBA PNG."""
    h = len(pixels)
    w = len(pixels[0])
    raw = bytearray()
    for row in pixels:
        raw.append(0)  # filter type 0 (none)
        for (r, g, b, a) in row:
            raw += bytes((r, g, b, a))

    def chunk(typ, data):
        return (struct.pack(">I", len(data)) + typ + data +
                struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF))

    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0)  # 8-bit RGBA
    idat = zlib.compress(bytes(raw), 9)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(sig + chunk(b"IHDR", ihdr) + chunk(b"IDAT", idat) +
                chunk(b"IEND", b""))
    print("wrote", os.path.relpath(path, os.path.join(HERE, "..")))


def canvas(w, h):
    return [[T for _ in range(w)] for _ in range(h)]


def px(cv, x, y, c):
    if 0 <= y < len(cv) and 0 <= x < len(cv[0]):
        cv[y][x] = c


def rect(cv, x0, y0, x1, y1, c):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            px(cv, x, y, c)


def from_grid(grid, mapping):
    """Build a canvas from a list of equal-length strings + a char->color map."""
    return [[mapping[ch] for ch in row] for row in grid]


# ---------------------------------------------------------------------------
# 16x16 item icons
# ---------------------------------------------------------------------------

def sword_icon():
    # Upright emerald blade with a brown handle.
    g = [
        "       oo       ",
        "      olgo      ",
        "      oglo      ",
        "      olgo      ",
        "      oglo      ",
        "      olgo      ",
        "      oglo      ",
        "      olgo      ",
        "      oglo      ",
        "      oglo      ",
        "    oodmmdoo    ",
        "      okko      ",
        "      obbo      ",
        "      okko      ",
        "      obbo      ",
        "       oo       ",
    ]
    return from_grid(g, {" ": T, "o": O, "d": D, "m": M, "g": G,
                         "l": L, "b": B, "k": K})


def helmet_icon():
    cv = canvas(16, 16)
    rect(cv, 3, 1, 12, 10, O)      # dark shell
    rect(cv, 4, 2, 11, 9, M)       # green fill
    rect(cv, 4, 2, 11, 3, G)       # lit top
    px(cv, 4, 2, L); px(cv, 5, 2, L); px(cv, 6, 2, W)
    rect(cv, 6, 6, 9, 9, T)        # face opening
    rect(cv, 5, 5, 10, 5, O)       # brow line above face
    px(cv, 5, 6, O); px(cv, 10, 6, O)
    px(cv, 5, 7, O); px(cv, 10, 7, O)
    return cv


def chestplate_icon():
    cv = canvas(16, 16)
    rect(cv, 2, 3, 13, 6, O)       # shoulders (dark)
    rect(cv, 3, 4, 12, 5, M)
    rect(cv, 4, 6, 11, 13, O)      # torso outline
    rect(cv, 5, 7, 10, 12, M)      # torso fill
    rect(cv, 5, 7, 10, 8, G)       # lit upper chest
    px(cv, 5, 7, L); px(cv, 6, 7, L)
    rect(cv, 7, 6, 8, 7, T)        # neck notch
    px(cv, 7, 6, O); px(cv, 8, 6, O)
    return cv


def leggings_icon():
    cv = canvas(16, 16)
    rect(cv, 4, 2, 11, 4, O)       # belt
    rect(cv, 5, 3, 10, 3, M)
    rect(cv, 4, 5, 6, 13, O)       # left leg
    rect(cv, 9, 5, 11, 13, O)      # right leg
    rect(cv, 5, 5, 5, 12, M)
    rect(cv, 10, 5, 10, 12, M)
    px(cv, 5, 5, G); px(cv, 10, 5, G)
    return cv


def boots_icon():
    cv = canvas(16, 16)
    # left boot
    rect(cv, 3, 9, 6, 14, O)
    rect(cv, 4, 10, 5, 13, M)
    rect(cv, 3, 13, 7, 14, O)
    px(cv, 4, 10, G)
    # right boot
    rect(cv, 9, 9, 12, 14, O)
    rect(cv, 10, 10, 11, 13, M)
    rect(cv, 8, 13, 12, 14, O)
    px(cv, 10, 10, G)
    return cv


def shield_icon():
    cv = canvas(16, 16)
    rect(cv, 3, 1, 12, 11, O)      # shield outline (top square-ish)
    rect(cv, 4, 12, 11, 13, O)     # taper
    rect(cv, 5, 14, 10, 14, O)     # point
    rect(cv, 4, 2, 11, 11, M)      # green field
    rect(cv, 5, 13, 10, 13, M)
    rect(cv, 6, 14, 9, 14, M)
    rect(cv, 4, 2, 11, 3, G)       # lit top
    px(cv, 4, 2, L); px(cv, 5, 2, W)
    rect(cv, 7, 3, 8, 12, D)       # vertical bar of a cross
    rect(cv, 4, 6, 11, 7, D)       # horizontal bar of a cross
    return cv


# ---------------------------------------------------------------------------
# Armor "layer" textures (64x32) -- these are painted onto the player body by
# the attachables. We fill them fully with an emerald scale pattern so every
# body part the armour geometry covers shows up solid green.
# ---------------------------------------------------------------------------

def armor_layer():
    cv = canvas(64, 32)
    for y in range(32):
        for x in range(64):
            # 2x2 emerald "scales" with a lit top-left and dark bottom-right.
            cx, cy = x % 4, y % 4
            if cx in (0, 1) and cy in (0, 1):
                c = G
            elif cx in (2, 3) and cy in (2, 3):
                c = D
            else:
                c = M
            # thin darker seams every 8px so the plating reads at body scale
            if x % 8 == 0 or y % 8 == 0:
                c = O
            px(cv, x, y, c)
    return cv


def main():
    write_png(os.path.join(ITEMS_DIR, "emerald_sword.png"), sword_icon())
    write_png(os.path.join(ITEMS_DIR, "emerald_helmet.png"), helmet_icon())
    write_png(os.path.join(ITEMS_DIR, "emerald_chestplate.png"), chestplate_icon())
    write_png(os.path.join(ITEMS_DIR, "emerald_leggings.png"), leggings_icon())
    write_png(os.path.join(ITEMS_DIR, "emerald_boots.png"), boots_icon())
    write_png(os.path.join(ITEMS_DIR, "emerald_shield.png"), shield_icon())
    write_png(os.path.join(ARMOR_DIR, "emerald_layer_1.png"), armor_layer())
    write_png(os.path.join(ARMOR_DIR, "emerald_layer_2.png"), armor_layer())


if __name__ == "__main__":
    main()
