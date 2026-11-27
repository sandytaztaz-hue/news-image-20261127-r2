#!/usr/bin/env python3
"""Sum 27 — font-fix renderer (written fresh from BRIEF-FONT-FIX.md).

Draws the 1024x1024 broadsheet for Friday 27 November 2026 with Pillow and
real anti-aliased TrueType fonts (DejaVu / Liberation). All 43 stories from
the R2 page, same layout, same facts — only the text rendering is new.
Build-time only: the repo's main.py (stdlib only) copies entry.png out.
"""
import math
import os
from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024
BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "entry.png")

DJ = "/usr/share/fonts/truetype/dejavu/"
LB = "/usr/share/fonts/truetype/liberation/"
F_SERIF_B = DJ + "DejaVuSerif-Bold.ttf"
F_SERIF = DJ + "DejaVuSerif.ttf"
F_SERIF_I = LB + "LiberationSerif-Italic.ttf"
F_SANS = DJ + "DejaVuSans.ttf"
F_SANS_B = DJ + "DejaVuSans-Bold.ttf"

WHITE = (255, 255, 255)
BLACK = (20, 20, 20)
INK = (30, 30, 30)
GREY = (90, 90, 90)
RED = (200, 30, 30)
DRED = (178, 24, 24)
GREEN = (30, 125, 50)
BLUE = (31, 79, 163)
ORANGE = (230, 126, 0)
TEAL = (15, 122, 114)

REGIONS = {
    "EUROPE": ("EUROPE", (200, 30, 30)),
    "MIDDLE EAST": ("MIDEAST", (240, 125, 0)),
    "SOUTH ASIA": ("S ASIA", (15, 122, 114)),
    "EAST ASIA": ("E ASIA", (31, 79, 163)),
    "SE ASIA": ("SE ASIA", (58, 166, 85)),
    "NORTH AMERICA": ("N AMER", (30, 125, 50)),
    "OCEANIA": ("OCEANIA", (123, 63, 160)),
    "AFRICA": ("AFRICA", (138, 109, 26)),
    "GLOBAL": ("SPACE", (43, 43, 74)),
}

_cache = {}


def font(path, size):
    key = (path, size)
    if key not in _cache:
        _cache[key] = ImageFont.truetype(path, size)
    return _cache[key]


def serif_b(s):
    return font(F_SERIF_B, s)


def serif(s):
    return font(F_SERIF, s)


def serif_i(s):
    return font(F_SERIF_I, s)


def sans(s):
    return font(F_SANS, s)


def sans_b(s):
    return font(F_SANS_B, s)


def tw(text, f):
    return f.getlength(text)


def wrap(text, f, maxw):
    """Greedy word wrap; returns list of lines, each <= maxw."""
    words = text.split(" ")
    lines, cur = [], ""
    for w in words:
        trial = w if not cur else cur + " " + w
        if tw(trial, f) <= maxw or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def para(d, x, y, text, f, maxw, leading, fill=INK, max_lines=None):
    """Draw wrapped paragraph; returns (lines_drawn, y_after)."""
    lines = wrap(text, f, maxw)
    if max_lines is not None:
        lines = lines[:max_lines]
    for ln in lines:
        d.text((x, y), ln, font=f, fill=fill)
        y += leading
    return len(lines), y


def fit_para(text, sizes, ffun, maxw, max_lines):
    """Pick the largest size from sizes whose wrap fits max_lines lines."""
    for s in sizes:
        f = ffun(s)
        lines = wrap(text, f, maxw)
        if len(lines) <= max_lines:
            return s, f, lines
    s = sizes[-1]
    f = ffun(s)
    return s, f, wrap(text, f, maxw)


def chip(d, x, y, text, f, bg, fg=WHITE, pad_x=5, pad_h=None):
    """Text chip; returns width."""
    w = int(tw(text, f)) + 2 * pad_x
    h = pad_h if pad_h else int(f.size * 1.45)
    d.rounded_rectangle([x, y, x + w, y + h], radius=2, fill=bg)
    d.text((x + pad_x, y + (h - f.size) / 2 - 1), text, font=f, fill=fg)
    return w


def badge(d, x_right, y, text, f, bg, pad_x=5):
    """Right-aligned status badge; returns left x."""
    w = int(tw(text, f)) + 2 * pad_x
    h = int(f.size * 1.5)
    x = x_right - w
    d.rectangle([x, y, x + w, y + h], fill=bg)
    d.text((x + pad_x, y + 1), text, font=f, fill=WHITE)
    return x


STATUS_BG = {
    "CONFIRMED": (30, 125, 50),
    "OFFICIAL": (31, 79, 163),
    "REPORTED": (68, 68, 68),
    "CLAIM": (230, 126, 0),
}

OVERFLOWS = []


def check(name, ok):
    if not ok:
        OVERFLOWS.append(name)
        print("OVERFLOW:", name)


# ---------------------------------------------------------------- scenes
def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def sky(d, box, top, bottom):
    x0, y0, x1, y1 = box
    n = 10
    for i in range(n):
        c = lerp(top, bottom, i / (n - 1))
        d.rectangle([x0, y0 + (y1 - y0) * i / n, x1, y0 + (y1 - y0) * (i + 1) / n],
                    fill=c)


def sun(d, cx, cy, r):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 205, 0))
    for k in range(8):
        a = k * math.pi / 4
        x2, y2 = cx + (r + 7) * math.cos(a), cy + (r + 7) * math.sin(a)
        d.line([cx + r * math.cos(a), cy + r * math.sin(a), x2, y2],
               fill=(255, 180, 0), width=2)


def windows(d, x, y, w, h, cols, rows, lit=(255, 240, 160), dark=(70, 90, 120)):
    cw, ch = w / cols, h / rows
    for r in range(rows):
        for c in range(cols):
            col = lit if (r * cols + c) % 3 else dark
            d.rectangle([x + c * cw + 2, y + r * ch + 2,
                         x + (c + 1) * cw - 2, y + (r + 1) * ch - 2], fill=col)


def building(d, x, yb, w, h, col):
    d.rectangle([x, yb - h, x + w, yb], fill=col)
    windows(d, x + 3, yb - h + 4, w - 6, h - 8, max(2, w // 12), max(2, h // 11))


def person(d, x, yb, col=(30, 30, 30), s=1):
    d.ellipse([x - 2 * s, yb - 9 * s, x + 2 * s, yb - 5 * s], fill=col)
    d.rectangle([x - 2 * s, yb - 5 * s, x + 2 * s, yb], fill=col)


def people_row(d, x0, yb, n, gap, col=(30, 30, 30)):
    for i in range(n):
        person(d, x0 + i * gap, yb, col)


def smoke(d, x, y, r, col=(120, 120, 120)):
    for dx, dy, rr in ((0, 0, r), (-r, r // 2, r * 3 // 4), (r, r // 2, r * 2 // 3)):
        d.ellipse([x + dx - rr, y + dy - rr, x + dx + rr, y + dy + rr], fill=col)


def flame(d, x, yb, w, h):
    d.polygon([(x, yb), (x + w * 0.28, yb - h * 0.75), (x + w * 0.5, yb - h),
               (x + w * 0.72, yb - h * 0.7), (x + w, yb)], fill=(255, 110, 0))
    d.polygon([(x + w * 0.25, yb), (x + w * 0.45, yb - h * 0.55),
               (x + w * 0.6, yb - h * 0.6), (x + w * 0.78, yb)], fill=(255, 205, 0))


def tree(d, x, yb, s=1):
    d.rectangle([x - 1, yb - 6 * s, x + 1, yb], fill=(90, 60, 20))
    d.ellipse([x - 5 * s, yb - 14 * s, x + 5 * s, yb - 4 * s], fill=(40, 140, 60))


def flag(d, x, yb, h, cols):
    d.rectangle([x, yb - h, x + 2, yb], fill=(60, 60, 60))
    w = 16
    for i, c in enumerate(cols):
        d.rectangle([x + 2 + w * i / len(cols), yb - h,
                     x + 2 + w * (i + 1) / len(cols), yb - h + 10], fill=c)


def truck(d, x, yb, col=(200, 30, 30)):
    d.rectangle([x, yb - 14, x + 26, yb - 4], fill=col)
    d.rectangle([x + 26, yb - 10, x + 36, yb - 4], fill=col)
    d.rectangle([x + 28, yb - 9, x + 34, yb - 5], fill=(180, 220, 240))
    for wx in (x + 6, x + 20, x + 30):
        d.ellipse([wx - 3, yb - 4, wx + 3, yb + 2], fill=(20, 20, 20))


# ---------------------------------------------------------------- data
HEROES = [
    dict(city="BANGKOK", field="DISASTER", badge="ALL UNITS SHUT",
         head="Massive fire engulfs Bangkok oil refinery",
         deck="Blaze at the Bangchak refinery injures several workers; the company shuts every unit.",
         why="Thailand's top refinery offline; fuel prices and flights face days of disruption.",
         source="Reuters", status="CONFIRMED"),
    dict(city="KUWAIT", field="WAR", badge="2 KILLED",
         head="Iranian drones kill two Italians in Kuwait",
         deck="Officials say two Italian nationals died in an Iranian drone attack on Kuwait. Rome confirms the deaths.",
         why="First Iranian strike to kill Europeans in the Gulf; Rome demands answers, oil jumps.",
         source="NYT", status="REPORTED"),
    dict(city="BRUSSELS", field="POLITICS", badge="2028-34 BUDGET",
         head="EU summit wraps up after two days on budget and Ukraine",
         deck="Leaders close the two-day Brussels summit on the 2028-34 budget and Ukraine funding. The budget deal is unfinished.",
         why="Seven years of EU spending and Kyiv's war funding now hinge on one unfinished deal.",
         source="EU Council", status="OFFICIAL"),
]

SMALL = [
    dict(city="GAZA", field="WAR", badge="10 KILLED",
         head="Israel kills 10 in Gaza",
         deck="Hamas weighs its response as strikes go on.",
         source="Reuters", status="REPORTED"),
    dict(city="KYIV", field="WAR", badge="MISSILES HIT",
         head="Russian missiles hit Kyiv",
         deck="Missiles hit Kyiv; the mayor reports damage. Residents shelter.",
         source="AP", status="REPORTED"),
    dict(city="RIYADH", field="WAR", badge="2 DOWN",
         head="Saudis intercept Houthi missiles",
         deck="Air defences down two Houthi missiles. Riyadh reports no damage.",
         source="Reuters", status="CONFIRMED"),
    dict(city="LONDON", field="MIGRATION", badge="SINCE 1997",
         head="UK migration falls to record low",
         deck="Net migration at its lowest since 1997. Arrivals fall as rules bite.",
         source="ONS", status="OFFICIAL"),
    dict(city="PYONGYANG", field="NUCLEAR", badge="MORE NUKES",
         head="Kim vows more nuclear weapons",
         deck="Kim pledges more nukes, snubs Trump.",
         source="KCNA", status="CLAIM"),
    dict(city="PRETORIA", field="POLITICS", badge="COURT WIN",
         head="Ramaphosa wins court fight",
         deck="Court backs Ramaphosa on impeachment report. President cleared.",
         source="Reuters", status="CONFIRMED"),
    dict(city="WELLINGTON", field="ELECTION", badge="67 / 131",
         head="NZ coalition holds 67 of 131",
         deck="Final count: coalition holds 67 of 131 seats. A two-seat majority.",
         source="Electoral Comm.", status="OFFICIAL"),
    dict(city="NEW YORK", field="STORM", badge="500,000 DARK",
         head="Storm leaves 500,000 in dark",
         deck="Thanksgiving storm cuts power to 500,000. Crews race to restore lines.",
         source="AP", status="REPORTED"),
    dict(city="NEW DELHI", field="COURT", badge="COURT RULES",
         head="Top court: PMLA needs a judge",
         deck="PMLA attachment needs a judicial member. Top court tightens rules.",
         source="Supreme Court", status="OFFICIAL"),
    dict(city="MUMBAI", field="BUSINESS", badge="COURT FIGHT",
         head="Tata Trusts fight chief pick in court",
         deck="Trusts fight Chandrasekaran in court.",
         source="Mint", status="REPORTED"),
]

ALSO = [
    (14, "Karachi", "Collapse kills 3, injures 14", "Dunya", "SOUTH ASIA"),
    (15, "New Delhi", "Court quashes ex-MP release", "SC", "SOUTH ASIA"),
    (16, "New Delhi", "Cabinet clears Rs 11,000 cr plan", "Govt", "SOUTH ASIA"),
    (17, "New Delhi", "GST cancellations auto from 1 Dec", "Govt", "SOUTH ASIA"),
    (18, "New Delhi", "IITs add 6,000 AI, robotics seats", "IIT", "SOUTH ASIA"),
    (19, "Beijing", "Border areas 'generally stable'", "China", "EAST ASIA"),
    (20, "Beijing", "Drones reshape Asia's militaries", "Reuters", "EAST ASIA"),
    (21, "Washington", "Trump unveils new tariffs", "White House", "NORTH AMERICA"),
    (22, "Washington", "Army hails Iowa explosives win", "US Army", "NORTH AMERICA"),
    (23, "Washington", "Huang cleared of security threat", "Reuters", "NORTH AMERICA"),
    (24, "Doha", "India A v Sri Lanka A semi-final", "Asia Cup", "MIDDLE EAST"),
    (25, "Christchurch", "India begin 2nd Test vs NZ, 11am", "NZC", "OCEANIA"),
    (26, "London", "Sinner out of Australian Open, knee", "ATP", "EUROPE"),
    (27, "London", "Barrett to captain All Blacks v England", "NZR", "EUROPE"),
    (28, "Paris", "Depardieu faces trial over 2018 rape", "AFP", "EUROPE"),
    (29, "Dhaka", "'India weakened Pakistan in 1971'", "Parliament", "SOUTH ASIA"),
    (30, "Islamabad", "Pakistan marks 25 Nov as space day", "Govt", "SOUTH ASIA"),
    (31, "Islamabad", "PM orders fast cybercrime reforms", "Govt", "SOUTH ASIA"),
    (32, "Muzaffarabad", "Assembly backs JAAC talks", "AJK", "SOUTH ASIA"),
    (33, "Geneva", "Gukesh faces Sindarov in Game 4", "FIDE", "EUROPE"),
    (34, "San Francisco", "Claude artifacts become apps", "Anthropic", "NORTH AMERICA"),
    (35, "Pasadena", "Planet hinted beyond Neptune", "astronomers", "GLOBAL"),
    (36, "Mumbai", "Flipkart CEO to step down next month", "company", "SOUTH ASIA"),
    (37, "Auckland", "Black Friday deals 'no cheaper'", "Consumer NZ", "OCEANIA"),
    (38, "Wellington", "School English curriculum paused", "Ministry", "OCEANIA"),
    (39, "Auckland", "Driver licence waits hit 80 days", "NZTA", "OCEANIA"),
    (40, "Sydney", "Kibon sidelined in PGA opener", "DP World Tour", "OCEANIA"),
    (41, "New York", "US markets reopen for short session", "NYSE", "NORTH AMERICA"),
    (42, "Brussels", "EU budget summit ends, no deal", "Reuters", "EUROPE"),
    (43, "New York", "Target, Kohl's gift giveaways", "The Street", "NORTH AMERICA"),
]

STATS = [
    ("2", "Italians killed in Kuwait"),
    ("3", "dead in Karachi collapse"),
    ("500,000", "homes dark in US storm"),
    ("10", "killed in Gaza strikes"),
    ("67/131", "NZ coalition's majority"),
    ("77,000", "UK net migration, lowest since 1997"),
    ("11,000", "Rs cr cabinet plan"),
]

TIMELINE = [
    ("03:00", "Bangkok fire"), ("06:00", "Kyiv missiles"),
    ("09:00", "EU summit wraps"), ("12:00", "Tata Trusts to court"),
    ("14:00", "NZ final result"), ("17:00", "Ramaphosa wins"),
    ("20:00", "Kim vows nukes"), ("21:00", "Storm 500,000 dark"),
]

REGION_STRIP = [("EUROPE", 8), ("MIDDLE EAST", 4), ("SOUTH ASIA", 12),
                ("EAST ASIA", 3), ("SE ASIA", 1), ("NORTH AMERICA", 7),
                ("OCEANIA", 6), ("AFRICA", 1), ("GLOBAL & SPACE", 1)]

FIELDS = ("14 FIELDS — Politics 7 · Sport 6 · Economy 5 · War 4 · Law 4 · "
          "Disaster 3 · Business 3 · Tech 2 · Space 2 · Education 2 · "
          "Defence 2 · Migration 1 · Nuclear 1 · Society 1")

DATE_ITEMS = ("× Macy's Parade postponed — announced 25 Nov  ·  "
              "× Cairo tanker fire, 31 dead — 25 Nov  ·  "
              "× Israel kills Hamas deputy minister in Gaza — 26 Nov  ·  "
              "× Congo Ebola passes 12,000 cases — 26 Nov  ·  "
              "× Chess Game 3 ends in a draw — 26 Nov  ·  "
              "× FedEx jet overruns Miami runway — 26 Nov  ·  "
              "× Hong Kong mourns Wang Fuk Court fire dead, one year on — 26 Nov")

SOURCES = ("SOURCES: Reuters · AP · NYT · ONS · Electoral Commission · KCNA · "
           "Mint · Dunya · FIDE · ATP · NZR · NZC · Anthropic · NYSE · "
           "The Street · Consumer NZ · EU Council · Supreme Court · US Army · "
           "White House · NZTA · AFP · Asia Cup · IIT · Parliament · AJK · "
           "DP World Tour · Govt · Ministry · China · SC")

PINS = {
    1: (100.5, 13.7, 0, 10), 2: (47.5, 29.4, 8, -8), 3: (4.35, 50.85, -4, -9),
    4: (34.5, 31.5, -10, 8), 5: (30.5, 50.45, 6, -9), 6: (46.7, 24.6, 10, 8),
    7: (-0.1, 51.5, -8, -9), 8: (125.75, 39.0, 4, -6), 9: (28.2, -25.7, 0, 10),
    10: (174.8, -41.3, -6, -8), 11: (-74.0, 40.7, -4, -6),
    12: (77.2, 28.6, 0, -10), 13: (72.9, 19.1, -8, 9),
}
PIN_REGION = {1: "SE ASIA", 2: "MIDDLE EAST", 3: "EUROPE", 4: "MIDDLE EAST",
              5: "EUROPE", 6: "MIDDLE EAST", 7: "EUROPE", 8: "EAST ASIA",
              9: "AFRICA", 10: "OCEANIA", 11: "NORTH AMERICA",
              12: "SOUTH ASIA", 13: "SOUTH ASIA"}


# ---------------------------------------------------------------- scene painters
def scene_bangkok(d, x, y, w, h):
    yb = y + h
    sky(d, (x, y, x + w, yb), (150, 205, 240), (220, 235, 245))
    sun(d, x + w - 28, y + 16, 9)
    d.rectangle([x, yb - 16, x + w, yb], fill=(120, 120, 120))
    d.rectangle([x, yb - 16, x + w, yb - 12], fill=(90, 90, 90))
    # refinery towers
    for tx, th in ((x + 12, 28), (x + 52, 32), (x + 92, 26)):
        d.rectangle([tx, yb - 16 - th, tx + 22, yb - 16], fill=(70, 70, 78))
        for band in range(3):
            d.rectangle([tx, yb - 16 - th + 8 + band * 13, tx + 22,
                         yb - 16 - th + 11 + band * 13], fill=(255, 190, 0))
        d.polygon([(tx + 4, yb - 16 - th), (tx + 11, yb - 16 - th - 8),
                   (tx + 18, yb - 16 - th)], fill=(50, 50, 56))
    d.rectangle([x + 130, yb - 34, x + w - 8, yb - 16], fill=(200, 200, 205))
    windows(d, x + 134, yb - 32, w - 146, 14, 8, 1, lit=(255, 220, 120))
    smoke(d, x + 60, y + 12, 7)
    smoke(d, x + 150, y + 8, 6, col=(140, 140, 140))
    flame(d, x + 140, yb - 16, 34, 26)
    flame(d, x + 200, yb - 16, 28, 20)
    flame(d, x + 255, yb - 16, 26, 18)
    truck(d, x + 14, yb - 16)
    d.line([x + 52, yb - 20, x + 150, yb - 34], fill=(20, 90, 200), width=3)
    d.line([x + 52, yb - 18, x + 205, yb - 30], fill=(20, 90, 200), width=2)
    people_row(d, x + 230, yb - 16, 3, 12, col=(200, 60, 30))
    people_row(d, x + 290, yb - 16, 2, 11)


def scene_kuwait(d, x, y, w, h):
    yb = y + h
    sky(d, (x, y, x + w, yb), (250, 225, 170), (240, 200, 130))
    d.rectangle([x, yb - 18, x + w, yb], fill=(225, 195, 130))
    # Kuwait towers: blue-green spheres on stems
    for tx in (x + 22, x + 58, x + 94):
        d.rectangle([tx - 3, yb - 40, tx + 3, yb - 18], fill=(60, 120, 130))
        d.ellipse([tx - 11, yb - 48, tx + 11, yb - 28], fill=(70, 140, 150))
        d.ellipse([tx - 6, yb - 44, tx + 6, yb - 34], fill=(120, 190, 200))
    # drone silhouette
    dx, dy = x + w // 2, y + 22
    d.ellipse([dx - 34, dy - 4, dx + 34, dy + 4], fill=(25, 25, 25))
    d.polygon([(dx - 8, dy), (dx + 40, dy - 10), (dx + 44, dy - 6), (dx + 6, dy + 3)],
              fill=(25, 25, 25))
    d.polygon([(dx - 8, dy), (dx + 30, dy + 12), (dx + 34, dy + 8), (dx + 4, dy + 3)],
              fill=(25, 25, 25))
    for px in (dx - 26, dx - 12, dx + 2):
        d.ellipse([px - 2, dy - 1, px + 2, dy + 3], fill=(120, 120, 120))
    flag(d, x + w - 52, yb - 18, 30, [(0, 150, 70), (255, 255, 255), (200, 30, 30)])
    # explosion starburst
    ex, ey = x + w - 78, yb - 32
    for k in range(8):
        a = k * math.pi / 4
        d.line([ex, ey, ex + 12 * math.cos(a), ey + 12 * math.sin(a)],
               fill=(255, 140, 0), width=3)
    d.ellipse([ex - 7, ey - 7, ex + 7, ey + 7], fill=(220, 30, 30))
    d.ellipse([ex - 3, ey - 3, ex + 3, ey + 3], fill=(255, 220, 0))
    smoke(d, ex - 14, ey - 10, 4, col=(110, 110, 110))
    building(d, x + w - 120, yb - 18, 26, 30, (120, 120, 130))
    building(d, x + 150, yb - 18, 22, 22, (140, 140, 148))
    truck(d, x + 150, yb - 18, col=(240, 240, 240))
    people_row(d, x + 200, yb - 18, 2, 11, col=(20, 60, 140))


def scene_brussels(d, x, y, w, h):
    yb = y + h
    sky(d, (x, y, x + w, yb), (140, 185, 235), (205, 225, 245))
    sun(d, x + w - 26, y + 15, 9)
    d.rectangle([x, yb - 12, x + w, yb], fill=(80, 140, 80))
    # EU quarter building
    d.rectangle([x + 16, yb - 46, x + w - 16, yb - 12], fill=(90, 105, 140))
    windows(d, x + 22, yb - 42, w - 44, 28, 12, 3, lit=(255, 240, 170))
    d.rectangle([x + 16, yb - 46, x + w - 16, yb - 40], fill=(60, 75, 110))
    for i in range(9):
        d.rectangle([x + 30 + i * 12, yb - 49, x + 36 + i * 12, yb - 46],
                    fill=(255, 220, 120))
    # row of flags
    flagsets = [[(0, 60, 180)], [(0, 0, 0), (255, 220, 0), (200, 30, 30)],
                [(0, 60, 180), (255, 255, 255), (200, 30, 30)],
                [(0, 0, 0), (200, 30, 30), (255, 220, 0)],
                [(0, 150, 70), (255, 255, 255), (200, 30, 30)]]
    for i, cols in enumerate(flagsets):
        flag(d, x + 26 + i * 56, yb - 12, 26, cols)
    people_row(d, x + w - 90, yb - 12, 4, 12)
    tree(d, x + 8, yb - 12)


def scene_small(d, idx, x, y, w, h):
    yb = y + h
    if idx == 0:  # Gaza
        sky(d, (x, y, x + w, yb), (250, 225, 180), (240, 205, 150))
        d.rectangle([x, yb - 10, x + w, yb], fill=(190, 165, 120))
        building(d, x + 8, yb - 10, 34, 26, (210, 190, 150))
        building(d, x + 48, yb - 10, 30, 22, (190, 170, 130))
        building(d, x + 84, yb - 10, 36, 26, (220, 200, 160))
        flame(d, x + 130, yb - 10, 22, 16)
        smoke(d, x + 140, y + 10, 5)
        people_row(d, x + 150, yb - 10, 3, 10)
    elif idx == 1:  # Kyiv
        sky(d, (x, y, x + w, yb), (120, 170, 230), (200, 220, 245))
        sun(d, x + 24, y + 12, 8)
        d.rectangle([x, yb - 10, x + w, yb], fill=(110, 130, 110))
        building(d, x + 10, yb - 10, 30, 24, (110, 125, 150))
        building(d, x + 46, yb - 10, 26, 18, (130, 145, 165))
        building(d, x + 78, yb - 10, 34, 26, (100, 115, 140))
        d.line([x + 130, y + 8, x + 165, y + 30], fill=(255, 255, 255), width=2)
        d.line([x + 150, y + 6, x + 175, y + 34], fill=(255, 255, 255), width=2)
        smoke(d, x + 168, y + 32, 4, col=(100, 100, 100))
        smoke(d, x + 140, y + 12, 4, col=(100, 100, 100))
        people_row(d, x + 120, yb - 10, 2, 10)
    elif idx == 2:  # Riyadh
        sky(d, (x, y, x + w, yb), (90, 200, 210), (190, 235, 240))
        d.rectangle([x, yb - 10, x + w, yb], fill=(200, 180, 130))
        for tx in (x + 16, x + 44, x + 72):
            d.rectangle([tx, yb - 28, tx + 12, yb - 10], fill=(240, 240, 240))
            d.polygon([(tx, yb - 28), (tx + 6, yb - 36), (tx + 12, yb - 28)],
                      fill=(200, 220, 230))
        d.line([x + 110, y + 30, x + 150, y + 6], fill=(255, 255, 255), width=2)
        d.line([x + 120, y + 34, x + 165, y + 10], fill=(255, 255, 255), width=2)
        smoke(d, x + 152, y + 8, 4, col=(110, 110, 110))
        smoke(d, x + 168, y + 12, 4, col=(110, 110, 110))
        tree(d, x + 100, yb - 10)
        people_row(d, x + 130, yb - 10, 2, 10, col=(20, 80, 60))
    elif idx == 3:  # London
        sky(d, (x, y, x + w, yb), (170, 200, 225), (220, 230, 240))
        d.rectangle([x, yb - 10, x + w, yb], fill=(90, 150, 90))
        building(d, x + 8, yb - 10, 26, 26, (120, 120, 130))
        d.rectangle([x + 40, yb - 32, x + 48, yb - 10], fill=(90, 90, 100))
        d.polygon([(x + 38, yb - 32), (x + 44, yb - 36), (x + 50, yb - 32)],
                  fill=(70, 70, 80))
        d.ellipse([x + 41, yb - 28, x + 47, yb - 22], fill=(255, 240, 160))
        building(d, x + 56, yb - 10, 30, 20, (140, 140, 148))
        # red double-decker bus
        d.rectangle([x + 100, yb - 24, x + 150, yb - 10], fill=(200, 30, 30))
        for wx in range(5):
            d.rectangle([x + 104 + wx * 9, yb - 22, x + 110 + wx * 9, yb - 17],
                        fill=(255, 240, 160))
        for wx in range(5):
            d.rectangle([x + 104 + wx * 9, yb - 15, x + 110 + wx * 9, yb - 11],
                        fill=(255, 240, 160))
        d.ellipse([x + 108, yb - 10, x + 114, yb - 4], fill=(20, 20, 20))
        d.ellipse([x + 138, yb - 10, x + 144, yb - 4], fill=(20, 20, 20))
        d.polygon([(x + 160, yb - 10), (x + 180, yb - 34), (x + w - 4, yb - 10)],
                  fill=(60, 130, 70))
        people_row(d, x + 92, yb - 10, 2, 9)
    elif idx == 4:  # Pyongyang
        sky(d, (x, y, x + w, yb), (25, 35, 90), (50, 60, 130))
        for sx, sy in ((x + 20, y + 8), (x + 60, y + 14), (x + 150, y + 10),
                       (x + 180, y + 18)):
            d.ellipse([sx - 1, sy - 1, sx + 1, sy + 1], fill=(255, 255, 255))
        d.rectangle([x, yb - 12, x + w, yb], fill=(180, 30, 30))
        # missile on launcher
        d.rectangle([x + 88, yb - 28, x + 108, yb - 12], fill=(230, 230, 230))
        d.polygon([(x + 88, yb - 28), (x + 98, yb - 36), (x + 108, yb - 28)],
                  fill=(200, 30, 30))
        d.rectangle([x + 96, yb - 26, x + 100, yb - 16], fill=(200, 30, 30))
        flag(d, x + 14, yb - 12, 24, [(200, 30, 30), (255, 255, 255), (0, 60, 180)])
        flag(d, x + 150, yb - 12, 24, [(200, 30, 30), (255, 255, 255), (0, 60, 180)])
        d.line([x + 118, yb - 30, x + 160, yb - 36], fill=(255, 220, 120), width=2)
        people_row(d, x + 40, yb - 12, 3, 10, col=(255, 255, 255))
    elif idx == 5:  # Pretoria
        sky(d, (x, y, x + w, yb), (150, 205, 240), (225, 235, 245))
        sun(d, x + w - 22, y + 12, 8)
        d.rectangle([x, yb - 10, x + w, yb], fill=(90, 140, 80))
        # courthouse with columns
        d.rectangle([x + 20, yb - 30, x + 110, yb - 10], fill=(240, 235, 220))
        d.polygon([(x + 16, yb - 30), (x + 65, yb - 36), (x + 114, yb - 30)],
                  fill=(220, 210, 190))
        for cx in (x + 28, x + 50, x + 72, x + 94):
            d.rectangle([cx, yb - 28, cx + 6, yb - 10], fill=(200, 190, 170))
        # scales of justice
        sx, sy = x + 140, yb - 24
        d.line([sx, sy - 12, sx, sy + 6], fill=(60, 60, 60), width=2)
        d.line([sx - 14, sy - 10, sx + 14, sy - 10], fill=(60, 60, 60), width=2)
        d.polygon([(sx - 18, sy), (sx - 10, sy), (sx - 14, sy - 8)], fill=(255, 200, 0))
        d.polygon([(sx + 10, sy), (sx + 18, sy), (sx + 14, sy - 8)], fill=(255, 200, 0))
        flag(d, x + 168, yb - 10, 26, [(200, 30, 30), (255, 255, 255), (0, 60, 180)])
        tree(d, x + 10, yb - 10)
    elif idx == 6:  # Wellington
        sky(d, (x, y, x + w, yb), (140, 195, 235), (215, 232, 245))
        d.rectangle([x, yb - 10, x + w, yb], fill=(80, 140, 80))
        building(d, x + 8, yb - 10, 28, 26, (150, 150, 160))
        building(d, x + 40, yb - 10, 24, 18, (170, 170, 178))
        d.polygon([(x + 70, yb - 10), (x + 110, yb - 34), (x + 150, yb - 10)],
                  fill=(60, 130, 70))
        d.polygon([(x + 130, yb - 10), (x + 165, yb - 28), (x + w - 4, yb - 10)],
                  fill=(50, 115, 65))
        # vote bars: green 67, grey 64
        bx, by = x + 96, y + 8
        d.rectangle([bx, by, bx + 46, by + 7], fill=(30, 125, 50))
        d.rectangle([bx + 48, by, bx + 92, by + 7], fill=(160, 160, 160))
        d.text((bx, by + 9), "67-64", font=sans_b(9), fill=INK)
        people_row(d, x + 60, yb - 10, 2, 10)
    elif idx == 7:  # New York storm
        sky(d, (x, y, x + w, yb), (70, 70, 120), (130, 130, 170))
        d.rectangle([x, yb - 10, x + w, yb], fill=(60, 60, 70))
        building(d, x + 8, yb - 10, 30, 24, (50, 50, 70))
        building(d, x + 42, yb - 10, 26, 18, (60, 60, 80))
        building(d, x + 72, yb - 10, 30, 26, (45, 45, 65))
        windows(d, x + 11, yb - 30, 24, 20, 3, 3, lit=(255, 220, 100))
        windows(d, x + 75, yb - 32, 24, 22, 3, 3, lit=(255, 220, 100))
        for rx in range(x + 110, x + w - 6, 12):
            d.line([rx, y + 6, rx - 5, y + 22], fill=(200, 210, 230), width=1)
        truck(d, x + 118, yb - 10, col=(255, 190, 0))
        d.line([x + 118, yb - 22, x + 150, yb - 34], fill=(40, 40, 40), width=2)
        d.line([x + 150, yb - 34, x + 182, yb - 22], fill=(40, 40, 40), width=2)
    elif idx == 8:  # New Delhi court
        sky(d, (x, y, x + w, yb), (250, 210, 150), (245, 225, 190))
        sun(d, x + 24, y + 12, 8)
        d.rectangle([x, yb - 10, x + w, yb], fill=(120, 110, 90))
        d.rectangle([x + 30, yb - 28, x + 120, yb - 10], fill=(180, 90, 60))
        d.polygon([(x + 26, yb - 28), (x + 75, yb - 36), (x + 124, yb - 28)],
                  fill=(150, 70, 45))
        for cx in (x + 38, x + 60, x + 82, x + 104):
            d.rectangle([cx, yb - 26, cx + 6, yb - 10], fill=(210, 190, 170))
        sx, sy = x + 150, yb - 24
        d.line([sx, sy - 12, sx, sy + 6], fill=(60, 60, 60), width=2)
        d.line([sx - 14, sy - 10, sx + 14, sy - 10], fill=(60, 60, 60), width=2)
        d.polygon([(sx - 18, sy), (sx - 10, sy), (sx - 14, sy - 8)], fill=(255, 200, 0))
        d.polygon([(sx + 10, sy), (sx + 18, sy), (sx + 14, sy - 8)], fill=(255, 200, 0))
        flag(d, x + 172, yb - 10, 26,
             [(255, 150, 0), (255, 255, 255), (0, 140, 70)])
    else:  # Mumbai
        sky(d, (x, y, x + w, yb), (150, 200, 235), (215, 232, 245))
        d.rectangle([x, yb - 12, x + w, yb], fill=(40, 110, 180))
        building(d, x + 8, yb - 12, 28, 24, (120, 125, 140))
        building(d, x + 40, yb - 12, 24, 18, (140, 145, 158))
        building(d, x + 68, yb - 12, 30, 26, (110, 115, 130))
        # gavel
        d.rectangle([x + 130, yb - 34, x + 158, yb - 26], fill=(120, 70, 30))
        d.rectangle([x + 142, yb - 26, x + 146, yb - 12], fill=(90, 55, 25))
        d.rectangle([x + 126, yb - 14, x + 162, yb - 12], fill=(140, 90, 40))
        d.polygon([(x + 168, yb - 12), (x + 182, yb - 30), (x + w - 4, yb - 12)],
                  fill=(200, 200, 205))
        tree(d, x + 112, yb - 12)


def draw_map(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(205, 232, 247))
    d.rectangle([x, y, x + w, y + h], outline=(90, 130, 160), width=1)
    for gx in range(1, 10):
        gx0 = x + w * gx / 10
        d.line([gx0, y, gx0, y + h], fill=(255, 255, 255), width=1)
    for gy in range(1, 4):
        gy0 = y + h * gy / 4
        d.line([x, gy0, x + w, gy0], fill=(255, 255, 255), width=1)
    land = (168, 208, 138)
    # North America
    d.polygon([(x + 8, y + 22), (x + 60, y + 8), (x + 150, y + 6), (x + 205, y + 16),
               (x + 195, y + 34), (x + 150, y + 40), (x + 120, y + 52),
               (x + 80, y + 44), (x + 30, y + 38)], fill=land)
    # South America
    d.polygon([(x + 210, y + 52), (x + 250, y + 46), (x + 272, y + 58),
               (x + 258, y + 82), (x + 232, y + 84), (x + 214, y + 66)], fill=land)
    # Europe + Asia (one wide mass)
    d.polygon([(x + 430, y + 10), (x + 560, y + 4), (x + 760, y + 6),
               (x + 950, y + 12), (x + 990, y + 22), (x + 940, y + 30),
               (x + 860, y + 26), (x + 800, y + 40), (x + 700, y + 44),
               (x + 620, y + 36), (x + 560, y + 42), (x + 500, y + 34),
               (x + 450, y + 26)], fill=land)
    # Africa
    d.polygon([(x + 470, y + 44), (x + 540, y + 40), (x + 580, y + 50),
               (x + 566, y + 76), (x + 520, y + 84), (x + 488, y + 66)],
              fill=land)
    # SE Asia islands
    d.polygon([(x + 780, y + 48), (x + 830, y + 44), (x + 850, y + 52),
               (x + 810, y + 58)], fill=land)
    d.polygon([(x + 700, y + 56), (x + 730, y + 54), (x + 736, y + 60),
               (x + 706, y + 62)], fill=land)
    # Australia
    d.polygon([(x + 830, y + 62), (x + 900, y + 58), (x + 940, y + 66),
               (x + 910, y + 78), (x + 850, y + 76)], fill=land)
    # UK + Japan dots
    d.ellipse([x + 452, y + 12, x + 460, y + 20], fill=land)
    d.ellipse([x + 918, y + 22, x + 928, y + 30], fill=land)
    # pins
    for num in range(1, 14):
        lon, lat, dx, dy = PINS[num]
        px = x + (lon + 170) / 360 * w + dx
        py = y + (75 - lat) / 130 * h + dy
        col = REGIONS[PIN_REGION[num]][1]
        d.ellipse([px - 10, py - 10, px + 10, py + 10], fill=col,
                  outline=WHITE, width=2)
        f = sans_b(10)
        t = str(num)
        d.text((px - tw(t, f) / 2, py - 7), t, font=f, fill=WHITE)


# ---------------------------------------------------------------- page layout
MX = 10
CW = W - 2 * MX  # 1004 usable width

MASTHEAD_SIZES = [58, 54, 50]
HERO_SCENE = 50
SMALL_SCENE = 38
MAP_H = 64
ALSO_LEAD = 11.5
STAT_H = 48


def main():
    img = Image.new("RGB", (W, H), WHITE)
    d = ImageDraw.Draw(img)
    y = 0

    # thin red rule
    d.rectangle([0, 0, W, 4], fill=RED)
    y = 6
    # kicker line
    d.text((MX, y), "THE WORLD IN ONE DAY", font=sans_b(11), fill=INK)
    right = "43 STORIES · 9 REGIONS · 14 FIELDS · EVERY ONE FIRST REPORTED FRI 27 NOV 2026"
    fr = sans_b(10)
    d.text((W - MX - tw(right, fr), y + 1), right, font=fr, fill=INK)
    y += 15

    # masthead: largest size that fits the width
    mh_text = "Friday 27 November 2026"
    mh_font = None
    for s in MASTHEAD_SIZES:
        f = serif_b(s)
        if tw(mh_text, f) <= CW:
            mh_font = f
            break
    if mh_font is None:
        mh_font = serif_b(MASTHEAD_SIZES[-1])
    bbox = d.textbbox((0, 0), mh_text, font=mh_font)
    mh_h = bbox[3] - bbox[1]
    d.text((MX, y - bbox[1]), mh_text, font=mh_font, fill=BLACK)
    y += mh_h + 3
    check("masthead", mh_h <= 72)

    # red italic kicker naming the 3 biggest stories
    rk = "Bangkok ablaze · Drones kill two Italians in Kuwait · EU summit wraps up"
    d.text((MX, y), rk, font=serif_i(16), fill=DRED)
    y += 20
    # fields line
    d.text((MX, y), FIELDS, font=sans(10), fill=INK)
    y += 13

    # ---- stat strip: 7 boxes
    y += 2
    stat_y = y
    gap = 3
    bw = (CW - 6 * gap) // 7
    for i, (num, label) in enumerate(STATS):
        bx = MX + i * (bw + gap)
        d.rectangle([bx, stat_y, bx + bw, stat_y + STAT_H], outline=(170, 170, 170), width=1)
        d.line([bx, stat_y, bx + bw, stat_y], fill=RED, width=2)
        nf = sans_b(26)
        if tw(num, nf) > bw - 8:
            nf = sans_b(23)
        d.text((bx + (bw - tw(num, nf)) / 2, stat_y + 2), num, font=nf, fill=INK)
        lf = sans(9)
        lines = wrap(label, lf, bw - 8)
        check("stat label " + num, len(lines) <= 2)
        ly = stat_y + 28
        for ln in lines:
            d.text((bx + (bw - tw(ln, lf)) / 2, ly), ln, font=lf, fill=GREY)
            ly += 10
    y = stat_y + STAT_H + 4

    # ---- region strip
    rx = MX
    rf = sans_b(10)
    for name, count in REGION_STRIP:
        col = REGIONS[name][1] if name in REGIONS else REGIONS["GLOBAL"][1]
        d.rectangle([rx, y + 1, rx + 11, y + 12], fill=col)
        t = "%s %d" % (name, count)
        d.text((rx + 15, y), t, font=rf, fill=INK)
        rx += 15 + tw(t, rf) + 10
    check("region strip width", rx <= W - MX)
    y += 15

    # ---- UTC timeline
    tl_y = y
    slot = CW / 8
    tf = sans_b(12)
    lf = sans(10)
    for i, (t, label) in enumerate(TIMELINE):
        cx = MX + slot * i + slot / 2
        d.text((cx - tw(t, tf) / 2, tl_y), t, font=tf, fill=INK)
        d.ellipse([cx - 4, tl_y + 17, cx + 4, tl_y + 25], fill=RED)
        lines = wrap(label, lf, slot - 6)
        check("timeline label " + t, len(lines) <= 1)
        d.text((cx - tw(label, lf) / 2, tl_y + 27), label, font=lf, fill=INK)
    d.line([MX, tl_y + 21, W - MX, tl_y + 21], fill=(120, 120, 120), width=1)
    # redraw dots over the line
    for i in range(8):
        cx = MX + slot * i + slot / 2
        d.ellipse([cx - 4, tl_y + 17, cx + 4, tl_y + 25], fill=RED)
    y = tl_y + 40

    # ---- heroes
    hero_w = (CW - 2 * 14) // 3
    hero_x = [MX, MX + hero_w + 14, MX + 2 * (hero_w + 14)]
    hero_painters = [scene_bangkok, scene_kuwait, scene_brussels]
    for k, hero in enumerate(HEROES):
        hx = hero_x[k]
        hy = y
        hero_painters[k](d, hx, hy, hero_w, HERO_SCENE)
        chip(d, hx + 4, hy + 4, hero["badge"], sans_b(10), RED, pad_h=15)
        cy = hy + HERO_SCENE + 3
        d.text((hx, cy), "%s — %s" % (hero["city"], hero["field"]),
               font=sans_b(12), fill=DRED)
        cy += 16
        _, hf, hlines = fit_para(hero["head"], [20, 19, 18], serif_b, hero_w, 2)
        check("hero head " + hero["city"], len(hlines) <= 2)
        for ln in hlines:
            d.text((hx, cy), ln, font=hf, fill=BLACK)
            cy += hf.size + 3
        cy += 1
        _, df, dlines = fit_para(hero["deck"], [11, 10], sans, hero_w, 2)
        check("hero deck " + hero["city"], len(dlines) <= 2)
        for ln in dlines:
            d.text((hx, cy), ln, font=df, fill=INK)
            cy += df.size + 3
        cy += 1
        # WHY IT MATTERS: bold red prefix + wrapped rest, max 2 lines
        wf = sans(10)
        wbf = sans_b(10)
        prefix = "WHY IT MATTERS:"
        pw = tw(prefix, wbf) + 5
        first = wrap(hero["why"], wf, hero_w - pw)
        rest = []
        if first:
            used = first[0]
            remaining = hero["why"][len(used):].strip()
            rest = wrap(remaining, wf, hero_w) if remaining else []
        wlines = ([first[0]] if first else []) + rest
        check("hero why " + hero["city"], len(wlines) <= 2)
        d.text((hx, cy), prefix, font=wbf, fill=DRED)
        if wlines:
            d.text((hx + pw, cy), wlines[0], font=wf, fill=INK)
        cy += 13
        if len(wlines) > 1:
            d.text((hx, cy), wlines[1], font=wf, fill=INK)
            cy += 13
        cy += 2
        sf = sans(10)
        d.text((hx, cy), "Source: " + hero["source"], font=sf, fill=GREY)
        badge(d, hx + hero_w, cy - 1, hero["status"], sans_b(9),
              STATUS_BG[hero["status"]])
        cy += 13
        if k == 0:
            hero_bottom = cy
    y = hero_bottom + 4

    # ---- small scenes, 2 rows x 5
    sw = (CW - 4 * 8) // 5
    sx0 = [MX + i * (sw + 8) for i in range(5)]
    for row in range(2):
        row_y = y
        for c in range(5):
            s = SMALL[row * 5 + c]
            x = sx0[c]
            scene_small(d, row * 5 + c, x, row_y, sw, SMALL_SCENE)
            chip(d, x + 3, row_y + 3, s["badge"], sans_b(9), RED, pad_h=13)
            ly = row_y + SMALL_SCENE + 2
            d.rectangle([x, ly, x + sw, ly + 13], fill=BLACK)
            d.text((x + 4, ly + 1), "%s — %s" % (s["city"], s["field"]),
                   font=sans_b(10), fill=WHITE)
            ly += 15
            _, hf, hlines = fit_para(s["head"], [16, 15, 14], serif_b, sw, 2)
            check("small head " + s["city"], len(hlines) <= 2)
            for ln in hlines:
                d.text((x, ly), ln, font=hf, fill=BLACK)
                ly += hf.size + 2
            ly += 1
            _, df, dlines = fit_para(s["deck"], [11, 10, 9], sans, sw, 2)
            check("small deck " + s["city"], len(dlines) <= 2)
            for ln in dlines:
                d.text((x, ly), ln, font=df, fill=INK)
                ly += df.size + 2
            ly += 1
            sf = sans(10)
            src = "Source: " + s["source"]
            d.text((x, ly), src, font=sf, fill=GREY)
            bx = badge(d, x + sw, ly - 1, s["status"], sans_b(9),
                       STATUS_BG[s["status"]])
            check("small source overlap " + s["city"],
                  tw(src, sf) + 4 < bx - x)
            ly += 13
            if c == 0:
                row_bottom = ly
        y = row_bottom + 4

    # ---- map band
    d.text((MX, y), "WHERE IT HAPPENED — STORIES 1-13", font=sans_b(13), fill=BLACK)
    y += 16
    draw_map(d, MX, y, CW, MAP_H)
    y += MAP_H + 3
    lx = MX
    lf = sans_b(10)
    for name, count in REGION_STRIP:
        col = REGIONS[name][1] if name in REGIONS else REGIONS["GLOBAL"][1]
        d.rectangle([lx, y + 1, lx + 10, y + 11], fill=col)
        t = "%s %d" % (name, count)
        d.text((lx + 13, y), t, font=lf, fill=INK)
        lx += 13 + tw(t, lf) + 14
    check("map legend width", lx <= W - MX)
    y += 14

    # ---- ALSO band
    d.text((MX, y), "ALSO ON FRIDAY 27 NOVEMBER — 30 MORE STORIES, NUMBERED AND COLOUR-MATCHED BY REGION",
           font=sans_b(14), fill=BLACK)
    y += 18
    col_w = (CW - 2 * 8) // 3
    col_x = [MX, MX + col_w + 8, MX + 2 * (col_w + 8)]
    for i, (num, city, head, src, region) in enumerate(ALSO):
        col = i // 10
        r = i % 10
        x = col_x[col]
        ry = y + r * ALSO_LEAD
        tag, tcol = REGIONS[region]
        nf = sans_b(10)
        d.text((x, ry), "%d." % num, font=nf, fill=INK)
        tx = x + tw("43. ", nf) + 2
        tagf = sans_b(8)
        tw_chip = chip(d, tx, ry, tag, tagf, tcol, pad_x=3, pad_h=11)
        hx = tx + tw_chip + 4
        avail = x + col_w - hx
        text = "%s — %s (%s)" % (city, head, src)
        done = False
        for fs in (11, 10, 9, 8):
            f = sans(fs)
            if tw(text, f) <= avail:
                d.text((hx, ry), text, font=f, fill=INK)
                done = True
                break
        if not done:
            f = sans(8)
            d.text((hx, ry), text, font=f, fill=INK)
            check("also row %d width" % num, tw(text, f) <= avail)
    y += 10 * ALSO_LEAD + 3

    # ---- DATE CHECK box
    box_y = y
    d.rectangle([MX, box_y, W - MX, box_y + 2], fill=RED)
    d.text((MX, box_y + 4), "DATE CHECK — WHAT WE LEFT OUT AND WHY",
           font=sans_b(12), fill=DRED)
    iy = box_y + 19
    _, iy = para(d, MX, iy, DATE_ITEMS, sans(9), CW, 12, fill=INK)
    iy += 1
    d.text((MX, iy), "HOW SURE:  ", font=sans_b(10), fill=INK)
    hx = MX + tw("HOW SURE:  ", sans_b(10))
    d.text((hx, iy), "CONFIRMED = 2+ outlets  ·  OFFICIAL = on the record  ·  "
                     "REPORTED = one outlet  ·  CLAIM = one side's account",
           font=sans(10), fill=INK)
    iy += 13
    _, iy = para(d, MX, iy, SOURCES, sans(9), CW, 11, fill=GREY)
    box_bottom = iy + 3
    d.rectangle([MX, box_bottom, W - MX, box_bottom + 2], fill=RED)
    d.rectangle([MX, box_y, MX + 2, box_bottom + 2], fill=RED)
    d.rectangle([W - MX - 2, box_y, W - MX, box_bottom + 2], fill=RED)
    y = box_bottom + 5

    # ---- footer
    foot = ("Every story above happened or was first reported on Friday "
            "27 November 2026. All drawings original, made for this page.")
    ff = sans(10)
    d.text(((W - tw(foot, ff)) / 2, y), foot, font=ff, fill=GREY)
    y += 13

    print("final y:", y, "canvas:", H)
    print("overflows:", OVERFLOWS if OVERFLOWS else "none")
    check("page fits", y <= H - 2)
    img.save(OUT)
    print("saved:", OUT, os.path.getsize(OUT), "bytes")


if __name__ == "__main__":
    main()
