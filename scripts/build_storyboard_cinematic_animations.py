"""Build high-frame animated WebP assets from 4-panel terrain storyboards."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.services.animation_assets import KOREAN_TITLES  # noqa: E402


SOURCE_ROOT = PROJECT_ROOT / "output" / "terrain-animation-assets"
OUTPUT_ROOT = PROJECT_ROOT / "assets" / "cinematic" / "storyboard_cinematic"

TARGET_SIZE = (640, 640)
FPS = 24
FRAME_DURATION_MS = round(1000 / FPS)
HOLD_FRAMES = 22
TRANSITION_FRAMES = 16
WEBP_QUALITY = 82
WEBP_METHOD = 2


def ease_in_out(value: float) -> float:
    return 0.5 - 0.5 * math.cos(math.pi * value)


def split_storyboard(image: Image.Image) -> list[Image.Image]:
    width, height = image.size
    panels: list[Image.Image] = []
    for index in range(4):
        left = round(index * width / 4)
        right = round((index + 1) * width / 4)
        panels.append(image.crop((left, 0, right, height)).convert("RGB"))
    return panels


def cover_resize(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    target_w, target_h = size
    scale = max(target_w / image.width, target_h / image.height)
    resized = image.resize((round(image.width * scale), round(image.height * scale)), Image.Resampling.LANCZOS)
    left = (resized.width - target_w) // 2
    top = (resized.height - target_h) // 2
    return resized.crop((left, top, left + target_w, top + target_h))


def contain_resize(image: Image.Image, size: tuple[int, int], margin: int = 28) -> Image.Image:
    target_w, target_h = size
    max_w = target_w - margin * 2
    max_h = target_h - margin * 2
    scale = min(max_w / image.width, max_h / image.height)
    return image.resize((round(image.width * scale), round(image.height * scale)), Image.Resampling.LANCZOS)


def camera_motion(category: str, landform_id: str, stage_index: int, progress: float) -> tuple[float, int, int]:
    """Return zoom and x/y shifts for a stage-specific camera move."""
    eased = ease_in_out(max(0.0, min(1.0, progress)))
    direction = -1 if stage_index % 2 else 1
    zoom = 1.02 + 0.035 * eased

    if category == "river_delta":
        x_shift = round(direction * (-20 + 40 * eased))
        y_shift = round(-10 + 20 * eased)
    elif category == "glacial_volcanic":
        x_shift = round(direction * (12 - 24 * eased))
        y_shift = round(-22 + 44 * eased)
    elif landform_id in {"barchan", "coastal_dune", "star_dune", "transverse_dune"}:
        x_shift = round(-28 + 56 * eased)
        y_shift = round(direction * 8)
        zoom = 1.015 + 0.04 * eased
    elif landform_id in {"spit_lagoon", "tombolo", "ria_coast", "sea_arch", "coastal_cliff"}:
        x_shift = round(direction * (26 - 52 * eased))
        y_shift = round(-8 + 16 * eased)
    else:
        x_shift = round(direction * (-14 + 28 * eased))
        y_shift = round(-14 + 28 * eased)

    return zoom, x_shift, y_shift


def stage_canvas(
    panel: Image.Image,
    *,
    category: str,
    landform_id: str,
    stage_index: int,
    progress: float,
) -> Image.Image:
    background = cover_resize(panel, TARGET_SIZE).filter(ImageFilter.GaussianBlur(radius=18))
    background = ImageEnhance.Brightness(background).enhance(0.68)
    background = ImageEnhance.Color(background).enhance(0.92)

    overlay = contain_resize(panel, TARGET_SIZE)
    zoom, x_shift, y_shift = camera_motion(category, landform_id, stage_index, progress)
    overlay = overlay.resize(
        (round(overlay.width * zoom), round(overlay.height * zoom)),
        Image.Resampling.LANCZOS,
    )

    canvas = background.copy()
    x = (TARGET_SIZE[0] - overlay.width) // 2 + x_shift
    y = (TARGET_SIZE[1] - overlay.height) // 2 + y_shift
    canvas.paste(overlay, (x, y))
    return canvas


def build_frames(panels: list[Image.Image], *, category: str, landform_id: str) -> list[Image.Image]:
    frames: list[Image.Image] = []
    for panel_index, panel in enumerate(panels):
        for hold_idx in range(HOLD_FRAMES):
            progress = hold_idx / max(HOLD_FRAMES - 1, 1)
            frames.append(
                stage_canvas(
                    panel,
                    category=category,
                    landform_id=landform_id,
                    stage_index=panel_index,
                    progress=progress,
                )
            )

        if panel_index == len(panels) - 1:
            continue

        next_panel = panels[panel_index + 1]
        for transition_idx in range(1, TRANSITION_FRAMES + 1):
            raw = transition_idx / (TRANSITION_FRAMES + 1)
            alpha = ease_in_out(raw)
            current_frame = stage_canvas(
                panel,
                category=category,
                landform_id=landform_id,
                stage_index=panel_index,
                progress=min(1.0, 0.78 + raw * 0.22),
            )
            next_frame = stage_canvas(
                next_panel,
                category=category,
                landform_id=landform_id,
                stage_index=panel_index + 1,
                progress=max(0.0, raw * 0.22),
            )
            frames.append(Image.blend(current_frame, next_frame, alpha))

    return frames


def save_animated_webp(frames: list[Image.Image], output_file: Path) -> None:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(
        output_file,
        save_all=True,
        append_images=frames[1:],
        duration=FRAME_DURATION_MS,
        loop=0,
        format="WEBP",
        quality=WEBP_QUALITY,
        method=WEBP_METHOD,
    )


def make_metadata_entry(
    landform_id: str,
    category: str,
    output_file: Path,
    storyboard_path: Path,
    frame_count: int,
) -> dict[str, object]:
    title = KOREAN_TITLES.get(landform_id, landform_id.replace("_", " "))
    return {
        "id": f"{landform_id}_storyboard_cinematic",
        "title": f"{title} 키프레임 preview",
        "category": category,
        "file": f"storyboard_cinematic/{output_file.name}",
        "format": "animated_webp",
        "frame_rate": FPS,
        "frame_count": frame_count,
        "duration": f"{frame_count * FRAME_DURATION_MS / 1000:.1f}s",
        "sources": [str(storyboard_path.relative_to(PROJECT_ROOT)).replace("\\", "/")],
        "description": "4개 핵심 이미지를 카메라 이동으로 훑는 preview입니다. 실제 형성과정 애니메이션은 3D stage 모델을 사용합니다.",
        "status": "ready",
    }


def build_animation(storyboard_path: Path, *, force: bool = False) -> dict[str, object]:
    landform_id = storyboard_path.name.removesuffix("_storyboard_draft.png")
    category = storyboard_path.parents[1].name
    output_file = OUTPUT_ROOT / f"{landform_id}_storyboard_cinematic.webp"
    frame_count = HOLD_FRAMES * 4 + TRANSITION_FRAMES * 3

    if output_file.exists() and output_file.stat().st_size > 1024 and not force:
        return make_metadata_entry(landform_id, category, output_file, storyboard_path, frame_count)

    image = Image.open(storyboard_path).convert("RGB")
    frames = build_frames(split_storyboard(image), category=category, landform_id=landform_id)
    save_animated_webp(frames, output_file)
    return make_metadata_entry(landform_id, category, output_file, storyboard_path, len(frames))


def merge_manifest(entries: list[dict[str, object]], metadata_path: Path, *, partial: bool) -> dict[str, object]:
    if partial and metadata_path.exists():
        manifest = json.loads(metadata_path.read_text(encoding="utf-8"))
        entry_by_id = {entry.get("id"): entry for entry in manifest.get("videos", [])}
        for entry in entries:
            entry_by_id[entry.get("id")] = entry
        manifest["videos"] = list(entry_by_id.values())
        return manifest

    return {
        "version": "1.0",
        "description": "Generated high-frame animated WebP assets from terrain storyboard images.",
        "videos": entries,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="Overwrite existing generated WebP animations.")
    parser.add_argument("--only", nargs="*", help="Optional landform ids to rebuild, for example spit_lagoon coastal_dune.")
    parser.add_argument("--limit", type=int, help="Build at most this many assets.")
    args = parser.parse_args()

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    storyboard_paths = sorted(SOURCE_ROOT.glob("*/*/*_storyboard_draft.png"))
    if args.only:
        wanted = set(args.only)
        storyboard_paths = [
            path for path in storyboard_paths
            if path.name.removesuffix("_storyboard_draft.png") in wanted
        ]
    if args.limit is not None:
        storyboard_paths = storyboard_paths[: max(args.limit, 0)]

    entries = [build_animation(path, force=args.force) for path in storyboard_paths]
    metadata_path = OUTPUT_ROOT / "metadata.json"
    manifest = merge_manifest(entries, metadata_path, partial=bool(args.only or args.limit))
    metadata_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"built={len(entries)}")
    print(f"frames_per_asset={HOLD_FRAMES * 4 + TRANSITION_FRAMES * 3}")
    print(f"fps={FPS}")
    print(f"output={OUTPUT_ROOT}")


if __name__ == "__main__":
    main()
