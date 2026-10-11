# Son

- `music.wav` — lit musical original : progression Am–F–C–G à 84 BPM, 4 mesures en boucle,
  nappe + pluck + sub, synthétisé par `build/gen_audio.py` (numpy). Aucune licence.
- `sfx.wav` — 12 effets calés sur les apparitions d'habillage + 2 swooshes (blips, impact
  du tampon, accord du CTA, nappe d'ouverture de la carte finale).
- `words.json` — horodatage mot à mot de la voix off (72 mots, 0,00 → 25,76 s),
  source des sous-titres et du calage des cartes.

Mixage : voix filtrée (passe-haut 85 Hz, −2,5 dB à 250 Hz, +2,5 dB à 3 kHz, +1,5 dB à 6,5 kHz),
compressée (seuil −20 dB, ratio 3:1), musique en sidechain-squeeze sous la voix
(seuil 0,03 / ratio 6 / attaque 25 ms / relâchement 420 ms), limiteur 0,95 puis
normalisation −14 LUFS / −1,5 dBTP.
