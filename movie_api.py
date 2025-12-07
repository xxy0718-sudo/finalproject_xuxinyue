# movie_api.py
"""
OMDb API wrapper for Film Mood Atlas.
"""

from typing import Dict
import requests


def fetch_movie(title: str, api_key: str) -> Dict[str, str]:
    """
    Fetch detailed movie information from OMDb.

    Raises:
        ValueError: if api_key is missing or movie not found.
    """
    if not api_key:
        raise ValueError("OMDb API key is required in the sidebar.")

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
        "director": data.get("Director", ""),
        "writer": data.get("Writer", ""),
    }
