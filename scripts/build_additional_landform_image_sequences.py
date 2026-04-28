"""Build additional terrain image sequences without any external image API.

Pipeline:
1. Read docs/TERRAIN_ADDITIONAL_IMAGE_SEQUENCE_SPECS.json.
2. Render local procedural 5x6 filmstrips from the terrain surface generators.
3. Import each filmstrip into frames plus animated WebP.
4. Build compact GIFs for the classroom gallery.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = PROJECT_ROOT / "docs" / "TERRAIN_ADDITIONAL_IMAGE_SEQUENCE_SPECS.json"
OUTPUT_ROOT = PROJECT_ROOT / "assets" / "cinematic" / "image_sequence"
DEFAULT_COLS = 5
DEFAULT_ROWS = 6
DEFAULT_FRAMES = 30
DEFAULT_FPS = 7
DEFAULT_TARGET_SIZE = 768
DEFAULT_GIF_MAX_SIZE = 384

sys.path.insert(0, str(PROJECT_ROOT))

from scripts.build_image_sequence_gifs import convert_webp_to_gif  # noqa: E402
from scripts.build_procedural_landform_filmstrips import build_filmstrip  # noqa: E402
from scripts.import_filmstrip_sequence import (  # noqa: E402
    save_animation,
    save_frames,
    split_filmstrip,
    title_for_landform,
    update_metadata,
)


def load_specs() -> list[dict[str, object]]:
    return json.loads(SPEC_PATH.read_text(encoding="utf-8"))["landforms"]


def filter_specs(specs: list[dict[str, object]], only: str | None) -> list[dict[str, object]]:
    if not only:
        return specs

    wanted = {item.strip() for item in only.split(",") if item.strip()}
    available = {str(item["id"]) for item in specs}
    unknown = sorted(wanted - available)
    if unknown:
        raise ValueError(f"Unknown landform ids: {', '.join(unknown)}")
    return [item for item in specs if str(item["id"]) in wanted]


def import_generated_filmstrip(
    landform_id: str,
    filmstrip_path: Path,
    *,
    cols: int,
    rows: int,
    trim_px: int,
    target_size: int,
    fps: int,
) -> Path:
    output_dir = OUTPUT_ROOT / landform_id
    output_dir.mkdir(parents=True, exist_ok=True)

    frames = split_filmstrip(
        filmstrip_path,
        cols=cols,
        rows=rows,
        trim_px=trim_px,
        target_size=target_size,
    )
    frame_paths = save_frames(frames, output_dir)
    animation_path = save_animation(frames, output_dir, landform_id, fps=fps)

    rel_animation = animation_path.relative_to(PROJECT_ROOT / "assets" / "cinematic").as_posix()
    rel_source = filmstrip_path.relative_to(PROJECT_ROOT).as_posix()
    update_metadata(
        {
            "id": f"{landform_id}_image_sequence",
            "title": f"{title_for_landform(landform_id)} 이미지 기반 형성과정",
            "category": "representative",
            "file": rel_animation,
            "format": "animated_webp",
            "frame_count": len(frame_paths),
            "fps": fps,
            "filmstrip_cols": cols,
            "filmstrip_rows": rows,
            "mode": "procedural_filmstrip_import",
            "status": "ready",
            "source_filmstrip": rel_source,
            "description": "API 없이 로컬 절차적 지형 렌더러로 만든 이미지 기반 형성과정 애니메이션입니다.",
        }
    )
    return animation_path


def build_landform(spec: dict[str, object], args: argparse.Namespace) -> tuple[Path, Path, Path | None]:
    landform_id = str(spec["id"])
    filmstrip_path = build_filmstrip(
        landform_id,
        frame_count=args.frames,
        cols=args.cols,
        rows=args.rows,
        cell_size=args.cell_size,
        gutter=args.gutter,
    )
    animation_path = import_generated_filmstrip(
        landform_id,
        filmstrip_path,
        cols=args.cols,
        rows=args.rows,
        trim_px=args.trim_px,
        target_size=args.target_size,
        fps=args.fps,
    )
    gif_path = None
    if not args.skip_gif:
        gif_path = convert_webp_to_gif(
            animation_path,
            max_size=args.gif_max_size,
            fallback_duration=round(1000 / max(args.fps, 1)),
            force=args.force,
        )
    return filmstrip_path, animation_path, gif_path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build additional landform image sequences locally, without an API key."
    )
    parser.add_argument("--only", help="Comma-separated landform ids to build.")
    parser.add_argument("--frames", type=int, default=DEFAULT_FRAMES)
    parser.add_argument("--cols", type=int, default=DEFAULT_COLS)
    parser.add_argument("--rows", type=int, default=DEFAULT_ROWS)
    parser.add_argument("--cell-size", type=int, default=384)
    parser.add_argument("--gutter", type=int, default=4)
    parser.add_argument("--trim-px", type=int, default=2)
    parser.add_argument("--target-size", type=int, default=DEFAULT_TARGET_SIZE)
    parser.add_argument("--fps", type=int, default=DEFAULT_FPS)
    parser.add_argument("--gif-max-size", type=int, default=DEFAULT_GIF_MAX_SIZE)
    parser.add_argument("--skip-gif", action="store_true")
    parser.add_argument("--force", action="store_true", help="Rebuild GIF even if it is newer than the WebP.")
    args = parser.parse_args()

    if args.frames != args.cols * args.rows:
        raise ValueError("frames must match cols * rows")

    specs = filter_specs(load_specs(), args.only)
    built = []
    for spec in specs:
        landform_id = str(spec["id"])
        filmstrip_path, animation_path, gif_path = build_landform(spec, args)
        built.append(landform_id)
        parts = [
            f"filmstrip={filmstrip_path.relative_to(PROJECT_ROOT)}",
            f"webp={animation_path.relative_to(PROJECT_ROOT)}",
        ]
        if gif_path is not None:
            parts.append(f"gif={gif_path.relative_to(PROJECT_ROOT)}")
        print(f"{landform_id}: " + " | ".join(parts))

    print(f"built={len(built)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
