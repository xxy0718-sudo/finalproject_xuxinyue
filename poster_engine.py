# poster_engine_v2.py
"""
A24-style cinematic mood poster generator.
Highly distinct outputs for different emotion vectors.
Each emotion influences geometry, layout, color and atmosphere.
"""

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from typing import Dict

from film_color_science import EMOTION_COLORS, EMOTION_LIST


def apply_vignette(img: Image.Image, strength: float = 0.6) -> Image.Image:
    """Add a soft cinematic vignette."""
    width, height = img.size
    vignette = Image.new("L", (width, height))
    draw = ImageDraw.Draw(vignette)

    for i in range(max(width, height)):
        alpha = int(255 * (i / max(width, height)))
        draw.ellipse(
            [
                (width/2 - i, height/2 - i),
                (width/2 + i, height/2 + i)
            ],
            fill=alpha
        )

    vignette = vignette.point(lambda x: int(x * strength))
    black = Image.new("RGB", (width, height), (0, 0, 0))
    return Image.composite(img, black, vignette)


def apply_grain(img: Image.Image, intensity: float = 0.3) -> Image.Image:
    """Add subtle film-grain texture."""
    arr = np.array(img).astype(np.float32)
    noise = np.random.normal(0, 25 * intensity, arr.shape)
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
    The dominant emotion defines the background mood,
    while individual emotions create distinct geometric elements.
    """

    # ---------------------------------------------
    # 1. Background based on dominant emotion
    # ---------------------------------------------
    dominant = max(emotions, key=emotions.get)
    base_color = EMOTION_COLORS[dominant]

    # Deep cinematic gradient background
    bg = Image.new("RGB", (size, size), (12, 12, 14))
    bg_draw = ImageDraw.Draw(bg)

    for y in range(size):
        t = y / size
        r = int(base_color[0] * t * 0.4)
        g = int(base_color[1] * t * 0.4)
        b = int(base_color[2] * t * 0.4)
        bg_draw.line([(0, y), (size, y)], fill=(r, g, b))

    img = bg.convert("RGBA")
    draw = ImageDraw.Draw(img, "RGBA")


    # ---------------------------------------------
    # 2. Shape logic: each emotion = distinct form
    # ---------------------------------------------
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

    for emotion, value in emotions.items():
        if value < 0.05:
            continue

        shape = emotion_shapes[emotion]
        color = EMOTION_COLORS[emotion]
        intensity = float(value)

        # Placement with cinematic asymmetry
        cx = np.random.randint(int(size * 0.2), int(size * 0.8))
        cy = np.random.randint(int(size * 0.2), int(size * 0.8))

        # ------------------- SHAPES -------------------

        # Joy → soft glowing circles
        if shape == "circle":
            radius = int(size * (0.08 + intensity * 0.25))
            draw.ellipse(
                [(cx - radius, cy - radius), (cx + radius, cy + radius)],
                fill=(*color, int(90 + intensity * 120))
            )

        # Tension → vertical bar
        elif shape == "v_bar":
            w = int(size * (0.04 + intensity * 0.12))
            h = int(size * (0.30 + intensity * 0.4))
            draw.rectangle(
                [(cx - w, cy - h), (cx + w, cy + h)],
                fill=(*color, int(70 + intensity * 150))
            )

        # Sadness → horizontal bar
        elif shape == "h_bar":
            w = int(size * (0.35 + intensity * 0.8))
            h = int(size * (0.06 + intensity * 0.12))
            draw.rectangle(
                [(cx - w, cy - h), (cx + w, cy + h)],
                fill=(*color, int(60 + intensity * 150))
            )

        # Fear → sharp triangle pointing upward
        elif shape == "triangle":
            t = int(size * (0.12 + intensity * 0.3))
            pts = [
                (cx, cy - t),
                (cx - t, cy + t),
                (cx + t, cy + t),
            ]
            draw.polygon(pts, fill=(*color, int(70 + intensity * 170)))

        # Anger → spiky radiation
        elif shape == "spike":
            spike_len = int(size * (0.12 + intensity * 0.25))
            for _ in range(12):
                angle = np.random.rand() * 2 * np.pi
                px = cx + int(np.cos(angle) * spike_len)
                py = cy + int(np.sin(angle) * spike_len)
                draw.line((cx, cy, px, py), fill=(*color, 130), width=3)

        # Calm → soft blob
        elif shape == "soft_blob":
            r = int(size * (0.12 + intensity * 0.25))
            draw.ellipse(
                [(cx - r, cy - r), (cx + r, cy + r)],
                fill=(*color, int(50 + intensity * 90))
            )

        # Nostalgia → grain patch
        elif shape == "grain_patch":
            patch = Image.new("RGBA", (int(size*0.4), int(size*0.4)), (*color, 60))
            patch = apply_grain(patch, 0.7)
            img.alpha_composite(patch, (cx - patch.width//2, cy - patch.height//2))

        # Hope → soft glowing orb
        elif shape == "glow_orb":
            r = int(size * (0.10 + intensity * 0.30))
            orb = Image.new("RGBA", (r*2, r*2))
            od = ImageDraw.Draw(orb)
            for i in range(r, 0, -1):
                alpha = int(120 * (i / r))
                od.ellipse(
                    [(r - i, r - i), (r + i, r + i)],
                    fill=(*color, alpha)
                )
            img.alpha_composite(orb, (cx - r, cy - r))

    # ---------------------------------------------
    # 3. Cinematic finishing touches
    # ---------------------------------------------
    final = img.convert("RGB")
    final = apply_grain(final, grain_strength)
    final = apply_vignette(final, vignette_strength)

    return final
