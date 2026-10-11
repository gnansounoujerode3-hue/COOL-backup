#!/usr/bin/env python3
"""Plan de montage : découpage des sous-titres en séquences + placements d'habillage."""

# Habillage : (asset, début, fin, x_centre, y_centre, animation)
OVERLAYS = [
    ("scrim", 0.00, 29.10, 540, 960, "static"),
    ("potato", 3.10, 4.40, 800, 1160, "rise"),
    ("title", 3.95, 6.35, 540, 352, "rise"),
    ("p1", 7.00, 8.55, 540, 1080, "rise"),
    ("p2", 8.55, 10.10, 540, 1080, "rise"),
    ("p3", 10.10, 11.80, 540, 1080, "rise"),
    ("stamp", 12.55, 13.65, 540, 1055, "pop"),
    ("foundation", 13.80, 16.90, 540, 950, "rise"),
    ("hundred", 17.20, 19.40, 540, 940, "pop"),
    ("split", 19.70, 22.35, 540, 950, "rise"),
    ("cta", 22.70, 25.85, 540, 1080, "pop"),
    ("endcard", 25.85, 29.10, 540, 960, "zoom"),
]

# niveaux sonores
AUDIO = {
    "voice_eq": "highpass=f=85,equalizer=f=250:t=q:w=1.1:g=-2.5,"
                "equalizer=f=3000:t=q:w=1.2:g=2.5,equalizer=f=6500:t=q:w=1.4:g=1.5",
    "music_level": 0.34,      # volume du lit musical (déjà ducké)
    "sfx_level": 0.5,
    "loudnorm": "I=-14:TP=-1.5:LRA=11",
}

FPS = 25
DURATION = 29.1
FADE_START = 28.62
FADE_DUR = 0.48


def split_cues(words, max_words=6, max_chars=40, gap=0.34):
    """Découpe la liste de mots (transcription) en séquences de sous-titres."""
    # 1) regroupement par phrase (silences)
    phrases, cur = [], [words[0]]
    for a, b in zip(words, words[1:]):
        if b["start"] - a["end"] > gap:
            phrases.append(cur)
            cur = [b]
        else:
            cur.append(b)
    phrases.append(cur)

    # 2) découpe de chaque phrase en séquences de <= max_words / max_chars,
    #    en préférant couper après une virgule ou un mot de liaison
    cues = []
    for ph in phrases:
        start_i = 0
        while start_i < len(ph):
            n = 0
            chars = 0
            best = None
            while start_i + n < len(ph):
                w = ph[start_i + n]["text"]
                chars += len(w) + 1
                n += 1
                if chars > max_chars or n > max_words:
                    n = max(1, n - 1)
                    break
                if w.endswith((",", ";", ":")) and n >= 3:
                    best = n
                if start_i + n == len(ph):
                    break
            if start_i + n < len(ph) and best and best >= 3:
                n = best
            chunk = ph[start_i:start_i + n]
            cues.append(chunk)
            start_i += n
    return cues


def tokenize(text):
    """Découpe un mot de transcription en tokens affichables ('-' collé, etc.)."""
    for ch in ("-", "/"):
        text = text.replace(ch, "\u00a0" + ch + "\u00a0")
    return text
