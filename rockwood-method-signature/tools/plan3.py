#!/usr/bin/env python3
"""Timeline v3 : scènes, coupes, compositions plein cadre et sous-titres cinétiques."""

FPS = 25
DURATION = 29.1
FADE_START = 28.55
FADE_DUR = 0.55

W, H = 1080, 1920
X_L, X_R = 72, 1008
RULE_Y = 168
CAP_Y = 1672          # ligne de base de la dernière ligne de sous-titre

# ------------------------------------------------------------------ palette
CREAM = (253, 247, 236)
GOLD = (233, 189, 124)
GOLD_DEEP = (198, 152, 92)
TERRA = (206, 122, 79)
SLATE = (129, 159, 178)
ESPRESSO = (26, 15, 12)
INK = (20, 11, 9)

# ------------------------------------------------------------------ scènes
SCENES = [
    # (t0, t1, libellé de la running head)
    (0.00, 3.00, "01 · HOOK"),
    (3.00, 6.55, "02 · THE PROMISE"),
    (6.55, 13.45, "03 · THE TOOLKIT"),
    (13.45, 17.05, "04 · THE FOUNDATION"),
    (17.05, 19.55, "05 · THE PROOF"),
    (19.55, 22.55, "06 · THE OUTCOME"),
    (22.55, 25.85, "07 · THE OFFER"),
    (25.85, 29.10, "08 · THE METHOD"),
]

# coupes (déclenchent le flou de fouet + les whooshes)
CUTS = [3.00, 6.55, 8.00, 9.40, 9.70, 10.70, 11.00, 12.00, 13.45, 17.05, 19.55, 22.55, 25.85]

# segments caméra : (t0, t1, zoom, dérive x, dérive y)
CAMERA = [
    (0.00, 3.00, 1.000, 0, 0),
    (3.00, 6.55, 1.045, -10, 6),
    (6.55, 13.45, 1.020, 8, -6),
    (13.45, 17.05, 1.052, -12, 10),
    (17.05, 19.55, 1.028, 6, 4),
    (19.55, 22.55, 1.060, -8, 12),
    (22.55, 25.85, 1.034, 10, 2),
    (25.85, 29.10, 1.014, 0, 0),
]

# ------------------------------------------------------------------ cutaways
# scènes plein cadre avec le sujet en médaillon
CUTAWAYS = [
    # (t0, t1, n°, kicker, titre l1, titre l2, sous-titre, accent, médaillon x, y, r)
    (8.00, 9.40, "01 / 03", "THE PLAYBOOK", "Financial", "Playbook",
     "the complete guide, step by step", GOLD, 250, 1336, 142),
    (9.70, 10.70, "02 / 03", "THE PLANNER", "Printable", "Bundle",
     "budget, debt, goals — print it", TERRA, 830, 1336, 142),
    (11.00, 12.00, "03 / 03", "THE OPTIMIZER", "AI Income", "Optimizer",
     "a plan tuned to your numbers", SLATE, 250, 1336, 142),
]

# ------------------------------------------------------------------ calques
# (nom, t0, t1, ancre, x, y, anim)
OVERLAYS = [
    ("scrim_top", 0.00, 29.10, "lt", 0, 0, "none"),
    ("scrim_bottom", 0.00, 29.10, "lb", 0, 1920, "none"),
    ("sticker", 3.02, 4.45, "c", 892, 452, "slap"),
    ("hl_title", 3.95, 6.40, "rt", X_R, 252, "rise"),
    ("card01", 6.85, 8.10, "lb", X_L, 1470, "rise"),
    ("card02", 9.55, 9.80, "lb", X_L, 1470, "rise"),
    ("card03", 10.80, 11.10, "lb", X_L, 1470, "rise"),
    ("stamp", 12.45, 13.60, "c", 540, 1012, "slap"),
    ("hl_foundation", 13.70, 17.00, "rt", X_R, 258, "rise"),
    ("count_base", 17.10, 19.50, "rt", X_R, 246, "rise"),
    ("split_top", 19.62, 22.45, "lt", X_L, 300, "slide_l"),
    ("split_bot", 19.98, 22.45, "lt", X_L, 412, "slide_r"),
    ("split_rule", 20.30, 22.45, "lt", X_L, 384, "draw"),
    ("pill", 22.60, 25.90, "c", 540, 1344, "rise"),
    ("glow", 25.55, 29.10, "c", 780, 600, "glow"),
    ("endcard", 25.85, 29.10, "lt", 0, 0, "card"),
]

# ------------------------------------------------------------------ mots-clés
KEYWORDS = {
    "finance", "potato", "method", "self-guided", "downloadable", "magic",
    "playbook", "planner", "bundle", "optimizer", "changer", "rock",
    "foundation", "100%", "hassle", "savings", "stress", "rockwoodmethod.com",
    "shop",
}

# ------------------------------------------------------------------ sous-titres
def split_cues(words, max_words=5, max_chars=32, gap=0.34):
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
            n, chars = 0, 0
            while i + n < len(ph):
                w = ph[i + n]["text"]
                nxt = chars + len(w) + (1 if n else 0)
                if n > 0 and (nxt > max_chars or n + 1 > max_words):
                    break
                chars, n = nxt, n + 1
            limit = max(1, n)
            if i + limit >= len(ph):
                cues.append(ph[i:i + limit])
                i += limit
                continue
            # choisir la meilleure coupe <= limit : ponctuation forte > faible > longueur
            best_j, best_score = None, None
            for j in range(1, limit + 1):
                prev = ph[i + j - 1]["text"]
                if j < limit and ph[i + j]["text"][:1] in ("-", "/", ".", "%"):
                    continue
                if prev.endswith((".", "!", "?")):
                    rank = 0
                elif prev.endswith((",", ";", ":", "%")):
                    rank = 1
                else:
                    rank = 2
                score = (rank, -j)
                if best_score is None or score < best_score:
                    best_j, best_score = j, score
            n = best_j or limit
            cues.append(ph[i:i + n])
            i += n

    # fusion des séquences éclair (moins de 0,7 s) pour éviter les flashs
    merged = []
    for c in cues:
        if merged:
            dur = c[-1]["end"] - c[0]["start"]
            prev = merged[-1]
            pdur = prev[-1]["end"] - prev[0]["start"]
            if dur < 0.7 or pdur < 0.7:
                low = min(c[0]["start"], prev[0]["start"])
                high = max(c[-1]["end"], prev[-1]["end"])
                ok_len = len(c) + len(prev) <= 9 and high - low <= 2.6
                if ok_len:
                    merged[-1] = prev + c
                    continue
        merged.append(c)
    return merged


def glue_before(cue, k):
    """Le mot k doit-il être collé au précédent ? ('-', '/', '.', '%', …)"""
    if k == 0:
        return False
    t = cue[k]["text"]
    return t[:1] in ("-", "/", ".", ",", "%", "'") or cue[k - 1]["text"].endswith("/")
