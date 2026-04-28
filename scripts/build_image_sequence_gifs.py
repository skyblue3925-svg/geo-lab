from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image


PROJECT_ROOT = Path(__file__).resolve().parents[1]
IMAGE_SEQUENCE_ROOT = PROJECT_ROOT / "assets" / "cinematic" / "image_sequence"


def iter_source_dirs(only: str | None = None) -> list[Path]:
    paths = sorted(path.parent for path in IMAGE_SEQUENCE_ROOT.glob("*/*_image_sequence.webp"))
    if only:
        wanted = {item.strip() for item in only.split(",") if item.strip()}
        paths = [path for path in paths if path.name in wanted]
    return paths


def frame_duration_ms(frame: Image.Image, fallback: int) -> int:
    duration = frame.info.get("duration", fallback)
    try:
        duration = int(duration)
    except (TypeError, ValueError):
        duration = fallback
    return max(duration, 20)


def resize_for_gallery(frame: Image.Image, max_size: int) -> Image.Image:
    image = frame.convert("RGB")
    if max(image.size) <= max_size:
        return image
    image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
    return image


def convert_sequence_to_gif(sequence_dir: Path, *, max_size: int, fallback_duration: int, force: bool) -> Path:
    landform_id = sequence_dir.name
    output_path = sequence_dir / f"{landform_id}_image_sequence.gif"
    frame_paths = sorted((sequence_dir / "frames").glob("frame_*.png"))
    source_path = sequence_dir / f"{landform_id}_image_sequence.webp"
    newest_source_mtime = max(
        [source_path.stat().st_mtime_ns if source_path.exists() else 0]
        + [frame_path.stat().st_mtime_ns for frame_path in frame_paths]
    )
    if output_path.exists() and not force and output_path.stat().st_mtime_ns >= newest_source_mtime:
        return output_path

    frames: list[Image.Image] = []
    durations: list[int] = []
    if frame_paths:
        for frame_path in frame_paths:
            with Image.open(frame_path) as frame:
                frames.append(resize_for_gallery(frame, max_size))
                durations.append(fallback_duration)
    elif source_path.exists():
        from PIL import ImageSequence

        image = Image.open(source_path)
        for frame in ImageSequence.Iterator(image):
            frames.append(resize_for_gallery(frame, max_size))
            durations.append(frame_duration_ms(frame, fallback_duration))
    else:
        raise FileNotFoundError(f"No source frames found in {sequence_dir}")

    if not frames:
        raise ValueError(f"No frames found in {sequence_dir}")

    first, *rest = frames
    first.save(
        output_path,
        save_all=True,
        append_images=rest,
        duration=durations,
        loop=0,
        optimize=False,
        disposal=2,
    )
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Build GIF gallery assets from terrain image-sequence frames.")
    parser.add_argument("--only", help="Comma-separated landform ids to rebuild.")
    parser.add_argument("--max-size", type=int, default=384, help="Maximum GIF width/height in pixels.")
    parser.add_argument("--duration-ms", type=int, default=140, help="Fallback frame duration in milliseconds.")
    parser.add_argument("--force", action="store_true", help="Rebuild even when GIF files are newer than WebP sources.")
    args = parser.parse_args()

    converted = []
    for sequence_dir in iter_source_dirs(args.only):
        output_path = convert_sequence_to_gif(
            sequence_dir,
            max_size=args.max_size,
            fallback_duration=args.duration_ms,
            force=args.force,
        )
        converted.append(output_path)
        print(f"{sequence_dir.name}: {output_path.relative_to(PROJECT_ROOT)}")

    print(f"Built {len(converted)} GIF files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
