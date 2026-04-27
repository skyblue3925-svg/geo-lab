"""Build smooth GIF animations from generated 4-panel terrain storyboards."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from PIL import Image, ImageFilter


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = PROJECT_ROOT / "output" / "terrain-animation-assets"
OUTPUT_ROOT = PROJECT_ROOT / "assets" / "cinematic" / "storyboard_smooth"

TARGET_SIZE = (640, 480)
FRAME_DURATION_MS = 50
HOLD_FRAMES = 6
TRANSITION_FRAMES = 12

KOREAN_TITLES = {
    "alluvial_fan": "선상지",
    "arcuate_delta": "원호상 삼각주",
    "arete": "아레트",
    "barchan": "바르한",
    "bird_foot_delta": "조족상 삼각주",
    "braided_river": "망상 하천",
    "caldera": "칼데라",
    "cirque": "권곡",
    "coastal_cliff": "해식애",
    "coastal_dune": "해안사구",
    "crater_lake": "화구호",
    "cuspate_delta": "첨상 삼각주",
    "delta": "삼각주",
    "estuary": "에스추어리",
    "fjord": "피오르",
    "free_meander": "자유곡류천",
    "horn": "호른",
    "karst_doline": "돌리네",
    "karren": "카렌",
    "lava_plateau": "용암대지",
    "mesa_butte": "메사와 뷰트",
    "pedestal_rock": "버섯바위",
    "pediment": "페디먼트",
    "playa": "플라야",
    "ria_coast": "리아스식 해안",
    "sea_arch": "해식아치",
    "shield_volcano": "순상화산",
    "spit_lagoon": "사주와 석호",
    "star_dune": "성상사구",
    "stratovolcano": "성층화산",
    "tombolo": "육계사주",
    "tower_karst": "탑 카르스트",
    "transverse_dune": "횡사구",
    "u_valley": "U자곡",
    "uvala": "우발라",
    "v_valley": "V자곡",
    "wadi": "와디",
    "waterfall": "폭포",
}


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


def contain_resize(image: Image.Image, size: tuple[int, int], margin: int = 24) -> Image.Image:
    target_w, target_h = size
    max_w = target_w - margin * 2
    max_h = target_h - margin * 2
    scale = min(max_w / image.width, max_h / image.height)
    return image.resize((round(image.width * scale), round(image.height * scale)), Image.Resampling.LANCZOS)


def stage_canvas(panel: Image.Image, zoom: float = 1.0, x_shift: int = 0, y_shift: int = 0) -> Image.Image:
    background = cover_resize(panel, TARGET_SIZE).filter(ImageFilter.GaussianBlur(radius=14))
    overlay = contain_resize(panel, TARGET_SIZE, margin=18)
    if zoom != 1.0:
        overlay = overlay.resize(
            (round(overlay.width * zoom), round(overlay.height * zoom)),
            Image.Resampling.LANCZOS,
        )
    canvas = background.copy()
    x = (TARGET_SIZE[0] - overlay.width) // 2 + x_shift
    y = (TARGET_SIZE[1] - overlay.height) // 2 + y_shift
    canvas.paste(overlay, (x, y))
    return canvas


def build_frames(panels: list[Image.Image]) -> list[Image.Image]:
    frames: list[Image.Image] = []
    prepared = [stage_canvas(panel) for panel in panels]
    for panel_index, frame in enumerate(prepared):
        for hold_idx in range(HOLD_FRAMES):
            progress = hold_idx / max(HOLD_FRAMES - 1, 1)
            zoom = 1.025 - 0.015 * progress
            shift = round((progress - 0.5) * 8)
            frames.append(stage_canvas(panels[panel_index], zoom=zoom, x_shift=shift))

        if panel_index == len(prepared) - 1:
            continue

        current = prepared[panel_index]
        next_frame = prepared[panel_index + 1]
        for transition_idx in range(1, TRANSITION_FRAMES + 1):
            alpha = ease_in_out(transition_idx / (TRANSITION_FRAMES + 1))
            frames.append(Image.blend(current, next_frame, alpha))

    return frames


def build_animation(storyboard_path: Path, *, force: bool = False) -> dict[str, str]:
    landform_id = storyboard_path.name.removesuffix("_storyboard_draft.png")
    category = storyboard_path.parents[1].name
    output_file = OUTPUT_ROOT / f"{landform_id}_storyboard_smooth.gif"
    if output_file.exists() and output_file.stat().st_size > 1024 and not force:
        frame_count = HOLD_FRAMES * 4 + TRANSITION_FRAMES * 3
        return make_metadata_entry(landform_id, category, output_file, storyboard_path, frame_count)

    image = Image.open(storyboard_path).convert("RGB")
    frames = build_frames(split_storyboard(image))

    gif_frames = [
        frame.convert("P", palette=Image.Palette.ADAPTIVE, colors=192)
        for frame in frames
    ]
    gif_frames[0].save(
        output_file,
        save_all=True,
        append_images=gif_frames[1:],
        duration=FRAME_DURATION_MS,
        loop=0,
        disposal=2,
        optimize=True,
    )

    return make_metadata_entry(landform_id, category, output_file, storyboard_path, len(frames))


def make_metadata_entry(
    landform_id: str,
    category: str,
    output_file: Path,
    storyboard_path: Path,
    frame_count: int,
) -> dict[str, str]:
    title = KOREAN_TITLES.get(landform_id, landform_id.replace("_", " "))
    return {
        "id": f"{landform_id}_storyboard_smooth",
        "title": f"{title} 이미지 기반 형성과정",
        "category": category,
        "file": f"storyboard_smooth/{output_file.name}",
        "duration": f"{frame_count * FRAME_DURATION_MS / 1000:.1f}s",
        "sources": [str(storyboard_path.relative_to(PROJECT_ROOT)).replace("\\", "/")],
        "description": "신규 4패널 생성 이미지를 단계별로 보간한 수업용 애니메이션입니다.",
        "status": "ready",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="Overwrite existing generated GIFs.")
    parser.add_argument("--only", nargs="*", help="Optional landform ids to rebuild, for example spit_lagoon coastal_dune.")
    args = parser.parse_args()

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    storyboard_paths = sorted(SOURCE_ROOT.glob("*/*/*_storyboard_draft.png"))
    if args.only:
        wanted = set(args.only)
        storyboard_paths = [
            path for path in storyboard_paths
            if path.name.removesuffix("_storyboard_draft.png") in wanted
        ]
    entries = [build_animation(path, force=args.force) for path in storyboard_paths]
    metadata_path = OUTPUT_ROOT / "metadata.json"
    if args.only and metadata_path.exists():
        manifest = json.loads(metadata_path.read_text(encoding="utf-8"))
        entry_by_id = {entry.get("id"): entry for entry in manifest.get("videos", [])}
        for entry in entries:
            entry_by_id[entry.get("id")] = entry
        manifest["videos"] = list(entry_by_id.values())
    else:
        manifest = {
            "version": "1.0",
            "description": "Generated smooth animations from terrain storyboard images.",
            "videos": entries,
        }
    metadata_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"built={len(entries)}")
    print(f"output={OUTPUT_ROOT}")


if __name__ == "__main__":
    main()
