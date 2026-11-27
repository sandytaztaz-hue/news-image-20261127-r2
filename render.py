#!/usr/bin/env python3
"""Sum 27 — DATE CHECK left-padding fix render.
Draws the 1024x1024 Friday 27 November 2026 broadsheet with Pillow/TrueType.
Written fresh from the prose brief; reproduces the current page exactly
except the DATE CHECK text now starts 10px inside the red box's left border,
and every other text block gets the same proper left padding.
"""
import os
from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "entry.png")

DJ = "/usr/share/fonts/truetype/dejavu/"
LB = "/usr/share/fonts/truetype/liberation/"

def serif_b(sz): return ImageFont.truetype(DJ + "DejaVuSerif-Bold.ttf", sz)
def serif_i(sz): return ImageFont.truetype(LB + "LiberationSerif-Italic.ttf", sz)
def sans(sz):    return ImageFont.truetype(DJ + "DejaVuSans.ttf", sz)
def sans_b(sz):  return ImageFont.truetype(DJ + "DejaVuSans-Bold.ttf", sz)

RED = (198, 12, 48)
BLACK = (15, 15, 15)
GREY = (90, 90, 90)
DARKGREY = (60, 60, 60)
WHITE = (255, 255, 255)
CREAM = (255, 253, 248)

REGION = {
    "EUROPE": (211, 47, 47), "MIDDLE EAST": (245, 124, 0), "MIDEAST": (245, 124, 0),
    "SOUTH ASIA": (0, 137, 123), "S ASIA": (0, 137, 123),
    "EAST ASIA": (21, 101, 192), "E ASIA": (21, 101, 192),
    "SE ASIA": (124, 179, 66), "NORTH AMERICA": (46, 125, 50), "N AMER": (46, 125, 50),
    "OCEANIA": (123, 31, 162), "AFRICA": (130, 119, 23),
    "GLOBAL & SPACE": (55, 71, 79), "SPACE": (55, 71, 79),
}
STATUS_COL = {"CONFIRMED": (46, 125, 50), "OFFICIAL": (21, 101, 192),
              "REPORTED": (66, 66, 66), "CLAIM": (230, 126, 34)}

im = Image.new("RGB", (W, H), CREAM)
d = ImageDraw.Draw(im)

def tw(text, font):
    return d.textlength(text, font=font)

def wrap(text, font, maxw):
    words = text.split()
    lines, cur = [], ""
    for w_ in words:
        t = (cur + " " + w_).strip()
        if tw(t, font) <= maxw:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w_
    if cur:
        lines.append(cur)
    return lines

def draw_wrapped(text, font, x, y, maxw, leading, fill=BLACK, max_lines=None):
    lines = wrap(text, font, maxw)
    if max_lines:
        assert len(lines) <= max_lines, f"wrap overflow ({len(lines)}>{max_lines}): {text!r}"
    for i, ln in enumerate(lines):
        d.text((x, y + i * leading), ln, font=font, fill=fill)
    return len(lines)

def chip(text, x, y, font, fg=WHITE, bg=None, pad=3):
    w_ = int(tw(text, font)) + pad * 2
    h_ = font.size + 4
    if bg is not None:
        d.rectangle([x, y, x + w_, y + h_], fill=bg)
    d.text((x + pad, y + 2), text, font=font, fill=fg)
    return w_

def status_badge(status, right_x, y):
    f = sans_b(9)
    w_ = int(tw(status, f)) + 8
    d.rectangle([right_x - w_, y, right_x, y + 13], fill=STATUS_COL[status])
    d.text((right_x - w_ + 4, y + 2), status, font=f, fill=WHITE)

def source_row(x, right_x, y, source, status):
    d.text((x, y), "Source: " + source, font=sans(9), fill=DARKGREY)
    status_badge(status, right_x, y - 1)

def windows(x, y, w, h, cols, rows, lit=(255, 214, 90), dark=(70, 90, 120)):
    cw, ch = w // cols, h // rows
    for r in range(rows):
        for c in range(cols):
            col = lit if (r * cols + c) % 3 else dark
            d.rectangle([x + c * cw + 2, y + r * ch + 2,
                         x + (c + 1) * cw - 2, y + (r + 1) * ch - 2], fill=col)

def badge_in_scene(x, y, text):
    f = sans_b(9)
    w_ = int(tw(text, f)) + 10
    d.rectangle([x + 4, y + 4, x + 4 + w_, y + 17], fill=RED)
    d.text((x + 9, y + 6), text, font=f, fill=WHITE)

def flame(x, y, s):
    d.polygon([(x, y), (x + s // 2, y - s), (x + s, y)], fill=(255, 140, 0))
    d.polygon([(x + s // 4, y), (x + s // 2, y - s // 2), (x + 3 * s // 4, y)],
              fill=(255, 220, 0))

def smoke(x, y, r, col=(150, 150, 150)):
    for dx, dy, rr in ((0, 0, r), (r, -r // 2, r * 3 // 4), (-r, -r // 2, r * 3 // 4)):
        d.ellipse([x + dx - rr, y + dy - rr, x + dx + rr, y + dy + rr], fill=col)

def building(x, y, w, h, col, win_lit=(255, 214, 90)):
    d.rectangle([x, y, x + w, y + h], fill=col)
    windows(x + 3, y + 4, w - 6, h - 8, max(2, w // 14), max(2, h // 12), lit=win_lit)

def tree(x, y, s=6):
    d.rectangle([x - 1, y, x + 1, y + s], fill=(101, 67, 33))
    d.ellipse([x - s, y - s, x + s, y], fill=(46, 125, 50))

def person(x, y, col=BLACK):
    d.ellipse([x - 2, y - 7, x + 2, y - 3], fill=col)
    d.rectangle([x - 2, y - 3, x + 2, y + 4], fill=col)

# ---------------------------------------------------------------- top bands
d.rectangle([0, 0, W, 4], fill=RED)
d.text((8, 8), "THE WORLD IN ONE DAY", font=sans_b(11), fill=BLACK)
rt = "43 STORIES \u00b7 9 REGIONS \u00b7 14 FIELDS \u00b7 EVERY ONE FIRST REPORTED FRI 27 NOV 2026"
d.text((W - 8 - tw(rt, sans_b(11)), 8), rt, font=sans_b(11), fill=BLACK)
d.text((8, 12), "Friday 27 November 2026", font=serif_b(58), fill=BLACK)
d.text((8, 76), "Bangkok ablaze \u00b7 Drones kill two Italians in Kuwait \u00b7 EU summit wraps up",
       font=serif_i(15), fill=RED)
d.text((8, 94), "14 FIELDS \u2014 Politics 7 \u00b7 Sport 6 \u00b7 Economy 5 \u00b7 War 4 \u00b7 Law 4 \u00b7 "
       "Disaster 3 \u00b7 Business 3 \u00b7 Tech 2 \u00b7 Space 2 \u00b7 Education 2 \u00b7 Defence 2 \u00b7 "
       "Migration 1 \u00b7 Nuclear 1 \u00b7 Society 1", font=sans(10), fill=BLACK)

# stat strip: 7 boxes
stats = [("2", "Italians killed in Kuwait"), ("3", "dead in Karachi collapse"),
         ("500,000", "homes dark in US storm"), ("10", "killed in Gaza strikes"),
         ("67/131", "NZ coalition's majority"), ("77,000", "UK net migration, lowest since 1997"),
         ("11,000", "Rs cr cabinet plan")]
sw = (1008 - 6 * 6) // 7
for i, (num, lab) in enumerate(stats):
    x0 = 8 + i * (sw + 6)
    d.rectangle([x0, 102, x0 + sw, 152], outline=(150, 150, 150), width=1)
    d.rectangle([x0, 102, x0 + sw, 105], fill=RED)
    nf = sans_b(25)
    d.text((x0 + (sw - tw(num, nf)) / 2, 105), num, font=nf, fill=BLACK)
    draw_wrapped(lab, sans(9), x0 + 4, 131, sw - 8, 10, fill=DARKGREY, max_lines=2)

# region strip
regions = [("EUROPE", 8), ("MIDDLE EAST", 4), ("SOUTH ASIA", 12), ("EAST ASIA", 3),
           ("SE ASIA", 1), ("NORTH AMERICA", 7), ("OCEANIA", 6), ("AFRICA", 1),
           ("GLOBAL & SPACE", 1)]
rx = 8
for name, n in regions:
    d.rectangle([rx, 158, rx + 10, 168], fill=REGION[name])
    t = f"{name} {n}"
    d.text((rx + 13, 157), t, font=sans_b(11), fill=BLACK)
    rx += 13 + int(tw(t, sans_b(11))) + 16

# UTC timeline
timeline = [("03:00", "Bangkok fire"), ("06:00", "Kyiv missiles"), ("09:00", "EU summit wraps"),
            ("12:00", "Tata Trusts to court"), ("14:00", "NZ final result"),
            ("17:00", "Ramaphosa wins"), ("20:00", "Kim vows nukes"), ("21:00", "Storm 500,000 dark")]
d.line([(20, 188), (1004, 188)], fill=GREY, width=2)
for i, (tm, lab) in enumerate(timeline):
    cx = 60 + i * 130
    d.ellipse([cx - 6, 182, cx + 6, 194], fill=RED, outline=WHITE, width=2)
    d.text((cx - tw(tm, sans_b(11)) / 2, 168), tm, font=sans_b(11), fill=BLACK)
    d.text((cx - tw(lab, sans(10)) / 2, 196), lab, font=sans(10), fill=BLACK)

# ---------------------------------------------------------------- scenes
def scene_bangkok(x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(255, 183, 77))
    d.ellipse([x + w - 40, y + 4, x + w - 12, y + 32], fill=(255, 236, 150))
    building(x + 8, y + 18, 46, h - 18, (120, 72, 60))
    building(x + 60, y + 10, 54, h - 10, (90, 60, 70))
    d.rectangle([x + 120, y + 22, x + 128, y + h], fill=(80, 80, 80))
    d.rectangle([x + 138, y + 16, x + 146, y + h], fill=(80, 80, 80))
    smoke(x + 150, y + 8, 7); smoke(x + 190, y + 6, 8)
    flame(x + 170, y + h - 12, 16); flame(x + 205, y + h - 10, 13); flame(x + 240, y + h - 12, 15)
    d.rectangle([x, y + h - 8, x + w, y + h], fill=(90, 90, 90))
    d.rectangle([x + 20, y + h - 16, x + 52, y + h - 8], fill=(211, 47, 47))
    person(x + 90, y + h - 10, (0, 60, 140)); person(x + 100, y + h - 10, (0, 60, 140))
    d.line([(x + 100, y + h - 12), (x + 170, y + h - 20)], fill=(30, 120, 200), width=2)
    badge_in_scene(x, y, "ALL UNITS SHUT")

def scene_kuwait(x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(250, 211, 144))
    d.ellipse([x + 12, y + 6, x + 34, y + 28], fill=(255, 244, 200))
    building(x + 10, y + 26, 50, h - 26, (150, 130, 110))
    building(x + 66, y + 30, 44, h - 30, (170, 150, 120))
    d.rectangle([x + 150, y + 20, x + 210, y + 30], fill=(90, 90, 90))
    d.ellipse([x + 172, y + 22, x + 188, y + 28], fill=(60, 60, 60))
    d.line([(x + 150, y + 25), (x + 120, y + 25)], fill=(60, 60, 60), width=2)
    d.line([(x + 210, y + 25), (x + 240, y + 25)], fill=(60, 60, 60), width=2)
    flame(x + 250, y + 34, 12)
    d.rectangle([x, y + h - 8, x + w, y + h], fill=(120, 100, 70))
    d.rectangle([x + 260, y + h - 18, x + 300, y + h - 8], fill=(90, 120, 90))
    badge_in_scene(x, y, "2 KILLED")

def scene_brussels(x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(140, 180, 230))
    building(x + 14, y + 14, 90, h - 14, (60, 90, 160))
    building(x + 112, y + 8, 100, h - 8, (40, 70, 140))
    building(x + 220, y + 18, 80, h - 18, (70, 100, 170))
    for bx in (14, 112, 220):
        windows(x + bx + 4, y + 16, 70, 22, 5, 2, lit=(255, 220, 120))
    for i, (sx, sy) in enumerate([(160, 12), (172, 18), (180, 28), (172, 38), (160, 42), (148, 38), (140, 28), (148, 18)]):
        d.ellipse([x + sx - 2, y + sy - 2, x + sx + 2, y + sy + 2], fill=(255, 220, 0))
    d.rectangle([x + 240, y + 4, x + 244, y + 20], fill=(200, 200, 200))
    d.rectangle([x + 244, y + 4, x + 262, y + 12], fill=(0, 60, 160))
    d.rectangle([x, y + h - 7, x + w, y + h], fill=(70, 140, 70))
    tree(x + 30, y + h - 12); tree(x + 310, y + h - 12)
    badge_in_scene(x, y, "2028-34 BUDGET")

def scene_small(x, y, w, h, kind):
    skies = {"gaza": (250, 220, 170), "kyiv": (150, 190, 235), "riyadh": (120, 200, 210),
             "london": (170, 180, 190), "pyongyang": (40, 60, 120), "pretoria": (250, 210, 130),
             "wellington": (140, 200, 160), "newyork": (70, 60, 130), "newdelhi": (250, 220, 150),
             "mumbai": (150, 190, 235)}
    d.rectangle([x, y, x + w, y + h], fill=skies[kind])
    if kind == "gaza":
        building(x + 6, y + 12, 34, h - 12, (200, 180, 130))
        building(x + 46, y + 18, 30, h - 18, (180, 160, 110))
        flame(x + 90, y + h - 8, 12); smoke(x + 110, y + 8, 6)
        d.polygon([(x + 140, y + h - 6), (x + 160, y + 10), (x + 180, y + h - 6)], fill=(255, 140, 0))
        badge_in_scene(x, y, "10 KILLED")
    elif kind == "kyiv":
        building(x + 6, y + 14, 36, h - 14, (90, 110, 150))
        building(x + 48, y + 10, 40, h - 10, (70, 90, 130))
        d.line([(x + 100, y + 4), (x + 130, y + 22)], fill=WHITE, width=2)
        d.line([(x + 140, y + 2), (x + 165, y + 20)], fill=WHITE, width=2)
        for px_ in (110, 130, 155):
            d.ellipse([x + px_, y + 24, x + px_ + 4, y + 28], fill=(255, 220, 0))
        badge_in_scene(x, y, "MISSILES HIT")
    elif kind == "riyadh":
        d.rectangle([x + 70, y + 6, x + 84, y + h], fill=(240, 240, 240))
        d.polygon([(x + 62, y + 6), (x + 77, y - 2), (x + 92, y + 6)], fill=(240, 240, 240))
        building(x + 6, y + 18, 34, h - 18, (200, 190, 160))
        d.ellipse([x + 120, y + 8, x + 132, y + 20], fill=(255, 220, 0))
        d.line([(x + 100, y + 26), (x + 126, y + 14)], fill=(60, 60, 60), width=2)
        d.line([(x + 150, y + 10), (x + 170, y + 24)], fill=(60, 60, 60), width=2)
        badge_in_scene(x, y, "2 DOWN")
    elif kind == "london":
        building(x + 6, y + 12, 40, h - 12, (120, 120, 120))
        building(x + 52, y + 8, 36, h - 8, (100, 100, 110))
        d.rectangle([x + 110, y + h - 16, x + 160, y + h - 6], fill=(200, 30, 30))
        windows(x + 114, y + h - 14, 42, 6, 5, 1, lit=(255, 240, 180))
        d.ellipse([x + 120, y + h - 4, x + 128, y + h + 2], fill=BLACK)
        d.ellipse([x + 144, y + h - 4, x + 152, y + h + 2], fill=BLACK)
        d.polygon([(x + 165, y + h - 6), (x + 185, y + 4), (x + 195, y + h - 6)], fill=(46, 125, 50))
        badge_in_scene(x, y, "SINCE 1997")
    elif kind == "pyongyang":
        d.rectangle([x + 20, y + 4, x + 24, y + h - 6], fill=(200, 200, 200))
        d.rectangle([x + 24, y + 4, x + 48, y + 14], fill=(211, 47, 47))
        d.rectangle([x + 70, y + 16, x + 150, y + h - 6], fill=(200, 200, 200))
        windows(x + 74, y + 20, 72, 12, 6, 1, lit=(255, 220, 0))
        d.polygon([(x + 160, y + h - 6), (x + 185, y + 8), (x + 195, y + h - 6)], fill=(120, 120, 140))
        badge_in_scene(x, y, "MORE NUKES")
    elif kind == "pretoria":
        building(x + 8, y + 12, 44, h - 12, (220, 200, 160))
        for cx_ in (16, 28, 40):
            d.rectangle([x + cx_, y + 18, x + cx_ + 4, y + h - 6], fill=(255, 255, 255))
        d.ellipse([x + 150, y + 4, x + 172, y + 26], fill=(255, 220, 0))
        tree(x + 90, y + h - 8); tree(x + 120, y + h - 8)
        d.rectangle([x, y + h - 6, x + w, y + h], fill=(90, 160, 90))
        badge_in_scene(x, y, "COURT WIN")
    elif kind == "wellington":
        d.polygon([(x, y + h), (x + 60, y + 8), (x + 120, y + h)], fill=(80, 160, 90))
        d.polygon([(x + 80, y + h), (x + 150, y + 2), (x + w, y + h)], fill=(60, 140, 80))
        d.text((x + 90, y + 12), "67-64", font=sans_b(10), fill=WHITE)
        badge_in_scene(x, y, "67 / 131")
    elif kind == "newyork":
        building(x + 6, y + 10, 34, h - 10, (50, 50, 90))
        building(x + 46, y + 16, 30, h - 16, (60, 60, 100))
        windows(x + 9, y + 14, 28, 16, 3, 2, lit=(255, 220, 0))
        d.rectangle([x + 100, y + h - 14, x + 140, y + h - 6], fill=(255, 200, 0))
        d.ellipse([x + 108, y + h - 4, x + 114, y + h + 2], fill=BLACK)
        d.ellipse([x + 128, y + h - 4, x + 134, y + h + 2], fill=BLACK)
        d.line([(x + 160, y + 4), (x + 150, y + 16), (x + 162, y + 16), (x + 150, y + 30)],
               fill=(255, 240, 0), width=2)
        badge_in_scene(x, y, "500,000 DARK")
    elif kind == "newdelhi":
        building(x + 10, y + 12, 60, h - 12, (230, 200, 150))
        for cx_ in (18, 32, 46, 58):
            d.rectangle([x + cx_, y + 18, x + cx_ + 4, y + h - 6], fill=(255, 255, 255))
        d.polygon([(x + 100, y + 10), (x + 130, y + 4), (x + 160, y + 10)], fill=(180, 60, 60))
        tree(x + 175, y + h - 8)
        badge_in_scene(x, y, "COURT RULES")
    elif kind == "mumbai":
        building(x + 6, y + 12, 36, h - 12, (150, 150, 170))
        building(x + 48, y + 8, 40, h - 8, (130, 130, 160))
        d.rectangle([x + 120, y + 8, x + 126, y + 26], fill=(120, 80, 40))
        d.rectangle([x + 108, y + 26, x + 138, y + 30], fill=(120, 80, 40))
        tree(x + 160, y + h - 8); tree(x + 180, y + h - 8)
        badge_in_scene(x, y, "COURT FIGHT")
    d.rectangle([x, y + h - 4, x + w, y + h], fill=(60, 60, 60))

# ---------------------------------------------------------------- heroes
heroes = [
    ("BANGKOK", "DISASTER", "Massive fire engulfs Bangkok oil refinery",
     "Blaze at the Bangchak refinery injures several workers; the company shuts every unit.",
     "Thailand's top refinery offline; fuel prices and flights face days of disruption.",
     "Reuters", "CONFIRMED", scene_bangkok),
    ("KUWAIT", "WAR", "Iranian drones kill two Italians in Kuwait",
     "Officials say two Italian nationals died in an Iranian drone attack on Kuwait. Rome confirms the deaths.",
     "First Iranian strike to kill Europeans in the Gulf; Rome demands answers, oil jumps.",
     "NYT", "REPORTED", scene_kuwait),
    ("BRUSSELS", "POLITICS", "EU summit wraps up after two days on budget and Ukraine",
     "Leaders close the two-day Brussels summit on the 2028-34 budget and Ukraine funding. The budget deal is unfinished.",
     "Seven years of EU spending and Kyiv's war funding now hinge on one unfinished deal.",
     "EU Council", "OFFICIAL", scene_brussels),
]
for i, (city, field, head, deck, why, src, st, fn) in enumerate(heroes):
    x0 = 8 + i * 339
    fn(x0, 208, 330, 50)
    d.rectangle([x0, 262, x0 + 330, 278], fill=BLACK)
    d.text((x0 + 6, 264), f"{city} \u2014 {field}", font=sans_b(12), fill=(255, 80, 80))
    draw_wrapped(head, serif_b(19), x0 + 2, 282, 326, 23, max_lines=2)
    draw_wrapped(deck, sans(10), x0 + 2, 332, 326, 13, max_lines=2)
    label = "WHY IT MATTERS: "
    lines = wrap(label + why, sans(10), 326)
    assert len(lines) <= 2, f"WHY overflow: {why!r}"
    d.text((x0 + 2, 364), label, font=sans_b(10), fill=RED)
    d.text((x0 + 2 + int(tw(label, sans_b(10))), 364), lines[0][len(label):], font=sans(10), fill=BLACK)
    if len(lines) > 1:
        d.text((x0 + 2, 377), lines[1], font=sans(10), fill=BLACK)
    source_row(x0 + 2, x0 + 330, 394, src, st)

# ---------------------------------------------------------------- small scenes
small = [
    ("GAZA", "WAR", "Israel kills 10 in Gaza", "Hamas weighs its response as strikes go on.",
     "Reuters", "REPORTED", "gaza"),
    ("KYIV", "WAR", "Russian missiles hit Kyiv", "Missiles hit Kyiv; the mayor reports damage. Residents shelter.",
     "AP", "REPORTED", "kyiv"),
    ("RIYADH", "WAR", "Saudis intercept Houthi missiles", "Air defences down two Houthi missiles. Riyadh reports no damage.",
     "Reuters", "CONFIRMED", "riyadh"),
    ("LONDON", "MIGRATION", "UK migration falls to record low", "Net migration at its lowest since 1997. Arrivals fall as rules bite.",
     "ONS", "OFFICIAL", "london"),
    ("PYONGYANG", "NUCLEAR", "Kim vows more nuclear weapons", "Kim pledges more nukes, snubs Trump.",
     "KCNA", "CLAIM", "pyongyang"),
    ("PRETORIA", "POLITICS", "Ramaphosa wins court fight", "Court backs Ramaphosa on impeachment report. President cleared.",
     "Reuters", "CONFIRMED", "pretoria"),
    ("WELLINGTON", "ELECTION", "NZ coalition holds 67 of 131", "Final count: coalition holds 67 of 131 seats. A two-seat majority.",
     "Electoral Comm.", "OFFICIAL", "wellington"),
    ("NEW YORK", "STORM", "Storm leaves 500,000 in dark", "Thanksgiving storm cuts power to 500,000. Crews race to restore lines.",
     "AP", "REPORTED", "newyork"),
    ("NEW DELHI", "COURT", "Top court: PMLA needs a judge", "PMLA attachment needs a judicial member. Top court tightens rules.",
     "Supreme Court", "OFFICIAL", "newdelhi"),
    ("MUMBAI", "BUSINESS", "Tata Trusts fight chief pick in court", "Trusts fight Chandrasekaran in court.",
     "Mint", "REPORTED", "mumbai"),
]
for idx, (city, field, head, deck, src, st, kind) in enumerate(small):
    row, col = divmod(idx, 5)
    x0 = 8 + col * 203
    sy = 402 if row == 0 else 536
    scene_small(x0, sy, 195, 36, kind)
    ly = sy + 40
    d.rectangle([x0, ly, x0 + 195, ly + 14], fill=BLACK)
    d.text((x0 + 6, ly + 1), f"{city} \u2014 {field}", font=sans_b(10), fill=(255, 80, 80))
    draw_wrapped(head, serif_b(16), x0 + 2, ly + 18, 191, 19, max_lines=2)
    draw_wrapped(deck, sans(9), x0 + 2, ly + 58, 191, 12, max_lines=2)
    source_row(x0 + 2, x0 + 195, ly + 86, src, st)

# ---------------------------------------------------------------- map
d.text((8, 670), "WHERE IT HAPPENED \u2014 STORIES 1-13", font=sans_b(13), fill=BLACK)
mx0, my0, mw, mh = 8, 686, 1008, 50
d.rectangle([mx0, my0, mx0 + mw, my0 + mh], fill=(214, 234, 248), outline=(120, 160, 200))
for gx in range(mx0 + 84, mx0 + mw, 84):
    d.line([(gx, my0), (gx, my0 + mh)], fill=(255, 255, 255), width=1)
for gy in (my0 + 16, my0 + 33):
    d.line([(mx0, gy), (mx0 + mw, gy)], fill=(255, 255, 255), width=1)
land = (169, 223, 191)
d.polygon([(60, 700), (150, 688), (260, 690), (300, 705), (240, 725), (120, 728), (70, 715)], fill=land)
d.polygon([(300, 712), (340, 710), (360, 728), (320, 734), (300, 724)], fill=land)
d.polygon([(480, 690), (540, 686), (560, 696), (520, 704), (485, 700)], fill=land)
d.polygon([(500, 706), (560, 704), (580, 724), (540, 734), (505, 722)], fill=land)
d.polygon([(580, 688), (760, 686), (900, 692), (880, 716), (760, 728), (640, 726), (590, 710)], fill=land)
d.polygon([(850, 720), (920, 718), (935, 730), (870, 734)], fill=land)
pins = [  # (number, region, x, y)
    (1, "S ASIA", 793, 710), (2, "MIDEAST", 645, 704), (3, "EUROPE", 524, 695),
    (4, "S ASIA", 608, 703), (5, "EUROPE", 598, 695), (6, "MIDEAST", 668, 718),
    (7, "EUROPE", 499, 695), (8, "E ASIA", 864, 700), (9, "AFRICA", 591, 725),
    (10, "OCEANIA", 983, 731), (11, "N AMER", 305, 699), (12, "S ASIA", 728, 702),
    (13, "S ASIA", 716, 716),
]
for num, reg, px_, py_ in pins:
    d.ellipse([px_ - 8, py_ - 8, px_ + 8, py_ + 8], fill=REGION[reg], outline=WHITE, width=2)
    t = str(num)
    d.text((px_ - tw(t, sans_b(8)) / 2, py_ - 6), t, font=sans_b(8), fill=WHITE)
rx = 8
for name, n in regions:
    d.rectangle([rx, 741, rx + 10, 751], fill=REGION[name])
    t = f"{name} {n}"
    d.text((rx + 13, 740), t, font=sans_b(11), fill=BLACK)
    rx += 13 + int(tw(t, sans_b(11))) + 16

# ---------------------------------------------------------------- ALSO list
d.text((8, 758), "ALSO ON FRIDAY 27 NOVEMBER \u2014 30 MORE STORIES, NUMBERED AND COLOUR-MATCHED BY REGION",
       font=sans_b(13), fill=BLACK)
also = [
    (14, "S ASIA", "Karachi", "Collapse kills 3, injures 14", "Dunya"),
    (15, "S ASIA", "New Delhi", "Court quashes ex-MP release", "SC"),
    (16, "S ASIA", "New Delhi", "Cabinet clears Rs 11,000 cr plan", "Govt"),
    (17, "S ASIA", "New Delhi", "GST cancellations auto from 1 Dec", "Govt"),
    (18, "S ASIA", "New Delhi", "IITs add 6,000 AI, robotics seats", "IIT"),
    (19, "E ASIA", "Beijing", "Border areas 'generally stable'", "China"),
    (20, "E ASIA", "Beijing", "Drones reshape Asia's militaries", "Reuters"),
    (21, "N AMER", "Washington", "Trump unveils new tariffs", "White House"),
    (22, "N AMER", "Washington", "Army hails Iowa explosives win", "US Army"),
    (23, "N AMER", "Washington", "Huang cleared of security threat", "Reuters"),
    (24, "MIDEAST", "Doha", "India A v Sri Lanka A semi-final", "Asia Cup"),
    (25, "OCEANIA", "Christchurch", "India begin 2nd Test vs NZ, 11am", "NZC"),
    (26, "EUROPE", "London", "Sinner out of Australian Open, knee", "ATP"),
    (27, "EUROPE", "London", "Barrett to captain All Blacks v England", "NZR"),
    (28, "EUROPE", "Paris", "Depardieu faces trial over 2018 rape", "AFP"),
    (29, "S ASIA", "Dhaka", "India weakened Pakistan in 1971", "Parliament"),
    (30, "S ASIA", "Islamabad", "Pakistan marks 25 Nov as space day", "Govt"),
    (31, "S ASIA", "Islamabad", "PM orders fast cybercrime reforms", "Govt"),
    (32, "S ASIA", "Muzaffarabad", "Assembly backs JAAC talks", "AJK"),
    (33, "EUROPE", "Geneva", "Gukesh faces Sindarov in Game 4", "FIDE"),
    (34, "N AMER", "San Francisco", "Claude artifacts become apps", "Anthropic"),
    (35, "SPACE", "Pasadena", "Planet hinted beyond Neptune", "astronomers"),
    (36, "S ASIA", "Mumbai", "Flipkart CEO to step down next month", "company"),
    (37, "OCEANIA", "Auckland", "Black Friday deals 'no cheaper'", "Consumer NZ"),
    (38, "OCEANIA", "Wellington", "School English curriculum paused", "Ministry"),
    (39, "OCEANIA", "Auckland", "Driver licence waits hit 80 days", "NZTA"),
    (40, "OCEANIA", "Sydney", "Kibon sidelined in PGA opener", "DP World Tour"),
    (41, "N AMER", "New York", "US markets reopen for short session", "NYSE"),
    (42, "EUROPE", "Brussels", "EU budget summit ends, no deal", "Reuters"),
    (43, "N AMER", "New York", "Target, Kohl's gift giveaways", "The Street"),
]
# auto-fit ALSO font so every row fits its column
also_font = None
for sz in (10, 9.5, 9, 8.5, 8):
    f = sans(sz)
    ok = True
    for num, reg, city, head, src in also:
        tagw = int(tw(reg, sans_b(8))) + 6
        w_ = int(tw(f"{num}. ", sans_b(sz))) + tagw + 4 + int(tw(f"{city} \u2014 {head} ({src})", f))
        if w_ > 326:
            ok = False
            break
    if ok:
        also_font = f
        break
assert also_font is not None, "ALSO rows do not fit even at 8px"
for idx, (num, reg, city, head, src) in enumerate(also):
    col, row = divmod(idx, 10)
    x0 = 8 + col * 339
    y0 = 776 + row * 13
    nf = sans_b(also_font.size)
    d.text((x0 + 4, y0), f"{num}.", font=nf, fill=BLACK)
    nx = x0 + 4 + int(tw(f"{num}.", nf)) + 3
    tagw = chip(reg, nx, y0, sans_b(8), bg=REGION[reg])
    d.text((nx + tagw + 4, y0), f"{city} \u2014 {head} ({src})", font=also_font, fill=BLACK)

# ---------------------------------------------------------------- DATE CHECK (the fix: 10px left padding)
bx0, by0, bx1, by1 = 10, 912, 1014, 1002
d.rectangle([bx0, by0, bx1, by1], outline=RED, width=3)
pad = 10
tx = bx0 + pad
tmax = bx1 - pad
d.text((tx, 917), "DATE CHECK \u2014 WHAT WE LEFT OUT AND WHY", font=sans_b(13), fill=RED)
leftout = ("\u00d7 Macy's Parade postponed \u2014 announced 25 Nov \u00b7 \u00d7 Cairo tanker fire, 31 dead "
           "\u2014 25 Nov \u00b7 \u00d7 Israel kills Hamas deputy minister in Gaza \u2014 26 Nov \u00b7 "
           "\u00d7 Congo Ebola passes 12,000 cases \u2014 26 Nov \u00b7 \u00d7 Chess Game 3 ends in a draw "
           "\u2014 26 Nov \u00b7 \u00d7 FedEx jet overruns Miami runway \u2014 26 Nov \u00b7 "
           "\u00d7 Hong Kong mourns Wang Fuk Court fire dead, one year on \u2014 26 Nov")
draw_wrapped(leftout, sans(10), tx, 934, tmax - tx, 13, max_lines=2)
d.text((tx, 961), "HOW SURE:", font=sans_b(10), fill=BLACK)
hw = int(tw("HOW SURE: ", sans_b(10)))
d.text((tx + hw, 961), "CONFIRMED = 2+ outlets \u00b7 OFFICIAL = on the record \u00b7 REPORTED = one outlet \u00b7 CLAIM = one side's account",
       font=sans(10), fill=BLACK)
sources = ("SOURCES: Reuters \u00b7 AP \u00b7 NYT \u00b7 ONS \u00b7 Electoral Commission \u00b7 KCNA \u00b7 Mint "
           "\u00b7 Dunya \u00b7 FIDE \u00b7 ATP \u00b7 NZR \u00b7 NZC \u00b7 Anthropic \u00b7 NYSE \u00b7 The Street "
           "\u00b7 Consumer NZ \u00b7 EU Council \u00b7 Supreme Court \u00b7 US Army \u00b7 White House \u00b7 NZTA "
           "\u00b7 AFP \u00b7 Asia Cup \u00b7 IIT \u00b7 Parliament \u00b7 AJK \u00b7 DP World Tour \u00b7 Govt "
           "\u00b7 Ministry \u00b7 China \u00b7 SC")
draw_wrapped(sources, sans(10), tx, 974, tmax - tx, 13, max_lines=2)

# footer
ft = "Every story above happened or was first reported on Friday 27 November 2026. All drawings original, made for this page."
d.text(((W - tw(ft, sans(10))) / 2, 1006), ft, font=sans(10), fill=DARKGREY)

im.save(OUT)
print("wrote", OUT, os.path.getsize(OUT), "bytes")
