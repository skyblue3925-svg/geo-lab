from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageSequence


PROJECT_ROOT = Path(__file__).resolve().parents[1]
IMAGE_SEQUENCE_ROOT = PROJECT_ROOT / "assets" / "cinematic" / "image_sequence"


def iter_source_webps(only: str | None = None) -> list[Path]:
    paths = sorted(IMAGE_SEQUENCE_ROOT.glob("*/*_image_sequence.webp"))
    if only:
        wanted = {item.strip() for item in only.split(",") if item.strip()}
        paths = [path for path in paths if path.parent.name in wanted]
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


def convert_webp_to_gif(source_path: Path, *, max_size: int, fallback_duration: int, force: bool) -> Path:
    landform_id = source_path.parent.name
    output_path = source_path.with_name(f"{landform_id}_image_sequence.gif")
    if output_path.exists() and not force and output_path.stat().st_mtime_ns >= source_path.stat().st_mtime_ns:
        return output_path

    image = Image.open(source_path)
    frames: list[Image.Image] = []
    durations: list[int] = []
    for frame in ImageSequence.Iterator(image):
        frames.append(resize_for_gallery(frame, max_size))
        durations.append(frame_duration_ms(frame, fallback_duration))

    if not frames:
        raise ValueError(f"No frames found in {source_path}")

    first, *rest = frames
    first.save(
        output_path,
        save_all=True,
        append_images=rest,
        duration=durations,
        loop=0,
        optimize=True,
        disposal=2,
    )
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Build GIF gallery assets from terrain image-sequence WebP files.")
    parser.add_argument("--only", help="Comma-separated landform ids to rebuild.")
    parser.add_argument("--max-size", type=int, default=384, help="Maximum GIF width/height in pixels.")
    parser.add_argument("--duration-ms", type=int, default=140, help="Fallback frame duration in milliseconds.")
    parser.add_argument("--force", action="store_true", help="Rebuild even when GIF files are newer than WebP sources.")
    args = parser.parse_args()

    converted = []
    for source_path in iter_source_webps(args.only):
        output_path = convert_webp_to_gif(
            source_path,
            max_size=args.max_size,
            fallback_duration=args.duration_ms,
            force=args.force,
        )
        converted.append(output_path)
        print(f"{source_path.parent.name}: {output_path.relative_to(PROJECT_ROOT)}")

    print(f"Built {len(converted)} GIF files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
