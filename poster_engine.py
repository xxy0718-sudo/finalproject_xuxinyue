# poster_engine.py
"""
Cinematic mood poster generator for Film Mood Atlas.
Uses soft light blobs, film grain, glow and vignette
to create atmospheric, movie-style abstract posters.
"""

from typing import Dict

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from film_color_science import EMOTION_COLORS, EMOTION_LIST


def apply_vignette(img: Image.Image, strength: float = 0.7) -> Image.Image:
    """Add a soft vignette around the edges."""
    from math import sqrt

    width, height = img.size
    vignette = Image.new("L", (width, height), 0)
    draw = ImageDraw.Draw(vignette)

    max_radius = sqrt(width**2 + height**2) / 2
    for i in range(int(max_radius)):
        alpha = int(255 * (i / max_radius))
        draw.ellipse(
            [(width / 2 - i, height / 2 - i), (width / 2 + i, height / 2 + i)],
            fill=alpha,
        )

    vignette = vignette.resize((width, height))
    vignette = vignette.point(lambda x: int(x * strength))

    img = img.convert("RGBA")
    black_layer = Image.new("RGBA", (width, height), (0, 0, 0, 255))
    img = Image.composite(black_layer, img, vignette)
    return img.convert("RGB")


def apply_grain(img: Image.Image, intensity: float = 0.25) -> Image.Image:
    """Add film-style grain (noise) to the image."""
    if intensity <= 0:
        return img

    arr = np.array(img).astype(np.float32)
    h, w, _ = arr.shape
    noise = np.random.normal(0, 30 * intensity, (h, w, 1))
    arr[..., :3] += noise
    arr = np.clip(arr, 0, 255).astype(np.uint8)
    return Image.fromarray(arr)


def apply_soft_glow(img: Image.Image, radius: int = 10, alpha: float = 0.35) -> Image.Image:
    """Simple soft-glow effect."""
    if radius <= 0 or alpha <= 0:
        return img

    blur = img.filter(ImageFilter.GaussianBlur(radius=radius))
    return Image.blend(img, blur, alpha=alpha)


def generate_mood_poster(
    emotions: Dict[str, float],
    size: int = 720,
    grain_strength: float = 0.3,
    vignette_strength: float = 0.7,
    glow_radius: int = 12,
    glow_alpha: float = 0.35,
) -> Image.Image:
    """
    Generate an abstract cinematic mood poster based on emotion values.
    Uses layered soft shapes instead of polygons / crystal patterns.
    """
    img = Image.new("RGB", (size, size), (6, 8, 12))
    draw = ImageDraw.Draw(img, "RGBA")

    center = (size // 2, size // 2)
    sorted_emotions = sorted(emotions.items(), key=lambda kv: kv[1], reverse=True)

    for emotion, value in sorted_emotions:
        if value <= 0.01:
            continue

        base_color = EMOTION_COLORS.get(emotion, (200, 200, 200))
        layers = int(8 + value * 40)

        for _ in range(layers):
            # position relative to center
            max_offset = int(size * (0.25 + 0.4 * value))
            offset_x = np.random.randint(-max_offset, max_offset + 1)
            offset_y = np.random.randint(-max_offset, max_offset + 1)

            radius = np.random.randint(int(size * 0.06), int(size * 0.22))
            cx = center[0] + offset_x
            cy = center[1] + offset_y

            alpha = int(40 + value * 120)
            jitter = 20
            r = int(np.clip(base_color[0] + np.random.randint(-jitter, jitter + 1), 0, 255))
            g = int(np.clip(base_color[1] + np.random.randint(-jitter, jitter + 1), 0, 255))
            b = int(np.clip(base_color[2] + np.random.randint(-jitter, jitter + 1), 0, 255))

            bbox = [cx - radius, cy - radius, cx + radius, cy + radius]
            draw.ellipse(bbox, fill=(r, g, b, alpha))

    # soft blending
    img = img.filter(ImageFilter.GaussianBlur(radius=4))
    img = apply_soft_glow(img, radius=glow_radius, alpha=glow_alpha)
    img = apply_grain(img, intensity=grain_strength)
    img = apply_vignette(img, strength=vignette_strength)

    return img
