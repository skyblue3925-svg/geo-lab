"""Build 3D terrain payloads from the local SimpleLEM simulation engine."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from app.services.terrain_3d_payload import build_terrain_3d_payload_from_history
from app.utils.lab_model import (
    build_lab_stage_history,
    configure_lab_scenario,
    create_lab_simple_lem,
)


SIMULATION_SCENARIO_LABELS: dict[str, str] = {
    "alluvial_fan": "선상지",
    "barchan": "바르한",
    "coastal_cliff": "해식애",
    "delta": "삼각주",
    "fjord": "피오르",
    "free_meander": "곡류 하천",
    "karst_doline": "카르스트 돌리네",
    "pediment": "사막 페디먼트",
    "stratovolcano": "화산",
    "u_valley": "U자곡",
    "v_valley": "V자곡",
}


def is_simulation_terrain_supported(landform_id: str) -> bool:
    return landform_id in SIMULATION_SCENARIO_LABELS


def build_simulation_terrain_3d_payload(
    landform_id: str,
    *,
    grid_size: int = 48,
    frame_count: int = 10,
) -> dict[str, Any] | None:
    return _build_simulation_terrain_3d_payload_cached(
        landform_id,
        max(8, int(grid_size)),
        max(1, int(frame_count)),
    )


@lru_cache(maxsize=64)
def _build_simulation_terrain_3d_payload_cached(
    landform_id: str,
    grid_size: int,
    frame_count: int,
) -> dict[str, Any] | None:
    scenario_label = SIMULATION_SCENARIO_LABELS.get(landform_id)
    if scenario_label is None:
        return None

    lem = create_lab_simple_lem(
        grid_size=grid_size,
        K=0.00012,
        D=0.012,
        U=0.00045,
        enable_isostasy=False,
        enable_karst=False,
        enable_exner=False,
        enable_slope_stability=False,
    )
    try:
        configure_lab_scenario(
            lem,
            selected_landform=scenario_label,
            grid_size=grid_size,
        )
    except (KeyError, ValueError):
        return None

    dt = 140.0
    lem.run(
        total_time=dt * max(frame_count - 1, 0),
        dt=dt,
        save_interval=1,
        verbose=False,
    )

    stage_history = build_lab_stage_history(
        scenario_label,
        lem.stats_history,
        lem.process_history,
    )
    payload = build_terrain_3d_payload_from_history(
        landform_id,
        history=lem.history,
        process_history=lem.process_history,
    )
    compact_stages = [_compact_stage(stage) for stage in stage_history]
    if compact_stages:
        payload["stageHistory"] = compact_stages
        payload["processLabels"] = [
            str(stage.get("title") or stage.get("caption") or "지형 변화")
            for stage in compact_stages
        ]
    else:
        payload["stageHistory"] = []
    payload["timeSteps"] = [float(value) for value in lem.time_steps]
    payload["simulationScenarioLabel"] = scenario_label
    return payload


def _compact_stage(stage: dict[str, Any]) -> dict[str, Any]:
    allowed_keys = (
        "title",
        "caption",
        "summary",
        "focus",
        "question",
        "process_order",
        "overlay_type",
        "stage_index",
        "dominant_summary",
        "balance_summary",
    )
    return {
        key: value
        for key in allowed_keys
        if (value := stage.get(key)) is not None
    }
