"""Build local procedural filmstrips for additional terrain image sequences.

This is an offline fallback for the no-API-key workflow. It renders the same
terrain generator payloads used by the 3D Lab into 5x6 filmstrips so the normal
filmstrip import and GIF gallery pipeline can be exercised immediately.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = PROJECT_ROOT / "docs" / "TERRAIN_ADDITIONAL_IMAGE_SEQUENCE_SPECS.json"
OUTPUT_ROOT = PROJECT_ROOT / "assets" / "cinematic" / "image_sequence"
DEFAULT_FRAME_COUNT = 30
DEFAULT_COLS = 5
DEFAULT_ROWS = 6
DEFAULT_CELL_SIZE = 384
DEFAULT_GUTTER = 4

sys.path.insert(0, str(PROJECT_ROOT))

from app.services.animation_assets import sample_landform_surface_sequence  # noqa: E402


WATER_LANDFORMS = {
    "barrier_island",
    "floodplain_natural_levee",
    "kettle_lake",
    "maar",
    "oxbow_lake",
    "polje",
    "sea_cave_stack",
    "thermokarst",
    "tidal_flat",
    "wave_cut_platform",
}

COASTAL_LANDFORMS = {"barrier_island", "marine_terrace", "sea_cave_stack", "tidal_flat", "wave_cut_platform"}
GLACIAL_LANDFORMS = {"drumlin", "esker", "kettle_lake", "moraine", "outwash_plain", "thermokarst"}
VOLCANIC_LANDFORMS = {"cinder_cone", "lava_dome", "maar"}
KARST_LANDFORMS = {"polje"}


def load_specs() -> list[dict[str, object]]:
    return json.loads(SPEC_PATH.read_text(encoding="utf-8"))["landforms"]


def normalize_stack(surfaces: list[np.ndarray]) -> np.ndarray:
    stack = np.stack([np.asarray(surface, dtype=float) for surface in surfaces])
    z_min = float(np.nanmin(stack))
    z_max = float(np.nanmax(stack))
    span = max(z_max - z_min, 1e-6)
    return np.clip((stack - z_min) / span, 0.0, 1.0)


def terrain_palette(landform_id: str, height: np.ndarray) -> np.ndarray:
    if landform_id in GLACIAL_LANDFORMS:
        low = np.array([112, 128, 118], dtype=float)
        mid = np.array([164, 160, 136], dtype=float)
        high = np.array([236, 242, 240], dtype=float)
    elif landform_id in VOLCANIC_LANDFORMS:
        low = np.array([66, 60, 54], dtype=float)
        mid = np.array([130, 96, 67], dtype=float)
        high = np.array([211, 188, 150], dtype=float)
    elif landform_id in KARST_LANDFORMS:
        low = np.array([80, 117, 88], dtype=float)
        mid = np.array([151, 158, 124], dtype=float)
        high = np.array([205, 198, 164], dtype=float)
    elif landform_id in COASTAL_LANDFORMS:
        low = np.array([147, 130, 91], dtype=float)
        mid = np.array([181, 164, 118], dtype=float)
        high = np.array([116, 122, 111], dtype=float)
    else:
        low = np.array([86, 123, 82], dtype=float)
        mid = np.array([160, 150, 98], dtype=float)
        high = np.array([128, 119, 102], dtype=float)

    h = height[..., None]
    lower_mix = np.clip(h / 0.55, 0.0, 1.0)
    upper_mix = np.clip((h - 0.55) / 0.45, 0.0, 1.0)
    base = low * (1.0 - lower_mix) + mid * lower_mix
    return base * (1.0 - upper_mix) + high * upper_mix


def water_mask(landform_id: str, height: np.ndarray, progress: float) -> np.ndarray:
    if landform_id not in WATER_LANDFORMS:
        return np.zeros_like(height, dtype=bool)

    y = np.linspace(0.0, 1.0, height.shape[0])[:, None]
    x = np.linspace(0.0, 1.0, height.shape[1])[None, :]
    lowland = height < np.quantile(height, 0.25)

    if landform_id in COASTAL_LANDFORMS:
        sea = np.repeat(y > (0.52 - 0.05 * progress), height.shape[1], axis=1)
        return sea | (lowland & (y > 0.38))
    if landform_id in {"kettle_lake", "thermokarst"}:
        return lowland & (progress > 0.35)
    if landform_id == "oxbow_lake":
        loop = ((x - 0.5) ** 2 / 0.16**2) + ((y - 0.5) ** 2 / 0.23**2)
        inner = ((x - 0.5) ** 2 / 0.095**2) + ((y - 0.5) ** 2 / 0.14**2)
        return ((loop < 1.0) & (inner > 0.55) & (progress > 0.62)) | lowland
    if landform_id == "maar":
        crater = ((x - 0.5) ** 2 + (y - 0.5) ** 2) < (0.18 + 0.03 * progress) ** 2
        return crater & (progress > 0.55)
    if landform_id == "polje":
        basin = ((x - 0.5) ** 2 / 0.30**2) + ((y - 0.56) ** 2 / 0.20**2) < 1.0
        return basin & (progress > 0.72)
    return lowland


def hillshade(height: np.ndarray) -> np.ndarray:
    dy, dx = np.gradient(height)
    slope = np.sqrt(dx * dx + dy * dy)
    aspect_light = (-0.65 * dx) + (-0.35 * dy)
    shade = 0.82 + 0.25 * aspect_light - 0.12 * slope
    return np.clip(shade, 0.58, 1.18)


def render_frame(landform_id: str, height: np.ndarray, *, progress: float, size: int) -> Image.Image:
    if landform_id == "lava_dome":
        return render_lava_dome_oblique(progress=progress, size=size)
    if landform_id == "tidal_flat":
        return render_tidal_flat_oblique(progress=progress, size=size)
    if landform_id == "marine_terrace":
        return render_marine_terrace_oblique(progress=progress, size=size)
    if landform_id == "kettle_lake":
        return render_kettle_lake_oblique(progress=progress, size=size)
    if landform_id == "outwash_plain":
        return render_outwash_plain_oblique(progress=progress, size=size)
    if landform_id == "thermokarst":
        return render_thermokarst_oblique(progress=progress, size=size)
    if landform_id == "cinder_cone":
        return render_cinder_cone_oblique(progress=progress, size=size)

    terrain = terrain_palette(landform_id, height)
    shaded = np.clip(terrain * hillshade(height)[..., None], 0, 255)

    mask = water_mask(landform_id, height, progress)
    if np.any(mask):
        water = np.array([68, 126, 154], dtype=float)
        shaded[mask] = shaded[mask] * 0.28 + water * 0.72

    image = Image.fromarray(np.uint8(shaded), mode="RGB").resize((size, size), Image.Resampling.BICUBIC)
    image = image.filter(ImageFilter.UnsharpMask(radius=1.1, percent=70, threshold=2))

    draw = ImageDraw.Draw(image, "RGBA")
    draw.rectangle((0, 0, size - 1, size - 1), outline=(0, 0, 0, 36), width=1)
    return image


def _vertical_gradient(size: int, top: tuple[int, int, int], bottom: tuple[int, int, int]) -> Image.Image:
    image = Image.new("RGB", (size, size), top)
    draw = ImageDraw.Draw(image)
    for y in range(size):
        t = y / max(size - 1, 1)
        color = tuple(round(top[i] * (1.0 - t) + bottom[i] * t) for i in range(3))
        draw.line((0, y, size, y), fill=color)
    return image


def _finish_scene(image: Image.Image) -> Image.Image:
    image = image.filter(ImageFilter.UnsharpMask(radius=1.1, percent=80, threshold=2))
    draw = ImageDraw.Draw(image, "RGBA")
    draw.rectangle((0, 0, image.width - 1, image.height - 1), outline=(0, 0, 0, 36), width=1)
    return image


def render_tidal_flat_oblique(*, progress: float, size: int) -> Image.Image:
    p = float(np.clip(progress, 0.0, 1.0))
    image = _vertical_gradient(size, (158, 178, 183), (111, 93, 71))
    draw = ImageDraw.Draw(image, "RGBA")
    horizon = size * 0.33
    waterline = size * (0.38 + 0.22 * p)

    draw.rectangle((0, 0, size, horizon), fill=(128, 162, 174, 180))
    draw.polygon([(0, horizon), (size, horizon), (size, waterline), (0, waterline + size * 0.05)], fill=(74, 132, 154, 205))
    draw.polygon([(0, waterline - size * 0.02), (size, waterline + size * 0.02), (size, size), (0, size)], fill=(132, 113, 81, 238))

    for band in range(8):
        y = waterline + size * (0.06 + band * 0.075)
        color = (164, 145, 104, 70) if band % 2 == 0 else (89, 74, 58, 55)
        draw.arc((-size * 0.12, y - size * 0.22, size * 1.12, y + size * 0.20), 4, 176, fill=color, width=max(1, size // 180))

    for idx, offset in enumerate([0.18, 0.35, 0.52, 0.68, 0.82]):
        points = []
        for step in range(18):
            t = step / 17
            y = waterline + t * (size - waterline)
            x = size * (offset + 0.08 * np.sin(t * np.pi * (1.2 + idx * 0.25) + idx))
            points.append((x, y))
        width = max(2, round(size * (0.010 + 0.020 * (1 - p))))
        draw.line(points, fill=(48, 103, 128, 160), width=width)
        draw.line([(x + width * 1.8, y) for x, y in points], fill=(58, 86, 92, 70), width=max(1, width // 2))

    for idx in range(24):
        x = size * ((idx * 0.137) % 1.0)
        y = waterline + size * (0.16 + ((idx * 0.217) % 0.68))
        draw.ellipse((x, y, x + size * 0.010, y + size * 0.005), fill=(68, 55, 43, 90))
    return _finish_scene(image)


def render_marine_terrace_oblique(*, progress: float, size: int) -> Image.Image:
    p = float(np.clip(progress, 0.0, 1.0))
    image = _vertical_gradient(size, (145, 169, 176), (90, 82, 65))
    draw = ImageDraw.Draw(image, "RGBA")
    sea_top = size * 0.60
    draw.rectangle((0, sea_top, size, size), fill=(62, 124, 152, 225))
    for i in range(5):
        y = sea_top + size * (0.05 + i * 0.07)
        draw.arc((-size * 0.1, y - size * 0.04, size * 1.1, y + size * 0.05), 5, 175, fill=(220, 232, 226, 80), width=max(1, size // 160))

    uplift = size * (0.04 + 0.12 * p)
    levels = [
        (size * 0.21 - uplift * 0.6, (103, 109, 83, 255)),
        (size * 0.37 - uplift * 0.35, (134, 123, 82, 255)),
        (size * 0.52 - uplift * 0.15, (171, 151, 96, 255)),
    ]
    left = size * 0.04
    right = size * 0.95
    for idx, (y, color) in enumerate(levels):
        draw.polygon(
            [(left, y), (right, y + size * 0.03), (right, y + size * 0.11), (left, y + size * 0.08)],
            fill=color,
        )
        cliff_y = y + size * 0.10
        draw.polygon(
            [(left, cliff_y), (right, cliff_y + size * 0.03), (right, cliff_y + size * 0.07), (left, cliff_y + size * 0.035)],
            fill=(74, 68, 56, 200),
        )
        if p > 0.28 + idx * 0.18:
            notch_y = cliff_y + size * 0.035
            draw.line((left + size * 0.08, notch_y, right - size * 0.06, notch_y + size * 0.02), fill=(224, 223, 196, 150), width=max(2, size // 90))

    beach_y = sea_top - size * (0.01 + 0.02 * p)
    draw.polygon([(0, beach_y), (size, beach_y + size * 0.035), (size, sea_top + size * 0.025), (0, sea_top)], fill=(196, 176, 122, 220))
    return _finish_scene(image)


def render_kettle_lake_oblique(*, progress: float, size: int) -> Image.Image:
    p = float(np.clip(progress, 0.0, 1.0))
    image = _vertical_gradient(size, (165, 177, 174), (117, 132, 109))
    draw = ImageDraw.Draw(image, "RGBA")
    draw.polygon([(0, size * 0.28), (size, size * 0.20), (size, size), (0, size)], fill=(144, 147, 118, 235))
    draw.polygon([(0, size * 0.30), (size * 0.38, size * 0.18), (size, size * 0.26), (size, size * 0.38), (0, size * 0.42)], fill=(218, 226, 224, int(170 * (1 - p))))

    basins = [(0.33, 0.56, 0.12, 0.08), (0.62, 0.63, 0.16, 0.10), (0.52, 0.43, 0.10, 0.06)]
    for idx, (cx, cy, rx, ry) in enumerate(basins):
        active = np.clip((p - 0.18 - idx * 0.08) / 0.55, 0.0, 1.0)
        x = size * cx
        y = size * cy
        rrx = size * rx * (0.65 + 0.35 * active)
        rry = size * ry * (0.65 + 0.35 * active)
        draw.ellipse((x - rrx * 1.08, y - rry * 1.15, x + rrx * 1.08, y + rry * 1.15), fill=(84, 77, 58, int(120 * active)))
        water_alpha = int(225 * active)
        draw.ellipse((x - rrx, y - rry, x + rrx, y + rry), fill=(67, 130, 153, water_alpha))
        draw.arc((x - rrx, y - rry, x + rrx, y + rry), 8, 172, fill=(224, 238, 234, int(110 * active)), width=max(1, size // 170))

    for i in range(26):
        x = size * ((i * 0.173) % 1.0)
        y = size * (0.36 + ((i * 0.119) % 0.52))
        draw.line((x, y, x + size * 0.025, y + size * 0.004), fill=(82, 91, 72, 80), width=1)
    return _finish_scene(image)


def render_outwash_plain_oblique(*, progress: float, size: int) -> Image.Image:
    p = float(np.clip(progress, 0.0, 1.0))
    image = _vertical_gradient(size, (158, 174, 178), (126, 116, 83))
    draw = ImageDraw.Draw(image, "RGBA")
    glacier_y = size * (0.20 + 0.12 * p)
    draw.polygon([(0, glacier_y - size * 0.08), (size * 0.55, glacier_y - size * 0.15), (size, glacier_y - size * 0.04), (size, glacier_y + size * 0.14), (0, glacier_y + size * 0.10)], fill=(218, 230, 230, 220))
    draw.polygon([(0, glacier_y + size * 0.08), (size, glacier_y + size * 0.13), (size, size), (0, size)], fill=(157, 139, 93, 235))

    fan_apex = (size * 0.50, glacier_y + size * 0.10)
    fan_w = size * (0.18 + 0.38 * p)
    draw.polygon(
        [fan_apex, (size * 0.50 - fan_w, size), (size * 0.50 + fan_w, size)],
        fill=(188, 165, 107, 145),
    )
    for idx in range(8):
        phase = idx * 0.82
        points = []
        for step in range(22):
            t = step / 21
            y = fan_apex[1] + t * (size - fan_apex[1])
            spread = (0.04 + 0.32 * t) * size * p
            x = fan_apex[0] + np.sin(t * np.pi * (2.2 + idx * 0.15) + phase) * spread + (idx - 3.5) * size * 0.012
            points.append((x, y))
        draw.line(points, fill=(55, 112, 142, 150), width=max(1, round(size * (0.006 + 0.006 * p))))
    for i in range(34):
        x = size * ((i * 0.197) % 1.0)
        y = glacier_y + size * (0.18 + ((i * 0.131) % 0.65))
        draw.ellipse((x, y, x + size * 0.013, y + size * 0.006), fill=(96, 82, 58, 70))
    return _finish_scene(image)


def render_thermokarst_oblique(*, progress: float, size: int) -> Image.Image:
    p = float(np.clip(progress, 0.0, 1.0))
    image = _vertical_gradient(size, (150, 166, 164), (87, 108, 84))
    draw = ImageDraw.Draw(image, "RGBA")
    draw.polygon([(0, size * 0.26), (size, size * 0.24), (size, size), (0, size)], fill=(97, 122, 88, 238))

    for col in range(6):
        for row in range(5):
            cx = size * (0.12 + col * 0.17 + (row % 2) * 0.035)
            cy = size * (0.36 + row * 0.13)
            r = size * 0.055
            pts = [
                (cx + np.cos(a) * r, cy + np.sin(a) * r * 0.55)
                for a in np.linspace(0, 2 * np.pi, 7)[:-1]
            ]
            draw.line(pts + [pts[0]], fill=(50, 66, 52, 55), width=1)

    ponds = [(0.30, 0.50, 0.12, 0.07), (0.60, 0.43, 0.15, 0.08), (0.47, 0.70, 0.18, 0.10), (0.78, 0.67, 0.10, 0.06)]
    for idx, (cx, cy, rx, ry) in enumerate(ponds):
        active = np.clip((p - idx * 0.12) / 0.62, 0.0, 1.0)
        x = size * cx
        y = size * cy
        rrx = size * rx * active
        rry = size * ry * active
        if active <= 0:
            continue
        draw.ellipse((x - rrx * 1.15, y - rry * 1.25, x + rrx * 1.15, y + rry * 1.25), fill=(57, 71, 56, int(100 * active)))
        draw.ellipse((x - rrx, y - rry, x + rrx, y + rry), fill=(54, 116, 139, int(210 * active)))
        if p > 0.7:
            draw.arc((x - rrx, y - rry, x + rrx, y + rry), 10, 170, fill=(205, 225, 222, 80), width=max(1, size // 180))
    return _finish_scene(image)


def render_cinder_cone_oblique(*, progress: float, size: int) -> Image.Image:
    p = float(np.clip(progress, 0.0, 1.0))
    image = _vertical_gradient(size, (143, 151, 148), (69, 60, 52))
    draw = ImageDraw.Draw(image, "RGBA")
    horizon = size * 0.34
    draw.polygon([(0, horizon + size * 0.08), (size * 0.34, horizon - size * 0.02), (size, horizon + size * 0.06), (size, size), (0, size)], fill=(73, 66, 58, 220))

    cx = size * 0.52
    base_y = size * 0.76
    rx = size * (0.10 + 0.25 * p)
    height = size * (0.08 + 0.38 * p)
    left = (cx - rx, base_y)
    right = (cx + rx, base_y)
    top = (cx, base_y - height)
    draw.polygon([left, top, right], fill=(91, 64, 47, 238))
    draw.polygon([top, right, (cx + rx * 0.12, base_y - height * 0.18)], fill=(54, 45, 39, 155))
    draw.polygon([left, top, (cx - rx * 0.08, base_y - height * 0.10)], fill=(130, 85, 57, 170))
    crater_rx = rx * (0.26 + 0.10 * p)
    crater_ry = size * (0.018 + 0.022 * p)
    draw.ellipse((cx - crater_rx, top[1] - crater_ry, cx + crater_rx, top[1] + crater_ry), fill=(34, 29, 27, 230))
    if p > 0.10:
        alpha = int(90 + 90 * min(p, 0.7))
        draw.ellipse((cx - size * 0.055, top[1] - size * 0.17, cx + size * 0.060, top[1] - size * 0.03), fill=(93, 83, 76, alpha))
        draw.polygon([(cx - size * 0.08, top[1] + size * 0.02), (cx + size * 0.08, top[1] + size * 0.02), (cx + size * 0.24, base_y + size * 0.06), (cx - size * 0.24, base_y + size * 0.06)], fill=(84, 59, 43, int(80 * p)))
    for idx in range(12):
        t = idx / 11
        y = top[1] + t * height * 0.96
        span = rx * t
        draw.line((cx - span * 0.80, y, cx + span * 0.82, y + size * 0.012), fill=(41, 35, 32, 65), width=1)
    return _finish_scene(image)


def render_lava_dome_oblique(*, progress: float, size: int) -> Image.Image:
    image = Image.new("RGB", (size, size), (128, 137, 139))
    draw = ImageDraw.Draw(image, "RGBA")

    for y in range(size):
        t = y / max(size - 1, 1)
        if t < 0.45:
            color = (
                round(150 - 52 * t),
                round(158 - 58 * t),
                round(160 - 63 * t),
            )
        else:
            color = (
                round(82 - 32 * (t - 0.45)),
                round(74 - 28 * (t - 0.45)),
                round(64 - 24 * (t - 0.45)),
            )
        draw.line((0, y, size, y), fill=color)

    horizon = round(size * 0.38)
    draw.polygon(
        [(0, horizon + size * 0.10), (size * 0.22, horizon - size * 0.03), (size * 0.58, horizon + size * 0.02), (size, horizon - size * 0.04), (size, size), (0, size)],
        fill=(64, 56, 50, 210),
    )
    draw.polygon(
        [(0, horizon + size * 0.18), (size * 0.34, horizon + size * 0.02), (size * 0.70, horizon + size * 0.12), (size, horizon + size * 0.00), (size, size), (0, size)],
        fill=(48, 43, 39, 230),
    )

    p = float(np.clip(progress, 0.0, 1.0))
    cx = size * 0.53
    base_y = size * 0.73
    radius_x = size * (0.10 + 0.29 * p)
    radius_y = size * (0.04 + 0.23 * p)
    height = size * (0.03 + 0.32 * p)

    if p > 0.08:
        steam_alpha = int(40 + 100 * min(p, 0.8))
        for idx in range(4):
            sx = cx + (idx - 1.5) * radius_x * 0.20
            sy = base_y - height - size * (0.05 + idx * 0.02)
            draw.ellipse(
                (sx - size * 0.045, sy - size * 0.08, sx + size * 0.055, sy + size * 0.03),
                fill=(205, 205, 198, steam_alpha),
            )

    for layer in range(14, -1, -1):
        lt = layer / 14
        y = base_y - height * lt
        rx = radius_x * (0.42 + 0.58 * (1 - lt ** 1.7))
        ry = radius_y * (0.26 + 0.74 * (1 - lt ** 1.3))
        shade = int(62 + 80 * lt)
        color = (shade + 28, shade + 12, shade, 236)
        if layer % 3 == 0:
            color = (shade + 45, shade + 25, shade + 8, 238)
        draw.ellipse((cx - rx, y - ry, cx + rx, y + ry), fill=color)

    glow = max(0.0, min((p - 0.12) / 0.28, 1.0)) * (1.0 - max(0.0, p - 0.72) * 1.8)
    if glow > 0:
        vent_y = base_y - height * 0.92
        draw.ellipse(
            (cx - radius_x * 0.18, vent_y - radius_y * 0.26, cx + radius_x * 0.18, vent_y + radius_y * 0.17),
            fill=(232, 96, 42, int(180 * glow)),
        )

    crack_count = 8
    for idx in range(crack_count):
        angle = -0.9 + idx * (1.8 / max(crack_count - 1, 1))
        start_y = base_y - height * (0.70 - 0.22 * np.cos(idx))
        start_x = cx + np.sin(angle) * radius_x * 0.20
        end_x = cx + np.sin(angle) * radius_x * (0.72 + 0.18 * (idx % 2))
        end_y = base_y - radius_y * (0.28 + 0.20 * (idx % 3))
        draw.line((start_x, start_y, end_x, end_y), fill=(32, 28, 25, 120), width=max(1, size // 120))

    if p > 0.72:
        scar = (p - 0.72) / 0.28
        draw.polygon(
            [
                (cx + radius_x * 0.18, base_y - height * 0.65),
                (cx + radius_x * (0.62 + 0.12 * scar), base_y - height * 0.34),
                (cx + radius_x * 0.42, base_y + radius_y * 0.24),
                (cx + radius_x * 0.05, base_y - height * 0.12),
            ],
            fill=(70, 50, 42, int(170 * scar)),
        )
        draw.ellipse(
            (cx + radius_x * 0.28, base_y - height * 0.30, cx + radius_x * 0.82, base_y + radius_y * 0.42),
            fill=(56, 47, 42, int(95 * scar)),
        )

    image = image.filter(ImageFilter.UnsharpMask(radius=1.2, percent=80, threshold=2))
    draw = ImageDraw.Draw(image, "RGBA")
    draw.rectangle((0, 0, size - 1, size - 1), outline=(0, 0, 0, 36), width=1)
    return image


def build_filmstrip(landform_id: str, *, frame_count: int, cols: int, rows: int, cell_size: int, gutter: int) -> Path:
    surfaces = sample_landform_surface_sequence(landform_id, frame_count=frame_count, grid_size=96)
    frames = normalize_stack(surfaces)

    sheet_w = cols * cell_size + (cols - 1) * gutter
    sheet_h = rows * cell_size + (rows - 1) * gutter
    sheet = Image.new("RGB", (sheet_w, sheet_h), (248, 248, 244))

    for index, frame in enumerate(frames):
        row = index // cols
        col = index % cols
        progress = index / max(frame_count - 1, 1)
        rendered = render_frame(landform_id, frame, progress=progress, size=cell_size)
        x = col * (cell_size + gutter)
        y = row * (cell_size + gutter)
        sheet.paste(rendered, (x, y))

    output_dir = OUTPUT_ROOT / landform_id / "filmstrip"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{landform_id}_procedural_filmstrip.png"
    sheet.save(output_path)
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Build procedural filmstrips for additional terrain landforms.")
    parser.add_argument("--only", help="Comma-separated landform ids.")
    parser.add_argument("--frames", type=int, default=DEFAULT_FRAME_COUNT)
    parser.add_argument("--cols", type=int, default=DEFAULT_COLS)
    parser.add_argument("--rows", type=int, default=DEFAULT_ROWS)
    parser.add_argument("--cell-size", type=int, default=DEFAULT_CELL_SIZE)
    parser.add_argument("--gutter", type=int, default=DEFAULT_GUTTER)
    args = parser.parse_args()

    specs = load_specs()
    if args.only:
        wanted = {item.strip() for item in args.only.split(",") if item.strip()}
        specs = [item for item in specs if str(item["id"]) in wanted]

    if args.frames != args.cols * args.rows:
        raise ValueError("frames must match cols * rows for a complete filmstrip")

    built = []
    for spec in specs:
        landform_id = str(spec["id"])
        output_path = build_filmstrip(
            landform_id,
            frame_count=args.frames,
            cols=args.cols,
            rows=args.rows,
            cell_size=args.cell_size,
            gutter=args.gutter,
        )
        built.append(output_path)
        print(f"{landform_id}: {output_path.relative_to(PROJECT_ROOT)}")

    print(f"built={len(built)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
