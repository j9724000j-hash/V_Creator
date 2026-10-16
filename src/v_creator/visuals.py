"""Deterministic, original 2D fantasy plates and readable Arabic title typography."""

from __future__ import annotations

from pathlib import Path
import random

import arabic_reshaper
from bidi.algorithm import get_display
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

from .spec import Scene

ROOT = Path(__file__).resolve().parents[2]
FONTS = ROOT / "assets" / "fonts"


def display_text(text: str) -> str:
    """Pillow's packaged FreeType lacks libraqm; shape Arabic before LTR drawing."""
    return get_display(arabic_reshaper.reshape(text)) if any("\u0600" <= c <= "\u06ff" for c in text) else text


def _palette(visual: str) -> tuple[np.ndarray, np.ndarray, tuple[int, int, int]]:
    palettes = {
        "portal": ((5, 12, 31), (37, 51, 79), (72, 220, 222)),
        "ruins": ((10, 15, 30), (54, 37, 57), (228, 169, 102)),
        "forest": ((4, 18, 29), (18, 63, 69), (121, 216, 199)),
        "stars": ((6, 9, 26), (42, 29, 70), (183, 162, 229)),
        "citadel": ((8, 13, 31), (40, 51, 77), (249, 196, 124)),
    }
    dark, light, accent = palettes[visual]
    return np.array(dark, dtype=np.float32), np.array(light, dtype=np.float32), accent


def _make_background(width: int, height: int, scene: Scene, seed: int) -> Image.Image:
    top, lower, accent = _palette(scene.visual)
    x = np.linspace(-1, 1, width, dtype=np.float32)[None, :]
    y = np.linspace(0, 1, height, dtype=np.float32)[:, None]
    horiz = np.exp(-((x * 1.5) ** 2))
    glow = np.exp(-((x * 2.1) ** 2 + ((y - 0.52) * 3.0) ** 2))
    fade = np.clip(y * 0.55 + horiz * 0.19 + glow * 0.24, 0, 1)
    # Using separable float arrays keeps even final-resolution rendering < 4 GB.
    arr = top[None, None, :] * (1 - fade[:, :, None]) + lower[None, None, :] * fade[:, :, None]
    accent_arr = np.array(accent, dtype=np.float32)
    arr += glow[:, :, None] * accent_arr[None, None, :] * 0.12
    arr *= (1 - 0.25 * (x**2) - 0.14 * (2 * y - 1) ** 2)[:, :, None]
    image = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")
    draw = ImageDraw.Draw(image, "RGBA")
    rng = random.Random(seed)
    for _ in range(int(width * height / 3500)):
        px, py = rng.randrange(width), rng.randrange(int(height * 0.73))
        size = rng.choice([1, 1, 1, 2, 3]) * max(1, round(width / 1200))
        alpha = rng.randrange(40, 190)
        draw.ellipse((px, py, px + size, py + size), fill=(216, 234, 255, alpha))
    cx = width // 2
    if scene.visual == "portal":
        rad = int(min(width * 0.17, height * 0.35))
        ring = Image.new("RGBA", image.size)
        ring_draw = ImageDraw.Draw(ring, "RGBA")
        ring_draw.ellipse((cx - rad, height * 0.53 - rad, cx + rad, height * 0.53 + rad),
                          outline=(*accent, 170), width=max(3, round(width * 0.005)))
        halo = ring.filter(ImageFilter.GaussianBlur(max(6, width // 75)))
        image = Image.alpha_composite(image, halo)
        image = Image.alpha_composite(image, ring)
    elif scene.visual in {"forest", "ruins", "citadel"}:
        foreground = ImageDraw.Draw(image, "RGBA")
        for layer in range(3):
            h = int(height * (0.54 + layer * 0.095))
            points = [(0, height)]
            for n in range(13):
                px = n * width // 12
                bump = rng.randint(-height // 9, height // 9)
                points.append((px, h + bump))
            points.append((width, height))
            shade = [12, 11, 9][layer]
            foreground.polygon(points, fill=(shade, shade + 11, shade + 23, 170 + layer * 20))
        if scene.visual in {"ruins", "citadel"}:
            for px in (int(width * 0.19), int(width * 0.77)):
                col_w = int(width * 0.035)
                foreground.rectangle((px, int(height * 0.22), px + col_w, int(height * 0.76)),
                                      fill=(17, 23, 38, 240))
                foreground.rectangle((px - col_w // 3, int(height * 0.20), px + col_w * 4 // 3,
                                      int(height * 0.24)), fill=(41, 49, 67, 235))
    return image


def _wrap(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    lines: list[str] = []
    current = ""
    for word in text.split():
        trial = f"{current} {word}".strip()
        if draw.textlength(display_text(trial), font=font) <= max_width or not current:
            current = trial
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def _text_layer(size: tuple[int, int], xy: tuple[float, float], text: str, font: ImageFont.FreeTypeFont,
                fill: tuple[int, int, int, int], anchor: str, stroke_width: int = 0,
                stroke_fill: tuple[int, int, int, int] | None = None) -> Image.Image:
    """Anti-aliased text as a straight-alpha RGBA layer (correct over transparency)."""
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    passes = []
    if stroke_width and stroke_fill:
        passes.append((stroke_fill, stroke_width))
    passes.append((fill, 0))
    for (r, g, b, a), width in passes:
        mask = Image.new("L", size, 0)
        ImageDraw.Draw(mask).text(xy, text, font=font, fill=255, anchor=anchor,
                                  stroke_width=width, stroke_fill=255)
        colour = Image.new("RGBA", size, (r, g, b, 0))
        colour.putalpha(mask.point(lambda v, a=a: v * a // 255))
        layer = Image.alpha_composite(layer, colour)
    return layer


def make_overlay(scene: Scene, width: int, height: int, ordinal: int, *, darken_image: bool) -> Image.Image:
    """Transparent RGBA layer: optional photo tint, haze, header and Arabic title.

    Kept separate from the background so camera moves (Ken Burns or depth
    parallax) never warp the typography. Every element is alpha-composited so
    the layer looks the same over any background.
    """
    size = (width, height)
    image = Image.new("RGBA", size, (0, 0, 0, 0))
    if darken_image:
        # Separate licensed/user images from generated artwork; always keep provenance in manifest.
        image = Image.alpha_composite(image, Image.new("RGBA", size, (3, 8, 23, 115)))
    top, lower, accent = _palette(scene.visual)
    for shape in ("band", "glow"):
        layer = Image.new("RGBA", size, (0, 0, 0, 0))
        painter = ImageDraw.Draw(layer)
        if shape == "band":
            painter.rectangle((0, height * 0.60, width, height), fill=(2, 6, 19, 130))
        else:
            painter.ellipse((int(width * 0.28), int(height * 0.14), int(width * 0.72), int(height * 0.72)),
                            fill=(*accent, 23))
        image = Image.alpha_composite(image, layer)
    margin = int(width * 0.07)
    font_small = ImageFont.truetype(FONTS / "NotoSansArabic.ttf", max(13, round(height * 0.029)))
    image = Image.alpha_composite(image, _text_layer(size, (margin, int(height * 0.083)), "V  /  C R E A T O R",
                                                     font_small, (220, 205, 178, 180), "lm"))
    image = Image.alpha_composite(image, _text_layer(size, (width - margin, int(height * 0.083)), f"{ordinal:02d}",
                                                     font_small, (*accent, 220), "rm"))
    measure = ImageDraw.Draw(image)
    title_size = max(28, int(height * 0.092))
    for _ in range(28):
        title_font = ImageFont.truetype(FONTS / "NotoKufiArabic.ttf", title_size)
        lines = _wrap(measure, scene.title, title_font, int(width * 0.82))
        if len(lines) <= 2 and all(measure.textlength(display_text(line), font=title_font) < width * 0.87 for line in lines):
            break
        title_size -= 2
    line_height = title_size * 1.45
    base_y = height * 0.77 - (len(lines) - 1) * line_height / 2
    for line_number, line in enumerate(lines):
        image = Image.alpha_composite(image, _text_layer(
            size, (width / 2, base_y + line_number * line_height), display_text(line), title_font,
            (249, 246, 240, 255), "mm", stroke_width=max(1, width // 640), stroke_fill=(9, 11, 27, 210)))
    rule_width = int(width * 0.075)
    y_rule = int(min(height * 0.91, base_y + len(lines) * line_height / 2 + height * 0.045))
    rule = Image.new("RGBA", size, (0, 0, 0, 0))
    ImageDraw.Draw(rule).rounded_rectangle((width // 2 - rule_width // 2, y_rule, width // 2 + rule_width // 2,
                                            y_rule + max(2, round(height * 0.004))), radius=2, fill=(*accent, 240))
    return Image.alpha_composite(image, rule)


def make_plate(scene: Scene, dest: Path, width: int, height: int, seed: int, ordinal: int) -> None:
    if scene.image:
        with Image.open(scene.image) as source:
            image = ImageOps.fit(source.convert("RGB"), (width, height), method=Image.Resampling.LANCZOS).convert("RGBA")
    else:
        image = _make_background(width, height, scene, seed)
    image = Image.alpha_composite(image, make_overlay(scene, width, height, ordinal,
                                                      darken_image=scene.image is not None))
    dest.parent.mkdir(parents=True, exist_ok=True)
    image.convert("RGB").save(dest, optimize=True)
