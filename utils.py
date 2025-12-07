# utils.py
"""
Small helper utilities for Film Mood Atlas.
"""

from typing import Dict
import pandas as pd

from film_color_science import EMOTION_LIST


def emotion_dict_to_df(emotions: Dict[str, float]) -> pd.DataFrame:
    """Convert an emotion dict into a tidy DataFrame."""
    return pd.DataFrame.from_dict(emotions, orient="index", columns=["intensity"])


def normalize_emotion_dict(emotions: Dict[str, float]) -> Dict[str, float]:
    """Ensure the emotion vector sums to 1.0."""
    total = sum(emotions.values())
    if total == 0:
        return {k: 0.0 for k in EMOTION_LIST}
    return {k: v / total for k, v in emotions.items()}
