# app.py
import io
import random
from typing import Dict, Tuple

import requests
import streamlit as st
from PIL import Image, ImageDraw, ImageFilter
import pandas as pd

import nltk
from nltk.sentiment import SentimentIntensityAnalyzer


# -------------------------------------------------
# Streamlit Page Config & Initialize VADER
# -------------------------------------------------
st.set_page_config(
    page_title="Film Mood Atlas",
    page_icon="🎬",
    layout="wide",
)

@st.cache_resource
def load_vader():
    nltk.download("vader_lexicon")
    return SentimentIntensityAnalyzer()

sia = load_vader()


# -------------------------------------------------
# Emotion Colors & Categories
# -------------------------------------------------
EMOTION_COLORS: Dict[str, Tuple[int, int, int]] = {
    "joy":        (250, 186, 90),
    "sadness":    (75, 102, 168),
    "fear":       (72, 180, 197),
    "anger":      (211, 71, 77),
    "calm":       (120, 148, 164),
    "nostalgia":  (196, 146, 104),
    "hope":       (160, 214, 140),
    "tension":    (143, 99, 189),
}

EMOTION_LIST = list(EMOTION_COLORS.keys())


# -------------------------------------------------
# Movie API (OMDb)
# -------------------------------------------------
def fetch_movie(title: str, api_key: str):
    """Fetch movie details from OMDb API"""
    if not api_key:
        raise ValueError("OMDb API key is required.")

    url = "http://www.omdbapi.com/"
    params = {
        "t": title,
        "apikey": api_key,
        "plot": "full",
    }
    resp = requests.get(url, params=params, timeout=10)
    data = resp.json()

    if data.get("Response") != "True":
        raise ValueError(data.get("Error", "Movie not found."))

    return {
        "title": data.get("Title", ""),
        "year": data.get("Year", ""),
        "genre": data.get("Genre", ""),
        "plot": data.get("Plot", ""),
        "poster": data.get("Poster", ""),
        "imdb_rating": data.get("imdbRating", ""),
        "runtime": data.get("Runtime", ""),
    }


# -------------------------------------------------
# Emotion Analysis
# -------------------------------------------------
def analyze_emotions(text: str) -> Dict[str, float]:
    """Map text into multi-emotion values."""
    vader_scores = sia.polarity_scores(text)

    # Base sentiment weights
    pos = vader_scores["pos"]
    neg = vader_scores["neg"]
    neu = vader_scores["neu"]

    # Expand into multiple emotions
    raw = {
        "joy": pos * 0.9,
        "hope": pos * 0.6,
        "calm": neu * 0.7,
        "nostalgia": neu * 0.3 + pos * 0.2,
        "sadness": neg * 0.7,
        "fear": neg * 0.5,
        "anger": neg * 0.6,
        "tension": neu * 0.2 + neg * 0.5,
    }

    # Normalize
    total = sum(raw.values())
    if total == 0:
        return {k: 0 for k in raw}
    return {k: v / total for k, v in raw.items()}


# -------------------------------------------------
# Poster Generator
# -------------------------------------------------
def generate_poster(emotions: Dict[str, float], size=600):
    """Generate an abstract mood poster based on emotion values."""
    img = Image.new("RGB", (size, size), (10, 10, 10))
    draw = ImageDraw.Draw(img)

    for emotion, value in emotions.items():
        if value <= 0:
            continue

        r, g, b = EMOTION_COLORS[emotion]

        # number of shapes
        n = int(value * 40) + 5

        for _ in range(n):
            x1 = random.randint(0, size)
            y1 = random.randint(0, size)
            x2 = x1 + random.randint(20, 200)
            y2 = y1 + random.randint(20, 200)

            shape_color = (
                int(r + random.randint(-20, 20)),
                int(g + random.randint(-20, 20)),
                int(b + random.randint(-20, 20)),
            )
            draw.ellipse([x1, y1, x2, y2], fill=shape_color, outline=None)

    # cinematic blur
    img = img.filter(ImageFilter.GaussianBlur(radius=6))
    return img


# -------------------------------------------------
# Sidebar
# -------------------------------------------------
st.sidebar.header("Settings")
api_key = st.sidebar.text_input("OMDb API Key", type="password")
size = st.sidebar.slider("Poster Size", 400, 1000, 650)


# -------------------------------------------------
# Main UI
# -------------------------------------------------
st.title("🎬 Film Mood Atlas")
st.write("Explore the emotional landscape of movies through generative mood posters.")

movie_title = st.text_input("Enter a movie title:", placeholder="e.g., Parasite, La La Land")

if st.button("Analyze Movie"):
    if not movie_title:
        st.warning("Please enter a movie title.")
        st.stop()

    try:
        movie = fetch_movie(movie_title, api_key)
    except Exception as e:
        st.error(str(e))
        st.stop()

    st.subheader(f"{movie['title']} ({movie['year']})")
    st.write(f"**Genre:** {movie['genre']}")
    st.write(f"**IMDB Rating:** {movie['imdb_rating']} ⭐")
    st.write("### Plot Summary")
    st.write(movie["plot"])

    # Emotion Analysis
    emotions = analyze_emotions(movie["plot"])
    df = pd.DataFrame.from_dict(emotions, orient="index", columns=["intensity"])

    st.write("### Emotion Distribution")
    st.bar_chart(df)

    # Generate Poster
    st.write("### Generative Mood Poster")
    poster = generate_poster(emotions, size=size)
    st.image(poster, caption="Mood Poster", use_column_width=True)

    # Download button
    buf = io.BytesIO()
    poster.save(buf, format="PNG")
    st.download_button(
        label="Download Poster as PNG",
        data=buf.getvalue(),
        file_name=f"{movie['title']}_mood_poster.png",
        mime="image/png"
    )

    st.write("### Emotion Data Table")
    st.dataframe(df.style.format("{:.3f}"))
