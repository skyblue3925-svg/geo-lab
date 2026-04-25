"""Terrain Lab scenario catalog.

The catalog is intentionally renderer-neutral. Streamlit pages, Three.js, and
Babylon.js should consume these scenario and factor definitions instead of
hard-coding separate terrain lists.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ADDITIONAL_SPEC_PATH = PROJECT_ROOT / "docs" / "TERRAIN_ADDITIONAL_IMAGE_SEQUENCE_SPECS.json"


@dataclass(frozen=True)
class TerrainLabScenario:
    landform_id: str
    title_ko: str
    group: str
    simulation_family: str
    procedural_surface_source: str
    formation_steps_ko: tuple[str, ...]
    process_factors: tuple[str, ...]
    image_prompt_en: str


@dataclass(frozen=True)
class ProcessFactorDefinition:
    factor_id: str
    label_ko: str
    unit: str
    min_value: float
    max_value: float
    default_value: float
    description_ko: str


GROUP_LABELS_KO = {
    "river": "하천 지형",
    "delta": "하구·삼각주 지형",
    "glacial": "빙하 지형",
    "volcanic": "화산 지형",
    "karst": "카르스트 지형",
    "arid": "건조 지형",
    "coastal": "해안 지형",
}


PROCESS_FACTOR_DEFINITIONS: dict[str, ProcessFactorDefinition] = {
    "ablation_rate": ProcessFactorDefinition("ablation_rate", "빙하 융해율", "상대값", 0, 100, 45, "빙하가 녹거나 승화되어 줄어드는 강도입니다."),
    "base_level_fall": ProcessFactorDefinition("base_level_fall", "기준면 하강", "상대값", 0, 100, 45, "하천이 더 깊게 침식하도록 만드는 하류 기준면 변화입니다."),
    "basal_shear_stress": ProcessFactorDefinition("basal_shear_stress", "빙하 기저 전단응력", "상대값", 0, 100, 55, "빙하 바닥이 퇴적물을 밀고 재배열하는 힘입니다."),
    "channel_aggradation": ProcessFactorDefinition("channel_aggradation", "하상 상승", "상대값", 0, 100, 45, "하도 안에 퇴적물이 쌓여 주변보다 높아지는 정도입니다."),
    "cliff_retreat_rate": ProcessFactorDefinition("cliff_retreat_rate", "해식애 후퇴율", "상대값", 0, 100, 50, "파랑 침식으로 절벽이 육지 쪽으로 물러나는 속도입니다."),
    "cutoff_threshold": ProcessFactorDefinition("cutoff_threshold", "목 절단 임계값", "상대값", 0, 100, 55, "곡류 목이 얼마나 좁아져야 절단되는지 나타냅니다."),
    "debris_supply": ProcessFactorDefinition("debris_supply", "암설 공급", "상대값", 0, 100, 55, "빙하나 사면으로 들어오는 자갈·암편 공급량입니다."),
    "dissolution_rate": ProcessFactorDefinition("dissolution_rate", "용식 강도", "상대값", 0, 100, 55, "석회암이 물에 녹아 지형을 낮추는 강도입니다."),
    "dome_growth_rate": ProcessFactorDefinition("dome_growth_rate", "돔 성장률", "상대값", 0, 100, 55, "점성이 높은 용암이 화구 주변에 쌓이는 속도입니다."),
    "ejecta_ring_height": ProcessFactorDefinition("ejecta_ring_height", "분출물 화구륜", "상대값", 0, 100, 40, "폭발 뒤 분화구 주변에 쌓이는 분출물의 높이입니다."),
    "eruption_rate": ProcessFactorDefinition("eruption_rate", "분출률", "상대값", 0, 100, 50, "마그마나 용암이 지표로 나오는 속도입니다."),
    "explosion_energy": ProcessFactorDefinition("explosion_energy", "폭발 에너지", "상대값", 0, 100, 55, "마그마-지하수 접촉으로 생기는 폭발의 강도입니다."),
    "flood_frequency": ProcessFactorDefinition("flood_frequency", "홍수 빈도", "회/상대시간", 0, 100, 50, "범람원이 물에 잠기는 빈도입니다."),
    "fracture_density": ProcessFactorDefinition("fracture_density", "절리 밀도", "상대값", 0, 100, 55, "물이나 파랑이 파고들 수 있는 균열의 많고 적음입니다."),
    "groundwater_contact": ProcessFactorDefinition("groundwater_contact", "지하수 접촉", "상대값", 0, 100, 55, "마그마 또는 암석이 지하수와 만나는 정도입니다."),
    "ice_flow_direction": ProcessFactorDefinition("ice_flow_direction", "빙하 흐름 방향", "도", 0, 360, 90, "빙하가 주로 이동하는 방향입니다."),
    "ice_retreat_rate": ProcessFactorDefinition("ice_retreat_rate", "빙하 후퇴율", "상대값", 0, 100, 45, "빙하 말단이 뒤로 물러나는 속도입니다."),
    "ice_thickness": ProcessFactorDefinition("ice_thickness", "빙하 두께", "상대값", 0, 100, 60, "빙하 침식과 퇴적을 좌우하는 얼음 두께입니다."),
    "ice_velocity": ProcessFactorDefinition("ice_velocity", "빙하 유속", "상대값", 0, 100, 50, "빙하가 이동하며 바닥을 깎고 퇴적물을 옮기는 속도입니다."),
    "incision_rate": ProcessFactorDefinition("incision_rate", "하방 침식률", "상대값", 0, 100, 55, "하천이 하상을 아래로 파고드는 강도입니다."),
    "joint_density": ProcessFactorDefinition("joint_density", "절리 밀도", "상대값", 0, 100, 55, "해식동이나 아치가 시작되기 쉬운 암석 균열 정도입니다."),
    "lateral_erosion": ProcessFactorDefinition("lateral_erosion", "측방 침식", "상대값", 0, 100, 60, "하천이 옆으로 이동하며 공격사면을 깎는 강도입니다."),
    "lava_viscosity": ProcessFactorDefinition("lava_viscosity", "용암 점성", "상대값", 0, 100, 70, "용암이 잘 흐르지 않고 돔처럼 쌓이는 정도입니다."),
    "limestone_purity": ProcessFactorDefinition("limestone_purity", "석회암 순도", "상대값", 0, 100, 65, "용식이 잘 일어나는 암석 조건입니다."),
    "longshore_drift": ProcessFactorDefinition("longshore_drift", "연안류 이동", "상대값", 0, 100, 55, "모래를 해안선 방향으로 옮기는 흐름의 강도입니다."),
    "magma_supply": ProcessFactorDefinition("magma_supply", "마그마 공급", "상대값", 0, 100, 50, "화산 지형을 성장시키거나 폭발을 유발하는 공급량입니다."),
    "meltwater_discharge": ProcessFactorDefinition("meltwater_discharge", "융빙수 유량", "상대값", 0, 100, 55, "빙하 밑 하천이 퇴적물을 운반하는 물의 양입니다."),
    "overbank_deposition": ProcessFactorDefinition("overbank_deposition", "범람 퇴적", "상대값", 0, 100, 55, "하천 밖으로 넘친 물이 퇴적물을 남기는 정도입니다."),
    "rock_resistance": ProcessFactorDefinition("rock_resistance", "암석 저항성", "상대값", 0, 100, 55, "침식에 버티는 암석의 강도입니다."),
    "sea_level_rise": ProcessFactorDefinition("sea_level_rise", "해수면 상승", "상대값", 0, 100, 35, "해안 퇴적체와 석호 위치를 바꾸는 해수면 변화입니다."),
    "sea_level_stability": ProcessFactorDefinition("sea_level_stability", "해수면 안정성", "상대값", 0, 100, 65, "파식대가 넓게 발달할 만큼 해수면이 오래 유지되는 정도입니다."),
    "seasonal_flooding": ProcessFactorDefinition("seasonal_flooding", "계절 침수", "상대값", 0, 100, 45, "카르스트 분지가 계절적으로 물에 잠기는 정도입니다."),
    "sediment_grain_size": ProcessFactorDefinition("sediment_grain_size", "퇴적물 입경", "상대값", 0, 100, 50, "조립질과 세립질 퇴적이 분화되는 기준입니다."),
    "sediment_load": ProcessFactorDefinition("sediment_load", "퇴적물 부하", "상대값", 0, 100, 55, "물이나 빙하가 운반하는 퇴적물의 양입니다."),
    "sediment_supply": ProcessFactorDefinition("sediment_supply", "퇴적물 공급", "상대값", 0, 100, 55, "하천이나 해안에 새로 들어오는 모래·자갈의 양입니다."),
    "settling_velocity": ProcessFactorDefinition("settling_velocity", "침강 속도", "상대값", 0, 100, 50, "입자가 물에서 가라앉는 속도입니다."),
    "slope_failure_threshold": ProcessFactorDefinition("slope_failure_threshold", "사면 붕괴 임계값", "상대값", 0, 100, 55, "돔이나 절벽 사면이 무너지기 시작하는 조건입니다."),
    "storm_overwash": ProcessFactorDefinition("storm_overwash", "폭풍 월파", "상대값", 0, 100, 35, "폭풍 때 파랑이 사주섬을 넘어 모래를 재배치하는 강도입니다."),
    "tidal_range": ProcessFactorDefinition("tidal_range", "조차", "상대값", 0, 100, 40, "파식면과 해안 침식 높이 범위를 넓히는 조석 차입니다."),
    "till_thickness": ProcessFactorDefinition("till_thickness", "빙력토 두께", "상대값", 0, 100, 55, "빙하 바닥에 쌓인 비분급 퇴적물의 두께입니다."),
    "terminal_position": ProcessFactorDefinition("terminal_position", "빙하 말단 위치", "상대값", 0, 100, 50, "모레인이 남는 빙하 끝 위치입니다."),
    "tunnel_slope": ProcessFactorDefinition("tunnel_slope", "빙하 밑 수로 경사", "상대값", 0, 100, 45, "에스커 퇴적물이 쌓이는 수로의 경사 조건입니다."),
    "uplift_rate": ProcessFactorDefinition("uplift_rate", "융기율", "상대값", 0, 100, 45, "하천이 옛 범람원을 단구로 남기도록 하는 지반 상승 속도입니다."),
    "water_pressure": ProcessFactorDefinition("water_pressure", "기저 수압", "상대값", 0, 100, 45, "빙하 바닥의 퇴적물 변형과 이동을 돕는 물의 압력입니다."),
    "water_table": ProcessFactorDefinition("water_table", "지하수위", "상대값", 0, 100, 50, "용식, 마르 호수, 폴리에 침수를 좌우하는 지하수 높이입니다."),
    "wave_angle": ProcessFactorDefinition("wave_angle", "파향", "도", 0, 90, 35, "연안류와 사주섬 성장 방향을 만드는 파랑 입사각입니다."),
    "wave_energy": ProcessFactorDefinition("wave_energy", "파랑 에너지", "상대값", 0, 100, 60, "해안 절벽, 파식대, 해식동을 깎는 파랑의 힘입니다."),
}


PARAMETER_MULTIPLIER_LABELS_KO = {
    "k_scale": "침식 반응",
    "d_scale": "사면 이동",
    "u_scale": "융기/기준면",
    "deposition_scale": "퇴적 반응",
    "water_scale": "물/수위 조건",
    "glacial_scale": "빙하 작용",
    "marine_scale": "파랑/해안 작용",
    "karst_scale": "용식 작용",
    "volcanic_scale": "화산 작용",
}


@lru_cache(maxsize=1)
def list_additional_lab_scenarios() -> tuple[TerrainLabScenario, ...]:
    raw = json.loads(ADDITIONAL_SPEC_PATH.read_text(encoding="utf-8"))
    scenarios = []
    for item in raw["landforms"]:
        scenarios.append(
            TerrainLabScenario(
                landform_id=str(item["id"]),
                title_ko=str(item["title_ko"]),
                group=str(item["group"]),
                simulation_family=str(item["simulation_family"]),
                procedural_surface_source=str(item["procedural_surface_source"]),
                formation_steps_ko=tuple(str(step) for step in item["formation_steps_ko"]),
                process_factors=tuple(str(factor) for factor in item["process_factors"]),
                image_prompt_en=str(item["image_prompt_en"]),
            )
        )
    return tuple(scenarios)


def get_additional_lab_scenario(landform_id: str) -> TerrainLabScenario | None:
    return next((scenario for scenario in list_additional_lab_scenarios() if scenario.landform_id == landform_id), None)


def list_additional_lab_scenarios_by_group(group: str) -> tuple[TerrainLabScenario, ...]:
    return tuple(scenario for scenario in list_additional_lab_scenarios() if scenario.group == group)


def get_process_factor_definition(factor_id: str) -> ProcessFactorDefinition | None:
    return PROCESS_FACTOR_DEFINITIONS.get(factor_id)


def process_factor_definitions_for_scenario(landform_id: str) -> tuple[ProcessFactorDefinition, ...]:
    scenario = get_additional_lab_scenario(landform_id)
    if scenario is None:
        return ()
    return tuple(PROCESS_FACTOR_DEFINITIONS[factor_id] for factor_id in scenario.process_factors)


def missing_process_factor_definitions() -> set[str]:
    used = {
        factor_id
        for scenario in list_additional_lab_scenarios()
        for factor_id in scenario.process_factors
    }
    return used - set(PROCESS_FACTOR_DEFINITIONS)


def scenario_slider_defaults(landform_id: str) -> dict[str, float]:
    return {
        definition.factor_id: definition.default_value
        for definition in process_factor_definitions_for_scenario(landform_id)
    }


def format_factor_value_lines(
    landform_id: str,
    factor_values: dict[str, float],
) -> tuple[str, ...]:
    lines = []
    for definition in process_factor_definitions_for_scenario(landform_id):
        value = factor_values.get(definition.factor_id, definition.default_value)
        lines.append(f"{definition.label_ko}: {float(value):.0f}")
    return tuple(lines)


def format_parameter_multiplier_lines(
    multipliers: dict[str, float],
    *,
    threshold: float = 0.08,
) -> tuple[str, ...]:
    active = []
    for key, value in multipliers.items():
        numeric = float(value)
        if abs(numeric - 1.0) < threshold:
            continue
        label = PARAMETER_MULTIPLIER_LABELS_KO.get(key, key)
        active.append((abs(numeric - 1.0), f"{label} x{numeric:.2f}"))
    active.sort(reverse=True)
    if not active:
        return ("기본값에 가까운 조건입니다.",)
    return tuple(line for _, line in active)


def build_lab_experiment_design_summary(
    landform_id: str,
    factor_values: dict[str, float],
    multipliers: dict[str, float],
) -> dict[str, object]:
    scenario = get_additional_lab_scenario(landform_id)
    if scenario is None:
        return {}

    return {
        "title": f"{scenario.title_ko} 실험 설계",
        "group": GROUP_LABELS_KO.get(scenario.group, scenario.group),
        "formation_steps": scenario.formation_steps_ko,
        "factor_lines": format_factor_value_lines(landform_id, factor_values),
        "multiplier_lines": format_parameter_multiplier_lines(multipliers),
        "simulation_family": scenario.simulation_family,
    }


def derive_lab_parameter_multipliers(
    landform_id: str,
    factor_values: dict[str, float],
) -> dict[str, float]:
    """Translate catalog factor sliders into coarse SimpleLEM multipliers."""

    scenario = get_additional_lab_scenario(landform_id)
    if scenario is None:
        return _neutral_multipliers()

    ratios = {
        factor_id: _slider_ratio(factor_id, factor_values.get(factor_id))
        for factor_id in scenario.process_factors
    }

    return {
        "k_scale": _mean_ratio(
            ratios,
            {
                "base_level_fall",
                "cliff_retreat_rate",
                "cutoff_threshold",
                "dissolution_rate",
                "explosion_energy",
                "flood_frequency",
                "fracture_density",
                "incision_rate",
                "joint_density",
                "lateral_erosion",
                "meltwater_discharge",
                "wave_energy",
            },
        ),
        "d_scale": _mean_ratio(
            ratios,
            {
                "basal_shear_stress",
                "debris_supply",
                "dome_growth_rate",
                "ice_velocity",
                "slope_failure_threshold",
                "storm_overwash",
                "till_thickness",
            },
        ),
        "u_scale": _mean_ratio(ratios, {"base_level_fall", "uplift_rate"}),
        "deposition_scale": _mean_ratio(
            ratios,
            {
                "channel_aggradation",
                "debris_supply",
                "ejecta_ring_height",
                "longshore_drift",
                "overbank_deposition",
                "sediment_grain_size",
                "sediment_load",
                "sediment_supply",
                "settling_velocity",
                "terminal_position",
            },
        ),
        "water_scale": _mean_ratio(
            ratios,
            {
                "flood_frequency",
                "groundwater_contact",
                "sea_level_rise",
                "seasonal_flooding",
                "water_pressure",
                "water_table",
            },
        ),
        "glacial_scale": _mean_ratio(
            ratios,
            {
                "ablation_rate",
                "basal_shear_stress",
                "ice_flow_direction",
                "ice_retreat_rate",
                "ice_thickness",
                "ice_velocity",
                "meltwater_discharge",
                "till_thickness",
            },
        ),
        "marine_scale": _mean_ratio(
            ratios,
            {
                "cliff_retreat_rate",
                "longshore_drift",
                "sea_level_rise",
                "sea_level_stability",
                "storm_overwash",
                "tidal_range",
                "wave_angle",
                "wave_energy",
            },
        ),
        "karst_scale": _mean_ratio(
            ratios,
            {
                "dissolution_rate",
                "fracture_density",
                "limestone_purity",
                "seasonal_flooding",
                "water_table",
            },
        ),
        "volcanic_scale": _mean_ratio(
            ratios,
            {
                "dome_growth_rate",
                "ejecta_ring_height",
                "eruption_rate",
                "explosion_energy",
                "groundwater_contact",
                "lava_viscosity",
                "magma_supply",
            },
        ),
    }


def _neutral_multipliers() -> dict[str, float]:
    return {
        "k_scale": 1.0,
        "d_scale": 1.0,
        "u_scale": 1.0,
        "deposition_scale": 1.0,
        "water_scale": 1.0,
        "glacial_scale": 1.0,
        "marine_scale": 1.0,
        "karst_scale": 1.0,
        "volcanic_scale": 1.0,
    }


def _slider_ratio(factor_id: str, value: float | None) -> float:
    definition = PROCESS_FACTOR_DEFINITIONS[factor_id]
    default = max(float(definition.default_value), 1.0)
    if value is None:
        value = definition.default_value
    return float(max(0.35, min(float(value) / default, 2.2)))


def _mean_ratio(ratios: dict[str, float], factor_ids: set[str]) -> float:
    values = [ratio for factor_id, ratio in ratios.items() if factor_id in factor_ids]
    if not values:
        return 1.0
    return float(max(0.35, min(sum(values) / len(values), 2.2)))
