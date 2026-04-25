"""Build 3D terrain payloads from the local SimpleLEM simulation engine."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Any

import numpy as np

from app.services.terrain_3d_payload import build_terrain_3d_payload, build_terrain_3d_payload_from_history
from engine.ideal_landforms import IDEAL_LANDFORM_GENERATORS


@dataclass(frozen=True)
class SimulationScenario:
    scenario_label: str
    family: str
    support_level: str
    caveat: str


DIRECT_CAVEAT = "SimpleLEM 물리장과 해당 지형의 이상 지형 표면을 함께 사용합니다."
PROXY_CAVEAT = "현재 엔진의 대표 물리과정으로 근사한 교육용 3D 시뮬레이션입니다."

FAMILY_STAGE_TITLES: dict[str, tuple[str, ...]] = {
    "river_delta": ("초기 경사 형성", "하천 침식", "퇴적과 분류", "지형 안정화"),
    "coastal_marine": ("해안 경계 형성", "파랑 침식", "퇴적물 재배치", "해안선 조정"),
    "glacial": ("빙하 집적", "빙하 침식", "골짜기 확장", "후퇴와 잔류 지형"),
    "karst": ("석회암 표면", "용식 집중", "함몰 확대", "배수망 안정화"),
    "aeolian_arid": ("건조 표면", "바람 침식", "모래 이동과 퇴적", "형태 이동"),
    "volcanic": ("분출 시작", "화산체 성장", "침식과 함몰", "후기 지형 조정"),
    "structural_differential": ("구조면 노출", "약한 층 침식", "잔구 분리", "차별 침식 안정화"),
}

FAMILY_OVERLAYS: dict[str, tuple[str, ...]] = {
    "river_delta": ("tectonic", "erosion", "deposition", "change"),
    "coastal_marine": ("marine", "erosion", "deposition", "change"),
    "glacial": ("glacial", "erosion", "change", "change"),
    "karst": ("karst", "erosion", "change", "change"),
    "aeolian_arid": ("wind", "erosion", "deposition", "change"),
    "volcanic": ("volcanic", "volcanic", "erosion", "change"),
    "structural_differential": ("tectonic", "erosion", "erosion", "change"),
}


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
    "floodplain_natural_levee": SimulationScenario("범람원과 자연제방", "river_delta", "process_proxy", PROXY_CAVEAT),
    "free_meander": SimulationScenario("곡류 하천", "river_delta", "direct_simple_lem", DIRECT_CAVEAT),
    "horn": SimulationScenario("U자곡", "glacial", "process_proxy", PROXY_CAVEAT),
    "karren": SimulationScenario("카르스트 돌리네", "karst", "process_proxy", PROXY_CAVEAT),
    "karst_doline": SimulationScenario("카르스트 돌리네", "karst", "direct_simple_lem", DIRECT_CAVEAT),
    "lava_plateau": SimulationScenario("화산", "volcanic", "process_proxy", PROXY_CAVEAT),
    "lava_dome": SimulationScenario("용암돔", "volcanic", "process_proxy", PROXY_CAVEAT),
    "maar": SimulationScenario("마르", "volcanic", "process_proxy", PROXY_CAVEAT),
    "mesa_butte": SimulationScenario("사막 페디먼트", "structural_differential", "process_proxy", PROXY_CAVEAT),
    "moraine": SimulationScenario("모레인", "glacial", "process_proxy", PROXY_CAVEAT),
    "drumlin": SimulationScenario("드럼린", "glacial", "process_proxy", PROXY_CAVEAT),
    "esker": SimulationScenario("에스커", "glacial", "process_proxy", PROXY_CAVEAT),
    "oxbow_lake": SimulationScenario("우각호", "river_delta", "process_proxy", PROXY_CAVEAT),
    "pedestal_rock": SimulationScenario("사막 페디먼트", "structural_differential", "process_proxy", PROXY_CAVEAT),
    "pediment": SimulationScenario("사막 페디먼트", "aeolian_arid", "direct_simple_lem", DIRECT_CAVEAT),
    "playa": SimulationScenario("사막 페디먼트", "aeolian_arid", "process_proxy", PROXY_CAVEAT),
    "polje": SimulationScenario("폴리에", "karst", "process_proxy", PROXY_CAVEAT),
    "ria_coast": SimulationScenario("해식애", "coastal_marine", "process_proxy", PROXY_CAVEAT),
    "river_terrace": SimulationScenario("하안단구", "river_delta", "process_proxy", PROXY_CAVEAT),
    "sea_arch": SimulationScenario("해식애", "coastal_marine", "process_proxy", PROXY_CAVEAT),
    "sea_cave_stack": SimulationScenario("해식동과 시스택", "coastal_marine", "process_proxy", PROXY_CAVEAT),
    "shield_volcano": SimulationScenario("화산", "volcanic", "process_proxy", PROXY_CAVEAT),
    "barrier_island": SimulationScenario("사주섬", "coastal_marine", "process_proxy", PROXY_CAVEAT),
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
    "wave_cut_platform": SimulationScenario("파식대", "coastal_marine", "process_proxy", PROXY_CAVEAT),
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

    payload, surface_source = _build_process_payload(landform_id, grid_size, frame_count)
    payload["modelSource"] = "terrain_process_proxy"
    stage_history = _build_stage_history(scenario, payload["surfaceFrameCount"])
    compact_stages = [_compact_stage(stage) for stage in stage_history]
    if compact_stages:
        payload["stageHistory"] = compact_stages
        payload["processLabels"] = [
            str(stage.get("title") or stage.get("caption") or "지형 변화")
            for stage in compact_stages
        ]
    else:
        payload["stageHistory"] = []
    payload["timeSteps"] = [float(idx) for idx in range(payload["surfaceFrameCount"])]
    payload["simulationScenarioLabel"] = scenario.scenario_label
    payload["simulationProcessFamily"] = scenario.family
    payload["simulationSupportLevel"] = scenario.support_level
    payload["simulationCaveat"] = scenario.caveat
    payload["terrainSurfaceSource"] = surface_source
    return payload


def _build_process_payload(
    landform_id: str,
    grid_size: int,
    frame_count: int,
) -> tuple[dict[str, Any], str]:
    try:
        return (
            build_terrain_3d_payload(
                landform_id,
                grid_size=grid_size,
                frame_count=frame_count,
            ),
            f"animated_landform:{landform_id}",
        )
    except Exception:
        fallback_history, surface_source = _build_static_ideal_surface_history(landform_id, grid_size, frame_count)
        return (
            build_terrain_3d_payload_from_history(
                landform_id,
                history=fallback_history,
            ),
            surface_source,
        )


def _build_static_ideal_surface_history(
    landform_id: str,
    grid_size: int,
    frame_count: int,
) -> tuple[list[np.ndarray], str]:
    generator = IDEAL_LANDFORM_GENERATORS.get(landform_id)
    if generator is None:
        final_surface = np.zeros((grid_size, grid_size), dtype=float)
        surface_source = f"zero_surface_fallback:{landform_id}"
    else:
        try:
            final_surface = np.asarray(generator(grid_size), dtype=float)
            surface_source = f"ideal_landform_fallback:{landform_id}"
        except Exception:
            final_surface = np.zeros((grid_size, grid_size), dtype=float)
            surface_source = f"zero_surface_fallback:{landform_id}"
        if final_surface.shape != (grid_size, grid_size):
            final_surface = np.zeros((grid_size, grid_size), dtype=float)
            surface_source = f"zero_surface_fallback:{landform_id}"
    final_surface = np.nan_to_num(final_surface, nan=0.0, posinf=0.0, neginf=0.0)
    base_surface = np.full_like(final_surface, float(np.min(final_surface)))
    if frame_count <= 1:
        return [final_surface], surface_source
    return [
        (base_surface * (1.0 - progress)) + (final_surface * progress)
        for progress in np.linspace(0.0, 1.0, frame_count)
    ], surface_source


def _build_stage_history(
    scenario: SimulationScenario,
    frame_count: int,
) -> list[dict[str, Any]]:
    titles = FAMILY_STAGE_TITLES.get(scenario.family, ("초기 지형", "작용 집중", "형태 변화", "후기 조정"))
    overlays = FAMILY_OVERLAYS.get(scenario.family, ("change", "erosion", "deposition", "change"))
    if frame_count <= 0:
        return []
    stages = []
    for idx in range(frame_count):
        title_index = 0 if frame_count == 1 else round(idx / (frame_count - 1) * (len(titles) - 1))
        title_index = max(0, min(len(titles) - 1, int(title_index)))
        title = titles[title_index]
        stages.append(
            {
                "title": title,
                "caption": f"{scenario.scenario_label}: {title}",
                "summary": scenario.caveat,
                "focus": "색 overlay가 강한 위치에서 지배 작용을 확인합니다.",
                "question": "이 지형에서 침식과 퇴적 중 어느 작용이 더 먼저 드러나나요?",
                "process_order": "초기 조건 → 지배 작용 → 형태 변화 → 후기 조정",
                "overlay_type": overlays[title_index % len(overlays)],
                "stage_index": title_index,
            }
        )
    return stages


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
