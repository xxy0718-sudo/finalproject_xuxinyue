# emotion_model.py
"""
Sentiment analysis and multi-emotion modeling for Film Mood Atlas.
"""

from typing import Dict, List

import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
import pandas as pd

from film_color_science import EMOTION_LIST


# -------------------------------
# VADER loader (cached by caller)
# -------------------------------
def load_vader() -> SentimentIntensityAnalyzer:
    nltk.download("vader_lexicon")
    return SentimentIntensityAnalyzer()


# -------------------------------
# Text segmentation
# -------------------------------
def split_plot_into_segments(text: str, max_chars: int = 280) -> List[str]:
    """
    Roughly split plot text into segments for building an emotion curve.
    Not perfect sentence splitting, but good enough for visual analysis.
    """
    if not text:
        return []

    raw_parts: List[str] = []
    for part in text.replace("?", ".").replace("!", ".").split("."):
        p = part.strip()
        if p:
            raw_parts.append(p)

    segments: List[str] = []
    current = ""
    for part in raw_parts:
        if len(current) + len(part) + 2 <= max_chars:
            if current:
                current += ". " + part
            else:
                current = part
        else:
            segments.append(current)
            current = part

    if current:
        segments.append(current)

    return segments


# -------------------------------
# Sentiment → Emotion Mapping
# -------------------------------
def map_sentiment_to_emotions(pos: float, neg: float, neu: float) -> Dict[str, float]:
    """
    Expand basic VADER positive / negative / neutral scores
    into a richer set of emotions used in our atlas.
    """
    raw = {
        "joy":      pos * 0.9,
        "hope":     pos * 0.6 + neu * 0.1,
        "calm":     neu * 0.7,
        "nostalgia": neu * 0.3 + pos * 0.15,
        "sadness":  neg * 0.7,
        "fear":     neg * 0.5 + neu * 0.1,
        "anger":    neg * 0.6,
        "tension":  neg * 0.4 + neu * 0.2,
    }

    total = sum(raw.values())
    if total == 0:
        return {k: 0.0 for k in raw}

    return {k: v / total for k, v in raw.items()}


def analyze_emotions_global(text: str, sia: SentimentIntensityAnalyzer) -> Dict[str, float]:
    """Compute a single global emotion vector for the whole plot."""
    scores = sia.polarity_scores(text)
    return map_sentiment_to_emotions(scores["pos"], scores["neg"], scores["neu"])


def analyze_emotion_curve(text: str, sia: SentimentIntensityAnalyzer) -> pd.DataFrame:
    """
    Create an emotion curve by splitting the plot into segments
    and analyzing each segment separately.

    Returns:
        DataFrame with:
        - segment_index
        - segment_text
        - compound, pos, neg, neu
        - emo_xxx for each emotion in EMOTION_LIST
    """
    segments = split_plot_into_segments(text)
    rows = []

    for idx, seg in enumerate(segments):
        vs = sia.polarity_scores(seg)
        emo = map_sentiment_to_emotions(vs["pos"], vs["neg"], vs["neu"])
        row = {
            "segment_index": idx,
            "segment_text": seg,
            "compound": vs["compound"],
            "pos": vs["pos"],
            "neg": vs["neg"],
            "neu": vs["neu"],
        }
        for e in EMOTION_LIST:
            row[f"emo_{e}"] = emo.get(e, 0.0)
        rows.append(row)

    if not rows:
        return pd.DataFrame()

    return pd.DataFrame(rows)


# -------------------------------
# Emotion Similarity
# -------------------------------
def cosine_similarity(vec1: Dict[str, float], vec2: Dict[str, float]) -> float:
    """
    Simple cosine similarity between two emotion vectors.
    Both vectors are dicts keyed by emotion name.
    """
    import math

    dot = 0.0
    norm1 = 0.0
    norm2 = 0.0

    for emo in EMOTION_LIST:
        v1 = vec1.get(emo, 0.0)
        v2 = vec2.get(emo, 0.0)
        dot += v1 * v2
        norm1 += v1 * v1
        norm2 += v2 * v2

    if norm1 == 0 or norm2 == 0:
        return 0.0

    return dot / math.sqrt(norm1 * norm2)
