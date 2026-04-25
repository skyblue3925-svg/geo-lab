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
    "glacial": "빙하·주빙하 지형",
    "volcanic": "화산 지형",
    "karst": "카르스트 지형",
    "arid": "건조 지형",
    "coastal": "해안 지형",
}


SCENARIO_KO_OVERRIDES: dict[str, tuple[str, tuple[str, ...]]] = {
    "oxbow_lake": (
        "우각호",
        ("자유곡류 발달", "공격사면 침식과 포인트바 퇴적", "목 부분 협착", "절단 뒤 호수화"),
    ),
    "floodplain_natural_levee": (
        "범람원과 자연제방",
        ("평탄한 하천 주변 저지", "홍수 범람", "하도 가까운 곳에 조립질 퇴적", "자연제방과 배후습지 분화"),
    ),
    "river_terrace": (
        "하안단구",
        ("기존 범람원 형성", "융기 또는 기준면 하강", "하천 재침식", "계단형 하상면 잔존"),
    ),
    "sea_cave_stack": (
        "해식동과 시스택",
        ("절리 있는 해식애", "파랑 침식 집중", "해식동과 아치 발달", "붕괴 후 시스택 잔존"),
    ),
    "wave_cut_platform": (
        "파식대",
        ("해식애 하부 침식", "절벽 후퇴", "평탄한 암반면 노출", "파식대 확장"),
    ),
    "barrier_island": (
        "사주섬",
        ("연안류 모래 이동", "해안과 평행한 사주 성장", "석호 분리", "폭풍 월파와 퇴적 재조정"),
    ),
    "moraine": (
        "모레인",
        ("빙하가 암설 운반", "말단부 암설 집적", "빙하 후퇴", "둔덕형 퇴적지형 잔존"),
    ),
    "drumlin": (
        "드럼린",
        ("빙하 하부 퇴적물 축적", "빙하 흐름 방향 압축", "유선형 언덕 성형", "빙하 후퇴 뒤 노출"),
    ),
    "esker": (
        "에스커",
        ("빙하 하부 융빙수 하천", "터널 안 퇴적", "빙하 후퇴", "구불구불한 능선 노출"),
    ),
    "maar": (
        "마르",
        ("마그마와 지하수 접촉", "수증기 폭발", "낮은 분화구 형성", "물 고임"),
    ),
    "lava_dome": (
        "용암돔",
        ("점성 높은 용암 상승", "분화구 주변 돔 성장", "균열과 붕괴", "급경사 돔 안정화"),
    ),
    "polje": (
        "폴리에",
        ("석회암 용식 확대", "우발레 병합", "평탄한 분지 바닥 발달", "계절적 침수와 배수 반복"),
    ),
    "tidal_flat": (
        "갯벌",
        ("조차 큰 완만한 해안", "세립 퇴적물 집적", "조석수로 발달", "노출·침수 반복"),
    ),
    "marine_terrace": (
        "해안단구",
        ("파식면 형성", "융기 또는 해수면 하강", "옛 파식면 상승", "계단형 해안면 보존"),
    ),
    "kettle_lake": (
        "케틀호",
        ("빙하 퇴적물 속 얼음 매몰", "사빙 융해", "함몰지 형성", "물 고임"),
    ),
    "outwash_plain": (
        "빙수평원",
        ("빙하 전면 융빙수 유출", "모래·자갈 운반", "망상류 퇴적", "완만한 평원 발달"),
    ),
    "thermokarst": (
        "열카르스트",
        ("영구동토 융해", "지표 침하", "융해 웅덩이 확대", "불규칙한 호수·습지 발달"),
    ),
    "cinder_cone": (
        "분석구",
        ("화산쇄설물 분출", "화구 주변 스코리아 퇴적", "원추체 성장", "정상 화구 유지"),
    ),
}


def _factor(
    factor_id: str,
    label_ko: str,
    default_value: float,
    description_ko: str,
    *,
    unit: str = "상대값",
    min_value: float = 0,
    max_value: float = 100,
) -> ProcessFactorDefinition:
    return ProcessFactorDefinition(
        factor_id,
        label_ko,
        unit,
        min_value,
        max_value,
        default_value,
        description_ko,
    )


PROCESS_FACTOR_DEFINITIONS: dict[str, ProcessFactorDefinition] = {
    "ablation_rate": _factor("ablation_rate", "빙하 융해율", 45, "빙하가 녹거나 승화하여 줄어드는 강도입니다."),
    "base_level_fall": _factor("base_level_fall", "기준면 하강", 45, "하천이 더 깊게 침식하도록 만드는 하류 기준면 변화입니다."),
    "basal_shear_stress": _factor("basal_shear_stress", "빙하저 전단응력", 55, "빙하 바닥이 퇴적물을 밀고 재배열하는 힘입니다."),
    "channel_aggradation": _factor("channel_aggradation", "하상 상승", 45, "하도 안에 퇴적물이 쌓여 주변보다 높아지는 정도입니다."),
    "cliff_retreat_rate": _factor("cliff_retreat_rate", "해식애 후퇴율", 50, "파랑 침식으로 절벽이 육지 쪽으로 물러나는 속도입니다."),
    "cutoff_threshold": _factor("cutoff_threshold", "절단 임계값", 55, "곡류 목이 얼마나 좁아져야 절단되는지 나타냅니다."),
    "debris_supply": _factor("debris_supply", "암설 공급", 55, "빙하나 사면으로 들어오는 암석 조각의 양입니다."),
    "dissolution_rate": _factor("dissolution_rate", "용식 속도", 55, "석회암이 물에 녹아 지형을 낮추는 강도입니다."),
    "dome_growth_rate": _factor("dome_growth_rate", "돔 성장률", 55, "점성 높은 용암이 분화구 주변에 쌓이는 속도입니다."),
    "ejecta_ring_height": _factor("ejecta_ring_height", "분출물 환 높이", 40, "폭발 뒤 분화구 주변에 쌓이는 분출물의 높이입니다."),
    "eruption_rate": _factor("eruption_rate", "분출률", 50, "마그마나 화산쇄설물이 지표로 나오는 속도입니다."),
    "explosion_energy": _factor("explosion_energy", "폭발 에너지", 55, "마그마와 지하수 접촉 등으로 생기는 폭발 강도입니다."),
    "flood_frequency": _factor("flood_frequency", "홍수 빈도", 50, "범람원이 물에 잠기는 빈도입니다.", unit="회/상대시간"),
    "fracture_density": _factor("fracture_density", "균열 밀도", 55, "물이 스며들거나 파랑이 파고들 수 있는 균열의 많고 적음입니다."),
    "groundwater_contact": _factor("groundwater_contact", "지하수 접촉", 55, "마그마 또는 암석이 지하수와 만나는 정도입니다."),
    "ice_flow_direction": _factor("ice_flow_direction", "빙하 흐름 방향", 90, "빙하가 주로 이동하는 방향입니다.", unit="도", max_value=360),
    "ice_retreat_rate": _factor("ice_retreat_rate", "빙하 후퇴율", 45, "빙하 말단이 뒤로 물러나는 속도입니다."),
    "ice_thickness": _factor("ice_thickness", "빙하 두께", 60, "빙하 침식과 퇴적을 좌우하는 얼음 두께입니다."),
    "ice_velocity": _factor("ice_velocity", "빙하 유속", 50, "빙하가 이동하며 바닥을 깎고 퇴적물을 끄는 속도입니다."),
    "incision_rate": _factor("incision_rate", "하방 침식률", 55, "하천이 하상을 아래로 깎아내는 강도입니다."),
    "joint_density": _factor("joint_density", "절리 밀도", 55, "해식 작용이 시작되기 쉬운 암석 균열의 정도입니다."),
    "lateral_erosion": _factor("lateral_erosion", "측방 침식", 60, "하천이 옆으로 이동하며 공격사면을 깎는 강도입니다."),
    "lava_viscosity": _factor("lava_viscosity", "용암 점성", 70, "용암이 잘 흐르지 않고 분화구 근처에 쌓이는 정도입니다."),
    "limestone_purity": _factor("limestone_purity", "석회암 순도", 65, "용식이 잘 일어나는 암석 조건입니다."),
    "longshore_drift": _factor("longshore_drift", "연안류 이동", 55, "모래를 해안선 방향으로 옮기는 흐름의 강도입니다."),
    "magma_supply": _factor("magma_supply", "마그마 공급", 50, "화산 지형을 성장시키거나 폭발을 유발하는 공급량입니다."),
    "meltwater_discharge": _factor("meltwater_discharge", "융빙수 유량", 55, "빙하 밖 하천이 퇴적물을 운반하는 물의 양입니다."),
    "overbank_deposition": _factor("overbank_deposition", "범람 퇴적", 55, "하천 밖으로 넘친 물이 퇴적물을 남기는 정도입니다."),
    "rock_resistance": _factor("rock_resistance", "암석 저항성", 55, "침식에 버티는 암석의 강도입니다."),
    "sea_level_rise": _factor("sea_level_rise", "해수면 상승", 35, "해안 퇴적체와 석호 위치를 바꾸는 해수면 변화입니다."),
    "sea_level_stability": _factor("sea_level_stability", "해수면 안정성", 65, "파식대가 넓게 발달할 만큼 해수면이 오래 유지되는 정도입니다."),
    "seasonal_flooding": _factor("seasonal_flooding", "계절 침수", 45, "분지나 저지가 계절적으로 물에 잠기는 정도입니다."),
    "sediment_grain_size": _factor("sediment_grain_size", "퇴적물 입경", 50, "조립질과 세립질 퇴적을 나누는 입자 크기 조건입니다."),
    "sediment_load": _factor("sediment_load", "퇴적물 부하", 55, "물이나 빙하가 운반하는 퇴적물의 양입니다."),
    "sediment_supply": _factor("sediment_supply", "퇴적물 공급", 55, "하천이나 해안에 새로 들어오는 모래·자갈의 양입니다."),
    "settling_velocity": _factor("settling_velocity", "침강 속도", 50, "입자가 물속에서 가라앉는 속도입니다."),
    "slope_failure_threshold": _factor("slope_failure_threshold", "사면 붕괴 임계값", 55, "돔이나 절벽 사면이 무너지기 시작하는 조건입니다."),
    "storm_overwash": _factor("storm_overwash", "폭풍 월파", 35, "폭풍 때 파랑이 사주섬을 넘어 모래를 재배치하는 강도입니다."),
    "tidal_range": _factor("tidal_range", "조차", 40, "노출과 침수가 반복되는 조석 차이입니다."),
    "till_thickness": _factor("till_thickness", "빙력토 두께", 55, "빙하 바닥에 쌓인 비분급 퇴적물의 두께입니다."),
    "terminal_position": _factor("terminal_position", "빙하 말단 위치", 50, "모레인이 남는 빙하 끝의 위치입니다."),
    "tunnel_slope": _factor("tunnel_slope", "빙하 하부 수로 경사", 45, "에스커 퇴적물이 쌓이는 수로의 경사 조건입니다."),
    "uplift_rate": _factor("uplift_rate", "융기율", 45, "옛 범람원이나 파식면을 높은 곳에 남기는 지반 상승 속도입니다."),
    "water_pressure": _factor("water_pressure", "기저 수압", 45, "빙하 바닥의 퇴적물 변형과 이동을 돕는 물의 압력입니다."),
    "water_table": _factor("water_table", "지하수위", 50, "용식, 마르 호수, 저지 침수를 좌우하는 지하수 높이입니다."),
    "wave_angle": _factor("wave_angle", "파향", 35, "연안류와 사주 성장 방향을 만드는 파랑 입사각입니다.", unit="도", max_value=90),
    "wave_energy": _factor("wave_energy", "파랑 에너지", 60, "해안 절벽, 파식대, 해식동을 깎는 파랑의 힘입니다."),
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
        landform_id = str(item["id"])
        title_ko = str(item["title_ko"])
        formation_steps_ko = tuple(str(step) for step in item["formation_steps_ko"])
        if landform_id in SCENARIO_KO_OVERRIDES:
            title_ko, formation_steps_ko = SCENARIO_KO_OVERRIDES[landform_id]
        scenarios.append(
            TerrainLabScenario(
                landform_id=landform_id,
                title_ko=title_ko,
                group=str(item["group"]),
                simulation_family=str(item["simulation_family"]),
                procedural_surface_source=str(item["procedural_surface_source"]),
                formation_steps_ko=formation_steps_ko,
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
