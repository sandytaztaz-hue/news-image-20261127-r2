#!/usr/bin/env python3
"""Render the Sum 27 Round 2 broadsheet: one 1024x1024 PNG summing up the
world news of Friday 27 November 2026 (43 stories, 9 regions, 14 fields).

Pure Python standard library only. The PNG writer is hand-rolled (zlib),
and every letter is drawn from a 5x7 bitmap font defined below -- no system
fonts, no image libraries, no network. Run: python3 render.py
Writes entry.png next to this file.
"""
import struct
import zlib
from pathlib import Path

W, H = 1024, 1024

# ---------------------------------------------------------------- PNG writer
def write_png(path, w, h, px):
    """px: bytearray of w*h*3 RGB bytes, top row first. Filter 0 rows."""
    def chunk(kind, data):
        c = struct.pack(">I", len(data)) + kind + data
        return c + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    raw = bytearray()
    stride = w * 3
    for y in range(h):
        raw.append(0)
        raw += px[y * stride:(y + 1) * stride]
    data = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(bytes(raw), 6)))
    data += chunk(b"IEND", b"")
    Path(path).write_bytes(data)

# ------------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(bg) * (w * h)

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = c

    def rect(self, x, y, w, h, c):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            self.px[i:i + (x1 - x0) * 3] = c * (x1 - x0)

    def hline(self, x, y, w, c, t=1):
        self.rect(x, y, w, t, c)

    def vline(self, x, y, h, c, t=1):
        self.rect(x, y, t, h, c)

    def line(self, x0, y0, x1, y1, c, t=1):
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        while True:
            self.rect(x0 - t // 2, y0 - t // 2, t, t, c)
            if x0 == x1 and y0 == y1:
                return
            e = 2 * err
            if e > -dy:
                err -= dy
                x0 += sx
            if e < dx:
                err += dx
                y0 += sy

    def circle(self, cx, cy, r, c):
        for yy in range(-r, r + 1):
            dx = int((r * r - yy * yy) ** 0.5)
            self.rect(cx - dx, cy + yy, dx * 2 + 1, 1, c)

    def ring(self, cx, cy, r, c, t=2):
        for a in range(360):
            import math
            x = int(cx + r * math.cos(math.radians(a)))
            y = int(cy + r * math.sin(math.radians(a)))
            self.rect(x, y, t, t, c)

    def ellipse(self, cx, cy, rx, ry, c):
        for yy in range(-ry, ry + 1):
            dx = int(rx * (1 - (yy / ry) ** 2) ** 0.5) if ry else 0
            self.rect(cx - dx, cy + yy, dx * 2 + 1, 1, c)

    def tri(self, x0, y0, x1, y1, x2, y2, c):
        # scanline triangle fill
        pts = sorted([(x0, y0), (x1, y1), (x2, y2)], key=lambda p: p[1])
        (ax, ay), (bx, by), (cx, cy) = pts
        def edge(xa, ya, xb, yb, y):
            if yb == ya:
                return xa
            return xa + (xb - xa) * (y - ya) / (yb - ya)
        for y in range(ay, cy + 1):
            if y < by:
                xa = edge(ax, ay, bx, by, y)
                xb = edge(ax, ay, cx, cy, y)
            else:
                xa = edge(bx, by, cx, cy, y)
                xb = edge(ax, ay, cx, cy, y)
            x0i, x1i = int(min(xa, xb)), int(max(xa, xb))
            self.rect(x0i, y, x1i - x0i + 1, 1, c)

    def poly(self, pts, c):
        # scanline polygon fill (simple, convex-ish shapes fine)
        ys = [p[1] for p in pts]
        for y in range(int(min(ys)), int(max(ys)) + 1):
            xs = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xs.append(x0 + (x1 - x0) * (y - y0) / (y1 - y0))
            if len(xs) >= 2:
                xs.sort()
                self.rect(int(xs[0]), y, int(xs[-1]) - int(xs[0]) + 1, 1, c)

    def vgrad(self, x, y, w, h, c1, c2):
        for yy in range(h):
            t = yy / max(1, h - 1)
            c = bytes(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))
            self.rect(x, y + yy, w, 1, c)

    def frame(self, x, y, w, h, c, t=1):
        self.rect(x, y, w, t, c)
        self.rect(x, y + h - t, w, t, c)
        self.rect(x, y, t, h, c)
        self.rect(x + w - t, y, t, h, c)

# -------------------------------------------------------------------- palette
WHITE = bytes((255, 255, 255))
BLACK = bytes((16, 16, 18))
INK = bytes((26, 26, 30))
GREY = bytes((110, 110, 115))
LGREY = bytes((205, 205, 208))
RED = bytes((196, 18, 28))
DRED = bytes((150, 10, 20))
BLUE = bytes((22, 72, 150))
LBLUE = bytes((207, 232, 245))
SKY = bytes((186, 222, 240))
PALE = bytes((245, 240, 224))
SAND = bytes((233, 214, 170))
GOLD = bytes((232, 178, 38))
ORANGE = bytes((232, 110, 24))
AMBER = bytes((245, 176, 44))
GREEN = bytes((34, 128, 74))
DGREEN = bytes((18, 92, 52))
TEAL = bytes((0, 128, 128))
PURPLE = bytes((112, 66, 160))
BROWN = bytes((120, 82, 48))
NAVY = bytes((24, 40, 84))
CREAM = bytes((255, 243, 214))
SMOKE = bytes((96, 96, 100))
LSMOKE = bytes((150, 150, 154))

# region colours (also used for map pins + ALSO tags)
REG_COL = {
    "EUROPE": bytes((196, 18, 28)),
    "MIDEAST": bytes((232, 110, 24)),
    "S ASIA": bytes((0, 128, 128)),
    "E ASIA": bytes((22, 72, 150)),
    "SE ASIA": bytes((0, 150, 90)),
    "N AMER": bytes((34, 128, 74)),
    "OCEANIA": bytes((112, 66, 160)),
    "AFRICA": bytes((150, 104, 24)),
    "SPACE": bytes((40, 40, 60)),
}
REG_FULL = {
    "EUROPE": "EUROPE", "MIDEAST": "MIDDLE EAST", "S ASIA": "SOUTH ASIA",
    "E ASIA": "EAST ASIA", "SE ASIA": "SE ASIA", "N AMER": "NORTH AMERICA",
    "OCEANIA": "OCEANIA", "AFRICA": "AFRICA", "SPACE": "GLOBAL & SPACE",
}

# ------------------------------------------------- 5x7 bitmap font (drawn here)
# Each glyph: 7 rows of 5 bits. Widths: most glyphs 5 units; narrow glyphs
# use only columns x0..x0+w-1 of their 5-wide bitmap. Advance = (w+1)*scale.
FONT = {
 '0': ("01110","10001","10011","10101","11001","10001","01110"),
 '1': ("00100","01100","00100","00100","00100","00100","01110"),
 '2': ("01110","10001","00001","00110","01000","10000","11111"),
 '3': ("11111","00010","00100","00010","00001","10001","01110"),
 '4': ("00010","00110","01010","10010","11111","00010","00010"),
 '5': ("11111","10000","11110","00001","00001","10001","01110"),
 '6': ("00110","01000","10000","11110","10001","10001","01110"),
 '7': ("11111","00001","00010","00100","01000","01000","01000"),
 '8': ("01110","10001","10001","01110","10001","10001","01110"),
 '9': ("01110","10001","10001","01111","00001","00010","01100"),
 'A': ("01110","10001","10001","11111","10001","10001","10001"),
 'B': ("11110","10001","10001","11110","10001","10001","11110"),
 'C': ("01110","10001","10000","10000","10000","10001","01110"),
 'D': ("11110","10001","10001","10001","10001","10001","11110"),
 'E': ("11111","10000","10000","11110","10000","10000","11111"),
 'F': ("11111","10000","10000","11110","10000","10000","10000"),
 'G': ("01110","10001","10000","10111","10001","10001","01111"),
 'H': ("10001","10001","10001","11111","10001","10001","10001"),
 'I': ("01110","00100","00100","00100","00100","00100","01110"),
 'J': ("00111","00010","00010","00010","00010","10010","01100"),
 'K': ("10001","10010","10100","11000","10100","10010","10001"),
 'L': ("10000","10000","10000","10000","10000","10000","11111"),
 'M': ("10001","11011","10101","10101","10001","10001","10001"),
 'N': ("10001","11001","10101","10011","10001","10001","10001"),
 'O': ("01110","10001","10001","10001","10001","10001","01110"),
 'P': ("11110","10001","10001","11110","10000","10000","10000"),
 'Q': ("01110","10001","10001","10001","10101","10010","01101"),
 'R': ("11110","10001","10001","11110","10100","10010","10001"),
 'S': ("01111","10000","10000","01110","00001","00001","11110"),
 'T': ("11111","00100","00100","00100","00100","00100","00100"),
 'U': ("10001","10001","10001","10001","10001","10001","01110"),
 'V': ("10001","10001","10001","10001","10001","01010","00100"),
 'W': ("10001","10001","10001","10101","10101","10101","01010"),
 'X': ("10001","10001","01010","00100","01010","10001","10001"),
 'Y': ("10001","10001","01010","00100","00100","00100","00100"),
 'Z': ("11111","00001","00010","00100","01000","10000","11111"),
 'a': ("00000","00000","01110","00001","01111","10001","01111"),
 'b': ("10000","10000","11110","10001","10001","10001","11110"),
 'c': ("00000","00000","01110","10000","10000","10001","01110"),
 'd': ("00001","00001","01111","10001","10001","10001","01111"),
 'e': ("00000","00000","01110","10001","11111","10000","01110"),
 'f': ("00110","01001","01000","11110","01000","01000","01000"),
 'g': ("00000","01111","10001","10001","01111","00001","01110"),
 'h': ("10000","10000","11110","10001","10001","10001","10001"),
 'i': ("00100","00000","01100","00100","00100","00100","01110"),
 'j': ("00100","00000","00100","00100","00100","10100","01100"),
 'k': ("10000","10000","10010","10100","11000","10100","10010"),
 'l': ("01100","00100","00100","00100","00100","00100","01110"),
 'm': ("00000","00000","11010","10101","10101","10101","10101"),
 'n': ("00000","00000","11110","10001","10001","10001","10001"),
 'o': ("00000","00000","01110","10001","10001","10001","01110"),
 'p': ("00000","11110","10001","10001","11110","10000","10000"),
 'q': ("00000","01111","10001","10001","01111","00001","00001"),
 'r': ("00000","00000","10110","11001","10000","10000","10000"),
 's': ("00000","00000","01111","10000","01110","00001","11110"),
 't': ("00100","00100","11110","00100","00100","00100","00110"),
 'u': ("00000","00000","10001","10001","10001","10011","01101"),
 'v': ("00000","00000","10001","10001","10001","01010","00100"),
 'w': ("00000","00000","10001","10101","10101","10101","01010"),
 'x': ("00000","00000","10001","01010","00100","01010","10001"),
 'y': ("00000","00000","10001","10001","01111","00001","01110"),
 'z': ("00000","00000","11111","00010","00100","01000","11111"),
 ' ': ("00000","00000","00000","00000","00000","00000","00000"),
 '.': ("00000","00000","00000","00000","00000","01100","01100"),
 ',': ("00000","00000","00000","00000","01100","00100","01000"),
 ':': ("00000","01100","01100","00000","01100","01100","00000"),
 ';': ("00000","01100","01100","00000","01100","00100","01000"),
 "'": ("00100","00100","01000","00000","00000","00000","00000"),
 '"': ("01010","01010","01010","00000","00000","00000","00000"),
 '!': ("00100","00100","00100","00100","00100","00000","00100"),
 '?': ("01110","10001","00001","00110","00100","00000","00100"),
 '-': ("00000","00000","00000","01110","00000","00000","00000"),
 '\u2013': ("00000","00000","00000","11110","00000","00000","00000"),
 '\u2014': ("00000","00000","00000","11111","00000","00000","00000"),
 '(': ("00010","00100","01000","01000","01000","00100","00010"),
 ')': ("01000","00100","00010","00010","00010","00100","01000"),
 '/': ("00001","00010","00010","00100","01000","01000","10000"),
 '&': ("01100","10010","10100","01000","10101","10010","01101"),
 '\u00b7': ("00000","00000","00000","01100","01100","00000","00000"),
 '%': ("11001","11010","00010","00100","01000","01011","10011"),
 '$': ("00100","01111","10100","01110","00101","11110","00100"),
 '#': ("01010","01010","11111","01010","11111","01010","01010"),
 '+': ("00000","00100","00100","11111","00100","00100","00000"),
 '=': ("00000","00000","11111","00000","11111","00000","00000"),
 '*': ("00000","10101","01110","10101","00000","00000","00000"),
 '_': ("00000","00000","00000","00000","00000","00000","11111"),
 '\u00d7': ("00000","10001","01010","00100","01010","10001","00000"),
}
# glyph width (units) and left column offset inside the 5-wide bitmap
GW = {' ': 3, 'i': 2, 'j': 2, 'l': 2, '.': 2, ',': 2, ':': 2, ';': 2,
      "'": 2, '!': 2, '\u00b7': 2, '(': 3, ')': 3, 'f': 3, 't': 3, 'r': 3,
      '-': 4, '\u2013': 4, '/': 4, '"': 4, '1': 3, 'I': 3}
GX = {'i': 1, 'j': 1, 'l': 1, '.': 1, ',': 1, ':': 1, ';': 1, "'": 1,
      '!': 1, '\u00b7': 1, '(': 1, ')': 1, 'f': 1, 't': 1, 'r': 1, '1': 1, 'I': 1}

def _norm(s):
    return (s.replace('\u2019', "'").replace('\u2018', "'")
             .replace('\u201c', '"').replace('\u201d', '"')
             .replace('\u2022', '\u00b7'))

def gw(ch):
    return GW.get(ch, 5)

def text_w(s, scale=1, gap=1):
    s = _norm(s)
    return sum((gw(c) + gap) * scale for c in s) - gap * scale

def draw_text(cv, x, y, s, scale=1, color=INK, bold=False, italic=False,
              gap=1):
    """Draw text at (x, y) top-left. Returns width in px."""
    s = _norm(s)
    cx = x
    for ch in s:
        g = FONT.get(ch, FONT['?'])
        x0 = GX.get(ch, 0)
        w = gw(ch)
        offs = [(0, 0)]
        if bold:
            offs.append((scale, 0))
        for dx, dy in offs:
            for r in range(7):
                slant = (6 - r) // 2 if italic else 0
                row = g[r]
                for cc in range(x0, x0 + w):
                    if row[cc] == '1':
                        cv.rect(cx + dx + slant * scale + (cc - x0) * scale,
                                y + dy + r * scale, scale, scale, color)
        cx += (w + gap) * scale
    return cx - x - gap * scale

def wrap_text(s, scale, max_w):
    """Greedy word wrap. Returns list of lines that fit max_w."""
    words = _norm(s).split(' ')
    lines, cur = [], ''
    for wd in words:
        trial = wd if not cur else cur + ' ' + wd
        if text_w(trial, scale) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = wd
    if cur:
        lines.append(cur)
    return lines

def para(cv, x, y, s, scale, max_w, color=INK, bold=False, leading=None,
         align='l'):
    """Draw wrapped paragraph, return height used."""
    lh = (7 * scale if leading is None else leading)
    lines = wrap_text(s, scale, max_w)
    for i, ln in enumerate(lines):
        lx = x
        if align == 'c':
            lx = x + (max_w - text_w(ln, scale)) // 2
        elif align == 'r':
            lx = x + max_w - text_w(ln, scale)
        draw_text(cv, lx, y + i * lh, ln, scale, color, bold)
    return len(lines) * lh

def chip(cv, x, y, s, bg, fg=WHITE, scale=1, pad=3):
    """Small coloured label chip; returns width."""
    w = text_w(s, scale) + pad * 2
    h = 7 * scale + pad * 2 - 2
    cv.rect(x, y, w, h, bg)
    draw_text(cv, x + pad, y + pad - 1, s, scale, fg, bold=True)
    return w

# ------------------------------------------------------- scene drawing bits
def person(cv, x, y, c, s=1):
    cv.circle(x, y, 2 * s, c)
    cv.rect(x - 2 * s, y + 2 * s, 4 * s, 5 * s, c)

def building(cv, x, y, w, h, c, win=WHITE, rows=3, cols=3, lit=True):
    cv.rect(x, y, w, h, c)
    if lit:
        for r in range(rows):
            for cc in range(cols):
                wx = x + 3 + cc * max(4, (w - 6) // max(1, cols))
                wy = y + 3 + r * max(4, (h - 6) // max(1, rows))
                if wx + 2 <= x + w - 2 and wy + 2 <= y + h - 2:
                    cv.rect(wx, wy, 2, 2, win)

def smoke(cv, x, y, puffs, c1=SMOKE, c2=LSMOKE, r0=5):
    for i, (dx, dy, r) in enumerate(puffs):
        cv.circle(x + dx, y + dy, r, c1 if i % 2 == 0 else c2)

def flame(cv, x, y, w, h):
    cv.tri(x, y + h, x + w // 2, y, x + w, y + h, ORANGE)
    cv.tri(x + w // 4, y + h, x + w // 2, y + h // 3, x + 3 * w // 4, y + h, GOLD)
    cv.circle(x + w // 2, y + 2 * h // 3, max(2, w // 5), GOLD)

def truck(cv, x, y, w=26, h=10, c=RED):
    cv.rect(x, y, w, h, c)
    cv.rect(x + w - 8, y - 5, 8, 5, c)
    cv.rect(x + 3, y + 2, 5, 4, WHITE)
    cv.circle(x + 5, y + h, 3, BLACK)
    cv.circle(x + w - 5, y + h, 3, BLACK)

def tree(cv, x, y, s=1):
    cv.rect(x, y, 2 * s, 4 * s, BROWN)
    cv.circle(x + s, y - 2 * s, 4 * s, GREEN)

def sun(cv, x, y, r=8, c=GOLD):
    cv.circle(x, y, r, c)
    for a in range(0, 360, 45):
        import math
        cv.line(int(x + (r + 2) * math.cos(math.radians(a))),
                int(y + (r + 2) * math.sin(math.radians(a))),
                int(x + (r + 5) * math.cos(math.radians(a))),
                int(y + (r + 5) * math.sin(math.radians(a))), c, 1)

def star(cv, x, y, c=WHITE, s=1):
    cv.rect(x - s, y, 2 * s + 1, 1, c)
    cv.rect(x, y - s, 1, 2 * s + 1, c)

def flag_v(cv, x, y, w, h, cols):
    n = len(cols)
    for i, c in enumerate(cols):
        cv.rect(x + i * w // n, y, w // n + 1, h, c)

def dome(cv, x, y, w, c=GOLD):
    cv.ellipse(x + w // 2, y, w // 2, w // 3, c)
    cv.rect(x, y, w, 2, c)

def scales(cv, x, y, c=BLACK, s=1):
    cv.vline(x, y, 10 * s, c, 1)
    cv.hline(x - 6 * s, y, 12 * s, c, 1)
    cv.line(x - 6 * s, y, x - 8 * s, y + 6 * s, c, 1)
    cv.line(x - 6 * s, y, x - 4 * s, y + 6 * s, c, 1)
    cv.line(x + 6 * s, y, x + 4 * s, y + 6 * s, c, 1)
    cv.line(x + 6 * s, y, x + 8 * s, y + 6 * s, c, 1)
    cv.tri(x - 8 * s, y + 6 * s, x - 4 * s, y + 6 * s, x - 6 * s, y + 9 * s, c)
    cv.tri(x + 4 * s, y + 6 * s, x + 8 * s, y + 6 * s, x + 6 * s, y + 9 * s, c)

def badge(cv, x, y, s, bg=RED):
    return chip(cv, x, y, s, bg, WHITE, 1, 3)

# ---------------------------------------------------------------- hero scenes
# Each hero scene is 322 wide x 90 tall. Daytime, saturated, packed.

def scene_bangkok(cv, x, y, w, h):
    cv.vgrad(x, y, w, h, bytes((168, 214, 240)), bytes((255, 232, 190)))
    sun(cv, x + w - 26, y + 16, 9)
    # refinery: towers, pipes, tanks
    cv.rect(x, y + h - 26, w, 26, bytes((150, 148, 142)))
    for tx in (x + 18, x + 58, x + 98):
        cv.rect(tx, y + 22, 16, h - 48, bytes((70, 70, 76)))
        for by in range(y + 26, y + h - 32, 8):
            cv.rect(tx, by, 16, 2, GOLD)
        cv.tri(tx + 2, y + 22, tx + 8, y + 12, tx + 14, y + 22, bytes((70, 70, 76)))
    cv.rect(x + 130, y + 48, 34, h - 74, WHITE)
    cv.rect(x + 130, y + 48, 34, 5, RED)
    cv.rect(x + 170, y + 56, 30, h - 80, WHITE)
    cv.rect(x + 170, y + 56, 30, 5, RED)
    cv.rect(x + 20, y + 44, 180, 4, bytes((60, 60, 64)))
    # flames over the middle units
    flame(cv, x + 200, y + 24, 34, 32)
    flame(cv, x + 242, y + 34, 24, 24)
    flame(cv, x + 124, y + 30, 18, 20)
    flame(cv, x + 160, y + 34, 16, 16)
    # smoke columns
    smoke(cv, x + 218, y + 8, [(0, 0, 7), (-8, -2, 6), (8, -3, 6), (0, -8, 5)])
    smoke(cv, x + 138, y + 12, [(0, 0, 6), (-6, -3, 5), (6, -3, 5)])
    # fire crews + hoses + truck, foreground
    truck(cv, x + 12, y + h - 22, 30, 10)
    cv.line(x + 44, y + h - 18, x + 120, y + h - 30, bytes((30, 90, 180)), 2)
    cv.line(x + 44, y + h - 16, x + 150, y + h - 36, bytes((30, 90, 180)), 2)
    for px, py in ((122, 54), (128, 50), (152, 48), (158, 44), (164, 40)):
        cv.rect(x + px, y + py, 2, 2, bytes((30, 90, 180)))
    person(cv, x + 60, y + h - 18, bytes((255, 200, 40)))
    person(cv, x + 72, y + h - 18, bytes((255, 200, 40)))
    person(cv, x + 250, y + h - 18, bytes((255, 200, 40)))
    cv.rect(x, y + h - 8, w, 8, bytes((90, 88, 84)))
    badge(cv, x + 6, y + 6, "ALL UNITS SHUT")

def scene_kuwait(cv, x, y, w, h):
    cv.vgrad(x, y, w, h, bytes((255, 226, 170)), bytes((150, 205, 235)))
    sun(cv, x + 30, y + 16, 9)
    # desert ground
    cv.rect(x, y + h - 26, w, 26, bytes((238, 205, 140)))
    cv.rect(x, y + h - 26, w, 3, bytes((210, 170, 95)))
    # Kuwait Towers left
    for tx, th in ((x + 22, 46), (x + 44, 58), (x + 64, 40)):
        cv.rect(tx, y + h - 26 - th, 5, th, bytes((70, 130, 150)))
        cv.circle(tx + 2, y + h - 26 - th + 12, 7, bytes((70, 130, 150)))
    # city blocks right
    building(cv, x + w - 90, y + h - 62, 20, 36, bytes((120, 120, 128)), rows=4, cols=3)
    building(cv, x + w - 66, y + h - 52, 16, 26, bytes((140, 140, 148)), rows=3, cols=2)
    building(cv, x + w - 46, y + h - 70, 24, 44, bytes((100, 100, 110)), rows=5, cols=3)
    # drone silhouette centre
    dx, dy = x + w // 2, y + 30
    cv.poly([(dx - 34, dy), (dx - 8, dy - 4), (dx + 8, dy - 4), (dx + 34, dy),
             (dx + 8, dy + 3), (dx, dy + 8), (dx - 8, dy + 3)], BLACK)
    cv.circle(dx, dy, 3, BLACK)
    for tx in (dx - 40, dx - 48, dx - 56):
        cv.rect(tx, dy + 1, 2, 2, WHITE)
    # explosion starburst under drone
    ex, ey = x + w // 2 + 58, y + 58
    for a in range(0, 360, 30):
        import math
        cv.line(ex, ey, int(ex + 16 * math.cos(math.radians(a))),
                int(ey + 16 * math.sin(math.radians(a))), ORANGE, 2)
    cv.circle(ex, ey, 9, GOLD)
    cv.circle(ex, ey, 5, RED)
    smoke(cv, ex, ey - 14, [(0, 0, 6), (-7, -2, 5), (7, -2, 5), (0, -8, 4)])
    # Italian flag on a pole
    cv.vline(x + w - 130, y + 18, 34, BLACK, 2)
    flag_v(cv, x + w - 128, y + 18, 24, 12, [GREEN, WHITE, RED])
    # people / vehicles foreground
    person(cv, x + 100, y + h - 16, bytes((30, 60, 120)))
    person(cv, x + 112, y + h - 16, bytes((30, 60, 120)))
    truck(cv, x + 150, y + h - 20, 26, 10, bytes((220, 220, 220)))
    badge(cv, x + 6, y + 6, "2 KILLED")

def scene_brussels(cv, x, y, w, h):
    cv.vgrad(x, y, w, h, bytes((140, 190, 240)), bytes((220, 235, 250)))
    sun(cv, x + w - 28, y + 16, 9)
    # Berlaymont: big blue-grey block, window grid, curved wing
    cv.rect(x + 20, y + 30, 200, h - 60, bytes((96, 120, 150)))
    for r in range(4):
        for cc in range(12):
            wx = x + 28 + cc * 16
            wy = y + 38 + r * 11
            cv.rect(wx, wy, 10, 6, bytes((255, 244, 190)) if (r + cc) % 3 else bytes((190, 215, 235)))
    cv.rect(x + 20, y + 30, 200, 6, bytes((70, 95, 125)))
    cv.rect(x + 220, y + 44, 70, h - 74, bytes((120, 140, 168)))
    for r in range(3):
        for cc in range(4):
            cv.rect(x + 228 + cc * 16, y + 52 + r * 11, 10, 6, bytes((255, 244, 190)))
    # circle of gold stars above the building
    import math
    for a in range(0, 360, 30):
        sx = int(x + 120 + 78 * math.cos(math.radians(a)))
        sy = int(y + 22 + 12 * math.sin(math.radians(a)))
        star(cv, sx, sy, GOLD, 1)
    # flags row in front
    for i, cols in enumerate(([BLUE], [bytes((0, 0, 0)), GOLD, RED],
                              [BLUE, WHITE, RED], [BLACK, RED, GOLD],
                              [GREEN, WHITE, RED])):
        fx = x + 30 + i * 26
        cv.vline(fx, y + h - 34, 22, BLACK, 1)
        if len(cols) == 1:
            cv.rect(fx + 1, y + h - 34, 18, 11, BLUE)
            star(cv, fx + 10, y + h - 29, GOLD, 1)
        else:
            flag_v(cv, fx + 1, y + h - 34, 18, 11, cols)
    # crowd + trees
    for px in range(x + 250, x + w - 8, 12):
        person(cv, px, y + h - 16, bytes((40, 40, 60)))
    tree(cv, x + 8, y + h - 14)
    cv.rect(x, y + h - 8, w, 8, bytes((90, 110, 90)))
    badge(cv, x + 6, y + 6, "2028-34 BUDGET", bg=BLUE)

# ------------------------------------------------------------ small scenes
# Each small scene is ~192 wide x 48 tall: bright sky, 4+ elements, badge.

def scene_gaza(cv, x, y, w, h):
    cv.vgrad(x, y, w, h, bytes((255, 228, 180)), bytes((245, 205, 140)))
    building(cv, x + 6, y + 16, 34, h - 24, bytes((214, 182, 130)), rows=3, cols=4)
    building(cv, x + 46, y + 10, 28, h - 18, bytes((198, 164, 110)), rows=4, cols=3)
    building(cv, x + 80, y + 20, 30, h - 28, bytes((222, 192, 140)), rows=2, cols=3)
    flame(cv, x + 118, y + 22, 18, 18)
    smoke(cv, x + 128, y + 10, [(0, 0, 6), (-6, -2, 5), (6, -2, 5)])
    person(cv, x + 150, y + h - 12, bytes((60, 40, 30)))
    person(cv, x + 162, y + h - 12, bytes((60, 40, 30)))
    person(cv, x + 174, y + h - 12, bytes((60, 40, 30)))
    tree(cv, x + w - 14, y + h - 10)
    cv.rect(x, y + h - 6, w, 6, bytes((170, 130, 80)))
    badge(cv, x + 4, y + 4, "10 KILLED")

def scene_kyiv(cv, x, y, w, h):
    cv.vgrad(x, y, w, h, bytes((140, 200, 240)), bytes((215, 235, 250)))
    # gold-domed church
    cv.rect(x + 10, y + 22, 26, h - 30, WHITE)
    dome(cv, x + 10, y + 20, 26)
    cv.rect(x + 40, y + 28, 16, h - 36, bytes((200, 210, 220)))
    building(cv, x + 62, y + 18, 22, h - 26, bytes((120, 130, 145)), rows=3, cols=2)
    building(cv, x + 88, y + 24, 20, h - 32, bytes((140, 150, 165)), rows=2, cols=2)
    # missile trails
    cv.line(x + 120, y + 6, x + 150, y + 26, WHITE, 2)
    cv.line(x + 150, y + 6, x + 128, y + 22, WHITE, 2)
    cv.circle(x + 120, y + 6, 3, GOLD)
    cv.circle(x + 150, y + 6, 3, GOLD)
    smoke(cv, x + 152, y + 30, [(0, 0, 5), (-5, -2, 4), (5, -2, 4)])
    person(cv, x + 170, y + h - 12, bytes((30, 60, 120)))
    cv.rect(x, y + h - 6, w, 6, bytes((90, 110, 90)))
    badge(cv, x + 4, y + 4, "MISSILES HIT", bg=NAVY)

def scene_riyadh(cv, x, y, w, h):
    cv.vgrad(x, y, w, h, bytes((120, 205, 220)), bytes((210, 240, 245)))
    # Kingdom Centre tower with arch
    cv.rect(x + 14, y + 10, 20, h - 18, WHITE)
    cv.tri(x + 14, y + 10, x + 24, y + 2, x + 34, y + 10, WHITE)
    cv.rect(x + 21, y + 14, 6, 8, bytes((120, 205, 220)))
    building(cv, x + 42, y + 18, 22, h - 26, bytes((230, 230, 235)), rows=3, cols=2)
    building(cv, x + 68, y + 24, 18, h - 32, bytes((210, 215, 225)), rows=2, cols=2)
    # interceptor arcs
    cv.line(x + 96, y + 44, x + 130, y + 12, WHITE, 2)
    cv.line(x + 110, y + 44, x + 150, y + 16, WHITE, 2)
    cv.circle(x + 130, y + 12, 4, GOLD)
    cv.circle(x + 150, y + 16, 4, GOLD)
    smoke(cv, x + 132, y + 10, [(0, 0, 4), (-4, -2, 3), (4, -2, 3)])
    person(cv, x + 168, y + h - 12, bytes((20, 90, 90)))
    person(cv, x + 178, y + h - 12, bytes((20, 90, 90)))
    cv.rect(x, y + h - 6, w, 6, bytes((200, 180, 120)))
    badge(cv, x + 4, y + 4, "2 DOWN", bg=TEAL)

def scene_london(cv, x, y, w, h):
    cv.vgrad(x, y, w, h, bytes((185, 215, 235)), bytes((240, 242, 245)))
    # Big Ben + dome + Shard
    cv.rect(x + 12, y + 10, 12, h - 18, bytes((150, 125, 80)))
    cv.tri(x + 12, y + 10, x + 18, y + 2, x + 24, y + 10, bytes((60, 90, 60)))
    cv.circle(x + 18, y + 16, 3, WHITE)
    cv.rect(x + 30, y + 24, 26, h - 32, bytes((170, 170, 180)))
    dome(cv, x + 30, y + 22, 26, bytes((120, 140, 120)))
    cv.tri(x + 62, y + h - 8, x + 76, y + 6, x + 90, y + h - 8, bytes((90, 130, 170)))
    building(cv, x + 96, y + 20, 20, h - 28, bytes((140, 150, 165)), rows=3, cols=2)
    # red bus + river
    cv.rect(x + 120, y + h - 20, 30, 10, RED)
    cv.rect(x + 124, y + h - 18, 22, 4, WHITE)
    cv.circle(x + 126, y + h - 9, 2, BLACK)
    cv.circle(x + 144, y + h - 9, 2, BLACK)
    cv.rect(x + 156, y + h - 14, 30, 4, bytes((120, 170, 210)))
    person(cv, x + 160, y + h - 20, bytes((40, 40, 60)))
    person(cv, x + 172, y + h - 20, bytes((40, 40, 60)))
    cv.rect(x, y + h - 6, w, 6, bytes((90, 110, 90)))
    badge(cv, x + 4, y + 4, "SINCE 1997", bg=NAVY)

def scene_pyongyang(cv, x, y, w, h):
    cv.vgrad(x, y, w, h, bytes((28, 48, 100)), bytes((60, 90, 160)))
    for sx, sy in ((14, 8), (40, 6), (70, 10), (120, 6), (160, 8), (180, 12)):
        star(cv, x + sx, y + sy, WHITE, 1)
    # floodlight beams
    cv.line(x + 30, y + h - 8, x + 70, y + 8, bytes((255, 240, 170)), 1)
    cv.line(x + 160, y + h - 8, x + 120, y + 8, bytes((255, 240, 170)), 1)
    # rocket on launcher
    cv.rect(x + 88, y + 12, 10, 24, WHITE)
    cv.tri(x + 88, y + 12, x + 93, y + 2, x + 98, y + 12, RED)
    cv.rect(x + 84, y + 36, 18, 4, bytes((80, 80, 90)))
    flame(cv, x + 88, y + 40, 10, 8)
    # parade square + flags + crowd
    cv.rect(x, y + h - 10, w, 10, bytes((200, 60, 60)))
    for fx in (x + 8, x + 150, x + 170):
        cv.vline(fx, y + 22, 16, WHITE, 1)
        cv.rect(fx + 1, y + 22, 12, 7, RED)
        star(cv, fx + 7, y + 25, WHITE, 1)
    for px in range(x + 120, x + 148, 8):
        person(cv, px, y + h - 16, bytes((220, 220, 230)))
    badge(cv, x + 4, y + 4, "MORE NUKES", bg=DRED)

def scene_pretoria(cv, x, y, w, h):
    cv.vgrad(x, y, w, h, bytes((150, 210, 245)), bytes((255, 240, 200)))
    sun(cv, x + w - 20, y + 12, 7)
    # court: pediment + columns
    cv.tri(x + 20, y + 14, x + 80, y + 14, x + 50, y + 4, bytes((220, 205, 170)))
    for cx in (x + 26, x + 44, x + 62, x + 80):
        cv.rect(cx, y + 14, 6, h - 28, WHITE)
    cv.rect(x + 20, y + h - 14, 66, 6, bytes((200, 185, 150)))
    cv.rect(x + 96, y + 20, 30, h - 28, bytes((190, 170, 130)))
    scales(cv, x + 140, y + 18, BLACK)
    flag_v(cv, x + 158, y + 8, 22, 12, [RED, WHITE, GREEN])
    tree(cv, x + 8, y + h - 12)
    person(cv, x + 130, y + h - 12, bytes((30, 60, 120)))
    cv.rect(x, y + h - 6, w, 6, bytes((90, 130, 80)))
    badge(cv, x + 4, y + 4, "COURT WIN", bg=DGREEN)

def scene_wellington(cv, x, y, w, h):
    cv.vgrad(x, y, w, h, bytes((150, 215, 245)), bytes((230, 245, 255)))
    # green hills + Beehive
    cv.ellipse(x + 30, y + h - 4, 46, 5, GREEN)
    cv.ellipse(x + w - 30, y + h - 4, 50, 5, bytes((60, 150, 90)))
    cv.rect(x + 12, y + 16, 22, h - 24, bytes((200, 200, 205)))
    cv.ellipse(x + 23, y + 16, 11, 6, bytes((200, 200, 205)))
    cv.rect(x + 40, y + 24, 16, h - 32, bytes((170, 175, 185)))
    # seat chart: 67 green vs 64 grey
    bx, by = x + 66, y + 10
    for i in range(10):
        cv.rect(bx + i * 5, by + 8 - (8 if i < 7 else 4), 4, (8 if i < 7 else 4), GREEN if i < 7 else LGREY)
    draw_text(cv, bx, by + 12, "67-64", 1, BLACK, bold=True)
    # harbour + boats
    cv.rect(x + 120, y + h - 14, 66, 6, bytes((90, 160, 210)))
    cv.tri(x + 130, y + h - 14, x + 136, y + h - 24, x + 142, y + h - 14, WHITE)
    person(cv, x + 160, y + h - 20, bytes((30, 60, 120)))
    badge(cv, x + 4, y + 4, "67 / 131", bg=PURPLE)

def scene_newyork(cv, x, y, w, h):
    cv.vgrad(x, y, w, h, bytes((120, 140, 175)), bytes((200, 210, 225)))
    # skyscrapers with lit windows
    building(cv, x + 8, y + 8, 22, h - 16, bytes((70, 80, 105)), win=GOLD, rows=4, cols=3)
    building(cv, x + 34, y + 16, 18, h - 24, bytes((90, 100, 125)), win=GOLD, rows=3, cols=2)
    building(cv, x + 56, y + 4, 20, h - 12, bytes((60, 70, 95)), win=GOLD, rows=5, cols=2)
    building(cv, x + 80, y + 14, 24, h - 22, bytes((80, 90, 115)), win=GOLD, rows=3, cols=3)
    # rain streaks
    for rx in range(x + 110, x + w - 6, 10):
        cv.line(rx, y + 6, rx - 3, y + 16, bytes((230, 240, 250)), 1)
        cv.line(rx, y + 26, rx - 3, y + 36, bytes((230, 240, 250)), 1)
    # sagging power line + dark houses
    cv.line(x + 108, y + 18, x + 140, y + 26, BLACK, 1)
    cv.line(x + 140, y + 26, x + 172, y + 18, BLACK, 1)
    cv.line(x + 140, y + 26, x + 140, y + 34, BLACK, 1)
    cv.rect(x + 112, y + h - 16, 26, 10, bytes((50, 50, 60)))
    cv.rect(x + 144, y + h - 16, 26, 10, bytes((50, 50, 60)))
    cv.rect(x + 176, y + h - 16, 14, 10, bytes((50, 50, 60)))
    truck(cv, x + 118, y + h - 12, 22, 8, bytes((220, 170, 40)))
    badge(cv, x + 4, y + 4, "500,000 DARK", bg=NAVY)

def scene_delhi(cv, x, y, w, h):
    cv.vgrad(x, y, w, h, bytes((255, 220, 170)), bytes((255, 240, 210)))
    sun(cv, x + w - 20, y + 12, 7)
    # red sandstone court + dome
    cv.rect(x + 16, y + 18, 66, h - 26, bytes((178, 90, 60)))
    dome(cv, x + 40, y + 16, 18, bytes((220, 200, 160)))
    for cx in (x + 22, x + 40, x + 58, x + 74):
        cv.rect(cx, y + 22, 4, h - 30, bytes((220, 200, 160)))
    cv.rect(x + 88, y + 24, 24, h - 32, bytes((200, 120, 85)))
    scales(cv, x + 128, y + 16, BLACK)
    flag_v(cv, x + 150, y + 8, 22, 12, [bytes((255, 140, 40)), WHITE, GREEN])
    tree(cv, x + 6, y + h - 12)
    person(cv, x + 118, y + h - 12, bytes((120, 40, 30)))
    cv.rect(x, y + h - 6, w, 6, bytes((90, 130, 80)))
    badge(cv, x + 4, y + 4, "COURT RULES", bg=DRED)

def scene_mumbai(cv, x, y, w, h):
    cv.vgrad(x, y, w, h, bytes((140, 200, 240)), bytes((220, 238, 250)))
    # towers + sea link curve
    building(cv, x + 8, y + 10, 20, h - 18, bytes((100, 115, 140)), rows=4, cols=2)
    building(cv, x + 32, y + 18, 18, h - 26, bytes((120, 135, 160)), rows=3, cols=2)
    building(cv, x + 54, y + 6, 22, h - 14, bytes((85, 100, 125)), rows=5, cols=2)
    cv.line(x + 80, y + h - 10, x + 130, y + h - 22, bytes((200, 200, 210)), 2)
    cv.line(x + 130, y + h - 22, x + 180, y + h - 10, bytes((200, 200, 210)), 2)
    cv.vline(x + 130, y + h - 30, 10, bytes((200, 200, 210)), 2)
    # sea + boat + gavel
    cv.rect(x + 80, y + h - 8, w - 80, 8, bytes((70, 140, 200)))
    cv.tri(x + 96, y + h - 16, x + 102, y + h - 24, x + 108, y + h - 16, WHITE)
    cv.rect(x + 150, y + 8, 3, 14, BROWN)
    cv.rect(x + 144, y + 6, 15, 6, BROWN)
    cv.rect(x + 146, y + 22, 12, 3, BROWN)
    person(cv, x + 170, y + h - 16, bytes((30, 60, 120)))
    badge(cv, x + 4, y + 4, "COURT FIGHT", bg=NAVY)

# ------------------------------------------------------------------- map
LAND = bytes((196, 222, 164))
OCEAN = bytes((208, 232, 244))
CONTINENTS = [
 # North America
 [(-168, 66), (-150, 70), (-135, 69), (-125, 71), (-110, 68), (-95, 69),
  (-85, 66), (-80, 73), (-68, 58), (-60, 55), (-55, 47), (-60, 45),
  (-70, 42), (-74, 39), (-76, 35), (-80, 32), (-81, 26), (-84, 30),
  (-90, 21), (-94, 18), (-97, 16), (-105, 20), (-110, 23), (-114, 29),
  (-117, 33), (-122, 37), (-124, 42), (-124, 48), (-130, 55), (-140, 60),
  (-152, 58), (-162, 58), (-168, 66)],
 # Greenland
 [(-58, 64), (-52, 60), (-43, 60), (-40, 64), (-32, 68), (-25, 70),
  (-20, 74), (-30, 76), (-45, 76), (-58, 74), (-58, 64)],
 # South America
 [(-80, 10), (-72, 12), (-62, 9), (-52, 5), (-50, 0), (-44, -3),
  (-35, -8), (-37, -13), (-40, -20), (-48, -27), (-52, -33), (-58, -35),
  (-62, -41), (-66, -47), (-69, -52), (-71, -54), (-74, -44), (-73, -37),
  (-71, -30), (-70, -20), (-77, -12), (-81, -5), (-80, 2), (-80, 10)],
 # Africa
 [(-17, 15), (-16, 21), (-13, 27), (-9, 31), (-5, 35), (0, 36), (6, 37),
  (10, 37), (15, 32), (20, 32), (25, 32), (30, 31), (32, 31), (35, 28),
  (37, 22), (39, 18), (43, 12), (48, 11), (51, 11), (51, 5), (48, 0),
  (43, -5), (40, -10), (40, -16), (36, -20), (33, -26), (29, -30),
  (26, -34), (20, -35), (17, -33), (15, -27), (12, -18), (12, -12),
  (9, -1), (9, 4), (4, 6), (-3, 5), (-8, 5), (-13, 8), (-17, 12),
  (-17, 15)],
 # Europe
 [(-10, 36), (-9, 38), (-9, 43), (-4, 44), (-2, 47), (-1, 49), (0, 51),
  (2, 51), (4, 53), (7, 54), (8, 57), (10, 58), (12, 56), (18, 56),
  (21, 55), (21, 58), (24, 59), (26, 60), (30, 62), (32, 64), (35, 66),
  (40, 67), (44, 68), (46, 66), (42, 63), (40, 60), (38, 58), (35, 55),
  (33, 52), (30, 50), (28, 47), (26, 45), (24, 44), (23, 40), (22, 38),
  (19, 42), (16, 44), (12, 44), (10, 44), (8, 44), (6, 43), (3, 42),
  (0, 39), (-2, 37), (-6, 36), (-9, 37), (-10, 36)],
 # Asia
 [(30, 60), (32, 64), (36, 66), (40, 68), (45, 68), (50, 69), (55, 69),
  (60, 70), (68, 72), (75, 73), (80, 73), (90, 75), (100, 76), (110, 74),
  (115, 73), (125, 72), (135, 72), (145, 72), (155, 70), (162, 69),
  (170, 67), (178, 66), (178, 64), (170, 60), (162, 59), (158, 56),
  (156, 52), (150, 59), (142, 54), (142, 50), (140, 45), (138, 42),
  (135, 40), (130, 38), (127, 40), (126, 38), (124, 33), (122, 30),
  (120, 27), (118, 24), (112, 22), (109, 18), (108, 13), (105, 9),
  (104, 8), (101, 7), (99, 10), (98, 14), (96, 16), (94, 18), (92, 21),
  (89, 22), (86, 20), (83, 17), (80, 13), (78, 8), (76, 10), (74, 15),
  (72, 20), (70, 22), (67, 25), (64, 25), (61, 25), (58, 26), (56, 27),
  (54, 27), (52, 28), (50, 29), (48, 30), (46, 30), (44, 30), (42, 32),
  (40, 34), (38, 36), (36, 36), (34, 36), (32, 36), (30, 36), (30, 40),
  (28, 42), (28, 46), (30, 50), (30, 55), (30, 60)],
 # Australia
 [(113, -22), (113, -26), (114, -30), (115, -33), (115, -35), (118, -35),
  (122, -34), (125, -33), (129, -32), (132, -32), (134, -33), (136, -35),
  (138, -35), (140, -38), (143, -39), (146, -39), (148, -38), (150, -37),
  (151, -34), (153, -30), (153, -27), (152, -24), (150, -22), (148, -20),
  (146, -19), (144, -15), (142, -11), (141, -13), (138, -15), (136, -12),
  (135, -12), (132, -12), (130, -13), (128, -14), (126, -14), (124, -16),
  (122, -17), (120, -19), (117, -20), (114, -22), (113, -22)],
 # SE Asia islands + Japan + UK + NZ + Madagascar (ellipses lon/lat/r)
]
ISLANDS = [(100, 2, 3, 2), (104, -2, 3, 2), (110, -7, 4, 2), (116, -8, 3, 2),
           (122, -4, 3, 2), (128, -2, 3, 2), (140, 38, 2, 3), (139, 35, 2, 2),
           (-2, 54, 2, 3), (167, -45, 2, 3), (174, -41, 2, 2), (47, -19, 2, 4),
           (100, 14, 2, 2), (105, 10, 2, 2), (96, 10, 2, 2)]

PINS = [  # (num, lon, lat, region key)
 (1, 100.5, 13.7, "SE ASIA"), (2, 48.0, 29.4, "MIDEAST"),
 (3, 4.4, 50.8, "EUROPE"), (4, 34.5, 31.5, "MIDEAST"),
 (5, 30.5, 50.4, "EUROPE"), (6, 46.7, 24.7, "MIDEAST"),
 (7, -0.1, 51.5, "EUROPE"), (8, 125.8, 39.0, "E ASIA"),
 (9, 28.2, -25.7, "AFRICA"), (10, 174.8, -41.3, "OCEANIA"),
 (11, -74.0, 40.7, "N AMER"), (12, 77.2, 28.6, "S ASIA"),
 (13, 72.9, 19.1, "S ASIA"),
]

# nudge pins apart where cities crowd (London/Brussels, Kuwait/Riyadh, Delhi/Mumbai)
PIN_OFF = {7: (-14, -8), 3: (12, -10), 2: (-4, -12), 6: (10, 8),
           12: (-6, -12), 13: (12, 12), 4: (8, 8), 5: (0, -6)}

def draw_map(cv, x, y, w, h):
    cv.rect(x, y, w, h, OCEAN)
    # graticule
    for lon in range(-150, 181, 30):
        gx = x + (lon + 170) / 360 * w
        cv.vline(int(gx), y, h, bytes((225, 240, 250)), 1)
    for lat in range(-30, 61, 30):
        gy = y + (80 - lat) / 138 * h
        cv.hline(x, int(gy), w, bytes((225, 240, 250)), 1)
    def px(lon, lat):
        return (x + (lon + 170) / 360 * w, y + (80 - lat) / 138 * h)
    for poly in CONTINENTS:
        cv.poly([px(lon, lat) for lon, lat in poly], LAND)
    for lon, lat, rx, ry in ISLANDS:
        cx, cy = px(lon, lat)
        cv.ellipse(int(cx), int(cy), max(2, int(rx * w / 360)),
                   max(2, int(ry * h / 138)), LAND)
    # pins
    for num, lon, lat, reg in PINS:
        cx, cy = px(lon, lat)
        ox, oy = PIN_OFF.get(num, (0, 0))
        cx, cy = int(cx) + ox, int(cy) + oy
        cv.circle(cx, cy, 9, WHITE)
        cv.circle(cx, cy, 8, REG_COL[reg])
        lab = str(num)
        draw_text(cv, cx - text_w(lab, 1) // 2, cy - 4, lab, 1, WHITE, bold=True)
    cv.frame(x, y, w, h, bytes((120, 140, 150)), 1)

# --------------------------------------------------------------------- data
STATUSES = {"CONFIRMED": GREEN, "OFFICIAL": BLUE, "REPORTED": bytes((70, 70, 80)),
            "CLAIM": ORANGE}

HEROES = [
 dict(scene=scene_bangkok, label="BANGKOK \u00b7 DISASTER",
      head="Massive fire engulfs Bangkok oil refinery",
      deck=("Blaze at the Bangchak refinery injures several workers; the "
            "company shuts every unit."),
      why="WHY IT MATTERS: Thailand's top refinery offline; fuel prices and flights face days of disruption.",
      src="Reuters", status="CONFIRMED"),
 dict(scene=scene_kuwait, label="KUWAIT \u00b7 WAR",
      head="Iranian drones kill two Italians in Kuwait",
      deck=("Officials say two Italian nationals died in an Iranian drone "
            "attack on Kuwait. Rome confirms the deaths."),
      why="WHY IT MATTERS: First Iranian strike to kill Europeans in the Gulf; Rome demands answers, oil jumps.",
      src="NYT", status="REPORTED"),
 dict(scene=scene_brussels, label="BRUSSELS \u00b7 POLITICS",
      head="EU summit wraps up after two days on budget and Ukraine",
      deck=("Leaders close the two-day Brussels summit on the 2028-34 budget "
            "and Ukraine funding. The budget deal is unfinished."),
      why="WHY IT MATTERS: Seven years of EU spending and Kyiv's war funding now hinge on one unfinished deal.",
      src="EU Council", status="OFFICIAL"),
]

SMALL = [
 dict(scene=scene_gaza, label="GAZA \u2014 WAR",
      head="Israel kills 10 in Gaza; Hamas weighs reply",
      deck=("Israel kills 10 in Gaza; Hamas weighs its response."),
      src="Reuters", status="REPORTED"),
 dict(scene=scene_kyiv, label="KYIV \u2014 WAR",
      head="Russian missiles hit Kyiv, mayor says",
      deck=("Missiles hit Kyiv; the mayor reports damage. Residents shelter."),
      src="AP", status="REPORTED"),
 dict(scene=scene_riyadh, label="RIYADH \u2014 WAR",
      head="Saudis intercept two Houthi missiles aimed at Riyadh",
      deck=("Air defences down two Houthi missiles. Riyadh reports no damage."),
      src="Reuters", status="CONFIRMED"),
 dict(scene=scene_london, label="LONDON \u2014 MIGRATION",
      head="UK net migration falls to lowest since 1997",
      deck=("Net migration at its lowest since 1997. Arrivals fall as rules bite."),
      src="ONS", status="OFFICIAL"),
 dict(scene=scene_pyongyang, label="PYONGYANG \u2014 NUCLEAR",
      head="Kim vows more nuclear weapons, snubs Trump overture",
      deck=("Kim pledges more nukes and snubs Trump. Pyongyang rejects the US."),
      src="KCNA", status="CLAIM"),
 dict(scene=scene_pretoria, label="PRETORIA \u2014 POLITICS",
      head="Ramaphosa wins court fight over report",
      deck=("Court backs Ramaphosa on impeachment report. President cleared."),
      src="Reuters", status="CONFIRMED"),
 dict(scene=scene_wellington, label="WELLINGTON \u2014 ELECTION",
      head="NZ final result: coalition holds 67 of 131 seats",
      deck=("Final count: coalition holds 67 of 131 seats. A two-seat majority."),
      src="Electoral Comm.", status="OFFICIAL"),
 dict(scene=scene_newyork, label="NEW YORK \u2014 STORM",
      head="Thanksgiving storm leaves 500,000 without power",
      deck=("Thanksgiving storm cuts power to 500,000. Crews race to restore lines."),
      src="AP", status="REPORTED"),
 dict(scene=scene_delhi, label="NEW DELHI \u2014 COURT",
      head="Top court: PMLA attachment needs a judicial member",
      deck=("PMLA attachment needs a judicial member. Top court tightens rules."),
      src="Supreme Court", status="OFFICIAL"),
 dict(scene=scene_mumbai, label="MUMBAI \u2014 BUSINESS",
      head="Tata Trusts take Chandrasekaran fight to court",
      deck=("Tata Trusts to fight reappointment in court. Boardroom row goes on."),
      src="Mint", status="REPORTED"),
]

ALSO = [
 (14, "Karachi", "S ASIA", "Collapse kills 3, injures 14", "Dunya"),
 (15, "New Delhi", "S ASIA", "Court quashes ex-MP release", "SC"),
 (16, "New Delhi", "S ASIA", "Cabinet clears Rs 11,000 cr plan", "Govt"),
 (17, "New Delhi", "S ASIA", "GST cancellations auto from 1 Dec", "Govt"),
 (18, "New Delhi", "S ASIA", "IITs add 6,000 AI, robotics seats", "IIT"),
 (19, "Beijing", "E ASIA", "Border areas 'generally stable'", "China"),
 (20, "Beijing", "E ASIA", "Drones reshape Asia's militaries", "Reuters"),
 (21, "Washington", "N AMER", "Trump unveils new tariffs", "White House"),
 (22, "Washington", "N AMER", "Army hails Iowa explosives win", "US Army"),
 (23, "Washington", "N AMER", "Huang cleared of security threat", "Reuters"),
 (24, "Doha", "MIDEAST", "India A v Sri Lanka A, semi-final", "Asia Cup"),
 (25, "Christchurch", "OCEANIA", "India begin 2nd Test vs NZ, 11am", "NZC"),
 (26, "London", "EUROPE", "Sinner out of Australian Open, knee", "ATP"),
 (27, "London", "EUROPE", "Barnett to captain All Blacks v England", "NZR"),
 (28, "Paris", "EUROPE", "Depardieu faces trial over 2018 rape", "AFP"),
 (29, "Dhaka", "S ASIA", "'India weakened Pakistan in 1971'", "Parliament"),
 (30, "Islamabad", "S ASIA", "Pakistan marks 25 Nov as space day", "Govt"),
 (31, "Islamabad", "S ASIA", "PM orders fast cybercrime reforms", "Govt"),
 (32, "Muzaffarabad", "S ASIA", "Assembly backs JAAC talks", "AJK"),
 (33, "Geneva", "EUROPE", "Gukesh faces Sindarov in Game 4", "FIDE"),
 (34, "San Francisco", "N AMER", "Claude artifacts become apps", "Anthropic"),
 (35, "Pasadena", "SPACE", "Planet hinted beyond Neptune", "astronomers"),
 (36, "Mumbai", "S ASIA", "Flipkart CEO to step down next month", "company"),
 (37, "Auckland", "OCEANIA", "Black Friday deals 'no cheaper'", "Consumer NZ"),
 (38, "Wellington", "OCEANIA", "School English curriculum paused", "Ministry"),
 (39, "Auckland", "OCEANIA", "Driver licence waits hit 80 days", "NZTA"),
 (40, "Sydney", "OCEANIA", "Kibon sidelined in PGA opener", "DP World Tour"),
 (41, "New York", "N AMER", "US markets reopen for short session", "NYSE"),
 (42, "Brussels", "EUROPE", "EU budget summit ends, no deal", "Reuters"),
 (43, "New York", "N AMER", "Target, Kohl's gift giveaways", "The Street"),
]

STATS = [
 ("2", "Italians killed in Kuwait"),
 ("3", "dead in Karachi collapse"),
 ("500,000", "homes dark in US storm"),
 ("10", "killed in Gaza strikes"),
 ("67/131", "NZ coalition's majority"),
 ("1997", "UK migration lowest since"),
 ("11,000", "Rs cr cabinet plan"),
]

REGIONS = [("EUROPE", 8), ("MIDEAST", 4), ("S ASIA", 12), ("E ASIA", 3),
           ("SE ASIA", 1), ("N AMER", 7), ("OCEANIA", 6), ("AFRICA", 1),
           ("SPACE", 1)]

UTC = [("03:00", "Bangkok fire"), ("06:00", "Kyiv missiles"),
       ("09:00", "EU summit wraps"), ("12:00", "Tata Trusts to court"),
       ("14:00", "NZ final result"), ("17:00", "Ramaphosa wins"),
       ("20:00", "Kim vows nukes"), ("21:00", "Storm: 500,000 dark")]

DATE_LEFT = ("Left out as other days' news:  \u00d7 Macy's parade postponed \u2014 "
  "announced 25 Nov  \u00b7  \u00d7 Cairo tanker fire, 31 dead \u2014 25 Nov  \u00b7  "
  "\u00d7 Israel kills Hamas deputy minister in Gaza \u2014 26 Nov  \u00b7  \u00d7 "
  "Congo Ebola passes 12,000 cases \u2014 26 Nov  \u00b7  \u00d7 Chess Game 3 ends "
  "in a draw \u2014 26 Nov  \u00b7  \u00d7 FedEx jet overruns Miami runway \u2014 "
  "26 Nov  \u00b7  \u00d7 Hong Kong mourns Wang Fuk Court fire dead, one year "
  "on \u2014 26 Nov")
HOW_SURE = ("HOW SURE:  CONFIRMED = 2+ outlets  \u00b7  OFFICIAL = on the record  "
  "\u00b7  REPORTED = one outlet  \u00b7  CLAIM = one side's account")
SOURCES = ("SOURCES: Reuters \u00b7 AP \u00b7 NYT \u00b7 ONS \u00b7 Electoral "
  "Commission \u00b7 KCNA \u00b7 Mint \u00b7 Dunya \u00b7 FIDE \u00b7 ATP \u00b7 NZR "
  "\u00b7 NZC \u00b7 Anthropic \u00b7 NYSE \u00b7 The Street \u00b7 Consumer NZ \u00b7 "
  "EU Council \u00b7 Supreme Court \u00b7 US Army \u00b7 White House \u00b7 NZTA "
  "\u00b7 AFP \u00b7 Asia Cup \u00b7 IIT \u00b7 Parliament \u00b7 AJK \u00b7 DP World "
  "Tour \u00b7 Govt \u00b7 Ministry \u00b7 China \u00b7 SC")
FIELDS_LINE = ("14 FIELDS \u2014 Politics 7 \u00b7 Sport 6 \u00b7 Economy 5 \u00b7 "
  "War 4 \u00b7 Law 4 \u00b7 Disaster 3 \u00b7 Business 3 \u00b7 Tech 2 \u00b7 "
  "Space 2 \u00b7 Education 2 \u00b7 Defence 2 \u00b7 Migration 1 \u00b7 "
  "Nuclear 1 \u00b7 Society 1")

# ------------------------------------------------------------------ layout
MX = 16            # left margin
RX = 1008          # right edge (1024 - 16)
CW = RX - MX       # 992 content width

def status_chip(cv, x_right, y, status):
    w = text_w(status, 1) + 6
    chip(cv, x_right - w, y, status, STATUSES[status], WHITE, 1, 3)
    return w

def why_block(cv, x, y, w, text):
    """'WHY IT MATTERS: ' in red bold, body wrapped (first line narrower)."""
    prefix = "WHY IT MATTERS: "
    pw = text_w(prefix, 1)
    body = text[len(prefix):] if text.startswith(prefix) else text
    lines1 = wrap_text(body, 1, w - pw)
    lines = []
    if lines1:
        lines.append(lines1[0])
        rest = " ".join(lines1[1:])
        if rest:
            lines += wrap_text(rest, 1, w)
    for i, ln in enumerate(lines[:2]):
        lx = x
        if i == 0:
            draw_text(cv, x, y, prefix, 1, RED, bold=True)
            lx = x + pw
        draw_text(cv, lx, y + i * 9, ln, 1, INK)
    return min(len(lines), 2) * 9

def render():
    cv = Canvas(W, H, WHITE)
    # --- top red rule + kicker
    cv.rect(0, 0, W, 5, RED)
    draw_text(cv, MX, 8, "THE WORLD IN ONE DAY", 2, INK, bold=True)
    rk = "43 STORIES \u00b7 9 REGIONS \u00b7 14 FIELDS \u00b7 EVERY ONE FIRST REPORTED FRI 27 NOV 2026"
    draw_text(cv, RX - text_w(rk, 1), 11, rk, 1, INK, bold=True)
    # --- masthead
    draw_text(cv, MX, 24, "Friday", 5, RED, bold=True)
    fw = text_w("Friday", 5)
    draw_text(cv, MX + fw, 24, " 27 November 2026", 5, INK, bold=True)
    # --- red kicker (hottest first)
    draw_text(cv, MX, 61, "Bangkok ablaze \u00b7 Drones kill two Italians in Kuwait \u00b7 EU summit wraps up",
              2, RED, bold=True, italic=True)
    # --- fields line
    draw_text(cv, MX, 77, FIELDS_LINE, 1, INK)
    # --- stat strip: hottest numbers first
    sx = 17
    for num, lab in STATS:
        cv.frame(sx, 90, 138, 40, LGREY, 1)
        cv.rect(sx, 90, 138, 3, RED)
        hot = num in ("2", "3", "500,000", "10")
        draw_text(cv, sx + (138 - text_w(num, 3)) // 2, 95, num, 3,
                  RED if hot else INK, bold=True)
        para(cv, sx + 4, 118, lab, 1, 130, GREY, leading=8, align='c')
        sx += 142
    # --- region strip
    for i, (key, n) in enumerate(REGIONS):
        x = MX + i * 110
        cv.rect(x, 137, 10, 10, REG_COL[key])
        draw_text(cv, x + 14, 138, "%s %d" % (REG_FULL[key], n), 1, INK, bold=True)
    # --- UTC timeline (starts with the hottest breaking moment)
    for i, (t, lab) in enumerate(UTC):
        cx = 78 + i * 124
        draw_text(cv, cx - text_w(t, 2) // 2, 154, t, 2, INK, bold=True)
        draw_text(cv, cx - text_w(lab, 1) // 2, 176, lab, 1, GREY)
    cv.hline(MX, 171, CW, GREY, 2)
    for i in range(8):
        cv.circle(78 + i * 124, 172, 4, RED)
    # --- heroes
    for hi, hs in enumerate(HEROES):
        x = MX + hi * 335
        hs["scene"](cv, x, 190, 322, 90)
        draw_text(cv, x, 283, hs["label"], 1, RED, bold=True)
        para(cv, x, 295, hs["head"], 2, 322, INK, bold=True, leading=15)
        para(cv, x, 327, hs["deck"], 1, 322, INK, leading=9)
        why_block(cv, x, 347, 322, hs["why"])
        draw_text(cv, x, 368, "Source: " + hs["src"], 1, GREY)
        status_chip(cv, x + 322, 366, hs["status"])
    # --- small scenes, 2 rows x 5
    for si, ss in enumerate(SMALL):
        row, col = si // 5, si % 5
        x = MX + col * 200
        y0 = 379 + row * 147
        ss["scene"](cv, x, y0, 192, 46)
        cv.rect(x, y0 + 49, 192, 12, BLACK)
        draw_text(cv, x + 4, y0 + 51, ss["label"], 1, WHITE, bold=True)
        para(cv, x, y0 + 64, ss["head"], 2, 192, INK, bold=True, leading=13)
        para(cv, x, y0 + 105, ss["deck"], 1, 192, INK, leading=9)
        draw_text(cv, x, y0 + 126, "Source: " + ss["src"], 1, GREY)
        status_chip(cv, x + 192, y0 + 124, ss["status"])
    # --- map band
    draw_text(cv, MX, 673, "WHERE IT HAPPENED \u2014 STORIES 1-13", 2, INK, bold=True)
    draw_map(cv, MX, 689, CW, 104)
    for i, (key, n) in enumerate(REGIONS):
        x = MX + i * 110
        cv.rect(x, 798, 10, 10, REG_COL[key])
        draw_text(cv, x + 14, 799, "%s %d" % (REG_FULL[key], n), 1, INK, bold=True)
    # --- ALSO band
    draw_text(cv, MX, 812, "ALSO ON FRIDAY 27 NOVEMBER \u2014 30 MORE STORIES, NUMBERED AND COLOUR-MATCHED BY REGION",
              2, INK, bold=True)
    for ci in range(3):
        x = MX + ci * 330
        for ri in range(10):
            num, city, reg, head, src = ALSO[ci * 10 + ri]
            y = 829 + ri * 12
            draw_text(cv, x, y, str(num) + ".", 1, INK, bold=True)
            chip(cv, x + 24, y - 1, reg, REG_COL[reg], WHITE, 1, 2)
            hx = x + 74
            full = city + " \u2014 " + head + " (" + src + ")"
            if text_w(full, 1, gap=0) > 254:
                print("ALSO OVERFLOW", num, text_w(full, 1, gap=0))
            draw_text(cv, hx, y, full, 1, INK, gap=0)
            tw = text_w(city + " \u2014 " + head, 1, gap=0)
            draw_text(cv, hx + tw + 3, y, "(" + src + ")", 1, GREY, gap=0)
    # --- DATE CHECK box
    cv.frame(MX, 952, CW, 60, RED, 2)
    draw_text(cv, MX + 6, 956, "DATE CHECK \u2014 WHAT WE LEFT OUT AND WHY", 1, RED, bold=True)
    items = DATE_LEFT.split("Left out as other days' news:  ", 1)[1]
    para(cv, MX + 6, 967, items, 1, CW - 12, INK, leading=9)
    draw_text(cv, MX + 6, 986, HOW_SURE, 1, INK, bold=True)
    para(cv, MX + 6, 996, SOURCES, 1, CW - 12, GREY, leading=8)
    # --- footer
    foot = ("Every story above happened or was first reported on Friday "
            "27 November 2026. All drawings original, made for this page.")
    draw_text(cv, (W - text_w(foot, 1)) // 2, 1015, foot, 1, GREY)
    return cv

def main():
    cv = render()
    out = Path(__file__).with_name("entry.png")
    write_png(out, W, H, cv.px)
    print("wrote", out, out.stat().st_size, "bytes")

if __name__ == "__main__":
    main()
