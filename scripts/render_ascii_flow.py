#!/usr/bin/env python3
"""Render the profile's restrained animated ASCII flow field."""

from __future__ import annotations

import argparse
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


WIDTH = 1200
HEIGHT = 300
FRAME_COUNT = 56
FRAME_DURATION_MS = 90

COLORS = {
    "background": (7, 9, 12),
    "panel": (10, 13, 16),
    "line": (28, 35, 40),
    "faint": (37, 47, 53),
    "mid": (61, 78, 85),
    "cool": (92, 139, 141),
    "warm": (151, 124, 79),
    "muted": (146, 155, 154),
    "text": (231, 229, 221),
}

FONT_PATH = Path("/System/Library/Fonts/Menlo.ttc")
FLOW_CHARS = ("-", "/", "|", "\\", "-", "/", "|", "\\")


def font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_PATH), size=size)


def centered_text(
    draw: ImageDraw.ImageDraw,
    xy: tuple[float, float],
    value: str,
    text_font: ImageFont.FreeTypeFont,
    fill: tuple[int, int, int],
) -> None:
    draw.text(xy, value, font=text_font, fill=fill, anchor="mm")


def field_vector(nx: float, ny: float, phase: float) -> tuple[float, float, float]:
    centers = (
        (
            0.30 + 0.07 * math.cos(phase),
            0.48 + 0.11 * math.sin(phase * 2.0),
            1.0,
        ),
        (
            0.72 + 0.08 * math.cos(phase + math.pi),
            0.52 + 0.10 * math.sin(phase * 1.5 + 0.8),
            -0.86,
        ),
    )

    vx = 0.18 + 0.14 * math.sin(ny * 8.0 + phase)
    vy = 0.08 * math.cos(nx * 10.0 - phase * 1.2)

    for cx, cy, spin in centers:
        dx = nx - cx
        dy = ny - cy
        radius = dx * dx + dy * dy + 0.025
        vx += spin * (-dy) / radius
        vy += spin * dx / radius

    magnitude = math.sqrt(vx * vx + vy * vy)
    return vx, vy, magnitude


def direction_char(vx: float, vy: float) -> str:
    angle = (math.atan2(-vy, vx) + 2.0 * math.pi) % (2.0 * math.pi)
    index = int((angle + math.pi / 8.0) / (math.pi / 4.0)) % 8
    return FLOW_CHARS[index]


def render_frame(index: int) -> Image.Image:
    phase = 2.0 * math.pi * index / FRAME_COUNT
    image = Image.new("RGB", (WIDTH, HEIGHT), COLORS["background"])
    draw = ImageDraw.Draw(image)

    flow_font = font(14)
    columns = 58
    rows = 17
    x_step = WIDTH / (columns + 1)
    y_step = HEIGHT / (rows + 1)

    for row in range(1, rows + 1):
        for column in range(1, columns + 1):
            nx = column / (columns + 1)
            ny = row / (rows + 1)
            vx, vy, magnitude = field_vector(nx, ny, phase)

            drift_x = 4.0 * math.sin(phase + row * 0.35)
            drift_y = 2.0 * math.cos(phase * 1.3 + column * 0.22)
            x = column * x_step + drift_x
            y = row * y_step + drift_y

            pulse = math.sin(phase * 1.4 + column * 0.31 - row * 0.24)
            if magnitude < 0.48:
                glyph = "."
                color = COLORS["faint"]
            else:
                glyph = direction_char(vx, vy)
                if pulse > 0.84:
                    color = COLORS["warm"]
                elif magnitude > 2.5:
                    color = COLORS["cool"]
                elif magnitude > 1.25:
                    color = COLORS["mid"]
                else:
                    color = COLORS["faint"]

            draw.text((x, y), glyph, font=flow_font, fill=color, anchor="mm")

    draw.rounded_rectangle(
        (242, 70, 958, 230),
        radius=8,
        fill=COLORS["panel"],
        outline=COLORS["line"],
        width=1,
    )

    small_font = font(13)
    title_font = font(48)
    subtitle_font = font(16)

    draw.text(
        (265, 92),
        "// SYSTEMS IN MOTION",
        font=small_font,
        fill=COLORS["cool"],
        anchor="lm",
    )
    draw.text(
        (935, 92),
        "FIELD 2026 / LOOP",
        font=small_font,
        fill=COLORS["faint"],
        anchor="rm",
    )
    centered_text(draw, (600, 143), "ISHAAN RANJAN", title_font, COLORS["text"])
    centered_text(
        draw,
        (600, 186),
        "SMALL MODELS  /  AGENT SYSTEMS  /  APPLIED AI",
        subtitle_font,
        COLORS["muted"],
    )
    centered_text(
        draw,
        (600, 211),
        "research -> systems -> useful products",
        small_font,
        COLORS["warm"],
    )

    return image


def build_palette() -> Image.Image:
    palette_image = Image.new("P", (1, 1))
    values: list[int] = []
    for color in COLORS.values():
        values.extend(color)
    values.extend([0] * (768 - len(values)))
    palette_image.putpalette(values)
    return palette_image


def quantize(frame: Image.Image, palette: Image.Image) -> Image.Image:
    return frame.quantize(palette=palette, dither=Image.Dither.NONE)


def write_contact_sheet(frames: list[Image.Image], output: Path) -> None:
    samples = [frames[index] for index in (0, 14, 28, 42)]
    sheet = Image.new("RGB", (WIDTH, HEIGHT), COLORS["background"])
    for index, sample in enumerate(samples):
        thumb = sample.resize((WIDTH // 2, HEIGHT // 2), Image.Resampling.LANCZOS)
        x = (index % 2) * (WIDTH // 2)
        y = (index // 2) * (HEIGHT // 2)
        sheet.paste(thumb, (x, y))
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("assets/ascii-flow.gif"),
        help="GIF output path",
    )
    parser.add_argument(
        "--contact-sheet",
        type=Path,
        help="Optional PNG showing four sampled frames",
    )
    args = parser.parse_args()

    frames = [render_frame(index) for index in range(FRAME_COUNT)]
    palette = build_palette()
    gif_frames = [quantize(frame, palette) for frame in frames]

    args.output.parent.mkdir(parents=True, exist_ok=True)
    gif_frames[0].save(
        args.output,
        save_all=True,
        append_images=gif_frames[1:],
        duration=FRAME_DURATION_MS,
        loop=0,
        optimize=True,
        disposal=2,
    )

    if args.contact_sheet:
        write_contact_sheet(frames, args.contact_sheet)


if __name__ == "__main__":
    main()
