#!/usr/bin/env python3
"""Timeline v2 : placement des calques éditoriaux + découpage des sous-titres."""

FPS = 25
DURATION = 29.1
FADE_START = 28.60
FADE_DUR = 0.50

X_L, X_R = 72, 1008
RULE_Y = 168

# ancrage : (coin, x, y)
#   rt = bord droit du contenu, y = bord haut du contenu
#   lb = bord gauche, y = bord bas du contenu
#   c  = centre
OVERLAYS = [
    # nom,        t0,     t1,    ancre, x,    y,    anim
    ("scrim_top", 0.00, 29.10, "lt",  0,    0,    "none"),
    ("scrim_bottom", 0.00, 29.10, "lb", 0, 1920, "none"),
    ("glow",      3.60, 6.60, "c",  880,  300,  "glow"),
    ("sticker",   3.05, 4.45, "c",  892,  452,  "slap"),
    ("hl_method", 3.95, 6.40, "rt", X_R,  252,  "rise"),
    ("rows01",    6.95, 8.60, "lb", X_L, 1490,  "rise"),
    ("rows02",    8.60, 10.15, "lb", X_L, 1490, "rise"),
    ("rows03",    10.15, 11.90, "lb", X_L, 1490, "rise"),
    ("stamp",     12.50, 13.70, "c", 540, 1152,  "slap"),
    ("hl_foundation", 13.75, 16.95, "rt", X_R, 258, "rise"),
    ("big100",    17.15, 19.45, "rt", X_R,  214,  "rise"),
    ("hl_after",  19.65, 22.40, "rt", X_R,  340,  "rise"),
    ("pill",      22.65, 25.90, "c", 540, 1344,  "rise"),
    ("glow",      25.60, 29.10, "c",  760,  620,  "glow"),
    ("endcard",   25.85, 29.10, "lt",  0,    0,    "card"),
]

# mots mis en valeur (serif italique or) dans les sous-titres
KEYWORDS = {
    "finance", "potato", "method", "self-guided", "downloadable", "magic",
    "playbook", "planner", "bundle", "optimizer", "changer", "rock",
    "foundation", "100%", "hassle", "savings", "stress", "rockwoodmethod.com",
    "shop",
}

ALPHA_DIM = "&H5C&"   # mots non encore prononcés


def split_cues(words, max_words=6, max_chars=40, gap=0.34):
    phrases, cur = [], [words[0]]
    for a, b in zip(words, words[1:]):
        if b["start"] - a["end"] > gap:
            phrases.append(cur)
            cur = [b]
        else:
            cur.append(b)
    phrases.append(cur)

    cues = []
    for ph in phrases:
        i = 0
        while i < len(ph):
            n, chars, best = 0, 0, None
            while i + n < len(ph):
                w = ph[i + n]["text"]
                chars += len(w) + 1
                n += 1
                if chars > max_chars or n > max_words:
                    n = max(1, n - 1)
                    break
                if w.endswith((",", ";", ":")) and n >= 3:
                    best = n
                if i + n == len(ph):
                    break
            if i + n < len(ph) and best and best >= 3:
                n = best
            cues.append(ph[i:i + n])
            i += n
    return cues
