import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from typing import Dict

from film_color_science import EMOTION_COLORS


def generate_mood_poster(
    emotions: Dict[str, float],
    size: int = 720,
    grain_strength: float = 0.3,
    vignette_strength: float = 0.5,
) -> Image.Image:

    # 1. dominant emotion → background tone
    dominant = max(emotions, key=emotions.get)
    base = EMOTION_COLORS.get(dominant, (80, 80, 80))

    img = Image.new("RGB", (size, size), (10, 10, 12))
    draw = ImageDraw.Draw(img)

    # simple gradient
    for y in range(size):
        t = y / size
        r = int(base[0] * t * 0.5)
        g = int(base[1] * t * 0.5)
        b = int(base[2] * t * 0.5)
        draw.line([(0, y), (size, y)], fill=(r, g, b))

    # 2. add 2–4 large geometric shapes (A24 minimalism)
    for emo, v in emotions.items():
        if v < 0.05:
            continue

        color = EMOTION_COLORS.get(emo, (200, 200, 200))
        alpha = int(60 + v * 150)

        cx = np.random.randint(size * 0.2, size * 0.8)
        cy = np.random.randint(size * 0.2, size * 0.8)

        shape_type = ["circle", "bar", "triangle"][np.random.randint(0, 3)]

        if shape_type == "circle":
            r = int(size * (0.08 + v * 0.25))
            draw.ellipse(
                [(cx - r, cy - r), (cx + r, cy + r)],
                fill=(color[0], color[1], color[2], alpha)
            )

        elif shape_type == "bar":
            w = int(size * (0.25 + v * 0.4))
            h = int(size * (0.04 + v * 0.1))
            draw.rectangle(
                [(cx - w, cy - h), (cx + w, cy + h)],
                fill=(color[0], color[1], color[2], alpha)
            )

        else:  # triangle
            t = int(size * (0.15 + v * 0.3))
            pts = [(cx, cy - t), (cx - t, cy + t), (cx + t, cy + t)]
            draw.polygon(pts, fill=(color[0], color[1], color[2], alpha))

    # 3. gaussian blur for cinematic softness
    img = img.filter(ImageFilter.GaussianBlur(3))

    return img
