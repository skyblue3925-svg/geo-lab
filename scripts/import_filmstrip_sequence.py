"""Import a generated filmstrip/contact sheet as an image-sequence animation."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = PROJECT_ROOT / "assets" / "cinematic" / "image_sequence"
DEFAULT_FPS = 7
DEFAULT_STAGE_FPS = 2


def default_fps_for_frame_count(frame_count: int) -> int:
    return DEFAULT_STAGE_FPS if frame_count <= 8 else DEFAULT_FPS


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
    cols: int | None,
    rows: int | None,
    trim_px: int,
    target_size: int,
) -> list[Image.Image]:
    image = Image.open(filmstrip_path).convert("RGB")
    if cols is None or rows is None:
        x_segments, y_segments = infer_filmstrip_cells(image)
    else:
        x_segments = _uniform_segments(image.width, cols)
        y_segments = _uniform_segments(image.height, rows)
    frames: list[Image.Image] = []

    for y_start, y_end in y_segments:
        for x_start, x_end in x_segments:
            left = x_start + trim_px
            top = y_start + trim_px
            right = x_end - trim_px
            bottom = y_end - trim_px
            frame = image.crop((left, top, right, bottom))
            frame = cover_resize(frame, (target_size, target_size))
            frames.append(frame)
    return frames


def infer_filmstrip_grid(image: Image.Image) -> tuple[int, int]:
    x_segments, y_segments = infer_filmstrip_cells(image)
    return len(x_segments), len(y_segments)


def infer_filmstrip_cells(image: Image.Image) -> tuple[list[tuple[int, int]], list[tuple[int, int]]]:
    x_groups = _separator_groups(image, axis="x")
    y_groups = _separator_groups(image, axis="y")
    x_segments = _segments_from_separator_groups(image.width, x_groups)
    y_segments = _segments_from_separator_groups(image.height, y_groups)

    if len(x_segments) != 5:
        x_count = _infer_axis_count_by_boundary_score(image, axis="x")
        x_segments = _segments_by_boundary_score(image, axis="x", count=x_count)
    if len(y_segments) < 5 or len(y_segments) > 6:
        y_count = _infer_axis_count_by_boundary_score(image, axis="y")
        y_segments = _segments_by_boundary_score(image, axis="y", count=y_count)

    return x_segments, y_segments


def _uniform_segments(limit: int, count: int) -> list[tuple[int, int]]:
    return [(round(index * limit / count), round((index + 1) * limit / count)) for index in range(count)]


def _infer_axis_count_by_boundary_score(image: Image.Image, *, axis: str) -> int:
    score = _axis_boundary_score(image, axis=axis)

    candidates: list[tuple[float, int]] = []
    for count in range(2, 9):
        total = 0.0
        for index in range(1, count):
            position = round(index * len(score) / count)
            start = max(0, position - 6)
            end = min(len(score), position + 7)
            total += float(score[start:end].max())
        candidates.append((total, count))
    return max(candidates)[1]


def _segments_by_boundary_score(image: Image.Image, *, axis: str, count: int) -> list[tuple[int, int]]:
    score = _axis_boundary_score(image, axis=axis)
    limit = len(score)
    average_span = limit / count
    search_radius = max(8, round(average_span * 0.35))
    boundaries: list[int] = []
    for index in range(1, count):
        expected = round(index * limit / count)
        start = max(1, expected - search_radius)
        end = min(limit - 1, expected + search_radius + 1)
        local = score[start:end]
        boundary = start + int(local.argmax())
        boundaries.append(boundary)

    segments: list[tuple[int, int]] = []
    start = 0
    for boundary in boundaries:
        if boundary > start:
            segments.append((start, boundary))
        start = boundary + 1
    if start < limit:
        segments.append((start, limit))
    return segments


def _axis_boundary_score(image: Image.Image, *, axis: str) -> np.ndarray:
    arr = np.asarray(image.convert("RGB")).astype(np.int16)
    if axis == "x":
        profile = arr.mean(axis=(0, 2))
        diff = np.abs(np.diff(arr, axis=1)).mean(axis=(0, 2))
    elif axis == "y":
        profile = arr.mean(axis=(1, 2))
        diff = np.abs(np.diff(arr, axis=0)).mean(axis=(1, 2))
    else:
        raise ValueError(f"Unsupported axis: {axis}")

    extreme_score = np.maximum(np.maximum(profile - 225, 25 - profile), 0)
    score = np.zeros(len(profile))
    score[: len(diff)] += diff
    score[1 : len(diff) + 1] += diff
    score += extreme_score * 2
    return score


def _segments_from_separator_groups(limit: int, groups: list[tuple[int, int]]) -> list[tuple[int, int]]:
    segments: list[tuple[int, int]] = []
    start = 0
    for separator_start, separator_end in groups:
        if separator_start > start:
            segments.append((start, separator_start))
        start = separator_end + 1
    if start < limit:
        segments.append((start, limit))
    return segments


def _separator_groups(image: Image.Image, *, axis: str) -> list[tuple[int, int]]:
    arr = np.asarray(image.convert("RGB"))
    if axis == "x":
        profile = arr.mean(axis=(0, 2))
        limit = image.width
    elif axis == "y":
        profile = arr.mean(axis=(1, 2))
        limit = image.height
    else:
        raise ValueError(f"Unsupported axis: {axis}")

    separator_indexes = np.flatnonzero((profile >= 235) | (profile <= 45))
    groups: list[tuple[int, int]] = []
    if len(separator_indexes) == 0:
        return groups

    start = int(separator_indexes[0])
    previous = start
    for raw_index in separator_indexes[1:]:
        index = int(raw_index)
        if index <= previous + 3:
            previous = index
            continue
        groups.append((start, previous))
        start = index
        previous = index
    groups.append((start, previous))

    filtered: list[tuple[int, int]] = []
    for start, end in groups:
        width = end - start + 1
        center = (start + end) / 2
        if width > 12:
            continue
        if center <= 4 or center >= limit - 5:
            continue
        filtered.append((start, end))
    return filtered


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
    parser.add_argument("--cols", type=int, default=None, help="Filmstrip columns. Defaults to separator/boundary auto-detect.")
    parser.add_argument("--rows", type=int, default=None, help="Filmstrip rows. Defaults to separator/boundary auto-detect.")
    parser.add_argument("--trim-px", type=int, default=2)
    parser.add_argument("--target-size", type=int, default=1024)
    parser.add_argument("--fps", type=int, default=None, help="Animation FPS. Defaults to 2 for short contact sheets, 7 otherwise.")
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
    if args.cols is None or args.rows is None:
        inferred_cols, inferred_rows = infer_filmstrip_grid(Image.open(saved_source))
        cols = inferred_cols
        rows = inferred_rows
    else:
        cols = args.cols
        rows = args.rows
    fps = args.fps if args.fps is not None else default_fps_for_frame_count(len(frames))
    frame_paths = save_frames(frames, output_dir)
    animation_path = save_animation(frames, output_dir, args.landform, fps=fps)

    rel_animation = animation_path.relative_to(PROJECT_ROOT / "assets" / "cinematic").as_posix()
    rel_source = saved_source.relative_to(PROJECT_ROOT).as_posix()
    entry = {
        "id": f"{args.landform}_image_sequence",
        "title": f"{title_for_landform(args.landform)} 이미지 기반 형성과정",
        "category": "representative",
        "file": rel_animation,
        "format": "animated_webp",
        "frame_count": len(frame_paths),
        "fps": fps,
        "filmstrip_cols": cols,
        "filmstrip_rows": rows,
        "mode": "filmstrip_import",
        "status": "ready",
        "source_filmstrip": rel_source,
        "description": "생성된 필름스트립을 프레임으로 분할해 만든 이미지 기반 형성과정 애니메이션입니다.",
    }
    update_metadata(entry)

    print(f"frames={len(frame_paths)}")
    print(f"grid={cols}x{rows}")
    print(f"fps={fps}")
    print(f"animation={animation_path}")
    print(f"source={saved_source}")


if __name__ == "__main__":
    main()
