"""Asset access helpers for generated terrain formation animations.

This module keeps filesystem knowledge out of Streamlit pages. Pages should ask
for storyboard assets, animation metadata, or image panels here instead of
repeating path and JSON handling.
"""

from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image


PROJECT_ROOT = Path(__file__).resolve().parents[2]
GENERATED_ASSET_ROOT = PROJECT_ROOT / "output" / "terrain-animation-assets"
CINEMATIC_ROOT = PROJECT_ROOT / "assets" / "cinematic"
STORYBOARD_SMOOTH_ROOT = CINEMATIC_ROOT / "storyboard_smooth"
STORYBOARD_CINEMATIC_ROOT = CINEMATIC_ROOT / "storyboard_cinematic"
IMAGE_SEQUENCE_ROOT = CINEMATIC_ROOT / "image_sequence"

IMAGE_MIME_TYPES = {
    ".gif": "image/gif",
    ".jpeg": "image/jpeg",
    ".jpg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
}

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

LANDFORM_GROUP_ORDER = (
    "river",
    "delta",
    "glacial",
    "volcanic",
    "karst",
    "arid",
    "coastal",
)

LANDFORM_GROUP_LABELS = {
    "river": "하천 지형",
    "delta": "하구·삼각주 지형",
    "glacial": "빙하 지형",
    "volcanic": "화산 지형",
    "karst": "카르스트 지형",
    "arid": "건조 지형",
    "coastal": "해안 지형",
}

LANDFORM_GROUP_BY_ID = {
    "alluvial_fan": "river",
    "braided_river": "river",
    "free_meander": "river",
    "v_valley": "river",
    "waterfall": "river",
    "arcuate_delta": "delta",
    "bird_foot_delta": "delta",
    "cuspate_delta": "delta",
    "delta": "delta",
    "estuary": "delta",
    "arete": "glacial",
    "cirque": "glacial",
    "fjord": "glacial",
    "horn": "glacial",
    "u_valley": "glacial",
    "caldera": "volcanic",
    "crater_lake": "volcanic",
    "lava_plateau": "volcanic",
    "shield_volcano": "volcanic",
    "stratovolcano": "volcanic",
    "karren": "karst",
    "karst_doline": "karst",
    "tower_karst": "karst",
    "uvala": "karst",
    "barchan": "arid",
    "mesa_butte": "arid",
    "pedestal_rock": "arid",
    "pediment": "arid",
    "playa": "arid",
    "star_dune": "arid",
    "transverse_dune": "arid",
    "wadi": "arid",
    "coastal_cliff": "coastal",
    "coastal_dune": "coastal",
    "ria_coast": "coastal",
    "sea_arch": "coastal",
    "spit_lagoon": "coastal",
    "tombolo": "coastal",
}


@dataclass(frozen=True)
class StoryboardAsset:
    landform_id: str
    title: str
    category: str
    storyboard_path: Path
    prompt_path: Path | None
    animation_path: Path | None
    smooth_animation_path: Path | None
    cinematic_animation_path: Path | None
    image_sequence_animation_path: Path | None
    image_sequence_dir: Path | None
    image_sequence_plan_path: Path | None

    @property
    def has_prompt(self) -> bool:
        return self.prompt_path is not None and self.prompt_path.exists()

    @property
    def has_animation(self) -> bool:
        return self.animation_path is not None and self.animation_path.exists()

    @property
    def has_smooth_animation(self) -> bool:
        return self.smooth_animation_path is not None and self.smooth_animation_path.exists()

    @property
    def has_cinematic_animation(self) -> bool:
        return self.cinematic_animation_path is not None and self.cinematic_animation_path.exists()

    @property
    def has_image_sequence(self) -> bool:
        return self.image_sequence_animation_path is not None and self.image_sequence_animation_path.exists()

    @property
    def has_image_sequence_plan(self) -> bool:
        return self.image_sequence_plan_path is not None and self.image_sequence_plan_path.exists()


@dataclass(frozen=True)
class ImageSequenceGifAsset:
    landform_id: str
    title: str
    category: str
    gif_path: Path
    source_webp_path: Path
    size_bytes: int
    frame_count: int
    width: int
    height: int


def title_for_landform(landform_id: str) -> str:
    return KOREAN_TITLES.get(landform_id, landform_id.replace("_", " "))


def landform_group_id_for_landform(landform_id: str) -> str:
    return LANDFORM_GROUP_BY_ID.get(landform_id, "other")


def landform_group_label_for_landform(landform_id: str) -> str:
    group_id = landform_group_id_for_landform(landform_id)
    return LANDFORM_GROUP_LABELS.get(group_id, "기타 지형")


def ordered_landform_group_labels() -> list[str]:
    return [LANDFORM_GROUP_LABELS[group_id] for group_id in LANDFORM_GROUP_ORDER]


def read_json(path: Path, fallback: dict[str, Any] | None = None) -> dict[str, Any]:
    if fallback is None:
        fallback = {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return fallback


def find_generated_storyboard_path(landform_key: str) -> Path | None:
    matches = sorted(GENERATED_ASSET_ROOT.glob(f"*/*/{landform_key}_storyboard_draft.png"))
    return matches[0] if matches else None


def find_generated_prompt_path(landform_key: str) -> Path | None:
    matches = sorted(GENERATED_ASSET_ROOT.glob(f"*/*/{landform_key}_prompt.md"))
    return matches[0] if matches else None


def find_image_sequence_dir(landform_key: str) -> Path | None:
    candidate = IMAGE_SEQUENCE_ROOT / landform_key
    return candidate if candidate.exists() else None


def find_image_sequence_animation_path(landform_key: str) -> Path | None:
    image_sequence_dir = find_image_sequence_dir(landform_key)
    if image_sequence_dir is None:
        return None
    candidate = image_sequence_dir / f"{landform_key}_image_sequence.webp"
    return candidate if candidate.exists() else None


def find_image_sequence_gif_path(landform_key: str) -> Path | None:
    image_sequence_dir = find_image_sequence_dir(landform_key)
    if image_sequence_dir is None:
        return None
    candidate = image_sequence_dir / f"{landform_key}_image_sequence.gif"
    return candidate if candidate.exists() else None


def image_sequence_gif_output_path(landform_key: str) -> Path:
    return IMAGE_SEQUENCE_ROOT / landform_key / f"{landform_key}_image_sequence.gif"


def resolve_cinematic_media_path(file_name: str) -> Path:
    return CINEMATIC_ROOT / file_name


def load_cinematic_metadata() -> dict[str, Any]:
    metadata = read_json(CINEMATIC_ROOT / "metadata.json", {"videos": []})
    seen_video_ids = {video.get("id") for video in metadata.get("videos", [])}
    for metadata_path in (
        IMAGE_SEQUENCE_ROOT / "metadata.json",
        STORYBOARD_CINEMATIC_ROOT / "metadata.json",
        STORYBOARD_SMOOTH_ROOT / "metadata.json",
    ):
        extra_metadata = read_json(metadata_path, {})
        for video in extra_metadata.get("videos", []):
            if video.get("id") not in seen_video_ids:
                metadata.setdefault("videos", []).append(video)
                seen_video_ids.add(video.get("id"))
    return metadata


def load_image_sequence_metadata() -> dict[str, Any]:
    return read_json(IMAGE_SEQUENCE_ROOT / "metadata.json", {"videos": []})


def list_storyboard_assets() -> list[StoryboardAsset]:
    assets: list[StoryboardAsset] = []
    for storyboard_path in sorted(GENERATED_ASSET_ROOT.glob("*/*/*_storyboard_draft.png")):
        landform_id = storyboard_path.name.removesuffix("_storyboard_draft.png")
        prompt_path = storyboard_path.with_name(f"{landform_id}_prompt.md")
        smooth_animation_path = STORYBOARD_SMOOTH_ROOT / f"{landform_id}_storyboard_smooth.gif"
        cinematic_animation_path = STORYBOARD_CINEMATIC_ROOT / f"{landform_id}_storyboard_cinematic.webp"
        image_sequence_dir = IMAGE_SEQUENCE_ROOT / landform_id
        image_sequence_animation_path = image_sequence_dir / f"{landform_id}_image_sequence.webp"
        image_sequence_plan_path = image_sequence_dir / "ai_inbetween_plan.json"
        if image_sequence_animation_path.exists():
            animation_path = image_sequence_animation_path
        elif cinematic_animation_path.exists():
            animation_path = cinematic_animation_path
        else:
            animation_path = smooth_animation_path
        assets.append(
            StoryboardAsset(
                landform_id=landform_id,
                title=title_for_landform(landform_id),
                category=storyboard_path.parents[1].name,
                storyboard_path=storyboard_path,
                prompt_path=prompt_path if prompt_path.exists() else None,
                animation_path=animation_path if animation_path.exists() else None,
                smooth_animation_path=smooth_animation_path if smooth_animation_path.exists() else None,
                cinematic_animation_path=cinematic_animation_path if cinematic_animation_path.exists() else None,
                image_sequence_animation_path=image_sequence_animation_path if image_sequence_animation_path.exists() else None,
                image_sequence_dir=image_sequence_dir if image_sequence_dir.exists() else None,
                image_sequence_plan_path=image_sequence_plan_path if image_sequence_plan_path.exists() else None,
            )
        )
    seen = {asset.landform_id for asset in assets}
    for image_sequence_dir in sorted(path for path in IMAGE_SEQUENCE_ROOT.iterdir() if path.is_dir() and not path.name.startswith("_")):
        landform_id = image_sequence_dir.name
        if landform_id in seen:
            continue
        filmstrip_path = find_image_sequence_filmstrip_path_for_landform(landform_id)
        if filmstrip_path is None:
            continue
        prompt_path = find_generated_prompt_path(landform_id)
        cinematic_animation_path = STORYBOARD_CINEMATIC_ROOT / f"{landform_id}_storyboard_cinematic.webp"
        smooth_animation_path = STORYBOARD_SMOOTH_ROOT / f"{landform_id}_storyboard_smooth.gif"
        image_sequence_animation_path = image_sequence_dir / f"{landform_id}_image_sequence.webp"
        image_sequence_plan_path = image_sequence_dir / "ai_inbetween_plan.json"
        assets.append(
            StoryboardAsset(
                landform_id=landform_id,
                title=title_for_landform(landform_id),
                category="image_sequence",
                storyboard_path=filmstrip_path,
                prompt_path=prompt_path if prompt_path is not None and prompt_path.exists() else None,
                animation_path=image_sequence_animation_path if image_sequence_animation_path.exists() else None,
                smooth_animation_path=smooth_animation_path if smooth_animation_path.exists() else None,
                cinematic_animation_path=cinematic_animation_path if cinematic_animation_path.exists() else None,
                image_sequence_animation_path=image_sequence_animation_path if image_sequence_animation_path.exists() else None,
                image_sequence_dir=image_sequence_dir,
                image_sequence_plan_path=image_sequence_plan_path if image_sequence_plan_path.exists() else None,
            )
        )
    return assets


def get_asset_counts() -> dict[str, int]:
    assets = list_storyboard_assets()
    return {
        "storyboards": len(assets),
        "prompts": sum(1 for asset in assets if asset.has_prompt),
        "animations": sum(1 for asset in assets if asset.has_animation),
        "smooth_gifs": sum(1 for asset in assets if asset.has_smooth_animation),
        "cinematic_webps": sum(1 for asset in assets if asset.has_cinematic_animation),
        "image_sequences": sum(1 for asset in assets if asset.has_image_sequence),
        "image_sequence_plans": sum(1 for asset in assets if asset.has_image_sequence_plan),
    }


def _inspect_image(path: Path) -> tuple[int, int, int]:
    try:
        image = Image.open(path)
        width, height = image.size
        frame_count = int(getattr(image, "n_frames", 1))
        return width, height, frame_count
    except Exception:
        return 0, 0, 0


def list_image_sequence_gif_assets() -> list[ImageSequenceGifAsset]:
    gif_assets: list[ImageSequenceGifAsset] = []
    for source_webp_path in sorted(IMAGE_SEQUENCE_ROOT.glob("*/*_image_sequence.webp")):
        landform_id = source_webp_path.parent.name
        gif_path = image_sequence_gif_output_path(landform_id)
        if not gif_path.exists():
            continue
        width, height, frame_count = _inspect_image(gif_path)
        gif_assets.append(
            ImageSequenceGifAsset(
                landform_id=landform_id,
                title=title_for_landform(landform_id),
                category=landform_group_label_for_landform(landform_id),
                gif_path=gif_path,
                source_webp_path=source_webp_path,
                size_bytes=gif_path.stat().st_size,
                frame_count=frame_count,
                width=width,
                height=height,
            )
        )
    return gif_assets


def get_storyboard_asset(landform_id: str) -> StoryboardAsset | None:
    for asset in list_storyboard_assets():
        if asset.landform_id == landform_id:
            return asset
    return None


def find_image_sequence_filmstrip_path(asset: StoryboardAsset) -> Path | None:
    if asset.image_sequence_dir is None:
        return None
    filmstrip_dir = asset.image_sequence_dir / "filmstrip"
    if not filmstrip_dir.exists():
        return None
    matches = sorted(filmstrip_dir.glob("*.png"))
    return matches[0] if matches else None


def find_image_sequence_filmstrip_path_for_landform(landform_id: str) -> Path | None:
    image_sequence_dir = find_image_sequence_dir(landform_id)
    if image_sequence_dir is None:
        return None
    filmstrip_dir = image_sequence_dir / "filmstrip"
    if not filmstrip_dir.exists():
        return None
    matches = sorted(filmstrip_dir.glob("*.png"))
    return matches[0] if matches else None


def get_image_sequence_frame_paths(asset: StoryboardAsset, *, max_frames: int | None = None) -> list[Path]:
    if asset.image_sequence_dir is None:
        return []
    frame_dir = asset.image_sequence_dir / "frames"
    if not frame_dir.exists():
        return []
    frames = sorted(frame_dir.glob("frame_*.png"))
    if max_frames is None or max_frames <= 0 or len(frames) <= max_frames:
        return frames

    selected: list[Path] = []
    for idx in np.linspace(0, len(frames) - 1, num=max_frames):
        selected.append(frames[int(round(float(idx)))])
    deduped: list[Path] = []
    seen: set[Path] = set()
    for frame in selected:
        if frame not in seen:
            deduped.append(frame)
            seen.add(frame)
    return deduped


def get_landform_asset_bundle(landform_id: str) -> dict[str, Any] | None:
    asset = get_storyboard_asset(landform_id)
    if asset is None:
        return None

    image_sequence_metadata = load_image_sequence_metadata()
    image_sequence_entry = next(
        (entry for entry in image_sequence_metadata.get("videos", []) if entry.get("id") == f"{landform_id}_image_sequence"),
        None,
    )

    return {
        "asset": asset,
        "filmstrip_path": find_image_sequence_filmstrip_path(asset),
        "frame_paths": get_image_sequence_frame_paths(asset),
        "image_sequence_entry": image_sequence_entry,
    }


@lru_cache(maxsize=256)
def _sample_landform_surface_cached(landform_id: str, stage_key: int, grid_size: int) -> np.ndarray:
    from engine.ideal_landforms import ANIMATED_LANDFORM_GENERATORS, IDEAL_LANDFORM_GENERATORS

    stage = stage_key / 1000.0
    generator = ANIMATED_LANDFORM_GENERATORS.get(landform_id) or IDEAL_LANDFORM_GENERATORS.get(landform_id)
    if generator is None:
        return np.zeros((grid_size, grid_size), dtype=float)

    try:
        result = generator(grid_size, stage, return_metadata=True)
    except TypeError:
        try:
            result = generator(grid_size, stage)
        except TypeError:
            result = generator(grid_size)

    if isinstance(result, tuple):
        result = result[0]
    return np.asarray(result, dtype=float)


def sample_landform_surface(landform_id: str, stage: float, *, grid_size: int = 48) -> np.ndarray:
    stage_key = int(round(float(np.clip(stage, 0.0, 1.0)) * 1000))
    return np.array(_sample_landform_surface_cached(landform_id, stage_key, grid_size), copy=True)


def sample_landform_surface_sequence(
    landform_id: str,
    *,
    frame_count: int = 10,
    grid_size: int = 48,
) -> list[np.ndarray]:
    if frame_count <= 1:
        return [sample_landform_surface(landform_id, 0.0, grid_size=grid_size)]
    return [
        sample_landform_surface(landform_id, idx / (frame_count - 1), grid_size=grid_size)
        for idx in range(frame_count)
    ]


def read_prompt_text(asset: StoryboardAsset) -> str:
    if not asset.has_prompt or asset.prompt_path is None:
        return ""
    return asset.prompt_path.read_text(encoding="utf-8")


def image_mime_type(path: Path) -> str:
    return IMAGE_MIME_TYPES.get(path.suffix.lower(), "application/octet-stream")


@lru_cache(maxsize=64)
def _read_image_data_uri(path_text: str, mtime_ns: int, size: int) -> str:
    path = Path(path_text)
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{image_mime_type(path)};base64,{encoded}"


def read_image_data_uri(path: Path) -> str:
    stat = path.stat()
    return _read_image_data_uri(str(path), stat.st_mtime_ns, stat.st_size)


def load_storyboard_panel_image(landform_key: str, stage: float, *, crop_label_band: bool = True) -> Image.Image | None:
    storyboard_path = find_generated_storyboard_path(landform_key)

    try:
        if storyboard_path is not None:
            image = Image.open(storyboard_path).convert("RGB")
            width, height = image.size
            panel_idx = int(np.clip(round(float(stage) * 3), 0, 3))
            left = round(panel_idx * width / 4)
            right = round((panel_idx + 1) * width / 4)
            top = round(height * 0.14) if crop_label_band else 0
            return image.crop((left, top, right, height))

        filmstrip_path = find_image_sequence_filmstrip_path_for_landform(landform_key)
        if filmstrip_path is None:
            return None
        image = Image.open(filmstrip_path).convert("RGB")
        width, height = image.size
        frame_idx = int(np.clip(round(float(stage) * 29), 0, 29))
        col = frame_idx % 5
        row = frame_idx // 5
        left = round(col * width / 5)
        right = round((col + 1) * width / 5)
        top = round(row * height / 6)
        bottom = round((row + 1) * height / 6)
        return image.crop((left, top, right, bottom))
    except Exception:
        return None


def load_generated_storyboard_texture(landform_key: str, stage: float) -> np.ndarray | None:
    panel = load_storyboard_panel_image(landform_key, stage, crop_label_band=True)
    if panel is None:
        return None
    return np.asarray(panel, dtype=np.uint8)
