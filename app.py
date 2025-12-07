# app.py
"""
Film Mood Atlas – Streamlit main application.

This app:
- Fetches movie data via OMDb
- Analyzes the plot using VADER sentiment
- Expands sentiment into multiple emotions
- Builds a narrative emotion curve
- Generates a cinematic mood poster
"""

import io

from PIL import Image
import pandas as pd
import requests
import streamlit as st

from movie_api import fetch_movie
from emotion_model import (
    load_vader,
    analyze_emotions_global,
    analyze_emotion_curve,
    cosine_similarity,
)
from poster_engine import generate_mood_poster
from film_color_science import EMOTION_DESCRIPTIONS
from utils import emotion_dict_to_df


# -----------------------------
# Streamlit configuration
# -----------------------------
st.set_page_config(
    page_title="Film Mood Atlas",
    page_icon="🎬",
    layout="wide",
)


# -----------------------------
# Load VADER (cached by Streamlit)
# -----------------------------
@st.cache_resource
def get_vader():
    return load_vader()


sia = get_vader()


# -----------------------------
# Sidebar settings
# -----------------------------
st.sidebar.header("Settings")

api_key = st.sidebar.text_input(
    "OMDb API Key",
    type="password",
    help="Get a free key from omdbapi.com and paste it here.",
)

poster_size = st.sidebar.slider("Poster Size (px)", 450, 1000, 720, step=10)
grain_strength = st.sidebar.slider("Film Grain", 0.0, 1.0, 0.35, 0.05)
vignette_strength = st.sidebar.slider("Vignette Strength", 0.0, 1.0, 0.75, 0.05)
glow_radius = st.sidebar.slider("Soft Glow Radius", 0, 30, 12, 1)
glow_alpha = st.sidebar.slider("Soft Glow Intensity", 0.0, 1.0, 0.35, 0.05)

st.sidebar.markdown("---")
st.sidebar.caption("Film Mood Atlas – explore movies through emotional landscapes.")


# -----------------------------
# Main layout
# -----------------------------
st.title("🎬 Film Mood Atlas")
st.write(
    "Analyze a film's plot, extract its emotional climate, "
    "and generate a cinematic mood poster."
)

input_col, hint_col = st.columns([2, 1])

with input_col:
    movie_title = st.text_input(
        "Enter a movie title:",
        placeholder="e.g., Parasite, La La Land, In the Mood for Love",
    )
with hint_col:
    st.markdown("**Tip:** Use the official English title for better API results.")

analyze_button = st.button("Analyze Movie", type="primary")


if analyze_button:
    if not movie_title:
        st.warning("Please enter a movie title first.")
        st.stop()

    # -------------------------------------------------
    # 1. Fetch movie data
    # -------------------------------------------------
    try:
        movie = fetch_movie(movie_title, api_key)
    except Exception as e:
        st.error(str(e))
        st.stop()

    # Top section: basic info + official poster
    info_col, poster_col = st.columns([2, 1])

    with info_col:
        st.subheader(f"{movie['title']} ({movie['year']})")
        if movie["genre"]:
            st.write(f"**Genre:** {movie['genre']}")
        if movie["director"]:
            st.write(f"**Director:** {movie['director']}")
        if movie["writer"]:
            st.write(f"**Writer:** {movie['writer']}")
        if movie["imdb_rating"] and movie["imdb_rating"] != "N/A":
            st.write(f"**IMDb Rating:** {movie['imdb_rating']} ⭐")
        if movie["runtime"]:
            st.write(f"**Runtime:** {movie['runtime']}")

        st.markdown("### Plot Summary")
        st.write(movie["plot"])

    with poster_col:
        if movie["poster"] and movie["poster"] != "N/A":
            try:
                resp = requests.get(movie["poster"], timeout=10)
                poster_img = Image.open(io.BytesIO(resp.content))
                st.image(poster_img, caption="Official Poster", use_column_width=True)
            except Exception:
                st.info("Poster image could not be loaded.")
        else:
            st.info("No poster available from OMDb.")

    if not movie["plot"]:
        st.warning("No plot text available for this movie – cannot analyze emotions.")
        st.stop()

    # -------------------------------------------------
    # 2. Emotion analysis (global + curve)
    # -------------------------------------------------
    global_emotions = analyze_emotions_global(movie["plot"], sia)
    df_global = emotion_dict_to_df(global_emotions)

    df_curve = analyze_emotion_curve(movie["plot"], sia)

    # -------------------------------------------------
    # 3. Tabs: Overview / Emotion Curve / Compare
    # -------------------------------------------------
    tab_overview, tab_curve, tab_compare, tab_data = st.tabs(
        ["Overview", "Emotion Curve", "Compare Movies", "Data & Details"]
    )

    # ----------------- Overview ----------------------
    with tab_overview:
        st.markdown("### Global Emotion Profile")
        st.bar_chart(df_global)

        sorted_emos = sorted(global_emotions.items(), key=lambda kv: kv[1], reverse=True)
        if sorted_emos:
            st.write("**Dominant Emotions:**")
            bullets = []
            for emo, val in sorted_emos[:3]:
                pct = f"{val * 100:.1f}%"
                desc = EMOTION_DESCRIPTIONS.get(emo, "")
                bullets.append(f"- **{emo.capitalize()}** ({pct}) – {desc}")
            st.markdown("\n".join(bullets))

        st.markdown("---")
        st.markdown("### Cinematic Mood Poster")

        mood_poster = generate_mood_poster(
            global_emotions,
            size=poster_size,
            grain_strength=grain_strength,
            vignette_strength=vignette_strength,
    
        )
        st.image(mood_poster, caption="Generated Mood Poster", use_column_width=True)

        buf = io.BytesIO()
        mood_poster.save(buf, format="PNG")
        st.download_button(
            label="Download Mood Poster (PNG)",
            data=buf.getvalue(),
            file_name=f"{movie['title'].replace(' ', '_')}_mood_poster.png",
            mime="image/png",
        )

    # ----------------- Emotion Curve -----------------
    with tab_curve:
        st.markdown("### Plot Emotion Curve")

        if df_curve.empty:
            st.info("Not enough plot data to build a curve.")
        else:
            # basic sentiment curve
            st.write("**Sentiment trajectory (compound / pos / neg / neu):**")
            curve_metrics = df_curve.set_index("segment_index")[
                ["compound", "pos", "neg", "neu"]
            ]
            st.line_chart(curve_metrics)

            # emotion dimensions
            emo_cols = [c for c in df_curve.columns if c.startswith("emo_")]
            df_emos = df_curve.set_index("segment_index")[emo_cols]
            df_emos = df_emos.rename(columns=lambda c: c.replace("emo_", ""))
            st.write("**Emotion dimensions over the plot:**")
            st.line_chart(df_emos)

            st.markdown(
                "Each point represents a segment of the plot. "
                "You can see how the emotional tone rises and falls across the narrative."
            )

            with st.expander("Show segments with text"):
                show_df = df_curve[["segment_index", "segment_text", "compound"]]
                st.dataframe(show_df)

    # ----------------- Compare Movies ----------------
    with tab_compare:
        st.markdown("### Compare Emotion Profiles Between Two Movies")

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown(f"**Movie A:** {movie['title']}")
            st.dataframe(df_global.style.format("{:.3f}"))

        # Second movie input
        with col_b:
            compare_title = st.text_input(
                "Enter a second movie title to compare:",
                key="compare_movie",
                placeholder="e.g., Whiplash",
            )
            compare_button = st.button("Analyze Second Movie")

        if compare_button and compare_title:
            try:
                movie_b = fetch_movie(compare_title, api_key)
                emo_b = analyze_emotions_global(movie_b["plot"], sia)
                df_b = emotion_dict_to_df(emo_b)

                st.markdown(f"#### Movie B: {movie_b['title']} ({movie_b['year']})")
                st.dataframe(df_b.style.format("{:.3f}"))

                # cosine similarity
                sim = cosine_similarity(global_emotions, emo_b)
                st.markdown(
                    f"**Mood Similarity:** {sim:.3f} "
                    "(cosine similarity of emotion vectors – closer to 1.0 means similar mood)"
                )

                # small combined chart
                combo = pd.concat(
                    [df_global.rename(columns={"intensity": movie["title"]}),
                     df_b.rename(columns={"intensity": movie_b["title"]})],
                    axis=1,
                )
                st.bar_chart(combo)

            except Exception as e:
                st.error(f"Could not analyze second movie: {e}")

    # ----------------- Data & Details ----------------
    with tab_data:
        st.markdown("### Global Emotion Data")
        st.dataframe(df_global.style.format("{:.3f}"))

        if not df_curve.empty:
            st.markdown("---")
            st.markdown("### Full Sentiment & Emotion Table")
            st.dataframe(df_curve)

        st.markdown("---")
        st.markdown("### How to Read This Atlas")
        st.write(
            "- **Global Emotion Profile** shows the overall emotional climate of the whole plot.\n"
            "- **Plot Emotion Curve** reveals how emotions evolve from beginning to end.\n"
            "- **Compare Movies** lets you see how similar two films are in terms of mood.\n"
            "- **Mood Poster** turns emotion data into cinematic abstract visuals."
        )
