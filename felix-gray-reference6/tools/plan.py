#!/usr/bin/env python3
"""Master timeline and configuration for Felix Gray (inspired by REFERENCE 6.mp4).

Video specs: 1080x1920 (9:16), 24 fps, 48.80s.
"""
import json
import os

W, H = 1080, 1920
FPS = 24
DURATION = 48.80
FADE_START = 48.30
FADE_DUR = 0.50

# Color Palette (from REFERENCE 6.mp4)
BG_DARK = (3, 7, 22)          # #030716 Deepest midnight navy
BG_CARD = (32, 36, 48)        # Dark glassmorphic UI card
BLUE_ELECTRIC = (41, 92, 255) # #295CFF Primary electric blue accent
BLUE_GLOW = (28, 72, 235)     # Outer glow sapphire
BLUE_ICE = (110, 155, 255)    # Partial word inner glow / highlight
RED_CRIMSON = (255, 40, 75)   # #FF284B Negative hook script accent
RED_GLOW = (220, 20, 55)      # Outer glow crimson
WHITE = (255, 255, 255)
DIM_WORD = (58, 82, 148)      # Unspoken word in ? cutaway

# Original camera cuts in video brut 5 - Copie.mp4
RAW_CUTS = [
    3.46, 6.92, 12.10, 17.52, 21.44, 22.40, 24.36, 28.70,
    32.03, 34.87, 36.75, 37.79, 39.33, 42.67, 46.63,
]

# Full-screen dark UI cutaways (inspired by REFERENCE 6.mp4)
# Cutaway 1: 12.10 - 16.45s (Dark Tablet + Notification Card Push-In)
# Cutaway 2: 25.15 - 30.05s (Central FG Orb + Pulsing Ripples + Dashed Orbit + 3 Nodes)
# Cutaway 3: 42.25 - 46.63s (Giant ? Watermark + Word-by-Word Reveal Question)
CUTAWAY_WINDOWS = [
    (12.10, 16.45, "ui_card"),
    (25.15, 30.05, "orbital"),
    (42.25, 46.63, "question"),
]

# Transitions (whip/zoom blur + blue flash)
TRANSITION_TIMES = sorted(set(RAW_CUTS + [12.10, 16.45, 25.15, 30.05, 42.25, 46.63]))

# Camera punch-in segments on live footage: (t0, t1, z0, z1, dx, dy)
CAMERA_SEGMENTS = [
    (0.00, 3.46, 1.00, 1.07, 0, -10),
    (3.46, 6.92, 1.02, 1.08, -8, 0),
    (6.92, 12.10, 1.00, 1.09, 0, -14),
    (16.45, 17.52, 1.04, 1.08, 6, 0),
    (17.52, 21.44, 1.00, 1.08, 0, 8),
    (21.44, 22.40, 1.06, 1.12, 0, -12),
    (22.40, 24.36, 1.00, 1.06, 0, 0),
    (24.36, 25.15, 1.03, 1.07, -6, 0),
    (30.05, 32.03, 1.02, 1.09, 0, -10),
    (32.03, 34.87, 1.00, 1.07, 0, 0),
    (34.87, 36.75, 1.02, 1.08, -8, 0),
    (36.75, 37.79, 1.00, 1.06, 0, 0),
    (37.79, 39.33, 1.02, 1.08, 0, -10),
    (39.33, 42.25, 1.00, 1.06, 6, 0),
    (46.63, 48.80, 1.02, 1.09, 0, -8),
]


def load_words():
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(os.path.dirname(here), "audio", "words.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
