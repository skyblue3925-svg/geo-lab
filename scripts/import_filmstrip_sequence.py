"""Import a generated filmstrip/contact sheet as an image-sequence animation."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

from PIL import Image


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = PROJECT_ROOT / "assets" / "cinematic" / "image_sequence"
DEFAULT_FPS = 11


def title_for_landform(landform_id: str) -> str:
    sys.path.insert(0, str(PROJECT_ROOT))
    try:
        from app.services.animation_assets import title_for_landform as app_title_for_landform

        return app_title_for_landform(landform_id)
    except Exception:
        return landform_id.replace("_", " ")


def split_filmstrip(
    filmstrip_path: Path,
    *,
    cols: int,
    rows: int,
    trim_px: int,
    target_size: int,
) -> list[Image.Image]:
    image = Image.open(filmstrip_path).convert("RGB")
    cell_w = image.width / cols
    cell_h = image.height / rows
    frames: list[Image.Image] = []

    for row in range(rows):
        for col in range(cols):
            left = round(col * cell_w) + trim_px
            top = round(row * cell_h) + trim_px
            right = round((col + 1) * cell_w) - trim_px
            bottom = round((row + 1) * cell_h) - trim_px
            frame = image.crop((left, top, right, bottom))
            frame = cover_resize(frame, (target_size, target_size))
            frames.append(frame)
    return frames


def cover_resize(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    target_w, target_h = size
    scale = max(target_w / image.width, target_h / image.height)
    resized = image.resize((round(image.width * scale), round(image.height * scale)), Image.Resampling.LANCZOS)
    left = (resized.width - target_w) // 2
    top = (resized.height - target_h) // 2
    return resized.crop((left, top, left + target_w, top + target_h))


def save_frames(frames: list[Image.Image], output_dir: Path) -> list[Path]:
    frame_dir = output_dir / "frames"
    if frame_dir.exists():
        shutil.rmtree(frame_dir)
    frame_dir.mkdir(parents=True, exist_ok=True)

    paths: list[Path] = []
    for index, frame in enumerate(frames):
        path = frame_dir / f"frame_{index:03d}.png"
        frame.save(path)
        paths.append(path)
    return paths


def save_animation(frames: list[Image.Image], output_dir: Path, landform_id: str, *, fps: int) -> Path:
    output_path = output_dir / f"{landform_id}_image_sequence.webp"
    duration_ms = round(1000 / max(fps, 1))
    frames[0].save(
        output_path,
        save_all=True,
        append_images=frames[1:],
        duration=duration_ms,
        loop=0,
        format="WEBP",
        quality=92,
        method=2,
    )
    return output_path


def update_metadata(entry: dict[str, object]) -> None:
    metadata_path = OUTPUT_ROOT / "metadata.json"
    if metadata_path.exists():
        manifest = json.loads(metadata_path.read_text(encoding="utf-8"))
    else:
        manifest = {
            "version": "1.0",
            "description": "Image-sequence terrain formation animations generated from filmstrip images.",
            "videos": [],
        }

    by_id = {item.get("id"): item for item in manifest.get("videos", [])}
    by_id[entry["id"]] = entry
    manifest["videos"] = list(by_id.values())
    metadata_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--landform", required=True)
    parser.add_argument("--filmstrip", required=True)
    parser.add_argument("--cols", type=int, default=5)
    parser.add_argument("--rows", type=int, default=6)
    parser.add_argument("--trim-px", type=int, default=2)
    parser.add_argument("--target-size", type=int, default=1024)
    parser.add_argument("--fps", type=int, default=DEFAULT_FPS)
    args = parser.parse_args()

    filmstrip_path = Path(args.filmstrip)
    if not filmstrip_path.exists():
        raise FileNotFoundError(filmstrip_path)

    output_dir = OUTPUT_ROOT / args.landform
    output_dir.mkdir(parents=True, exist_ok=True)
    source_dir = output_dir / "filmstrip"
    source_dir.mkdir(parents=True, exist_ok=True)
    saved_source = source_dir / filmstrip_path.name
    if filmstrip_path.resolve() != saved_source.resolve():
        shutil.copyfile(filmstrip_path, saved_source)

    frames = split_filmstrip(
        saved_source,
        cols=args.cols,
        rows=args.rows,
        trim_px=args.trim_px,
        target_size=args.target_size,
    )
    frame_paths = save_frames(frames, output_dir)
    animation_path = save_animation(frames, output_dir, args.landform, fps=args.fps)

    rel_animation = animation_path.relative_to(PROJECT_ROOT / "assets" / "cinematic").as_posix()
    rel_source = saved_source.relative_to(PROJECT_ROOT).as_posix()
    entry = {
        "id": f"{args.landform}_image_sequence",
        "title": f"{title_for_landform(args.landform)} 이미지 기반 형성과정",
        "category": "representative",
        "file": rel_animation,
        "format": "animated_webp",
        "frame_count": len(frame_paths),
        "fps": args.fps,
        "mode": "filmstrip_import",
        "status": "ready",
        "source_filmstrip": rel_source,
        "description": "생성된 필름스트립을 프레임으로 분할해 만든 이미지 기반 형성과정 애니메이션입니다.",
    }
    update_metadata(entry)

    print(f"frames={len(frame_paths)}")
    print(f"animation={animation_path}")
    print(f"source={saved_source}")


if __name__ == "__main__":
    main()
