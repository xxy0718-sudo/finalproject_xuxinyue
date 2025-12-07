# film_color_science.py
"""
Film color psychology and emotion palettes for Film Mood Atlas.
"""

from typing import Dict, Tuple

# Base emotion colors (inspired by film color grading)
EMOTION_COLORS: Dict[str, Tuple[int, int, int]] = {
    "joy":        (248, 198, 110),   # warm golden
    "sadness":    (63,  92,  160),   # deep blue
    "fear":       (75,  165, 180),   # cold teal
    "anger":      (204,  68,  82),   # red
    "calm":       (120, 148, 164),   # grey blue
    "nostalgia":  (190, 140, 102),   # film brown
    "hope":       (166, 214, 150),   # soft green
    "tension":    (138,  96, 190),   # purple
}

EMOTION_DESCRIPTIONS: Dict[str, str] = {
    "joy": "Warm, uplifting tone – moments of happiness and light.",
    "sadness": "Melancholic, reflective atmosphere – loss, regret, longing.",
    "fear": "Unease and anxiety – psychological or physical danger.",
    "anger": "Conflict and confrontation – rage, injustice, explosion.",
    "calm": "Peaceful stillness – quiet, contemplation, balance.",
    "nostalgia": "Memory and longing – looking back at the past with emotion.",
    "hope": "Healing and recovery – new beginnings, reconciliation.",
    "tension": "Suspense and uncertainty – edge-of-seat feeling.",
}

EMOTION_LIST = list(EMOTION_COLORS.keys())
