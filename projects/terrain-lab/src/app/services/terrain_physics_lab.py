from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np

from app.utils.lab_model import (
    build_lab_stage_history,
    configure_lab_scenario,
    create_lab_simple_lem,
    describe_lab_process_stage,
    format_process_summary,
)
from app.services.river_morphology_kernel import RiverKernelParameters, run_river_morphology_model
from app.services.geomorphic_process_kernels import (
    ProcessKernelParameters,
    run_process_morphology_model,
)
from app.services.animation_assets import KOREAN_TITLES, LANDFORM_GROUP_BY_ID, LANDFORM_GROUP_LABELS, PROJECT_ROOT
from app.services.geomorphic_engine import GeomorphicEngineParameters, run_geomorphic_engine
from app.services.morphometric_metrics import compute_morphometric_metrics
from app.services.terrain_lab_catalog import (
    GROUP_LABELS_KO,
    list_additional_lab_scenarios,
    process_factor_definitions_for_scenario,
)


@dataclass(frozen=True)
class PhysicsLabScenario:
    landform_id: str
    title: str
    group: str
    model_label: str
    primary_factor: str
    secondary_factor: str
    default_force: int = 55
    default_uplift: int = 35
    default_diffusion: int = 35
    default_time: int = 40_000


@dataclass(frozen=True)
class PhysicsLabTheory:
    landform_id: str
    model_family: str
    equations: tuple[tuple[str, str, str], ...]
    assumptions: tuple[str, ...]
    classroom_note: str


@dataclass(frozen=True)
class ForceModuleSpec:
    module_id: str
    label_ko: str
    force_type: str
    equation: str
    classroom_meaning: str
    output_fields: tuple[str, ...]
    scenario_groups: tuple[str, ...]
    scenario_ids: tuple[str, ...] = ()


FORCE_MODULE_SPECS: tuple[ForceModuleSpec, ...] = (
    ForceModuleSpec(
        "fluvial",
        "하천 침식·운반",
        "외적 작용",
        "E = K A^m S^n,  Qc = f(Q, S)",
        "유량, 집수면적, 경사가 커질수록 하천이 하방 침식과 운반을 강화합니다.",
        ("fluvial_erosion", "drainage_area", "transport_capacity", "deposition"),
        ("river", "delta"),
        ("waterfall", "v_valley", "alluvial_fan", "oxbow_lake", "river_terrace"),
    ),
    ForceModuleSpec(
        "hillslope_diffusion",
        "사면 확산",
        "외적 작용",
        "∂z/∂t = D∇²z",
        "급경사면은 무너지고 낮은 곳은 메워지면서 표면이 완만해집니다.",
        ("diffusion",),
        ("river", "delta", "glacial", "coastal", "arid", "volcanic", "karst"),
    ),
    ForceModuleSpec(
        "marine",
        "파랑·해안 작용",
        "외적 작용",
        "R = f(W, sea level, sediment budget)",
        "해수면 근처에서 파랑 에너지가 집중되면 해식애 후퇴, 파식대, 해빈 퇴적이 분리되어 나타납니다.",
        ("wave_energy", "shoreline_retreat", "wave_cut_platform", "beach_deposition", "longshore_transport"),
        ("coastal", "delta"),
        ("coastal_cliff", "wave_cut_platform", "marine_terrace", "sea_cave_stack", "spit_lagoon", "tombolo", "ria_coast", "estuary"),
    ),
    ForceModuleSpec(
        "glacial",
        "빙하 침식·퇴적",
        "외적 작용",
        "Eg ∝ Hi Ui |∇z|",
        "빙하 두께와 흐름이 커질수록 바닥 침식이 강해지고, 후퇴 지점에는 모레인 퇴적이 남습니다.",
        ("ice_thickness", "glacial_velocity", "glacial", "moraine"),
        ("glacial",),
        ("u_valley", "moraine", "drumlin", "esker", "kettle_lake", "outwash_plain", "thermokarst"),
    ),
    ForceModuleSpec(
        "aeolian",
        "바람·모래 이동",
        "외적 작용",
        "qs ∝ u*³,  Δz = lee deposition - stoss erosion",
        "풍상면은 깎이고 풍하면에는 모래가 쌓여 사구 이동 방향이 드러납니다.",
        ("wind_vector_x", "wind_vector_y", "sand_flux", "stoss_erosion", "lee_deposition", "dune_migration"),
        ("arid",),
        ("barchan", "transverse_dune", "star_dune", "coastal_dune"),
    ),
    ForceModuleSpec(
        "volcanic",
        "화산체 성장",
        "내적 작용",
        "C = eruption rate,  spread ∝ 1 / viscosity",
        "분출률, 용암 점성, 냉각 조건에 따라 용암돔·순상화산·성층화산의 성장 방식이 달라집니다.",
        ("volcanic_construction", "lava_flow", "viscosity_resistance", "cooling_limited_spread"),
        ("volcanic",),
        ("lava_dome", "shield_volcano", "stratovolcano", "lava_plateau", "caldera", "crater_lake"),
    ),
    ForceModuleSpec(
        "explosive_volcanism",
        "폭발성 화산 작용",
        "내적 작용",
        "Cr = f(explosion energy, magma-water contact)",
        "마그마와 지하수 접촉 또는 화산쇄설물 공급이 커지면 화구 굴착과 분석구 성장이 강화됩니다.",
        ("explosion_energy", "crater_excavation", "ejecta_deposition", "pyroclastic_cone_growth", "magma_water_contact"),
        ("volcanic",),
        ("maar", "cinder_cone", "caldera", "crater_lake", "stratovolcano"),
    ),
    ForceModuleSpec(
        "karst_groundwater",
        "카르스트·지하수",
        "외적 작용",
        "Sr ∝ water supply × rock solubility × fracture density",
        "석회암 용식, 균열 밀도, 지하수 집중이 커질수록 돌리네·우발라·폴리에 발달 조건이 강해집니다.",
        ("groundwater_flow", "solution_rate", "subsurface_drainage", "collapse_risk", "sinkhole_density"),
        ("karst",),
        ("karst_doline", "uvala", "polje", "karren", "tower_karst"),
    ),
    ForceModuleSpec(
        "tectonic_boundary",
        "융기·침강 기준면",
        "내적/경계 조건",
        "U = dz/dt,  base level = sea level or outlet level",
        "지반이 오르거나 기준면이 낮아지면 침식 여력이 커지고, 반대 조건에서는 퇴적 공간이 커집니다.",
        ("tectonic",),
        ("river", "delta", "glacial", "coastal", "arid", "volcanic", "karst"),
    ),
)


BASE_SCENARIOS: tuple[PhysicsLabScenario, ...] = (
    PhysicsLabScenario("v_valley", "V자곡", "하천 지형", "V자곡", "하천 침식력", "강수량", 60, 45, 25, 45_000),
    PhysicsLabScenario("alluvial_fan", "선상지", "하천 지형", "선상지", "퇴적물 공급", "경사 완화", 55, 35, 40, 35_000),
    PhysicsLabScenario("delta", "삼각주", "하구·삼각주", "삼각주", "퇴적물 공급", "해수면 안정성", 50, 20, 35, 35_000),
    PhysicsLabScenario("u_valley", "U자곡", "빙하 지형", "U자곡", "빙하 침식력", "빙하 두께", 65, 25, 20, 55_000),
    PhysicsLabScenario("coastal_cliff", "해식애", "해안 지형", "해식애", "파랑 에너지", "해수면 위치", 60, 20, 30, 40_000),
    PhysicsLabScenario("barchan", "바르한", "건조 지형", "바르한", "풍속", "모래 공급", 58, 10, 25, 30_000),
    PhysicsLabScenario("lava_dome", "용암돔", "화산 지형", "용암돔", "분출률", "점성/확산", 62, 35, 28, 28_000),
    PhysicsLabScenario("karst_doline", "돌리네", "카르스트 지형", "카르스트 돌리네", "용식 강도", "지하수 흐름", 52, 5, 22, 45_000),
)


def _scenario_from_catalog() -> tuple[PhysicsLabScenario, ...]:
    existing_ids = {scenario.landform_id for scenario in BASE_SCENARIOS}
    scenarios: list[PhysicsLabScenario] = []
    for item in list_additional_lab_scenarios():
        if item.landform_id in existing_ids:
            continue
        factor_defs = process_factor_definitions_for_scenario(item.landform_id)
        primary = factor_defs[0].label_ko if factor_defs else "주 작용 강도"
        secondary = factor_defs[1].label_ko if len(factor_defs) > 1 else "보조 조건"
        if item.group == "river":
            defaults = (58, 35, 34, 40_000)
        elif item.group == "coastal":
            defaults = (60, 24, 32, 42_000)
        elif item.group == "glacial":
            defaults = (63, 25, 24, 55_000)
        elif item.group == "volcanic":
            defaults = (62, 34, 28, 30_000)
        elif item.group == "karst":
            defaults = (56, 8, 24, 48_000)
        elif item.group == "arid":
            defaults = (58, 10, 25, 32_000)
        else:
            defaults = (55, 35, 35, 40_000)
        scenarios.append(
            PhysicsLabScenario(
                item.landform_id,
                item.title_ko,
                GROUP_LABELS_KO.get(item.group, item.group),
                item.title_ko,
                primary,
                secondary,
                *defaults,
            )
        )
    return tuple(scenarios)


def _generic_factor_labels(group: str) -> tuple[str, str, tuple[int, int, int, int]]:
    if group == "river":
        return "하천 침식·운반", "퇴적물 공급", (58, 35, 34, 40_000)
    if group == "delta":
        return "하천 퇴적 공급", "해수면·파랑 조건", (56, 25, 34, 38_000)
    if group == "coastal":
        return "파랑·연안류 에너지", "퇴적물/해수면 조건", (60, 24, 32, 42_000)
    if group == "glacial":
        return "빙하 침식·운반", "빙하 두께/융빙수", (63, 25, 24, 55_000)
    if group == "volcanic":
        return "분출·화산체 성장", "점성/함몰 조건", (62, 34, 28, 30_000)
    if group == "karst":
        return "용식 강도", "지하수 흐름", (56, 8, 24, 48_000)
    if group == "arid":
        return "바람·건조 침식", "퇴적물 공급", (58, 10, 25, 32_000)
    return "주 작용 강도", "보조 조건", (55, 35, 35, 40_000)


def _scenario_from_animation_catalog(existing_ids: set[str]) -> tuple[PhysicsLabScenario, ...]:
    scenarios: list[PhysicsLabScenario] = []
    for landform_id, title in sorted(KOREAN_TITLES.items(), key=lambda item: item[1]):
        if landform_id in existing_ids:
            continue
        group = LANDFORM_GROUP_BY_ID.get(landform_id, "river")
        primary, secondary, defaults = _generic_factor_labels(group)
        scenarios.append(
            PhysicsLabScenario(
                landform_id,
                title,
                LANDFORM_GROUP_LABELS.get(group, group),
                title,
                primary,
                secondary,
                *defaults,
            )
        )
    return tuple(scenarios)


CATALOG_SCENARIOS = _scenario_from_catalog()
SCENARIOS: tuple[PhysicsLabScenario, ...] = (
    BASE_SCENARIOS
    + CATALOG_SCENARIOS
    + _scenario_from_animation_catalog(
        {scenario.landform_id for scenario in BASE_SCENARIOS + CATALOG_SCENARIOS}
    )
)


THEORY_NOTES: dict[str, PhysicsLabTheory] = {
    "v_valley": PhysicsLabTheory(
        "v_valley",
        "하천 침식 + 사면 확산",
        (
            ("하천 침식", "E = K A^m S^n", "집수면적 A와 경사 S가 클수록 하방 침식이 커집니다."),
            ("사면 완화", "∂z/∂t = D∇²z", "경사가 급한 곳은 확산적으로 낮아지고 완만해집니다."),
            ("퇴적 한계", "Q_s ≤ Q_c", "운반능력보다 많은 퇴적물은 하류나 완경사부에 남습니다."),
        ),
        (
            "강수량은 유량과 집수 효과를 키우는 상대값으로 사용합니다.",
            "암석 차이와 식생 피복은 아직 하나의 침식계수 K 안에 묶여 있습니다.",
        ),
        "V자곡은 하방 침식이 사면 완화보다 우세할 때 깊고 좁은 골짜기로 발달합니다.",
    ),
    "alluvial_fan": PhysicsLabTheory(
        "alluvial_fan",
        "하천 운반능력 감소 + 퇴적",
        (
            ("운반능력", "Q_c ∝ Q S", "유량 Q와 경사 S가 낮아지면 운반 가능한 퇴적물 양이 줄어듭니다."),
            ("퇴적", "D_s = max(Q_s - Q_c, 0)", "운반능력을 넘는 퇴적물이 산지 출구에 쌓입니다."),
        ),
        (
            "선상지의 실제 입도 분급은 단순화해 퇴적물 공급과 경사 완화로 표현합니다.",
            "홍수 빈도와 유로 변동은 현재 하나의 시간 평균 효과로 처리합니다.",
        ),
        "선상지는 급경사 산지 하천이 완경사 평지로 나오며 에너지를 잃을 때 잘 발달합니다.",
    ),
    "delta": PhysicsLabTheory(
        "delta",
        "하천 퇴적 + 기준면/해수면 조건",
        (
            ("하천 공급", "D_s = f(Q_s, Q_c)", "하천이 운반한 퇴적물이 하구에서 쌓입니다."),
            ("기준면", "base level = sea level", "해수면이 안정적일수록 퇴적체가 넓게 보존됩니다."),
        ),
        (
            "파랑과 조석의 세부 분류는 아직 약한 해안 작용 항으로만 반영합니다.",
            "삼각주의 조류형·파랑형·하천형 구분은 다음 프리셋 확장 단계에서 나눕니다.",
        ),
        "삼각주는 하천 퇴적물 공급이 해안의 제거 작용보다 클 때 전진합니다.",
    ),
    "u_valley": PhysicsLabTheory(
        "u_valley",
        "빙하 침식 + 모레인 퇴적",
        (
            ("빙하 침식", "E_g ∝ H_i U_i |∇z|", "빙하 두께 H와 속도 U가 클수록 바닥 침식이 커집니다."),
            ("빙하 퇴적", "D_m = f(debris, retreat)", "빙하가 약해지거나 후퇴하면 암설이 남습니다."),
        ),
        (
            "빙하 역학은 교육용 상대 모델이며 실제 열역학·질량수지 계산은 단순화되어 있습니다.",
            "빙하 두께는 침식력과 유속을 동시에 키우는 보조 조건입니다.",
        ),
        "U자곡은 빙하가 골짜기 바닥과 양쪽 사면을 넓게 깎을 때 만들어집니다.",
    ),
    "coastal_cliff": PhysicsLabTheory(
        "coastal_cliff",
        "파랑 에너지 + 해안선 후퇴",
        (
            ("파랑 침식", "R_c ∝ W / R_r", "파랑 에너지 W가 크고 암석 저항 R이 작을수록 후퇴가 커집니다."),
            ("파식대", "P = flatten(z ≈ sea level)", "해수면 근처의 암반면이 반복적으로 깎여 평탄화됩니다."),
        ),
        (
            "조석, 암석 절리, 폭풍 파랑은 현재 파랑 에너지와 해수면 위치로 압축해 표현합니다.",
            "실제 해안선 좌표 변화가 아니라 격자 표면의 상대 후퇴로 계산합니다.",
        ),
        "해식애는 파랑 침식이 절벽 하부에 집중되고 상부가 붕괴하면서 후퇴합니다.",
    ),
    "barchan": PhysicsLabTheory(
        "barchan",
        "바람 운반 + 풍상/풍하 퇴적",
        (
            ("모래 이동", "q_s ∝ u_*^3", "풍속이 커질수록 모래 이동량이 빠르게 증가합니다."),
            ("풍상 침식", "E_s = f(stoss)", "바람을 맞는 쪽에서는 모래가 깎이고 이동합니다."),
            ("풍하 퇴적", "D_l = f(lee)", "그늘진 풍하면에는 모래가 쌓입니다."),
        ),
        (
            "현재 바람 방향은 고정된 주풍 방향장으로 계산합니다.",
            "모래 공급이 적고 바닥이 단단한 조건을 바르한 기본 조건으로 둡니다.",
        ),
        "바르한은 모래 공급이 제한된 곳에서 초승달 모양으로 이동하는 사구입니다.",
    ),
    "lava_dome": PhysicsLabTheory(
        "lava_dome",
        "화산 분출 + 점성 제한 확산",
        (
            ("분출 성장", "C_v = eruption rate", "중앙부 공급률이 클수록 돔이 높아집니다."),
            ("점성 저항", "spread ∝ 1 / viscosity", "점성이 클수록 멀리 흐르지 못하고 중심부에 쌓입니다."),
            ("냉각 제한", "L_c = f(cooling)", "냉각이 빠르면 확산 범위가 작아집니다."),
        ),
        (
            "용암 온도, 결정 함량, 붕괴류는 현재 점성/확산 슬라이더로 묶여 있습니다.",
            "성층화산·순상화산은 같은 화산 모듈의 다른 프리셋으로 확장할 예정입니다.",
        ),
        "용암돔은 점성이 큰 용암이 분화구 주변에 두껍게 쌓이며 성장합니다.",
    ),
    "karst_doline": PhysicsLabTheory(
        "karst_doline",
        "용식 + 지하수 집중 + 붕괴 위험",
        (
            ("용식률", "S_r ∝ water × solubility", "물 공급과 석회암 용해도가 클수록 지표가 낮아집니다."),
            ("지하 배수", "G = ∇h_w", "지하수 흐름이 집중되는 곳에서 용식이 커집니다."),
            ("붕괴 위험", "C_r = f(void, slope)", "지하 공동과 경사가 커지면 함몰 가능성이 커집니다."),
        ),
        (
            "석회암 순도와 절리망은 현재 용식 강도 안에 통합되어 있습니다.",
            "동굴 네트워크는 명시적 3D 공간으로 계산하지 않고 표면 변화로 환산합니다.",
        ),
        "돌리네는 석회암 용식과 지하 배수 집중, 때로는 붕괴가 함께 만든 폐쇄 와지입니다.",
    ),
}


FAMILY_THEORY_NOTES: dict[str, PhysicsLabTheory] = {
    "river": THEORY_NOTES["alluvial_fan"],
    "river_delta": THEORY_NOTES["delta"],
    "coastal": THEORY_NOTES["coastal_cliff"],
    "coastal_marine": THEORY_NOTES["coastal_cliff"],
    "glacial": THEORY_NOTES["u_valley"],
    "volcanic": THEORY_NOTES["lava_dome"],
    "karst": THEORY_NOTES["karst_doline"],
    "arid": THEORY_NOTES["barchan"],
}


def list_physics_lab_scenarios() -> tuple[PhysicsLabScenario, ...]:
    return SCENARIOS


def list_force_module_specs() -> tuple[ForceModuleSpec, ...]:
    return FORCE_MODULE_SPECS


def _scenario_group_key(landform_id: str) -> str:
    catalog = next((scenario for scenario in list_additional_lab_scenarios() if scenario.landform_id == landform_id), None)
    if catalog is not None:
        return catalog.group
    return LANDFORM_GROUP_BY_ID.get(landform_id, "")


def force_module_specs_for_scenario(landform_id: str) -> tuple[ForceModuleSpec, ...]:
    group = _scenario_group_key(landform_id)
    active = []
    for module in FORCE_MODULE_SPECS:
        if landform_id in module.scenario_ids or group in module.scenario_groups:
            active.append(module)
    return tuple(active)


def force_module_rows_for_scenario(landform_id: str) -> tuple[dict[str, str], ...]:
    return tuple(
        {
            "작용 모듈": module.label_ko,
            "구분": module.force_type,
            "대표식": module.equation,
            "교육적 의미": module.classroom_meaning,
            "출력 필드": ", ".join(module.output_fields),
        }
        for module in force_module_specs_for_scenario(landform_id)
    )


def _force_module_payload(module: ForceModuleSpec) -> dict[str, Any]:
    return {
        "module_id": module.module_id,
        "label_ko": module.label_ko,
        "force_type": module.force_type,
        "equation": module.equation,
        "classroom_meaning": module.classroom_meaning,
        "output_fields": tuple(module.output_fields),
        "scenario_groups": tuple(module.scenario_groups),
        "scenario_ids": tuple(module.scenario_ids),
    }


def _field_activity(process_fields: dict[str, Any], field_name: str) -> float:
    value = process_fields.get(field_name)
    if value is None:
        return 0.0
    array = np.nan_to_num(np.asarray(value, dtype=float), nan=0.0, posinf=0.0, neginf=0.0)
    return float(np.sum(np.abs(array)))


def _active_force_field_rows(process_fields: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    rows = []
    for field_name in sorted(process_fields):
        activity = _field_activity(process_fields, field_name)
        if activity <= 0.0:
            continue
        rows.append({"field": field_name, "activity": activity})
    rows.sort(key=lambda row: float(row["activity"]), reverse=True)
    return tuple(rows)


def _force_module_diagnostics(
    landform_id: str,
    process_history: list[dict[str, Any]],
) -> tuple[dict[str, Any], ...]:
    final_fields = process_history[-1] if process_history else {}
    diagnostics = []
    for module in force_module_specs_for_scenario(landform_id):
        field_activities = {
            field_name: _field_activity(final_fields, field_name)
            for field_name in module.output_fields
        }
        active_fields = tuple(
            field_name
            for field_name, activity in field_activities.items()
            if activity > 0.0
        )
        diagnostics.append(
            {
                "module_id": module.module_id,
                "label_ko": module.label_ko,
                "force_type": module.force_type,
                "equation": module.equation,
                "output_fields": tuple(module.output_fields),
                "active_fields": active_fields,
                "activity": float(sum(field_activities.values())),
                "status": "active" if active_fields else "available",
            }
        )
    return tuple(diagnostics)


def _attach_force_module_runtime(result: dict[str, Any], landform_id: str) -> dict[str, Any]:
    process_history = list(result.get("process_history") or [])
    result["force_modules"] = tuple(
        _force_module_payload(module)
        for module in force_module_specs_for_scenario(landform_id)
    )
    result["active_force_fields"] = _active_force_field_rows(process_history[-1] if process_history else {})
    result["module_diagnostics"] = _force_module_diagnostics(landform_id, process_history)
    return result


def get_physics_lab_theory(landform_id: str) -> PhysicsLabTheory:
    if landform_id in THEORY_NOTES:
        return THEORY_NOTES[landform_id]
    catalog = next((scenario for scenario in list_additional_lab_scenarios() if scenario.landform_id == landform_id), None)
    if catalog is not None:
        return FAMILY_THEORY_NOTES.get(catalog.simulation_family, FAMILY_THEORY_NOTES.get(catalog.group, THEORY_NOTES["v_valley"]))
    group = LANDFORM_GROUP_BY_ID.get(landform_id)
    if group is not None:
        return FAMILY_THEORY_NOTES.get(group, THEORY_NOTES["v_valley"])
    return THEORY_NOTES["v_valley"]


def active_physics_lab_rows() -> tuple[dict[str, str], ...]:
    return tuple(
        {
            "상태": "실험 가능",
            "지형": scenario.title,
            "분류": scenario.group,
            "주 작용": scenario.primary_factor,
            "보조 조건": scenario.secondary_factor,
            "모델 계열": get_physics_lab_theory(scenario.landform_id).model_family,
        }
        for scenario in SCENARIOS
    )


def planned_physics_lab_rows() -> tuple[dict[str, str], ...]:
    active_ids = {scenario.landform_id for scenario in SCENARIOS}
    rows = []
    image_sequence_root = PROJECT_ROOT / "assets" / "cinematic" / "image_sequence"
    if not image_sequence_root.exists():
        return ()
    for path in sorted(item for item in image_sequence_root.iterdir() if item.is_dir()):
        landform_id = path.name
        if landform_id.startswith("_") or landform_id in active_ids:
            continue
        rows.append(
            {
                "상태": "프리셋 예정",
                "지형": KOREAN_TITLES.get(landform_id, landform_id.replace("_", " ")),
                "분류": "분류 매핑 예정",
                "주 작용": "계열 판정 필요",
                "보조 조건": "초기조건/검증지표 설계 필요",
                "모델 계열": "공통 엔진 프리셋 예정",
            }
        )
    return tuple(rows)


def get_physics_lab_scenario(landform_id: str) -> PhysicsLabScenario:
    for scenario in SCENARIOS:
        if scenario.landform_id == landform_id:
            return scenario
    return SCENARIOS[0]


def _map_range(value: int | float, low: float, high: float) -> float:
    value = float(np.clip(value, 0, 100))
    return low + (value / 100.0) * (high - low)


def _normalize_surface(surface: np.ndarray) -> np.ndarray:
    array = np.asarray(surface, dtype=float)
    return np.nan_to_num(array, nan=0.0, posinf=0.0, neginf=0.0)


def _change_summary(initial: np.ndarray, final: np.ndarray) -> dict[str, float]:
    change = _normalize_surface(final) - _normalize_surface(initial)
    return {
        "mean_change": float(np.mean(change)),
        "max_uplift": float(np.max(change)),
        "max_lowering": float(np.min(change)),
        "relief": float(np.max(final) - np.min(final)),
        "active_fraction": float(np.mean(np.abs(change) >= max(float(np.max(np.abs(change))) * 0.25, 1e-9))),
    }


def validate_lab_result_contract(result: dict[str, Any]) -> tuple[str, ...]:
    """Return issue codes for Lab simulation contract violations."""
    issues: list[str] = []
    required_keys = ("history", "times", "process_history", "stats_history", "kernel")
    for key in required_keys:
        if key not in result:
            issues.append(f"missing:{key}")
    if "config" not in result and "parameters" not in result:
        issues.append("missing:config_or_parameters")
    for key in ("force_modules", "active_force_fields", "module_diagnostics"):
        if key in result and not isinstance(result[key], tuple):
            issues.append(f"{key}:not_tuple")

    history = result.get("history")
    times = result.get("times")
    process_history = result.get("process_history")
    stats_history = result.get("stats_history")

    if not isinstance(history, list) or not history:
        issues.append("history:empty")
        return tuple(issues)
    if not isinstance(times, list) or len(times) != len(history):
        issues.append("times:length_mismatch")
    if not isinstance(process_history, list) or len(process_history) != len(history):
        issues.append("process_history:length_mismatch")
    if not isinstance(stats_history, list) or len(stats_history) != len(history):
        issues.append("stats_history:length_mismatch")

    frame_shape: tuple[int, ...] | None = None
    for idx, frame in enumerate(history):
        array = np.asarray(frame, dtype=float)
        if array.ndim != 2:
            issues.append(f"history:{idx}:not_2d")
            continue
        if frame_shape is None:
            frame_shape = array.shape
        elif array.shape != frame_shape:
            issues.append(f"history:{idx}:shape_mismatch")
        if not bool(np.isfinite(array).all()):
            issues.append(f"history:{idx}:nonfinite")

    if isinstance(times, list):
        numeric_times = np.asarray(times, dtype=float)
        if not bool(np.isfinite(numeric_times).all()):
            issues.append("times:nonfinite")
        elif numeric_times.size > 1 and bool(np.any(np.diff(numeric_times) < 0.0)):
            issues.append("times:not_monotonic")

    if frame_shape is not None and isinstance(process_history, list) and process_history:
        final_fields = process_history[-1]
        if not isinstance(final_fields, dict):
            issues.append("process_history:final_not_dict")
        else:
            for key, value in final_fields.items():
                array = np.asarray(value, dtype=float)
                if array.shape != frame_shape:
                    issues.append(f"process_field:{key}:shape_mismatch")
                if not bool(np.isfinite(array).all()):
                    issues.append(f"process_field:{key}:nonfinite")

    diagnostics = result.get("module_diagnostics")
    if isinstance(diagnostics, tuple):
        process_fields = process_history[-1] if isinstance(process_history, list) and process_history else {}
        for idx, diagnostic in enumerate(diagnostics):
            if not isinstance(diagnostic, dict):
                issues.append(f"module_diagnostic:{idx}:not_dict")
                continue
            for field_name in diagnostic.get("active_fields", ()):
                if field_name not in process_fields:
                    issues.append(f"module_diagnostic:{idx}:unknown_field:{field_name}")

    return tuple(issues)


def _run_river_kernel_scenario(
    scenario: PhysicsLabScenario,
    *,
    force: int,
    secondary: int,
    uplift: int,
    diffusion: int,
    total_time: int,
    grid_size: int,
) -> dict[str, Any]:
    force_scale = _map_range(force, 0.55, 2.2)
    secondary_scale = _map_range(secondary, 0.55, 1.9)
    deposition_scale = 1.0
    water_scale = secondary_scale
    sediment_scale = 1.0
    base_level = 0.0

    if scenario.landform_id == "alluvial_fan":
        sediment_scale = force_scale
        deposition_scale = _map_range(secondary, 0.75, 1.9)
        water_scale = _map_range(100 - secondary, 0.75, 1.35)
    elif scenario.landform_id == "delta":
        sediment_scale = force_scale
        deposition_scale = _map_range(secondary, 0.7, 1.8)
        water_scale = _map_range(force, 0.75, 1.45)
        base_level = _map_range(secondary, -2.0, 8.0)

    params = RiverKernelParameters(
        landform_id=scenario.landform_id,
        grid_size=grid_size,
        total_time_years=total_time,
        erodibility_k=_map_range(force, 0.000035, 0.00042),
        diffusion_d=_map_range(diffusion, 0.006, 0.052),
        uplift_rate=_map_range(uplift, -0.00008, 0.00042),
        water_discharge_scale=water_scale,
        sediment_supply_scale=sediment_scale,
        deposition_rate=0.36 * deposition_scale,
        base_level=base_level,
    )
    raw = run_river_morphology_model(params)
    history = [_normalize_surface(frame) for frame in raw["history"]]
    stats_history = list(raw["stats_history"])
    process_history = list(raw["process_history"])
    stage_history = build_lab_stage_history(scenario.model_label, stats_history, process_history)
    final_stage = describe_lab_process_stage(
        scenario.model_label,
        1.0,
        stats_history[-1] if stats_history else None,
        process_fields=process_history[-1] if process_history else None,
    )
    return {
        "scenario": scenario,
        "config": params,
        "history": history,
        "times": list(raw["times"]),
        "stats_history": stats_history,
        "process_history": process_history,
        "stage_history": stage_history,
        "final_stage": final_stage,
        "change": _change_summary(history[0], history[-1]),
        "metrics": compute_morphometric_metrics(scenario.landform_id, history, process_history),
        "dominant_process": format_process_summary(stats_history[-1] if stats_history else None),
        "kernel": raw["kernel"],
        "kernel_notes": (
            "Stream Power Law(E=K A^m S^n), 사면 확산, 퇴적물 운반/퇴적, "
            "기저면 조건을 결합한 하천 지형 커널 v1입니다."
        ),
    }


def _run_process_kernel_scenario(
    scenario: PhysicsLabScenario,
    *,
    force: int,
    secondary: int,
    uplift: int,
    diffusion: int,
    total_time: int,
    grid_size: int,
) -> dict[str, Any]:
    params = ProcessKernelParameters(
        landform_id=scenario.landform_id,
        grid_size=grid_size,
        total_time_years=total_time,
        force_scale=_map_range(force, 0.45, 2.35),
        secondary_scale=_map_range(secondary, 0.45, 2.0),
        uplift_rate=_map_range(uplift, -0.00008, 0.00038),
        diffusion_d=_map_range(diffusion, 0.004, 0.052),
        base_level=0.0,
    )
    raw = run_process_morphology_model(params)
    history = [_normalize_surface(frame) for frame in raw["history"]]
    stats_history = list(raw["stats_history"])
    process_history = list(raw["process_history"])
    stage_history = build_lab_stage_history(scenario.model_label, stats_history, process_history)
    final_stage = describe_lab_process_stage(
        scenario.model_label,
        1.0,
        stats_history[-1] if stats_history else None,
        process_fields=process_history[-1] if process_history else None,
    )
    return {
        "scenario": scenario,
        "config": params,
        "history": history,
        "times": list(raw["times"]),
        "stats_history": stats_history,
        "process_history": process_history,
        "stage_history": stage_history,
        "final_stage": final_stage,
        "change": _change_summary(history[0], history[-1]),
        "metrics": compute_morphometric_metrics(scenario.landform_id, history, process_history),
        "dominant_process": format_process_summary(stats_history[-1] if stats_history else None),
        "kernel": raw["kernel"],
        "kernel_notes": (
            "계열별 물리 작용장을 직접 계산하는 process kernel v1입니다. "
            "각 프레임은 표면고도, 침식·퇴적·운반·구조 작용장을 함께 반환합니다."
        ),
    }


def _scenario_engine_parameters(
    scenario: PhysicsLabScenario,
    *,
    force: int,
    secondary: int,
    uplift: int,
    diffusion: int,
    total_time: int,
    grid_size: int,
) -> GeomorphicEngineParameters:
    primary = _map_range(force, 0.0, 2.2)
    support = _map_range(secondary, 0.0, 1.8)
    uplift_rate = _map_range(uplift, -0.00008, 0.00042)
    diffusion_d = _map_range(diffusion, 0.004, 0.052)
    process: dict[str, float] = {
        "fluvial": 0.0,
        "sediment": max(support, 0.15),
        "marine": 0.0,
        "glacial": 0.0,
        "aeolian": 0.0,
        "volcanic": 0.0,
        "karst": 0.0,
        "groundwater": 0.0,
    }
    base_level = 0.0
    engine_preset_id = _engine_preset_id(scenario.landform_id)

    group = LANDFORM_GROUP_BY_ID.get(scenario.landform_id, "")

    if scenario.landform_id == "v_valley":
        process.update(fluvial=primary, sediment=0.35 + support * 0.35)
    elif scenario.landform_id in {"alluvial_fan", "oxbow_lake", "floodplain_natural_levee", "river_terrace"} or group == "river":
        process.update(fluvial=0.55 + primary * 0.55, sediment=0.85 + primary * 0.75 + support * 0.45)
        uplift_rate *= 0.45
        if scenario.landform_id in {"river_terrace", "waterfall"}:
            uplift_rate = max(uplift_rate, 0.00008 + primary * 0.00004)
            process["sediment"] *= 0.6
        if scenario.landform_id in {"oxbow_lake", "free_meander"}:
            process["sediment"] *= 0.9
            diffusion_d *= 1.15
    elif scenario.landform_id == "delta" or group == "delta":
        process.update(fluvial=0.45 + primary * 0.45, sediment=1.1 + primary * 0.9 + support * 0.45, marine=0.02 + support * 0.08)
        uplift_rate *= 0.3
        base_level = _map_range(secondary, -2.0, 8.0)
        if scenario.landform_id in {"estuary", "ria_coast"}:
            process["marine"] = 0.45 + primary * 0.35
            process["sediment"] *= 0.65
    elif scenario.landform_id in {"u_valley", "moraine", "drumlin", "esker", "kettle_lake", "outwash_plain", "thermokarst"} or group == "glacial":
        process.update(glacial=primary, sediment=0.45 + support * 0.4)
        if scenario.landform_id in {"esker", "outwash_plain"}:
            process.update(fluvial=0.35 + support * 0.45, sediment=0.85 + support * 0.75)
        if scenario.landform_id in {"kettle_lake", "thermokarst"}:
            process.update(karst=0.15 + support * 0.25, groundwater=0.25 + support * 0.45)
    elif scenario.landform_id in {"coastal_cliff", "sea_cave_stack", "wave_cut_platform", "barrier_island", "tidal_flat", "marine_terrace"} or group == "coastal":
        process.update(marine=primary, sediment=0.35 + support * 0.35)
        if scenario.landform_id in {"barrier_island", "tidal_flat", "spit_lagoon", "tombolo", "coastal_dune"}:
            process["sediment"] = 0.85 + support * 0.8
            process["marine"] = 0.35 + primary * 0.45
        if scenario.landform_id == "marine_terrace":
            uplift_rate = max(uplift_rate, 0.0001 + primary * 0.00003)
        base_level = _map_range(secondary, -4.0, 6.0)
    elif scenario.landform_id == "barchan" or group == "arid":
        process.update(aeolian=primary, sediment=0.55 + support * 0.7)
        if scenario.landform_id in {"pediment", "wadi", "playa"}:
            process.update(fluvial=0.12 + support * 0.25)
        if scenario.landform_id in {"mesa_butte", "pedestal_rock"}:
            diffusion_d *= 0.65
        uplift_rate *= 0.1
    elif scenario.landform_id in {"lava_dome", "maar", "cinder_cone"} or group == "volcanic":
        process.update(volcanic=primary, sediment=0.35 + support * 0.2)
        diffusion_d = _map_range(secondary, 0.006, 0.06)
        if scenario.landform_id in {"maar", "crater_lake", "caldera"}:
            process.update(groundwater=0.35 + support * 0.55, karst=0.15 + support * 0.25)
            diffusion_d *= 1.2
            if scenario.landform_id == "maar":
                process["sediment"] = 0.55 + support * 0.35
        if scenario.landform_id in {"cinder_cone", "stratovolcano"}:
            process["sediment"] = 0.65 + support * 0.45
            diffusion_d *= 0.75
        if scenario.landform_id in {"shield_volcano", "lava_plateau"}:
            diffusion_d *= 1.45
    elif scenario.landform_id in {"karst_doline", "polje"} or group == "karst":
        process.update(karst=primary, groundwater=0.45 + support, sediment=0.25 + support * 0.2)
        uplift_rate *= 0.2
        if scenario.landform_id in {"polje", "uvala"}:
            process["sediment"] = 0.35 + support * 0.45
            diffusion_d *= 1.4

    return GeomorphicEngineParameters(
        preset_id=engine_preset_id,
        grid_size=grid_size,
        total_time_years=total_time,
        fluvial=process["fluvial"],
        sediment=process["sediment"],
        marine=process["marine"],
        glacial=process["glacial"],
        aeolian=process["aeolian"],
        volcanic=process["volcanic"],
        karst=process["karst"],
        groundwater=process["groundwater"],
        uplift_rate=uplift_rate,
        diffusion_d=diffusion_d,
        base_level=base_level,
        sea_level=base_level if process["marine"] > 0.0 else None,
        wave_energy_scale=0.75 + process["marine"] * 0.22,
        wind_direction_degrees=_map_range(secondary, 62.0, 118.0) if process["aeolian"] > 0.0 else 90.0,
        wind_speed=process["aeolian"] if process["aeolian"] > 0.0 else None,
        sand_supply=process["sediment"] if process["aeolian"] > 0.0 else None,
        eruption_rate=process["volcanic"] if process["volcanic"] > 0.0 else None,
        explosion_energy=_map_range(force, 0.45, 1.8) if scenario.landform_id in {"maar", "caldera", "crater_lake"} else 0.0,
        magma_water_contact=_map_range(secondary, 0.35, 1.6) if scenario.landform_id in {"maar", "crater_lake"} else 0.0,
        pyroclastic_supply=_map_range(secondary, 0.35, 1.5) if scenario.landform_id in {"cinder_cone", "stratovolcano"} else 0.0,
        viscosity=np.clip(_map_range(100 - secondary, 0.12, 0.95), 0.05, 1.0) if process["volcanic"] > 0.0 else None,
        lava_spread=_map_range(secondary, 0.65, 1.85) if process["volcanic"] > 0.0 else 1.0,
        cooling_rate=_map_range(100 - secondary, 0.55, 1.55) if process["volcanic"] > 0.0 else 1.0,
        rock_solubility=0.65 + process["karst"] * 0.24 if process["karst"] > 0.0 else 1.0,
        water_supply=process["groundwater"] if process["groundwater"] > 0.0 else None,
        fracture_density=_map_range(force, 0.55, 1.8) if process["karst"] > 0.0 else 1.0,
        seasonal_flooding=_map_range(secondary, 0.25, 1.6) if scenario.landform_id in {"polje", "uvala"} else 0.0,
    )


def _engine_preset_id(landform_id: str) -> str:
    group = LANDFORM_GROUP_BY_ID.get(landform_id, "")
    if landform_id == "v_valley":
        return "v_valley"
    if landform_id == "delta" or group == "delta":
        return "delta"
    if landform_id in {"alluvial_fan", "oxbow_lake", "floodplain_natural_levee", "river_terrace"} or group == "river":
        return "alluvial_fan"
    if landform_id in {"u_valley", "moraine", "drumlin", "esker", "kettle_lake", "outwash_plain", "thermokarst"} or group == "glacial":
        return "u_valley"
    if landform_id in {"wave_cut_platform", "spit_lagoon", "tombolo", "marine_terrace"}:
        return landform_id
    if landform_id in {"coastal_cliff", "sea_cave_stack", "barrier_island", "tidal_flat"} or group == "coastal":
        return "coastal_cliff"
    if landform_id == "barchan" or group == "arid":
        return "barchan"
    if landform_id in {"maar", "cinder_cone"}:
        return landform_id
    if landform_id in {"stratovolcano", "shield_volcano", "lava_plateau"}:
        return landform_id
    if landform_id in {"lava_dome"} or group == "volcanic":
        return "lava_dome"
    if landform_id in {"polje"}:
        return "polje"
    if landform_id in {"tower_karst", "karren", "uvala"}:
        return landform_id
    if landform_id in {"karst_doline"} or group == "karst":
        return "karst_doline"
    return landform_id


def _run_common_engine_scenario(
    scenario: PhysicsLabScenario,
    *,
    force: int,
    secondary: int,
    uplift: int,
    diffusion: int,
    total_time: int,
    grid_size: int,
) -> dict[str, Any]:
    params = _scenario_engine_parameters(
        scenario,
        force=force,
        secondary=secondary,
        uplift=uplift,
        diffusion=diffusion,
        total_time=total_time,
        grid_size=grid_size,
    )
    raw = run_geomorphic_engine(params)
    history = [_normalize_surface(frame) for frame in raw["history"]]
    stats_history = list(raw["stats_history"])
    process_history = list(raw["process_history"])
    stage_history = build_lab_stage_history(scenario.model_label, stats_history, process_history)
    final_stage = describe_lab_process_stage(
        scenario.model_label,
        1.0,
        stats_history[-1] if stats_history else None,
        process_fields=process_history[-1] if process_history else None,
    )
    return _attach_force_module_runtime({
        "scenario": scenario,
        "config": params,
        "history": history,
        "times": list(raw["times"]),
        "stats_history": stats_history,
        "process_history": process_history,
        "stage_history": stage_history,
        "final_stage": final_stage,
        "change": _change_summary(history[0], history[-1]),
        "metrics": compute_morphometric_metrics(scenario.landform_id, history, process_history),
        "dominant_process": format_process_summary(stats_history[-1] if stats_history else None),
        "kernel": raw["kernel"],
        "kernel_notes": (
            "공통 지형물리 엔진 v2입니다. 지형별 전용 식이 아니라 하천·해안·빙하·바람·화산·"
            "카르스트·구조운동·사면확산 작용장을 같은 시간 적분 루프에서 합산합니다."
        ),
    }, scenario.landform_id)


def _apply_user_factors(
    lem: Any,
    scenario: PhysicsLabScenario,
    *,
    force: int,
    secondary: int,
) -> None:
    force_scale = _map_range(force, 0.45, 2.25)
    secondary_scale = _map_range(secondary, 0.55, 1.85)

    if scenario.landform_id in {"v_valley", "alluvial_fan", "delta"}:
        lem.precipitation *= secondary_scale
        lem.K *= force_scale
        lem.enable_sediment_transport = True
    elif scenario.landform_id == "u_valley":
        lem.Kg *= force_scale
        lem.glacier_ela = _map_range(100 - secondary, 80.0, 260.0)
        lem.enable_glacial = True
        lem.enable_glacial_deposit = True
    elif scenario.landform_id == "coastal_cliff":
        lem.Km *= force_scale
        lem.sea_level = _map_range(secondary, -10.0, 45.0)
        lem.enable_marine = True
    elif scenario.landform_id == "barchan":
        lem.Ka *= force_scale
        lem.wind_direction = _map_range(secondary, -0.8, 0.8)
        lem.enable_aeolian = True
    elif scenario.landform_id == "lava_dome":
        lem.volcanic_rate *= force_scale
        lem.D *= _map_range(secondary, 0.35, 1.65)
        lem.enable_volcanic = True
    elif scenario.landform_id == "karst_doline":
        lem.Kk *= force_scale
        lem.water_table = _map_range(secondary, 20.0, 90.0)
        lem.enable_karst = True
        lem.enable_groundwater = True


@lru_cache(maxsize=64)
def run_physics_lab_simulation(
    landform_id: str,
    force: int,
    secondary: int,
    uplift: int,
    diffusion: int,
    total_time: int,
    grid_size: int,
) -> dict[str, Any]:
    scenario = get_physics_lab_scenario(landform_id)
    if scenario.landform_id in {item.landform_id for item in SCENARIOS}:
        return _run_common_engine_scenario(
            scenario,
            force=force,
            secondary=secondary,
            uplift=uplift,
            diffusion=diffusion,
            total_time=total_time,
            grid_size=grid_size,
        )

    lem = create_lab_simple_lem(
        grid_size=grid_size,
        K=_map_range(force, 0.000015, 0.00055),
        D=_map_range(diffusion, 0.0008, 0.055),
        U=_map_range(uplift, -0.00012, 0.00065),
        enable_isostasy=False,
        enable_karst=scenario.landform_id == "karst_doline",
        enable_exner=True,
        enable_slope_stability=True,
    )
    config = configure_lab_scenario(lem, selected_landform=scenario.model_label, grid_size=grid_size)
    _apply_user_factors(lem, scenario, force=force, secondary=secondary)

    dt = 250.0
    total_time = int(np.clip(total_time, 5_000, 120_000))
    save_interval = max(int(total_time / dt / 24), 1)
    history, times = lem.run(total_time=total_time, dt=dt, save_interval=save_interval, verbose=False)
    stage_history = build_lab_stage_history(scenario.model_label, lem.stats_history, lem.process_history)
    final_stage = describe_lab_process_stage(
        scenario.model_label,
        1.0,
        lem.stats_history[-1] if lem.stats_history else None,
        process_fields=lem.process_history[-1] if lem.process_history else None,
    )

    return _attach_force_module_runtime({
        "scenario": scenario,
        "config": config,
        "history": [_normalize_surface(frame) for frame in history],
        "times": list(times),
        "stats_history": list(lem.stats_history),
        "process_history": list(lem.process_history),
        "stage_history": stage_history,
        "final_stage": final_stage,
        "change": _change_summary(history[0], history[-1]),
        "metrics": compute_morphometric_metrics(scenario.landform_id, history, list(lem.process_history)),
        "dominant_process": format_process_summary(lem.stats_history[-1] if lem.stats_history else None),
        "kernel": "simple_lem",
        "kernel_notes": "기존 SimpleLEM 기반 실험 경로입니다. 계열별 전용 커널로 순차 교체할 예정입니다.",
    }, scenario.landform_id)
