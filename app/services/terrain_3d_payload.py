"""Shared 3D terrain payloads for browser renderers."""

from __future__ import annotations

from typing import Any

import numpy as np

from app.services.animation_assets import sample_landform_surface_sequence, title_for_landform


RIVER_DELTA_LANDFORMS = {
    "alluvial_fan",
    "arcuate_delta",
    "bird_foot_delta",
    "braided_river",
    "cuspate_delta",
    "delta",
    "free_meander",
    "v_valley",
    "wadi",
    "waterfall",
}

GLACIAL_LANDFORMS = {"arete", "cirque", "fjord", "horn", "u_valley"}
COASTAL_LANDFORMS = {"coastal_cliff", "estuary", "ria_coast", "sea_arch", "spit_lagoon", "tombolo"}
VOLCANIC_LANDFORMS = {"caldera", "crater_lake", "lava_plateau", "shield_volcano", "stratovolcano"}
KARST_LANDFORMS = {"karst_doline", "karren", "tower_karst", "uvala"}
AEOLIAN_ARID_LANDFORMS = {"barchan", "coastal_dune", "pediment", "playa", "star_dune", "transverse_dune"}

PLAN_CAMERA_LANDFORMS = {
    "arcuate_delta",
    "bird_foot_delta",
    "braided_river",
    "cuspate_delta",
    "delta",
    "free_meander",
    "spit_lagoon",
    "tombolo",
}


def build_terrain_3d_payload(
    landform_id: str,
    *,
    grid_size: int = 48,
    frame_count: int = 10,
    height_scale: float = 18.0,
) -> dict[str, Any]:
    """Build renderer-neutral terrain frames and process overlays."""

    safe_grid_size = max(int(grid_size), 2)
    safe_frame_count = max(int(frame_count), 1)
    surfaces = sample_landform_surface_sequence(
        landform_id,
        frame_count=safe_frame_count,
        grid_size=safe_grid_size,
    )
    surfaces = _ensure_visible_formation_sequence(surfaces)
    normalized = _normalize_surface_stack(np.stack(surfaces).astype(float))

    elevation_frames = [_flatten_frame(frame) for frame in normalized]
    water_frames = [_flatten_frame(_infer_water_depth(frame, landform_id)) for frame in normalized]
    erosion_frames = [_flatten_frame(frame) for frame in _infer_erosion_frames(normalized, landform_id)]
    deposition_frames = [_flatten_frame(frame) for frame in _infer_deposition_frames(normalized, landform_id)]
    flow_frames = [_flatten_flow_frame(frame) for frame in normalized]

    family = _classify_family(landform_id)
    return {
        "landformId": landform_id,
        "title": title_for_landform(landform_id),
        "family": family,
        "gridSize": safe_grid_size,
        "surfaceFrames": elevation_frames,
        "elevationFrames": elevation_frames,
        "waterDepthFrames": water_frames,
        "erosionFrames": erosion_frames,
        "depositionFrames": deposition_frames,
        "flowFrames": flow_frames,
        "surfaceFrameCount": len(elevation_frames),
        "heightScale": float(height_scale),
        "processLabels": _process_labels_for(landform_id, family),
        "cameraProfile": _camera_profile_for(landform_id, family),
        "teachingAnnotations": _teaching_annotations_for(landform_id, family, len(elevation_frames)),
    }


def build_terrain_3d_payload_from_history(
    landform_id: str,
    *,
    history: list[np.ndarray],
    process_history: list[dict[str, Any]] | None = None,
    height_scale: float = 18.0,
) -> dict[str, Any]:
    """Build a shared 3D payload from simulation history and process fields."""

    if not history:
        raise ValueError("history must contain at least one elevation frame")

    raw_frames = [np.asarray(frame, dtype=float) for frame in history]
    first_shape = raw_frames[0].shape
    if len(first_shape) != 2 or first_shape[0] != first_shape[1]:
        raise ValueError("history frames must be square 2D arrays")
    if any(frame.shape != first_shape for frame in raw_frames):
        raise ValueError("all history frames must have the same shape")

    grid_size = int(first_shape[0])
    normalized = _normalize_surface_stack(np.stack(raw_frames).astype(float))
    family = _classify_family(landform_id)

    erosion_fields = []
    deposition_fields = []
    for idx, frame in enumerate(normalized):
        process_fields = process_history[idx] if process_history and idx < len(process_history) else {}
        erosion = _process_field(process_fields, ("total_erosion", "erosion"), frame.shape)
        deposition = _process_field(process_fields, ("deposition",), frame.shape)
        if not np.any(erosion):
            erosion = _infer_erosion_frames(normalized[max(idx - 1, 0): idx + 1], landform_id)[-1]
        if not np.any(deposition):
            deposition = _infer_deposition_frames(normalized[max(idx - 1, 0): idx + 1], landform_id)[-1]
        erosion_fields.append(_normalize_field(erosion))
        deposition_fields.append(_normalize_field(deposition))

    elevation_frames = [_flatten_frame(frame) for frame in normalized]
    return {
        "landformId": landform_id,
        "title": title_for_landform(landform_id),
        "family": family,
        "modelSource": "simulation_history",
        "gridSize": grid_size,
        "surfaceFrames": elevation_frames,
        "elevationFrames": elevation_frames,
        "waterDepthFrames": [_flatten_frame(_infer_water_depth(frame, landform_id)) for frame in normalized],
        "erosionFrames": [_flatten_frame(frame) for frame in erosion_fields],
        "depositionFrames": [_flatten_frame(frame) for frame in deposition_fields],
        "flowFrames": [_flatten_flow_frame(frame) for frame in normalized],
        "surfaceFrameCount": len(elevation_frames),
        "heightScale": float(height_scale),
        "processLabels": _process_labels_for(landform_id, family),
        "cameraProfile": _camera_profile_for(landform_id, family),
        "teachingAnnotations": _teaching_annotations_for(landform_id, family, len(elevation_frames)),
    }


def _normalize_surface_stack(stacked: np.ndarray) -> np.ndarray:
    z_min = float(np.nanmin(stacked))
    z_max = float(np.nanmax(stacked))
    span = max(z_max - z_min, 1e-6)
    return np.clip((stacked - z_min) / span, 0.0, 1.0)


def _ensure_visible_formation_sequence(surfaces: list[np.ndarray]) -> list[np.ndarray]:
    if len(surfaces) <= 1:
        return surfaces

    stacked = np.stack([np.asarray(surface, dtype=float) for surface in surfaces]).astype(float)
    normalized = _normalize_surface_stack(stacked)
    start_end_delta = float(np.mean(np.abs(normalized[-1] - normalized[0])))
    if start_end_delta >= 0.02:
        return surfaces

    final_surface = np.nan_to_num(stacked[-1], nan=0.0, posinf=0.0, neginf=0.0)
    relief = float(np.nanmax(final_surface) - np.nanmin(final_surface))
    if relief <= 1e-6:
        return surfaces

    base_level = float(np.nanquantile(final_surface, 0.08))
    final_surface = _expand_sparse_relief(final_surface, base_level)
    base_surface = np.full_like(final_surface, base_level)
    return [
        (base_surface * (1.0 - progress)) + (final_surface * progress)
        for progress in np.linspace(0.0, 1.0, len(surfaces))
    ]


def _expand_sparse_relief(surface: np.ndarray, base_level: float) -> np.ndarray:
    relief = np.clip(np.asarray(surface, dtype=float) - base_level, 0.0, None)
    max_relief = float(np.max(relief)) if relief.size else 0.0
    if max_relief <= 1e-6:
        return surface

    active_fraction = float(np.mean((relief / max_relief) > 0.08))
    if active_fraction >= 0.08:
        return surface

    expanded = relief.copy()
    for _ in range(4):
        padded = np.pad(expanded, 1, mode="edge")
        blurred = (
            (padded[1:-1, 1:-1] * 4.0)
            + padded[:-2, 1:-1]
            + padded[2:, 1:-1]
            + padded[1:-1, :-2]
            + padded[1:-1, 2:]
        ) / 8.0
        expanded = np.maximum(expanded, blurred * 0.92)

    return np.maximum(surface, base_level + expanded)


def _process_field(process_fields: dict[str, Any], keys: tuple[str, ...], shape: tuple[int, int]) -> np.ndarray:
    for key in keys:
        if key not in process_fields:
            continue
        field = np.asarray(process_fields[key], dtype=float)
        if field.shape == shape:
            return _normalize_field(field)
    return np.zeros(shape, dtype=float)


def _flatten_frame(frame: np.ndarray) -> list[float]:
    return np.flipud(np.asarray(frame, dtype=float)).reshape(-1).round(5).tolist()


def _classify_family(landform_id: str) -> str:
    if landform_id in RIVER_DELTA_LANDFORMS:
        return "river_delta"
    if landform_id in COASTAL_LANDFORMS:
        return "coastal_marine"
    if landform_id in GLACIAL_LANDFORMS:
        return "glacial"
    if landform_id in VOLCANIC_LANDFORMS:
        return "volcanic"
    if landform_id in KARST_LANDFORMS:
        return "karst"
    if landform_id in AEOLIAN_ARID_LANDFORMS:
        return "aeolian_arid"
    return "structural_differential"


def _infer_water_depth(frame: np.ndarray, landform_id: str) -> np.ndarray:
    if landform_id in AEOLIAN_ARID_LANDFORMS and landform_id not in {"playa", "wadi"}:
        return np.zeros_like(frame)

    low_threshold = float(np.quantile(frame, 0.22))
    valley_water = np.clip(low_threshold - frame, 0.0, None)
    if float(np.max(valley_water)) > 0.0:
        valley_water = valley_water / max(float(np.max(valley_water)), 1e-6)

    if landform_id in {"delta", "arcuate_delta", "bird_foot_delta", "cuspate_delta", "estuary", "ria_coast"}:
        y = np.linspace(0.0, 1.0, frame.shape[0])[:, None]
        seaward = np.repeat(np.clip(y - 0.42, 0.0, 1.0), frame.shape[1], axis=1)
        return np.maximum(valley_water, seaward)

    if landform_id in {"crater_lake", "fjord", "spit_lagoon", "tombolo", "playa"}:
        return valley_water

    return valley_water * 0.7


def _infer_erosion_frames(frames: np.ndarray, landform_id: str) -> list[np.ndarray]:
    erosion_frames: list[np.ndarray] = []
    previous = frames[0]
    for idx, frame in enumerate(frames):
        change = np.clip(previous - frame, 0.0, None) if idx else np.zeros_like(frame)
        fallback = _focused_gradient(frame)
        if landform_id in {"v_valley", "waterfall", "free_meander", "braided_river"}:
            change = np.maximum(change, fallback * (0.25 + idx / max(len(frames) - 1, 1)))
        erosion_frames.append(_normalize_field(change))
        previous = frame
    return erosion_frames


def _infer_deposition_frames(frames: np.ndarray, landform_id: str) -> list[np.ndarray]:
    deposition_frames: list[np.ndarray] = []
    previous = frames[0]
    for idx, frame in enumerate(frames):
        change = np.clip(frame - previous, 0.0, None) if idx else np.zeros_like(frame)
        if landform_id in {"alluvial_fan", "delta", "arcuate_delta", "bird_foot_delta", "cuspate_delta"}:
            low_slope = 1.0 - _focused_gradient(frame)
            lowland = np.clip(0.58 - frame, 0.0, None)
            change = np.maximum(change, low_slope * lowland * (0.2 + idx / max(len(frames) - 1, 1)))
        deposition_frames.append(_normalize_field(change))
        previous = frame
    return deposition_frames


def _focused_gradient(frame: np.ndarray) -> np.ndarray:
    dy, dx = np.gradient(frame)
    return _normalize_field(np.sqrt((dx * dx) + (dy * dy)))


def _normalize_field(field: np.ndarray) -> np.ndarray:
    clean = np.nan_to_num(np.asarray(field, dtype=float), nan=0.0, posinf=0.0, neginf=0.0)
    max_value = float(np.max(clean)) if clean.size else 0.0
    if max_value <= 1e-9:
        return np.zeros_like(clean)
    return np.clip(clean / max_value, 0.0, 1.0)


def _flatten_flow_frame(frame: np.ndarray) -> dict[str, list[float]]:
    dy, dx = np.gradient(frame)
    magnitude = np.sqrt((dx * dx) + (dy * dy))
    magnitude = np.where(magnitude <= 1e-9, 1.0, magnitude)
    flow_x = -dx / magnitude
    flow_y = -dy / magnitude
    return {
        "x": _flatten_frame(flow_x),
        "y": _flatten_frame(flow_y),
    }


def _process_labels_for(landform_id: str, family: str) -> list[str]:
    if landform_id == "v_valley":
        return ["하방 침식", "하천 유로", "사면 조정"]
    if family == "river_delta":
        return ["하천 운반", "퇴적", "분류"]
    if family == "coastal_marine":
        return ["파랑 침식", "연안류", "해수면"]
    if family == "glacial":
        return ["빙하 침식", "과굴", "빙하 퇴적"]
    if family == "volcanic":
        return ["분출", "용암 축적", "붕괴"]
    if family == "karst":
        return ["용식", "지하 배수", "잔류 지형"]
    if family == "aeolian_arid":
        return ["바람 운반", "퇴적", "건조 침식"]
    return ["차별 침식", "암석 경도", "구조 지형"]


def _camera_profile_for(landform_id: str, family: str) -> dict[str, Any]:
    if landform_id in PLAN_CAMERA_LANDFORMS:
        return {"mode": "plan", "reason": "분류, 퇴적 전면, 평면 패턴 관찰"}
    if landform_id in {"v_valley", "u_valley", "fjord", "waterfall"}:
        return {"mode": "valley_follow", "reason": "곡저와 사면 단면 관찰"}
    if family in {"volcanic", "karst", "structural_differential"}:
        return {"mode": "low_oblique", "reason": "높이 차와 경계면 관찰"}
    return {"mode": "low_oblique", "reason": "형태와 과정 overlay 동시 관찰"}


def _teaching_annotations_for(landform_id: str, family: str, frame_count: int) -> list[dict[str, Any]]:
    midpoint = max(frame_count // 2, 0)
    final_frame = max(frame_count - 1, 0)
    labels = _process_labels_for(landform_id, family)
    return [
        {
            "frame": 0,
            "label": labels[0],
            "text": "처음에는 지형의 기준면과 지배 작용이 어디에서 시작되는지 확인합니다.",
        },
        {
            "frame": midpoint,
            "label": labels[min(1, len(labels) - 1)],
            "text": "중간 단계에서는 침식과 퇴적이 서로 다른 위치에 나타나는지 봅니다.",
        },
        {
            "frame": final_frame,
            "label": labels[-1],
            "text": "마지막에는 과정의 누적 결과가 대표 지형 형태로 읽히는지 확인합니다.",
        },
    ]
