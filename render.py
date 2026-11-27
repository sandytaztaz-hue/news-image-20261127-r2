#!/usr/bin/env python3
"""Sum 27 clip-fix renderer -- fresh Pillow + TrueType drawing program.

Draws the 1024x1024 broadsheet for make.fun news-image-20261127
(Friday 27 November 2026, 43 stories). This is a CLIPPED-TEXT fix:
every text block is measured BEFORE it is placed, every band starts at
(measured bottom of the block above + clearance), and ALL boxes/scenes
are painted FIRST with ALL text painted LAST, so nothing can ever paint
over text. Clearance rule: >=6px empty space below every text line or
badge before the next drawing, box, or rule starts.

Run: python3 render.py   -> writes entry.png next to this file.
"""
import os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
DJ = "/usr/share/fonts/truetype/dejavu/"
LB = "/usr/share/fonts/truetype/liberation/"


def F(path, size):
    return ImageFont.truetype(path, size)


# ---------------------------------------------------------------- fonts
SERIF_B = DJ + "DejaVuSerif-Bold.ttf"
SERIF_I = LB + "LiberationSerif-Italic.ttf"
SANS = DJ + "DejaVuSans.ttf"
SANS_B = DJ + "DejaVuSans-Bold.ttf"
LSANS = LB + "LiberationSans-Regular.ttf"
LSANS_B = LB + "LiberationSans-Bold.ttf"

f_kicker = F(SANS_B, 13)
f_kicker_r = F(SANS_B, 12)
f_mast = F(SERIF_B, 56)
f_redkick = F(SERIF_I, 15)
f_fields = F(SANS, 11)
f_statnum = F(SANS_B, 28)
f_statlab = F(SANS, 10)
f_region = F(SANS_B, 11)
f_time = F(SANS_B, 11)
f_tlabel = F(SANS, 11)
f_badge_h = F(SANS_B, 10)
f_badge_s = F(SANS_B, 9)
f_bar_city = F(SANS_B, 12)
f_bar_field = F(SANS_B, 11)
f_hhero = F(SERIF_B, 19)
f_hsmall = F(SERIF_B, 16)
f_deck = F(SANS, 11)
f_why = F(SANS, 11)
f_why_b = F(SANS_B, 11)
f_src = F(SANS_B, 10)
f_srcbadge = F(SANS_B, 9)
f_maphead = F(SANS_B, 13)
f_legend = F(SANS_B, 10)
f_alsohead = F(SANS_B, 13)
f_also = F(LSANS, 10)
f_also_b = F(LSANS_B, 10)
f_dctitle = F(SANS_B, 12)
f_dc = F(SANS, 10)
f_dc_b = F(SANS_B, 10)
f_footer = F(SANS, 11)

# ---------------------------------------------------------------- colours
WHITE = (255, 255, 255)
PAPER = (255, 255, 255)
INK = (17, 17, 17)
GREY = (70, 70, 70)
RED = (200, 16, 46)
RED_DK = (160, 14, 38)
RED_LT = (255, 90, 90)
BLACK = (17, 17, 17)
GREEN_OK = (14, 122, 61)
BLUE_OFF = (31, 95, 204)
DARK_REP = (34, 34, 34)
ORANGE_CL = (230, 126, 0)
BADGE_RED = (200, 16, 46)

REGION = {
    "EUROPE": (212, 61, 42),
    "MIDDLE EAST": (245, 130, 32),
    "SOUTH ASIA": (14, 138, 123),
    "EAST ASIA": (31, 111, 214),
    "SE ASIA": (140, 198, 63),
    "NORTH AMERICA": (30, 122, 52),
    "OCEANIA": (123, 44, 191),
    "AFRICA": (138, 125, 0),
    "GLOBAL & SPACE": (58, 71, 86),
}
REGION_TAG = {
    "EUROPE": "EUROPE", "MIDDLE EAST": "MIDEAST", "SOUTH ASIA": "S ASIA",
    "EAST ASIA": "E ASIA", "SE ASIA": "SE ASIA", "NORTH AMERICA": "N AMER",
    "OCEANIA": "OCEANIA", "AFRICA": "AFRICA", "GLOBAL & SPACE": "SPACE",
}
BADGE_FILL = {
    "CONFIRMED": GREEN_OK, "OFFICIAL": BLUE_OFF,
    "REPORTED": DARK_REP, "CLAIM": ORANGE_CL,
}

W, H = 1024, 1024
ML, MR = 8, 1016          # left / right content edges
CW = MR - ML              # 1008

# ---------------------------------------------------------------- data
FIELDS_LINE = ("14 FIELDS \u2014 Politics 7 \u00b7 Sport 6 \u00b7 Economy 5 \u00b7 War 4 "
               "\u00b7 Law 4 \u00b7 Disaster 3 \u00b7 Business 3 \u00b7 Tech 2 \u00b7 Space 2 "
               "\u00b7 Education 2 \u00b7 Defence 2 \u00b7 Migration 1 \u00b7 Nuclear 1 "
               "\u00b7 Society 1")

STATS = [
    ("2", "Italians killed in Kuwait"),
    ("3", "dead in Karachi collapse"),
    ("500,000", "homes dark in US storm"),
    ("10", "killed in Gaza strikes"),
    ("67/131", "NZ coalition's majority"),
    ("77,000", "UK net migration, lowest since 1997"),
    ("11,000", "Rs cr cabinet plan"),
]

REGIONS = [
    ("EUROPE", 8), ("MIDDLE EAST", 4), ("SOUTH ASIA", 12), ("EAST ASIA", 3),
    ("SE ASIA", 1), ("NORTH AMERICA", 7), ("OCEANIA", 6), ("AFRICA", 1),
    ("GLOBAL & SPACE", 1),
]

TIMELINE = [
    ("03:00", "Bangkok fire"), ("06:00", "Kyiv missiles"),
    ("09:00", "EU summit wraps"), ("12:00", "Tata Trusts to court"),
    ("14:00", "NZ final result"), ("17:00", "Ramaphosa wins"),
    ("20:00", "Kim vows nukes"), ("21:00", "Storm 500,000 dark"),
]

# heroes: city, field, region, scene kind, scene badge, headline, deck, why, source, status
HEROES = [
    ("BANGKOK", "DISASTER", "SE ASIA", "bangkok", "ALL UNITS SHUT",
     "Massive fire engulfs Bangkok oil refinery",
     "Blaze at the Bangchak refinery injures several workers; the company shuts every unit.",
     "Thailand's top refinery offline; fuel prices and flights face days of disruption.",
     "Reuters", "CONFIRMED"),
    ("KUWAIT", "WAR", "MIDDLE EAST", "kuwait", "2 KILLED",
     "Iranian drones kill two Italians in Kuwait",
     "Officials say two Italian nationals died in an Iranian drone attack on Kuwait. Rome confirms the deaths.",
     "First Iranian strike to kill Europeans in the Gulf; Rome demands answers, oil jumps.",
     "NYT", "REPORTED"),
    ("BRUSSELS", "POLITICS", "EUROPE", "brussels", "2028-34 BUDGET",
     "EU summit wraps up after two days on budget and Ukraine",
     "Leaders close the two-day Brussels summit on the 2028-34 budget and Ukraine funding. The deal is unfinished.",
     "Seven years of EU spending and Kyiv's war funding now hinge on one unfinished deal.",
     "EU Council", "OFFICIAL"),
]

# small scenes: city, field, region, scene kind, scene badge, headline, deck, source, status
SMALL = [
    ("GAZA", "WAR", "MIDDLE EAST", "gaza", "10 KILLED",
     "Israel kills 10 in Gaza",
     "Hamas weighs its response as strikes go on.",
     "Reuters", "REPORTED"),
    ("KYIV", "WAR", "EUROPE", "kyiv", "MISSILES HIT",
     "Russian missiles hit Kyiv",
     "Missiles hit Kyiv; the mayor reports damage. Residents shelter.",
     "AP", "REPORTED"),
    ("RIYADH", "WAR", "MIDDLE EAST", "riyadh", "2 DOWN",
     "Saudis intercept Houthi missiles",
     "Air defences down two Houthi missiles. No damage in Riyadh.",
     "Reuters", "CONFIRMED"),
    ("LONDON", "MIGRATION", "EUROPE", "london", "SINCE 1997",
     "UK migration falls to record low",
     "Net migration at its lowest since 1997. Arrivals fall as rules bite.",
     "ONS", "OFFICIAL"),
    ("PYONGYANG", "NUCLEAR", "EAST ASIA", "pyongyang", "MORE NUKES",
     "Kim vows more nuclear weapons",
     "Kim pledges more nukes, snubs Trump.",
     "KCNA", "CLAIM"),
    ("PRETORIA", "POLITICS", "AFRICA", "pretoria", "COURT WIN",
     "Ramaphosa wins court fight",
     "Ramaphosa wins bid to overturn impeachment report.",
     "Reuters", "CONFIRMED"),
    ("WELLINGTON", "ELECTION", "OCEANIA", "wellington", "67 / 131",
     "NZ coalition holds 67 of 131",
     "Final count: coalition holds 67 of 131 seats. A two-seat majority.",
     "Electoral Comm.", "OFFICIAL"),
    ("NEW YORK", "STORM", "NORTH AMERICA", "newyork", "500,000 DARK",
     "Storm leaves 500,000 in dark",
     "Thanksgiving storm cuts power to 500,000. Crews race to restore it.",
     "AP", "REPORTED"),
    ("NEW DELHI", "COURT", "SOUTH ASIA", "newdelhi", "COURT RULES",
     "Top court: PMLA needs a judge",
     "PMLA attachment needs a judicial member. Court tightens rules.",
     "Supreme Court", "OFFICIAL"),
    ("MUMBAI", "BUSINESS", "SOUTH ASIA", "mumbai", "COURT FIGHT",
     "Tata Trusts fight chief pick in court",
     "Trusts fight Chandrasekaran in court.",
     "Mint", "REPORTED"),
]

# ALSO items 14-43: (number, region, headline incl. city, source)
# Headlines pre-shortened where needed so each full line ends >=8px before
# the next column (measured with Liberation Sans 10).
ALSO = [
    (14, "SOUTH ASIA", "Karachi \u2014 Collapse kills 3, injures 14", "Dunya"),
    (15, "SOUTH ASIA", "New Delhi \u2014 Court quashes ex-MP release", "SC"),
    (16, "SOUTH ASIA", "New Delhi \u2014 Cabinet clears Rs 11,000 cr plan", "Govt"),
    (17, "SOUTH ASIA", "New Delhi \u2014 GST cancellations from 1 Dec", "Govt"),
    (18, "SOUTH ASIA", "New Delhi \u2014 IITs add 6,000 AI, robotics seats", "IIT"),
    (19, "EAST ASIA", "Beijing \u2014 Border areas \u2018generally stable\u2019", "China"),
    (20, "EAST ASIA", "Beijing \u2014 Drones reshape Asia\u2019s militaries", "Reuters"),
    (21, "NORTH AMERICA", "Washington \u2014 Trump unveils tariffs", "White House"),
    (22, "NORTH AMERICA", "Washington \u2014 Army hails Iowa blast win", "US Army"),
    (23, "NORTH AMERICA", "Washington \u2014 Huang cleared of threat", "Reuters"),
    (24, "MIDDLE EAST", "Doha \u2014 India v Sri Lanka A semi-final", "Asia Cup"),
    (25, "OCEANIA", "Christchurch \u2014 India begin 2nd Test, 11am", "NZC"),
    (26, "EUROPE", "London \u2014 Sinner out of Australian Open, knee", "ATP"),
    (27, "EUROPE", "London \u2014 Barrett to captain All Blacks v England", "NZR"),
    (28, "EUROPE", "Paris \u2014 Depardieu faces trial over 2018 rape", "AFP"),
    (29, "SOUTH ASIA", "Dhaka \u2014 India weakened Pakistan in 1971", "Parliament"),
    (30, "SOUTH ASIA", "Islamabad \u2014 Pakistan marks 25 Nov as space day", "Govt"),
    (31, "SOUTH ASIA", "Islamabad \u2014 PM orders fast cybercrime reforms", "Govt"),
    (32, "SOUTH ASIA", "Muzaffarabad \u2014 Assembly backs JAAC talks", "AJK"),
    (33, "EUROPE", "Geneva \u2014 Gukesh faces Sindarov in Game 4", "FIDE"),
    (34, "NORTH AMERICA", "San Francisco \u2014 Claude artifacts as apps", "Anthropic"),
    (35, "GLOBAL & SPACE", "Pasadena \u2014 Planet hinted past Neptune", "astronomers"),
    (36, "SOUTH ASIA", "Mumbai \u2014 Flipkart CEO to step down", "company"),
    (37, "OCEANIA", "Auckland \u2014 Friday deals \u2018no cheaper\u2019", "Consumer NZ"),
    (38, "OCEANIA", "Wellington \u2014 English curriculum paused", "Ministry"),
    (39, "OCEANIA", "Auckland \u2014 Driver licence waits hit 80 days", "NZTA"),
    (40, "OCEANIA", "Sydney \u2014 Kibon out of PGA opener", "DP World Tour"),
    (41, "NORTH AMERICA", "New York \u2014 Markets reopen for short session", "NYSE"),
    (42, "EUROPE", "Brussels \u2014 EU budget summit ends, no deal", "Reuters"),
    (43, "NORTH AMERICA", "New York \u2014 Target, Kohl\u2019s gift giveaways", "The Street"),
]

DC_ITEMS = ("\u00d7 Macy\u2019s Parade postponed \u2014 announced 25 Nov \u00b7 "
            "\u00d7 Cairo tanker fire, 31 dead \u2014 25 Nov \u00b7 "
            "\u00d7 Israel kills Hamas deputy minister in Gaza \u2014 26 Nov \u00b7 "
            "\u00d7 Congo Ebola passes 12,000 cases \u2014 26 Nov \u00b7 "
            "\u00d7 Chess Game 3 ends in a draw \u2014 26 Nov \u00b7 "
            "\u00d7 FedEx jet overruns Miami runway \u2014 26 Nov \u00b7 "
            "\u00d7 Hong Kong mourns Wang Fuk Court fire dead, one year on \u2014 26 Nov")
DC_HOWSURE = ("HOW SURE: CONFIRMED = 2+ outlets \u00b7 OFFICIAL = on the record "
              "\u00b7 REPORTED = one outlet \u00b7 CLAIM = one side\u2019s account")
DC_SOURCES = ("SOURCES: Reuters \u00b7 AP \u00b7 NYT \u00b7 ONS \u00b7 Electoral Commission "
              "\u00b7 KCNA \u00b7 Mint \u00b7 Dunya \u00b7 FIDE \u00b7 ATP \u00b7 NZR \u00b7 NZC "
              "\u00b7 Anthropic \u00b7 NYSE \u00b7 The Street \u00b7 Consumer NZ \u00b7 EU Council "
              "\u00b7 Supreme Court \u00b7 US Army \u00b7 White House \u00b7 NZTA \u00b7 AFP "
              "\u00b7 Asia Cup \u00b7 IIT \u00b7 Parliament \u00b7 AJK \u00b7 DP World Tour "
              "\u00b7 Govt \u00b7 Ministry \u00b7 China \u00b7 SC")

FOOTER = ("Every story above happened or was first reported on Friday 27 November 2026. "
          "All drawings original, made for this page.")

# map pins: (story no, region, fx, fy) as fractions of the map box
PINS = [
    (1, "SE ASIA", 0.77, 0.50), (2, "MIDDLE EAST", 0.63, 0.40),
    (3, "EUROPE", 0.49, 0.26), (4, "MIDDLE EAST", 0.585, 0.50),
    (5, "EUROPE", 0.535, 0.16), (6, "MIDDLE EAST", 0.625, 0.58),
    (7, "EUROPE", 0.455, 0.16), (8, "EAST ASIA", 0.855, 0.32),
    (9, "AFRICA", 0.505, 0.80), (10, "OCEANIA", 0.955, 0.85),
    (11, "NORTH AMERICA", 0.21, 0.32), (12, "SOUTH ASIA", 0.72, 0.40),
    (13, "SOUTH ASIA", 0.66, 0.64),
]


# ---------------------------------------------------------------- helpers
def ink_h(font, text):
    """Height of the actual ink box of `text` in `font`."""
    b = font.getbbox(text)
    return b[3] - b[1]


def wrap(font, text, maxw, max_lines=None):
    """Greedy word wrap; returns list of lines, each <= maxw."""
    words = text.split(" ")
    lines, cur = [], ""
    for wd in words:
        trial = (cur + " " + wd).strip()
        if font.getlength(trial) <= maxw or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = wd
    if cur:
        lines.append(cur)
    if max_lines is not None and len(lines) > max_lines:
        raise ValueError("wrap overflow (%d > %d lines): %r"
                         % (len(lines), max_lines, text))
    return lines


class Canvas:
    """Collects background ops (boxes/scenes/lines) and text ops separately;
    text is always painted after every drawing, so nothing can cover text."""

    def __init__(self):
        self.bg = []      # callables taking ImageDraw
        self.tx = []      # callables taking ImageDraw
        self.clearances = []  # (label, text_bottom, next_top)

    def rect(self, box, fill=None, outline=None, width=1):
        self.bg.append(lambda d: d.rectangle(box, fill=fill, outline=outline,
                                             width=width))

    def line(self, xy, fill, width=1):
        self.bg.append(lambda d: d.line(xy, fill=fill, width=width))

    def ellipse(self, box, fill=None, outline=None, width=1):
        self.bg.append(lambda d: d.ellipse(box, fill=fill, outline=outline,
                                           width=width))

    def polygon(self, pts, fill=None, outline=None):
        self.bg.append(lambda d: d.polygon(pts, fill=fill, outline=outline))

    def paste(self, img, box):
        self.bg.append(lambda d: d._image.paste(img, box))

    def text(self, xy, s, font, fill):
        """Draw `s` with its ink top at xy[1] (baseline-independent)."""
        b = font.getbbox(s)
        self.tx.append(lambda d: d.text((xy[0], xy[1] - b[1]), s, font=font,
                                        fill=fill))

    def text_c(self, cx, y_top, s, font, fill):
        """Centred text, ink top at y_top."""
        w = font.getlength(s)
        self.text((cx - w / 2, y_top), s, font, fill)

    def check(self, label, text_bottom, next_top):
        self.clearances.append((label, text_bottom, next_top))


def draw_lines(cv, x, y_top, font, lines, leading, fill):
    """Draw wrapped lines starting with ink top y_top; return ink bottom."""
    b = font.getbbox(lines[0]) if lines else (0, 0, 0, 0)
    for i, ln in enumerate(lines):
        cv.text((x, y_top + i * leading), ln, font, fill)
    last = font.getbbox(lines[-1]) if lines else (0, 0, 0, 0)
    return y_top + (len(lines) - 1) * leading + (last[3] - last[1])

# ---------------------------------------------------------------- scenes
# Every scene is painted onto its own small image and pasted into its box,
# so scene art can never escape its rectangle or touch any text.

def _layer(w, h, sky):
    im = Image.new("RGB", (w, h), sky)
    return im, ImageDraw.Draw(im)


def _building(d, x, y, w, h, colour, win=(255, 230, 120), cols=3, rows=2):
    d.rectangle([x, y, x + w, y + h], fill=colour)
    if w < 14 or h < 10:
        return
    for r in range(rows):
        for c in range(cols):
            wx = x + 3 + c * ((w - 6) // max(cols, 1))
            wy = y + 3 + r * ((h - 6) // max(rows, 1))
            d.rectangle([wx, wy, wx + 3, wy + 4], fill=win)


def _ground(d, w, h, colour=(70, 70, 70)):
    d.rectangle([0, h - 5, w, h], fill=colour)


def _smoke(d, x, y, s=1.0):
    g = (150, 150, 150)
    d.ellipse([x, y, x + 9 * s, y + 7 * s], fill=g)
    d.ellipse([x + 4 * s, y - 5 * s, x + 13 * s, y + 2 * s], fill=(170, 170, 170))
    d.ellipse([x + 8 * s, y - 9 * s, x + 16 * s, y - 2 * s], fill=g)


def _flame(d, x, y, s=1.0):
    d.polygon([(x, y), (x + 5 * s, y - 12 * s), (x + 10 * s, y)],
              fill=(255, 110, 0))
    d.polygon([(x + 2 * s, y), (x + 5 * s, y - 7 * s), (x + 8 * s, y)],
              fill=(255, 210, 0))


def _tree(d, x, y, s=1.0, colour=(34, 139, 34)):
    d.rectangle([x + 3 * s, y, x + 5 * s, y + 7 * s], fill=(120, 72, 20))
    d.ellipse([x, y - 7 * s, x + 8 * s, y + 1 * s], fill=colour)


def _badge(d, w, text, font):
    tw = font.getlength(text)
    bw = int(tw) + 10
    bh = 15 if font is f_badge_h else 13
    d.rectangle([4, 4, 4 + bw, 4 + bh], fill=BADGE_RED)
    b = font.getbbox(text)
    d.text((4 + 5, 4 + (bh - (b[3] - b[1])) / 2 - b[1]), text,
           font=font, fill=WHITE)


def scene(kind, w, h, hero=False):
    bf = f_badge_h if hero else f_badge_s
    if kind == "bangkok":
        im, d = _layer(w, h, (255, 233, 168))
        d.ellipse([w - 34, 4, w - 8, 30], fill=(255, 214, 90))
        _building(d, 6, h - 34, 34, 29, (120, 120, 125), cols=4, rows=3)
        _building(d, 46, h - 28, 26, 23, (90, 90, 100), cols=3, rows=2)
        d.rectangle([w - 78, h - 30, w - 58, h - 5], fill=(170, 170, 175))
        d.rectangle([w - 74, h - 26, w - 62, h - 5], fill=(200, 200, 205))
        d.rectangle([w - 52, h - 36, w - 46, h - 5], fill=(80, 80, 85))
        _smoke(d, w - 58, 6, 1.1)
        _smoke(d, w - 96, 10, 0.9)
        _flame(d, 84, h - 8, 1.2)
        _flame(d, 104, h - 8, 1.0)
        _flame(d, 122, h - 8, 0.8)
        d.rectangle([8, h - 14, 40, h - 6], fill=(200, 16, 46))
        d.rectangle([12, h - 12, 18, h - 8], fill=(180, 220, 255))
        d.rectangle([22, h - 12, 36, h - 8], fill=(180, 220, 255))
        d.line([40, h - 9, 84, h - 7], fill=(20, 90, 200), width=2)
        _ground(d, w, h, (90, 90, 90))
        _badge(d, w, "ALL UNITS SHUT", bf)
    elif kind == "kuwait":
        im, d = _layer(w, h, (247, 215, 116))
        d.ellipse([w - 40, 5, w - 16, 29], fill=(255, 240, 170))
        _building(d, 8, h - 30, 40, 25, (210, 180, 120), cols=4, rows=2)
        _building(d, 54, h - 24, 30, 19, (190, 160, 100), cols=3, rows=2)
        d.polygon([(w - 70, h - 20), (w - 58, h - 34), (w - 46, h - 20)],
                  fill=(255, 140, 0))
        d.polygon([(w - 66, h - 20), (w - 58, h - 29), (w - 50, h - 20)],
                  fill=(255, 220, 0))
        d.rectangle([w // 2 - 4, 12, w // 2 + 22, 18], fill=(90, 90, 95))
        d.line([w // 2 - 12, 10, w // 2 + 30, 10], fill=(60, 60, 65), width=2)
        d.line([w // 2 - 12, 20, w // 2 + 30, 20], fill=(60, 60, 65), width=2)
        d.ellipse([w // 2 - 2, 6, w // 2 + 4, 12], fill=(60, 60, 65))
        _tree(d, w - 24, h - 16, 1.1, (60, 140, 60))
        d.rectangle([0, h - 12, w, h - 5], fill=(222, 184, 120))
        _ground(d, w, h, (150, 120, 70))
        _badge(d, w, "2 KILLED", bf)
    elif kind == "brussels":
        im, d = _layer(w, h, (191, 217, 242))
        _building(d, 8, h - 34, 52, 29, (40, 80, 160), win=(255, 220, 60),
                  cols=5, rows=3)
        _building(d, 66, h - 30, 44, 25, (60, 100, 180), win=(255, 220, 60),
                  cols=4, rows=3)
        _building(d, 116, h - 26, 40, 21, (30, 60, 130), win=(255, 220, 60),
                  cols=4, rows=2)
        d.rectangle([w - 62, 6, w - 8, 22], fill=(0, 51, 153))
        for k in range(8):
            import math
            a = math.pi * 2 * k / 8
            d.ellipse([w - 35 + 7 * math.cos(a) - 1, 14 + 5 * math.sin(a) - 1,
                       w - 35 + 7 * math.cos(a) + 1, 14 + 5 * math.sin(a) + 1],
                      fill=(255, 204, 0))
        _tree(d, 12, h - 18, 1.0)
        _tree(d, w - 96, h - 18, 0.9)
        d.rectangle([0, h - 12, w, h - 5], fill=(90, 170, 90))
        _ground(d, w, h, (70, 130, 70))
        _badge(d, w, "2028-34 BUDGET", bf)
    elif kind == "gaza":
        im, d = _layer(w, h, (242, 216, 160))
        _building(d, 6, h - 26, 30, 21, (200, 180, 140), cols=3, rows=2)
        _building(d, 42, h - 22, 26, 17, (180, 160, 120), cols=3, rows=2)
        d.polygon([(w - 60, h - 6), (w - 34, h - 32), (w - 8, h - 6)],
                  fill=(255, 120, 0))
        d.polygon([(w - 52, h - 6), (w - 34, h - 22), (w - 16, h - 6)],
                  fill=(255, 200, 0))
        _smoke(d, w - 46, 4, 0.9)
        _ground(d, w, h, (120, 100, 70))
        _badge(d, w, "10 KILLED", bf)
    elif kind == "kyiv":
        im, d = _layer(w, h, (156, 200, 232))
        _building(d, 6, h - 26, 34, 21, (70, 90, 120), cols=4, rows=2)
        _building(d, 46, h - 22, 28, 17, (90, 110, 140), cols=3, rows=2)
        d.line([20, 6, 70, 26], fill=(255, 255, 255), width=2)
        d.line([60, 4, 110, 24], fill=(255, 255, 255), width=2)
        for (x, y) in [(30, h - 12), (60, h - 14), (95, h - 12), (130, h - 14)]:
            d.ellipse([x, y, x + 5, y + 5], fill=(255, 220, 0))
        _ground(d, w, h, (60, 60, 70))
        _badge(d, w, "MISSILES HIT", bf)
    elif kind == "riyadh":
        im, d = _layer(w, h, (127, 196, 196))
        d.ellipse([w - 30, 4, w - 8, 26], fill=(255, 230, 120))
        _building(d, 6, h - 24, 36, 19, (220, 200, 160), cols=4, rows=2)
        _building(d, 48, h - 20, 28, 15, (200, 180, 140), cols=3, rows=2)
        d.line([10, 8, 60, 24], fill=(255, 255, 255), width=2)
        d.line([70, 6, 120, 22], fill=(255, 255, 255), width=2)
        d.ellipse([58, 22, 66, 30], fill=(255, 220, 0))
        d.ellipse([118, 20, 126, 28], fill=(255, 220, 0))
        _ground(d, w, h, (140, 110, 70))
        _badge(d, w, "2 DOWN", bf)
    elif kind == "london":
        im, d = _layer(w, h, (201, 207, 214))
        _building(d, 6, h - 28, 30, 23, (110, 115, 125), cols=3, rows=3)
        _building(d, 42, h - 24, 26, 19, (130, 135, 145), cols=3, rows=2)
        d.rectangle([w - 60, h - 34, w - 52, h - 5], fill=(90, 95, 105))
        d.ellipse([w - 58, h - 38, w - 52, h - 32], fill=(255, 220, 0))
        d.rectangle([w - 96, h - 16, w - 66, h - 6], fill=(200, 16, 46))
        d.rectangle([w - 92, h - 14, w - 84, h - 10], fill=(180, 220, 255))
        d.rectangle([w - 80, h - 14, w - 72, h - 10], fill=(180, 220, 255))
        d.ellipse([w - 92, h - 7, w - 88, h - 3], fill=(20, 20, 20))
        d.ellipse([w - 74, h - 7, w - 70, h - 3], fill=(20, 20, 20))
        _tree(d, 12, h - 16, 1.0, (40, 120, 40))
        _ground(d, w, h, (80, 80, 85))
        _badge(d, w, "SINCE 1997", bf)
    elif kind == "pyongyang":
        im, d = _layer(w, h, (31, 42, 92))
        d.ellipse([w - 32, 4, w - 12, 24], fill=(230, 230, 200))
        d.polygon([(w - 78, h - 5), (w - 52, h - 30), (w - 26, h - 5)],
                  fill=(110, 110, 125))
        d.polygon([(w - 66, h - 5), (w - 52, h - 22), (w - 38, h - 5)],
                  fill=(140, 140, 155))
        _building(d, 8, h - 24, 34, 19, (50, 55, 90), cols=4, rows=2)
        _building(d, 48, h - 20, 26, 15, (60, 65, 100), cols=3, rows=2)
        _ground(d, w, h, (25, 25, 35))
        _badge(d, w, "MORE NUKES", bf)
    elif kind == "pretoria":
        im, d = _layer(w, h, (255, 227, 163))
        d.ellipse([w - 34, 4, w - 10, 28], fill=(255, 214, 90))
        d.rectangle([10, h - 26, w - 10, h - 5], fill=(240, 235, 220))
        for cx in range(16, w - 12, 12):
            d.rectangle([cx, h - 24, cx + 4, h - 7], fill=(200, 195, 180))
        d.polygon([(8, h - 26), (w // 2, h - 34), (w - 8, h - 26)],
                  fill=(180, 60, 60))
        _tree(d, 6, h - 14, 0.9, (140, 80, 180))
        _tree(d, w - 20, h - 14, 0.9, (140, 80, 180))
        _ground(d, w, h, (120, 100, 80))
        _badge(d, w, "COURT WIN", bf)
    elif kind == "wellington":
        im, d = _layer(w, h, (191, 227, 192))
        d.polygon([(0, h - 5), (w // 3, h - 26), (2 * w // 3, h - 5)],
                  fill=(60, 160, 80))
        d.polygon([(w // 3, h - 5), (2 * w // 3, h - 30), (w, h - 5)],
                  fill=(40, 140, 60))
        d.rectangle([10, h - 24, 10 + 34, h - 10], fill=(255, 255, 255))
        d.rectangle([12, h - 22, 12 + 22, h - 12], fill=(30, 122, 52))
        d.rectangle([12, h - 22, 12 + 12, h - 12], fill=(120, 120, 120))
        d.text((70, 6), "67-64", font=F(SANS_B, 10), fill=(30, 90, 40))
        _tree(d, w - 26, h - 16, 0.9)
        _ground(d, w, h, (50, 110, 50))
        _badge(d, w, "67 / 131", bf)
    elif kind == "newyork":
        im, d = _layer(w, h, (59, 42, 110))
        _building(d, 6, h - 28, 30, 23, (40, 40, 70), cols=3, rows=3)
        _building(d, 42, h - 24, 28, 19, (55, 55, 85), cols=3, rows=2)
        _building(d, 76, h - 30, 30, 25, (35, 35, 60), cols=3, rows=3)
        d.polygon([(w - 40, 4), (w - 52, 16), (w - 42, 16), (w - 54, 28),
                   (w - 34, 14), (w - 44, 14)],
                  fill=(255, 220, 0))
        d.rectangle([0, h - 12, w, h - 5], fill=(30, 30, 50))
        _ground(d, w, h, (25, 25, 40))
        _badge(d, w, "500,000 DARK", bf)
    elif kind == "newdelhi":
        im, d = _layer(w, h, (242, 193, 78))
        d.rectangle([10, h - 26, w - 10, h - 5], fill=(245, 240, 225))
        for cx in range(16, w - 12, 12):
            d.rectangle([cx, h - 24, cx + 4, h - 7], fill=(210, 205, 190))
        d.pieslice([w // 2 - 16, h - 40, w // 2 + 16, h - 8], 180, 360,
                   fill=(180, 60, 60))
        _tree(d, 6, h - 14, 0.9)
        _tree(d, w - 20, h - 14, 0.9)
        _ground(d, w, h, (120, 95, 60))
        _badge(d, w, "COURT RULES", bf)
    elif kind == "mumbai":
        im, d = _layer(w, h, (168, 208, 240))
        _building(d, 6, h - 26, 36, 21, (90, 110, 150), cols=4, rows=2)
        _building(d, 48, h - 22, 30, 17, (110, 130, 170), cols=3, rows=2)
        d.rectangle([w - 66, h - 22, w - 40, h - 14], fill=(120, 72, 20))
        d.rectangle([w - 56, h - 14, w - 50, h - 6], fill=(120, 72, 20))
        d.rectangle([w - 96, h - 10, w - 70, h - 6], fill=(150, 110, 70))
        _tree(d, 12, h - 16, 0.9)
        _ground(d, w, h, (90, 90, 100))
        _badge(d, w, "COURT FIGHT", bf)
    else:
        raise ValueError("unknown scene %r" % kind)
    return im


def draw_map(w, h):
    """Bright world map with numbered pins, on its own layer."""
    im, d = _layer(w, h, (198, 222, 240))
    for gx in range(0, w, 62):
        d.line([gx, 0, gx, h], fill=(220, 234, 248), width=1)
    for gy in range(0, h, 12):
        d.line([0, gy, w, gy], fill=(220, 234, 248), width=1)
    land = (168, 214, 158)
    d.polygon([(0.06 * w, 0.16 * h), (0.16 * w, 0.10 * h), (0.28 * w, 0.14 * h),
               (0.27 * w, 0.42 * h), (0.20 * w, 0.55 * h), (0.10 * w, 0.45 * h)],
              fill=land)
    d.polygon([(0.22 * w, 0.62 * h), (0.27 * w, 0.58 * h), (0.30 * w, 0.72 * h),
               (0.26 * w, 0.95 * h), (0.22 * w, 0.85 * h)], fill=land)
    d.polygon([(0.45 * w, 0.10 * h), (0.54 * w, 0.08 * h), (0.55 * w, 0.30 * h),
               (0.47 * w, 0.32 * h), (0.44 * w, 0.20 * h)], fill=land)
    d.polygon([(0.56 * w, 0.28 * h), (0.67 * w, 0.28 * h), (0.70 * w, 0.50 * h),
               (0.68 * w, 0.64 * h), (0.62 * w, 0.64 * h), (0.58 * w, 0.55 * h),
               (0.55 * w, 0.40 * h)], fill=land)
    d.polygon([(0.46 * w, 0.36 * h), (0.54 * w, 0.34 * h), (0.55 * w, 0.62 * h),
               (0.51 * w, 0.90 * h), (0.47 * w, 0.70 * h), (0.44 * w, 0.50 * h)],
              fill=land)
    d.polygon([(0.54 * w, 0.08 * h), (0.70 * w, 0.06 * h), (0.88 * w, 0.12 * h),
               (0.90 * w, 0.38 * h), (0.80 * w, 0.55 * h), (0.66 * w, 0.50 * h),
               (0.58 * w, 0.30 * h)], fill=land)
    d.polygon([(0.84 * w, 0.62 * h), (0.92 * w, 0.58 * h), (0.95 * w, 0.75 * h),
               (0.88 * w, 0.85 * h), (0.83 * w, 0.72 * h)], fill=land)
    pin_font = F(SANS_B, 9)
    for num, region, fx, fy in PINS:
        cx, cy = int(fx * w), int(fy * h)
        r = 8
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=REGION[region],
                  outline=WHITE, width=2)
        s = str(num)
        b = pin_font.getbbox(s)
        d.text((cx - (b[2] - b[0]) / 2 - b[0], cy - (b[3] - b[1]) / 2 - b[1]),
               s, font=pin_font, fill=WHITE)
    return im

# ---------------------------------------------------------------- layout
STAT_H = 58
LEAD_HERO_HEAD = 21
LEAD_SMALL_HEAD = 18
LEAD_DECK = 14
LEAD_WHY = 14
LEAD_ALSO = 13
LEAD_DC = 12


def wrap_why(prefix, body, first_w, rest_w):
    """Wrap a WHY line: first line shares width with the bold prefix."""
    words = body.split(" ")
    lines, cur, first = [], "", True
    for wd in words:
        lim = first_w if first else rest_w
        trial = (cur + " " + wd).strip()
        if f_why.getlength(trial) <= lim or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur, first = wd, False
    if cur:
        lines.append(cur)
    if len(lines) > 2:
        raise ValueError("WHY overflow: %r" % body)
    return lines


def build(hero_h, small_h, map_h):
    cv = Canvas()
    y = 0
    cv.rect([0, 0, W, 4], fill=RED)
    # ---- kicker row
    y = 7
    cv.text((ML, y), "THE WORLD IN ONE DAY", f_kicker, INK)
    rk = ("43 STORIES \u00b7 9 REGIONS \u00b7 14 FIELDS \u00b7 EVERY ONE FIRST "
          "REPORTED FRI 27 NOV 2026")
    cv.text((MR - f_kicker_r.getlength(rk), y), rk, f_kicker_r, INK)
    kicker_b = y + ink_h(f_kicker, "THE WORLD IN ONE DAY")
    # ---- masthead
    y = kicker_b + 3
    cv.text((ML, y), "Friday 27 November 2026", f_mast, INK)
    mast_b = y + ink_h(f_mast, "Friday 27 November 2026")
    # ---- red italic kicker
    y = mast_b + 3
    rk2 = ("Bangkok ablaze \u00b7 Drones kill two Italians in Kuwait "
           "\u00b7 EU summit wraps up")
    cv.text((ML, y), rk2, f_redkick, RED)
    rk2_b = y + ink_h(f_redkick, rk2)
    # ---- fields line (own clear band)
    y = rk2_b + 4
    cv.text((ML, y), FIELDS_LINE, f_fields, INK)
    fields_b = y + ink_h(f_fields, FIELDS_LINE)
    # ---- stat strip (DEFECT 1 zone: >=6px below the fields line)
    stat_y = fields_b + 7
    cv.check("fields->stat", fields_b, stat_y)
    n = len(STATS)
    gap = 6
    bw = (CW - gap * (n - 1)) / n
    xs = [ML + i * (bw + gap) for i in range(n)]
    for i, (num, lab) in enumerate(STATS):
        x0 = int(round(xs[i]))
        x1 = int(round(xs[i] + bw)) if i < n - 1 else MR
        cv.rect([x0, stat_y, x1, stat_y + STAT_H], fill=WHITE,
                outline=(180, 180, 180), width=1)
        cv.rect([x0, stat_y, x1, stat_y + 3], fill=RED)
        cv.text_c((x0 + x1) / 2, stat_y + 7, num, f_statnum, INK)
        num_b = stat_y + 7 + ink_h(f_statnum, num)
        lab_lines = wrap(f_statlab, lab, (x1 - x0) - 8, max_lines=2)
        ly = num_b + 3
        for j, ln in enumerate(lab_lines):
            cv.text_c((x0 + x1) / 2, ly + j * 11.5, ln, f_statlab, GREY)
    stat_b = stat_y + STAT_H
    # ---- region strip
    reg_y = stat_b + 5
    items = []
    for name, cnt in REGIONS:
        items.append((REGION[name], "%s %d" % (name, cnt)))
    widths = [10 + 4 + f_region.getlength(t) for _, t in items]
    rgap = (CW - sum(widths)) / (len(items) - 1)
    rx = ML
    for (col, t), wd in zip(items, widths):
        cv.rect([int(rx), int(reg_y + 1), int(rx + 10), int(reg_y + 11)],
                fill=col)
        cv.text((rx + 14, reg_y), t, f_region, INK)
        rx += wd + rgap
    reg_b = reg_y + ink_h(f_region, "EUROPE 8")
    # ---- UTC timeline
    tl_y = reg_b + 5
    slot = CW / 8.0
    line_y = tl_y + 18
    cv.line([ML, line_y, MR, line_y], fill=(120, 120, 120), width=2)
    for i, (tm, lab) in enumerate(TIMELINE):
        cx = ML + (i + 0.5) * slot
        cv.text_c(cx, tl_y, tm, f_time, INK)
        cv.ellipse([cx - 5, line_y - 5, cx + 5, line_y + 5], fill=RED)
        cv.text_c(cx, line_y + 7, lab, f_tlabel, INK)
    tl_b = line_y + 7 + ink_h(f_tlabel, "Bangkok fire")
    # ---- heroes
    hero_xs = [ML, 346, 684]
    hero_ws = [330, 330, 332]
    hs_y = tl_b + 7
    cv.check("timeline->hero-scenes", tl_b, hs_y)
    hero_bottom = 0
    for (city, field, region, kind, sbadge, head, deck, why, src,
         status), x, w in zip(HEROES, hero_xs, hero_ws):
        cv.paste(scene(kind, w, hero_h, hero=True), (x, hs_y))
        bar_y = hs_y + hero_h
        cv.rect([x, bar_y, x + w, bar_y + 17], fill=BLACK)
        cv.text((x + 6, bar_y + 3), city, f_bar_city, WHITE)
        fx = x + 6 + f_bar_city.getlength(city)
        cv.text((fx, bar_y + 4), " \u2014 " + field, f_bar_field, RED_LT)
        hy = bar_y + 17 + 4
        hl = wrap(f_hhero, head, w, max_lines=2)
        head_b = draw_lines(cv, x, hy, f_hhero, hl, LEAD_HERO_HEAD, INK)
        dy = head_b + 3
        dl = wrap(f_deck, deck, w, max_lines=2)
        deck_b = draw_lines(cv, x, dy, f_deck, dl, LEAD_DECK, INK)
        wy = deck_b + 3
        prefix = "WHY IT MATTERS: "
        pw = f_why_b.getlength(prefix)
        wl = wrap_why(prefix, why, w - pw, w)
        cv.text((x, wy), prefix, f_why_b, RED)
        why_b = wy
        for j, ln in enumerate(wl):
            lx = x + (pw if j == 0 else 0)
            cv.text((lx, wy + j * LEAD_WHY), ln, f_why, INK)
            why_b = wy + j * LEAD_WHY + ink_h(f_why, ln)
        sy = why_b + 4
        cv.text((x, sy), "Source: " + src, f_src, INK)
        bw_ = int(f_srcbadge.getlength(status)) + 10
        cv.rect([x + w - bw_, sy, x + w, sy + 13], fill=BADGE_FILL[status])
        b = f_srcbadge.getbbox(status)
        cv.tx.append(lambda d, x=x, w=w, bw_=bw_, sy=sy, b=b,
                       status=status: d.text(
            (x + w - bw_ + 5, sy + (13 - (b[3] - b[1])) / 2 - b[1]),
            status, font=f_srcbadge, fill=WHITE))
        hero_bottom = max(hero_bottom, sy + 13)
    # ---- small scenes, two rows (DEFECT 2/3 zones: >=6px below sources)
    small_xs = [ML, 211, 414, 617, 820]
    small_ws = [195, 195, 195, 195, 196]
    row_bottom = hero_bottom
    for row in range(2):
        sc_y = row_bottom + 7
        cv.check("sources->row%d-scenes" % (row + 1), row_bottom, sc_y)
        row_bottom = 0
        for k in range(5):
            (city, field, region, kind, sbadge, head, deck, src,
             status) = SMALL[row * 5 + k]
            x, w = small_xs[k], small_ws[k]
            cv.paste(scene(kind, w, small_h), (x, sc_y))
            bar_y = sc_y + small_h
            cv.rect([x, bar_y, x + w, bar_y + 16], fill=BLACK)
            cv.text((x + 6, bar_y + 3), city, f_bar_city, WHITE)
            fx = x + 6 + f_bar_city.getlength(city)
            cv.text((fx, bar_y + 4), " \u2014 " + field, f_bar_field, RED_LT)
            hy = bar_y + 16 + 4
            hl = wrap(f_hsmall, head, w, max_lines=2)
            head_b = draw_lines(cv, x, hy, f_hsmall, hl, LEAD_SMALL_HEAD,
                                INK)
            dy = head_b + 3
            dl = wrap(f_deck, deck, w, max_lines=2)
            deck_b = draw_lines(cv, x, dy, f_deck, dl, LEAD_DECK, INK)
            sy = deck_b + 4
            cv.text((x, sy), "Source: " + src, f_src, INK)
            bw_ = int(f_srcbadge.getlength(status)) + 10
            cv.rect([x + w - bw_, sy, x + w, sy + 13],
                    fill=BADGE_FILL[status])
            b = f_srcbadge.getbbox(status)
            cv.tx.append(lambda d, x=x, w=w, bw_=bw_, sy=sy, b=b,
                           status=status: d.text(
                (x + w - bw_ + 5, sy + (13 - (b[3] - b[1])) / 2 - b[1]),
                status, font=f_srcbadge, fill=WHITE))
            row_bottom = max(row_bottom, sy + 13)
    # ---- map band
    mh_y = row_bottom + 6
    cv.check("row2-sources->map-header", row_bottom, mh_y)
    cv.text((ML, mh_y), "WHERE IT HAPPENED \u2014 STORIES 1-13", f_maphead,
            INK)
    mh_b = mh_y + ink_h(f_maphead, "WHERE IT HAPPENED")
    map_y = mh_b + 4
    cv.paste(draw_map(CW, map_h), (ML, map_y))
    map_b = map_y + map_h
    leg_y = map_b + 4
    litems = [(REGION[name], "%s %d" % (name, cnt))
              for name, cnt in REGIONS]
    lwidths = [9 + 3 + f_legend.getlength(t) for _, t in litems]
    lgap = (CW - sum(lwidths)) / (len(litems) - 1)
    lx = ML
    for (col, t), wd in zip(litems, lwidths):
        cv.rect([int(lx), int(leg_y + 1), int(lx + 9), int(leg_y + 10)],
                fill=col)
        cv.text((lx + 12, leg_y), t, f_legend, INK)
        lx += wd + lgap
    leg_b = leg_y + ink_h(f_legend, "EUROPE 8")
    # ---- ALSO band (>=8px clearance at column ends)
    ah_y = leg_b + 6
    cv.text((ML, ah_y),
            "ALSO ON FRIDAY 27 NOVEMBER \u2014 30 MORE STORIES, NUMBERED AND "
            "COLOUR-MATCHED BY REGION", f_alsohead, INK)
    ah_b = ah_y + ink_h(f_alsohead, "ALSO ON FRIDAY 27 NOVEMBER")
    rows_y = ah_b + 3
    also_xs = [ML, 346, 684]
    also_ws = [331, 331, 332]
    min_clear = 999
    for col in range(3):
        x, w = also_xs[col], also_ws[col]
        for i in range(10):
            num, region, head, src = ALSO[col * 10 + i]
            ry = rows_y + i * LEAD_ALSO
            num_s = "%d. " % num
            cv.text((x, ry), num_s, f_also_b, INK)
            tag = REGION_TAG[region]
            tx0 = x + f_also_b.getlength(num_s) + 4
            tw = f_also_b.getlength(tag) + 8
            cv.rect([int(tx0), int(ry + 1), int(tx0 + tw), int(ry + 11)],
                    fill=REGION[region])
            b = f_also_b.getbbox(tag)
            cv.tx.append(lambda d, tx0=tx0, ry=ry, b=b, tag=tag: d.text(
                (tx0 + 4, ry + (10 - (b[3] - b[1])) / 2 - b[1]),
                tag, font=f_also_b, fill=WHITE))
            hx = tx0 + tw + 4
            cv.text((hx, ry), "%s (%s)" % (head, src), f_also, INK)
            line_right = (hx + f_also.getlength("%s (%s)" % (head, src)))
            clear = (x + w) - line_right
            min_clear = min(min_clear, clear)
            if clear < 8:
                raise ValueError("ALSO #%d ends %dpx before next column "
                                 "(need >=8): %r" % (num, clear, head))
    also_b = rows_y + 9 * LEAD_ALSO + ink_h(f_also, "Karachi")
    # ---- DATE CHECK box
    dc_y = also_b + 7
    cv.check("also->datecheck", also_b, dc_y)
    tx0 = ML + 10
    inner_w = MR - 10 - tx0
    dc_lines = []
    dc_lines.append(("title", ["DATE CHECK \u2014 WHAT WE LEFT OUT AND WHY"]))
    dc_lines.append(("items", wrap(f_dc, DC_ITEMS, inner_w)))
    dc_lines.append(("howsure", [DC_HOWSURE]))
    dc_lines.append(("sources", wrap(f_dc, DC_SOURCES, inner_w)))
    box_h = 6
    for kind, lines in dc_lines:
        box_h += (ink_h(f_dctitle if kind == "title" else f_dc_b
                        if kind == "howsure" else f_dc, lines[0])
                  + (len(lines) - 1) * LEAD_DC)
        box_h += 3
    box_h += 3  # bottom pad (6 total incl. the last +3)
    cv.rect([ML, dc_y, MR, dc_y + box_h], fill=WHITE, outline=RED, width=2)
    cy = dc_y + 6
    for kind, lines in dc_lines:
        if kind == "title":
            cv.text((tx0, cy), lines[0], f_dctitle, RED)
            cy += ink_h(f_dctitle, lines[0]) + 3
        elif kind == "howsure":
            cv.text((tx0, cy), lines[0], f_dc_b, INK)
            cy += ink_h(f_dc_b, lines[0]) + 3
        else:
            cy = draw_lines(cv, tx0, cy, f_dc, lines, LEAD_DC, INK) + 3
    dc_b = dc_y + box_h
    # ---- footer
    ft_y = dc_b + 4
    cv.text_c(W / 2, ft_y, FOOTER, f_footer, GREY)
    ft_b = ft_y + ink_h(f_footer, FOOTER)
    return cv, ft_b, min_clear


def render():
    combos = []
    for hh in (50, 48, 46, 44, 42):
        for sh in (38, 36, 34, 32):
            for mh in (50, 48, 46, 44, 42):
                combos.append((hh + sh + mh, hh, sh, mh))
    combos.sort(reverse=True)
    chosen = None
    rejects = []
    for _, hh, sh, mh in combos:
        try:
            cv, bottom, min_clear = build(hh, sh, mh)
        except ValueError as e:
            rejects.append(str(e))
            continue
        bad = [(l, b, t) for (l, b, t) in cv.clearances if t - b < 6]
        if bad:
            rejects.append("clearance %s" % (bad,))
            continue
        if bottom > 1022:
            continue
        chosen = (hh, sh, mh, cv, bottom, min_clear)
        break
    if not chosen:
        print("rejects seen:", sorted(set(rejects))[:5])
        raise SystemExit("no layout fits 1024px height")
    hh, sh, mh, cv, bottom, min_clear = chosen
    print("layout: hero_scene=%d small_scene=%d map=%d bottom=%d "
          "min_also_clear=%dpx" % (hh, sh, mh, bottom, min_clear))
    for label, b, t in cv.clearances:
        print("  clearance %-28s text_bottom=%d next_top=%d gap=%d"
              % (label, b, t, t - b))
    im = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(im)
    for op in cv.bg:
        op(d)
    for op in cv.tx:
        op(d)
    out = os.path.join(HERE, "entry.png")
    im.save(out)
    print("wrote %s (%dx%d)" % (out, W, H))
    return out


if __name__ == "__main__":
    render()
