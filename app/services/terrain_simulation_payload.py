"""Build 3D terrain payloads from the local SimpleLEM simulation engine."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Any

import numpy as np

from app.services.terrain_3d_payload import build_terrain_3d_payload_from_history
from app.utils.lab_model import (
    build_lab_stage_history,
    configure_lab_scenario,
    create_lab_simple_lem,
)
from engine.ideal_landforms import IDEAL_LANDFORM_GENERATORS


@dataclass(frozen=True)
class SimulationScenario:
    scenario_label: str
    family: str
    support_level: str
    caveat: str


DIRECT_CAVEAT = "SimpleLEM 물리장과 해당 지형의 이상 지형 표면을 함께 사용합니다."
PROXY_CAVEAT = "현재 엔진의 대표 물리과정으로 근사한 교육용 3D 시뮬레이션입니다."


SIMULATION_SCENARIOS: dict[str, SimulationScenario] = {
    "alluvial_fan": SimulationScenario("선상지", "river_delta", "direct_simple_lem", DIRECT_CAVEAT),
    "arcuate_delta": SimulationScenario("삼각주", "river_delta", "process_proxy", PROXY_CAVEAT),
    "arete": SimulationScenario("U자곡", "glacial", "process_proxy", PROXY_CAVEAT),
    "barchan": SimulationScenario("바르한", "aeolian_arid", "direct_simple_lem", DIRECT_CAVEAT),
    "bird_foot_delta": SimulationScenario("삼각주", "river_delta", "process_proxy", PROXY_CAVEAT),
    "braided_river": SimulationScenario("평원", "river_delta", "process_proxy", PROXY_CAVEAT),
    "caldera": SimulationScenario("화산", "volcanic", "process_proxy", PROXY_CAVEAT),
    "cirque": SimulationScenario("U자곡", "glacial", "process_proxy", PROXY_CAVEAT),
    "coastal_cliff": SimulationScenario("해식애", "coastal_marine", "direct_simple_lem", DIRECT_CAVEAT),
    "coastal_dune": SimulationScenario("바르한", "aeolian_arid", "process_proxy", PROXY_CAVEAT),
    "crater_lake": SimulationScenario("화산", "volcanic", "process_proxy", PROXY_CAVEAT),
    "cuspate_delta": SimulationScenario("삼각주", "river_delta", "process_proxy", PROXY_CAVEAT),
    "delta": SimulationScenario("삼각주", "river_delta", "direct_simple_lem", DIRECT_CAVEAT),
    "estuary": SimulationScenario("해식애", "coastal_marine", "process_proxy", PROXY_CAVEAT),
    "fjord": SimulationScenario("피오르", "glacial", "direct_simple_lem", DIRECT_CAVEAT),
    "free_meander": SimulationScenario("곡류 하천", "river_delta", "direct_simple_lem", DIRECT_CAVEAT),
    "horn": SimulationScenario("U자곡", "glacial", "process_proxy", PROXY_CAVEAT),
    "karren": SimulationScenario("카르스트 돌리네", "karst", "process_proxy", PROXY_CAVEAT),
    "karst_doline": SimulationScenario("카르스트 돌리네", "karst", "direct_simple_lem", DIRECT_CAVEAT),
    "lava_plateau": SimulationScenario("화산", "volcanic", "process_proxy", PROXY_CAVEAT),
    "mesa_butte": SimulationScenario("사막 페디먼트", "structural_differential", "process_proxy", PROXY_CAVEAT),
    "pedestal_rock": SimulationScenario("사막 페디먼트", "structural_differential", "process_proxy", PROXY_CAVEAT),
    "pediment": SimulationScenario("사막 페디먼트", "aeolian_arid", "direct_simple_lem", DIRECT_CAVEAT),
    "playa": SimulationScenario("사막 페디먼트", "aeolian_arid", "process_proxy", PROXY_CAVEAT),
    "ria_coast": SimulationScenario("해식애", "coastal_marine", "process_proxy", PROXY_CAVEAT),
    "sea_arch": SimulationScenario("해식애", "coastal_marine", "process_proxy", PROXY_CAVEAT),
    "shield_volcano": SimulationScenario("화산", "volcanic", "process_proxy", PROXY_CAVEAT),
    "spit_lagoon": SimulationScenario("해식애", "coastal_marine", "process_proxy", PROXY_CAVEAT),
    "star_dune": SimulationScenario("바르한", "aeolian_arid", "process_proxy", PROXY_CAVEAT),
    "stratovolcano": SimulationScenario("화산", "volcanic", "direct_simple_lem", DIRECT_CAVEAT),
    "tombolo": SimulationScenario("해식애", "coastal_marine", "process_proxy", PROXY_CAVEAT),
    "tower_karst": SimulationScenario("카르스트 돌리네", "karst", "process_proxy", PROXY_CAVEAT),
    "transverse_dune": SimulationScenario("바르한", "aeolian_arid", "process_proxy", PROXY_CAVEAT),
    "u_valley": SimulationScenario("U자곡", "glacial", "direct_simple_lem", DIRECT_CAVEAT),
    "uvala": SimulationScenario("카르스트 돌리네", "karst", "process_proxy", PROXY_CAVEAT),
    "v_valley": SimulationScenario("V자곡", "river_delta", "direct_simple_lem", DIRECT_CAVEAT),
    "wadi": SimulationScenario("V자곡", "aeolian_arid", "process_proxy", PROXY_CAVEAT),
    "waterfall": SimulationScenario("V자곡", "river_delta", "process_proxy", PROXY_CAVEAT),
}


def is_simulation_terrain_supported(landform_id: str) -> bool:
    return landform_id in SIMULATION_SCENARIOS


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
    scenario = SIMULATION_SCENARIOS.get(landform_id)
    if scenario is None:
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
            selected_landform=scenario.scenario_label,
            grid_size=grid_size,
        )
    except (KeyError, ValueError):
        return None
    surface_source = _apply_landform_initial_surface(lem, landform_id, grid_size)

    dt = 140.0
    lem.run(
        total_time=dt * max(frame_count - 1, 0),
        dt=dt,
        save_interval=1,
        verbose=False,
    )

    stage_history = build_lab_stage_history(
        scenario.scenario_label,
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
    payload["simulationScenarioLabel"] = scenario.scenario_label
    payload["simulationProcessFamily"] = scenario.family
    payload["simulationSupportLevel"] = scenario.support_level
    payload["simulationCaveat"] = scenario.caveat
    payload["terrainSurfaceSource"] = surface_source
    return payload


def _apply_landform_initial_surface(lem: Any, landform_id: str, grid_size: int) -> str:
    generator = IDEAL_LANDFORM_GENERATORS.get(landform_id)
    if generator is None:
        return "scenario_default"
    try:
        surface = np.asarray(generator(grid_size), dtype=float)
    except Exception:
        return "scenario_default"
    if surface.shape != (grid_size, grid_size):
        return "scenario_default"
    surface = np.nan_to_num(surface, nan=0.0, posinf=0.0, neginf=0.0)
    surface = surface - float(np.min(surface))
    lem.set_initial_topography(surface, initial_soil=0.75)
    return f"ideal_landform:{landform_id}"


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
