# poster_engine.py
"""
A24-style cinematic mood poster generator.
Highly distinct outputs for different emotion vectors.
Each emotion influences geometry, layout, color, and atmosphere.
"""

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from typing import Dict

from film_color_science import EMOTION_COLORS


def apply_vignette(img: Image.Image, strength: float = 0.5) -> Image.Image:
    """Add a subtle cinematic vignette."""
    width, height = img.size
    vignette = Image.new("L", (width, height))
    draw = ImageDraw.Draw(vignette)

    for i in range(max(width, height)):
        alpha = int(255 * (i / max(width, height)))
        draw.ellipse(
            [(width/2 - i, height/2 - i),
             (width/2 + i, height/2 + i)],
            fill=alpha,
        )

    vignette = vignette.point(lambda x: int(x * strength))

    black = Image.new("RGB", (width, height), (0, 0, 0))
    return Image.composite(img, black, vignette)


def apply_grain(img: Image.Image, intensity: float = 0.3) -> Image.Image:
    """Add subtle film-grain noise."""
    arr = np.array(img).astype(np.float32)
    noise = np.random.normal(0, 28 * intensity, arr.shape)
    arr = np.clip(arr + noise, 0, 255).astype(np.uint8)
    return Image.fromarray(arr)


def generate_mood_poster(
    emotions: Dict[str, float],
    size: int = 720,
    grain_strength: float = 0.35,
    vignette_strength: float = 0.55,
) -> Image.Image:
    """
    Generate an A24-style cinematic poster.
    The dominant emotion defines the background tone,
    while other emotions generate abstract geometric elements.
    """

    # -----------------------------
    # 1. Background: dominant emotion → gradient tone
    # -----------------------------
    dominant = max(emotions, key=emotions.get)
    base_color = EMOTION_COLORS.get(dominant, (80, 80, 80))

    bg = Image.new("RGB", (size, size), (10, 10, 12))
    draw_bg = ImageDraw.Draw(bg)

    for y in range(size):
        t = y / size
        r = int(base_color[0] * t * 0.4)
        g = int(base_color[1] * t * 0.4)
        b = int(base_color[2] * t * 0.4)
        draw_bg.line([(0, y), (size, y)], fill=(r, g, b))

    img = bg.convert("RGBA")
    draw = ImageDraw.Draw(img, "RGBA")

    # -----------------------------
    # 2. Emotion → geometric shape mapping
    # -----------------------------
    emotion_shapes = {
        "joy": "circle",
        "sadness": "h_bar",
        "fear": "triangle",
        "anger": "spike",
        "calm": "soft_blob",
        "nostalgia": "grain_patch",
        "hope": "glow_orb",
        "tension": "v_bar",
    }

    for emo, val in emotions.items():
        if val < 0.05:
            continue

        intensity = float(val)
        color = EMOTION_COLORS.get(emo, (200, 200, 200))
        shape = emotion_shapes[emo]

        cx = np.random.randint(int(size * 0.2), int(size * 0.8))
        cy = np.random.randint(int(size * 0.2), int(size * 0.8))

        # ---- Shapes ----

        # Joy → glowing circle
        if shape == "circle":
            r = int(size * (0.1 + intensity * 0.3))
            draw.ellipse(
                [(cx - r, cy - r), (cx + r, cy + r)],
                fill=(*color, int(90 + intensity * 120)),
            )

        # Tension → vertical bar
        elif shape == "v_bar":
            w = int(size * (0.05 + intensity * 0.12))
            h = int(size * (0.25 + intensity * 0.4))
            draw.rectangle(
                [(cx - w, cy - h), (cx + w, cy + h)],
                fill=(*color, int(70 + intensity * 150)),
            )

        # Sadness → horizontal bar
        elif shape == "h_bar":
            w = int(size * (0.35 + intensity * 0.8))
            h = int(size * (0.05 + intensity * 0.12))
            draw.rectangle(
                [(cx - w, cy - h), (cx + w, cy + h)],
                fill=(*color, int(60 + intensity * 150)),
            )

        # Fear → triangle
        elif shape == "triangle":
            t = int(size * (0.15 + intensity * 0.3))
            pts = [(cx, cy - t), (cx - t, cy + t), (cx + t, cy + t)]
            draw.polygon(pts, fill=(*color, int(70 + intensity * 170)))

        # Anger → spiky direction lines
        elif shape == "spike":
            L = int(size * (0.15 + intensity * 0.3))
            for _ in range(14):
                angle = np.random.rand() * 2 * np.pi
                px = cx + int(np.cos(angle) * L)
                py = cy + int(np.sin(angle) * L)
                draw.line((cx, cy, px, py), fill=(*color, 130), width=3)

        # Calm → soft simple blob
        elif shape == "soft_blob":
            r = int(size * (0.18 + intensity * 0.3))
            draw.ellipse(
                [(cx - r, cy - r), (cx + r, cy + r)],
                fill=(*color, int(50 + intensity * 90)),
            )

        # Nostalgia → film-grain patch
        elif shape == "grain_patch":
            patch_size = int(size * 0.45)
            patch = Image.new("RGBA", (patch_size, patch_size), (*color, 60))
            patch = apply_grain(patch, 0.7)
            img.alpha_composite(patch, (cx - patch_size//2, cy - patch_size//2))

        # Hope → glowing orb
        elif shape == "glow_orb":
            r = int(size * (0.12 + intensity * 0.35))
            orb = Image.new("RGBA", (r * 2, r * 2))
            d = ImageDraw.Draw(orb)
            for i in range(r, 0, -1):
                alpha = int(120 * (i / r))
                d.ellipse([(r - i, r - i), (r + i, r + i)], fill=(*color, alpha))
            img.alpha_composite(orb, (cx - r, cy - r))

    # -----------------------------
    # 3. Finishing (grain + vignette)
    # -----------------------------
    final = img.convert("RGB")
    final = apply_grain(final, grain_strength)
    final = apply_vignette(final, vignette_strength)

    return final
