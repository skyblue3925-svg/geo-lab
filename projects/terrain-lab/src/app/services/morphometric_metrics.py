from __future__ import annotations

from typing import Any

import numpy as np


def _field(process_fields: dict[str, Any], key: str, shape: tuple[int, int]) -> np.ndarray:
    value = process_fields.get(key)
    if value is None:
        return np.zeros(shape, dtype=float)
    return np.nan_to_num(np.asarray(value, dtype=float), nan=0.0, posinf=0.0, neginf=0.0)


def _safe_ratio(numerator: float, denominator: float) -> float:
    if abs(denominator) <= 1e-12:
        return 0.0
    return float(numerator / denominator)


def _centerline_concentration(field: np.ndarray) -> float:
    magnitude = np.abs(field)
    total = float(np.sum(magnitude))
    if total <= 0.0:
        return 0.0
    cols = magnitude.shape[1]
    width = max(cols // 8, 1)
    center = cols // 2
    return float(np.sum(magnitude[:, center - width : center + width + 1]) / total)


def _lower_half_fraction(field: np.ndarray) -> float:
    magnitude = np.abs(field)
    total = float(np.sum(magnitude))
    if total <= 0.0:
        return 0.0
    split = max(magnitude.shape[0] // 2, 1)
    return float(np.sum(magnitude[split:, :]) / total)


def _shoreline_concentration(field: np.ndarray) -> float:
    magnitude = np.abs(field)
    total = float(np.sum(magnitude))
    if total <= 0.0:
        return 0.0
    cols = magnitude.shape[1]
    start = int(cols * 0.55)
    end = int(cols * 0.82)
    return float(np.sum(magnitude[:, start:end]) / total)


def _radial_concentration(field: np.ndarray, radius: float) -> float:
    magnitude = np.abs(field)
    total = float(np.sum(magnitude))
    if total <= 0.0:
        return 0.0
    rows, cols = magnitude.shape
    y, x = np.indices(magnitude.shape, dtype=float)
    r = np.hypot((x / max(cols - 1, 1)) - 0.5, (y / max(rows - 1, 1)) - 0.5)
    return float(np.sum(magnitude[r <= radius]) / total)


def _weighted_lateral_spread(field: np.ndarray, row_start_fraction: float) -> float:
    magnitude = np.maximum(np.asarray(field, dtype=float), 0.0)
    rows, cols = magnitude.shape
    start = int(rows * row_start_fraction)
    window = magnitude[start:, :]
    total = float(np.sum(window))
    if total <= 0.0:
        return 0.0
    x = np.linspace(-1.0, 1.0, cols)
    weights = np.sum(window, axis=0)
    mean = float(np.sum(weights * x) / total)
    variance = float(np.sum(weights * np.square(x - mean)) / total)
    return float(np.clip(np.sqrt(max(variance, 0.0)), 0.0, 1.0))


def _cross_section_profile(surface: np.ndarray) -> np.ndarray:
    rows = surface.shape[0]
    start = int(rows * 0.38)
    end = max(int(rows * 0.62), start + 1)
    return np.mean(surface[start:end, :], axis=0)


def _valley_depth_index(surface: np.ndarray) -> float:
    profile = _cross_section_profile(surface)
    cols = profile.shape[0]
    width = max(cols // 10, 1)
    center = cols // 2
    center_mean = float(np.mean(profile[center - width : center + width + 1]))
    side_width = max(cols // 5, 1)
    side_mean = float(np.mean(np.concatenate([profile[:side_width], profile[-side_width:]])))
    relief = max(float(np.max(surface) - np.min(surface)), 1e-9)
    return float(np.clip((side_mean - center_mean) / relief, 0.0, 1.0))


def _u_floor_width_index(surface: np.ndarray) -> float:
    profile = _cross_section_profile(surface)
    span = max(float(np.max(profile) - np.min(profile)), 1e-9)
    low_floor = profile <= float(np.min(profile)) + span * 0.22
    cols = profile.shape[0]
    center = cols // 2
    central_band = low_floor[max(center - cols // 4, 0) : min(center + cols // 4 + 1, cols)]
    return float(np.mean(central_band))


def _shoreline_gradient_index(surface: np.ndarray) -> float:
    _gy, gx = np.gradient(surface)
    cols = surface.shape[1]
    start = int(cols * 0.58)
    end = max(int(cols * 0.76), start + 1)
    shore_grad = float(np.mean(np.abs(gx[:, start:end])))
    total_grad = float(np.mean(np.abs(gx))) + 1e-9
    return float(np.clip(shore_grad / total_grad, 0.0, 5.0))


def _radial_symmetry_index(surface: np.ndarray) -> float:
    rows, cols = surface.shape
    y, x = np.indices(surface.shape, dtype=float)
    r = np.hypot((x / max(cols - 1, 1)) - 0.5, (y / max(rows - 1, 1)) - 0.5)
    bins = np.linspace(0.0, 0.55, 9)
    penalties: list[float] = []
    for low, high in zip(bins[:-1], bins[1:], strict=False):
        mask = (r >= low) & (r < high)
        if np.count_nonzero(mask) < 4:
            continue
        values = surface[mask]
        penalties.append(float(np.std(values) / (abs(float(np.mean(values))) + 1e-9)))
    if not penalties:
        return 0.0
    return float(np.clip(1.0 / (1.0 + float(np.mean(penalties))), 0.0, 1.0))


def _central_depression_index(surface: np.ndarray) -> float:
    rows, cols = surface.shape
    y, x = np.indices(surface.shape, dtype=float)
    r = np.hypot((x / max(cols - 1, 1)) - 0.5, (y / max(rows - 1, 1)) - 0.5)
    center = float(np.mean(surface[r <= 0.16]))
    rim = float(np.mean(surface[(r >= 0.24) & (r <= 0.38)]))
    relief = max(float(np.max(surface) - np.min(surface)), 1e-9)
    return float(np.clip((rim - center) / relief, 0.0, 1.0))


def compute_morphometric_metrics(
    landform_id: str,
    history: list[np.ndarray],
    process_history: list[dict[str, Any]],
) -> dict[str, float | str]:
    if not history:
        return {}
    initial = np.asarray(history[0], dtype=float)
    final = np.asarray(history[-1], dtype=float)
    change = final - initial
    fields = process_history[-1] if process_history else {}
    shape = final.shape

    erosion = _field(fields, "total_erosion", shape)
    deposition = _field(fields, "deposition", shape)
    diffusion = _field(fields, "diffusion", shape)
    transport = _field(fields, "transport", shape)
    tectonic = _field(fields, "tectonic", shape)
    glacial = _field(fields, "glacial", shape)
    marine = _field(fields, "marine", shape)
    wave_energy = _field(fields, "wave_energy", shape)
    shoreline_retreat = _field(fields, "shoreline_retreat", shape)
    wave_cut_platform = _field(fields, "wave_cut_platform", shape)
    beach_deposition = _field(fields, "beach_deposition", shape)
    longshore_transport = _field(fields, "longshore_transport", shape)
    wave_refraction = _field(fields, "wave_refraction", shape)
    coastal_sediment_budget = _field(fields, "coastal_sediment_budget", shape)
    aeolian = _field(fields, "aeolian", shape)
    volcanic = _field(fields, "volcanic", shape)
    lava_flow = _field(fields, "lava_flow", shape)
    viscosity_resistance = _field(fields, "viscosity_resistance", shape)
    cooling_limited_spread = _field(fields, "cooling_limited_spread", shape)
    crater_excavation = _field(fields, "crater_excavation", shape)
    ejecta_deposition = _field(fields, "ejecta_deposition", shape)
    pyroclastic_cone_growth = _field(fields, "pyroclastic_cone_growth", shape)
    karst = _field(fields, "karst", shape)
    groundwater = _field(fields, "groundwater", shape)
    groundwater_flow = _field(fields, "groundwater_flow", shape)
    subsurface_drainage = _field(fields, "subsurface_drainage", shape)
    collapse_risk = _field(fields, "collapse_risk", shape)
    ponor_drainage = _field(fields, "ponor_drainage", shape)
    seasonal_flooding = _field(fields, "seasonal_flooding", shape)
    polje_floor_aggradation = _field(fields, "polje_floor_aggradation", shape)

    erosion_total = float(np.sum(np.maximum(erosion, 0.0)))
    deposition_total = float(np.sum(np.maximum(deposition, 0.0)))
    construction_total = float(np.sum(np.maximum(tectonic, 0.0))) + float(np.sum(np.maximum(volcanic, 0.0)))
    relief = float(np.max(final) - np.min(final))
    change_peak = max(float(np.max(np.abs(change))), 1e-9)

    metrics: dict[str, float | str] = {
        "relief": relief,
        "mean_change": float(np.mean(change)),
        "active_area_ratio": float(np.mean(np.abs(change) >= change_peak * 0.25)),
        "erosion_deposition_ratio": _safe_ratio(erosion_total, deposition_total),
        "deposition_erosion_ratio": _safe_ratio(deposition_total, erosion_total),
        "construction_erosion_ratio": _safe_ratio(construction_total, erosion_total),
        "diffusion_share": _safe_ratio(float(np.sum(np.abs(diffusion))), erosion_total + deposition_total + construction_total),
        "centerline_process_focus": _centerline_concentration(erosion + transport + glacial),
        "downstream_deposition_focus": _lower_half_fraction(deposition),
        "shoreline_process_focus": _shoreline_concentration(marine),
        "wave_refraction_focus": _shoreline_concentration(wave_refraction),
        "longshore_transport_ratio": _safe_ratio(
            float(np.sum(np.abs(longshore_transport))),
            float(np.sum(np.abs(beach_deposition)) + np.sum(np.abs(shoreline_retreat))),
        ),
        "wave_cut_efficiency": _safe_ratio(
            float(np.sum(np.abs(wave_cut_platform))),
            float(np.sum(np.abs(wave_energy))),
        ),
        "coastal_budget_balance": _safe_ratio(
            float(np.sum(coastal_sediment_budget)),
            float(np.sum(np.abs(beach_deposition)) + np.sum(np.abs(longshore_transport)) + np.sum(np.abs(shoreline_retreat))),
        ),
        "dune_transport_focus": _lower_half_fraction(aeolian),
        "volcanic_core_focus": _radial_concentration(volcanic, 0.18),
        "lava_spread_efficiency": _safe_ratio(
            float(np.sum(np.abs(lava_flow)) + np.sum(np.abs(cooling_limited_spread))),
            float(np.sum(np.abs(volcanic)) + np.sum(np.abs(viscosity_resistance))),
        ),
        "viscosity_constraint_index": _safe_ratio(
            float(np.sum(np.abs(viscosity_resistance))),
            float(np.sum(np.abs(volcanic)) + np.sum(np.abs(lava_flow))),
        ),
        "explosive_excavation_ratio": _safe_ratio(
            float(np.sum(np.abs(crater_excavation))),
            float(np.sum(np.abs(volcanic)) + np.sum(np.abs(ejecta_deposition)) + np.sum(np.abs(pyroclastic_cone_growth))),
        ),
        "pyroclastic_growth_ratio": _safe_ratio(
            float(np.sum(np.abs(ejecta_deposition)) + np.sum(np.abs(pyroclastic_cone_growth))),
            float(np.sum(np.abs(volcanic)) + np.sum(np.abs(lava_flow))),
        ),
        "karst_sink_focus": _radial_concentration(karst + groundwater, 0.24),
        "groundwater_concentration_index": _radial_concentration(groundwater_flow + subsurface_drainage, 0.30),
        "subsurface_drainage_ratio": _safe_ratio(
            float(np.sum(np.abs(subsurface_drainage)) + np.sum(np.abs(ponor_drainage))),
            float(np.sum(np.abs(karst)) + np.sum(np.abs(groundwater_flow))),
        ),
        "collapse_risk_index": float(np.max(np.abs(collapse_risk))),
        "karst_flood_aggradation_ratio": _safe_ratio(
            float(np.sum(np.abs(seasonal_flooding)) + np.sum(np.abs(polje_floor_aggradation))),
            float(np.sum(np.abs(karst)) + np.sum(np.abs(subsurface_drainage))),
        ),
        "valley_depth_index": _valley_depth_index(final),
        "u_floor_width_index": _u_floor_width_index(final),
        "fan_lateral_spread_index": _weighted_lateral_spread(deposition, 0.32),
        "delta_front_spread_index": _weighted_lateral_spread(deposition, 0.55),
        "shoreline_gradient_index": _shoreline_gradient_index(final),
        "dune_migration_index": _safe_ratio(float(np.sum(np.maximum(deposition, 0.0))), float(np.sum(np.maximum(erosion, 0.0)))),
        "dome_symmetry_index": _radial_symmetry_index(final),
        "closed_depression_index": _central_depression_index(final),
    }

    metrics["diagnosis"] = diagnose_metrics(landform_id, metrics)
    return metrics


def diagnose_metrics(landform_id: str, metrics: dict[str, float | str]) -> str:
    def val(key: str) -> float:
        return float(metrics.get(key, 0.0) or 0.0)

    if landform_id == "v_valley":
        if val("centerline_process_focus") >= 0.45 and val("erosion_deposition_ratio") >= 1.2:
            return "하천 중심부 침식이 뚜렷해 V자곡 형성 조건이 강합니다."
        return "계곡 중심 침식이 약합니다. 하천 침식력이나 융기 경향을 높여 비교하세요."
    if landform_id == "alluvial_fan":
        if val("downstream_deposition_focus") >= 0.55 and val("deposition_erosion_ratio") >= 0.6:
            return "하류·출구부 퇴적 집중이 뚜렷해 선상지 조건이 잘 나타납니다."
        return "퇴적 집중이 약합니다. 퇴적물 공급이나 경사 완화 조건을 높여 보세요."
    if landform_id == "delta":
        if val("downstream_deposition_focus") >= 0.6 and val("deposition_erosion_ratio") >= 0.8:
            return "하구부 퇴적 우세가 나타나 삼각주 성장 조건이 형성됩니다."
        return "삼각주 전면 퇴적이 약합니다. 퇴적물 공급과 해수면 안정성을 조정하세요."
    if landform_id == "u_valley":
        if val("centerline_process_focus") >= 0.35:
            return "빙하 침식이 계곡 축에 집중되어 U자곡 발달 방향이 보입니다."
        return "빙하 축 방향 침식이 분산되어 있습니다. 빙하 침식력이나 두께를 높여 보세요."
    if landform_id in {"coastal_cliff", "wave_cut_platform", "spit_lagoon", "tombolo", "marine_terrace"}:
        if landform_id in {"spit_lagoon", "tombolo"} and val("longshore_transport_ratio") >= 0.2:
            return "연안 표사 이동과 해빈 퇴적이 함께 나타나 해안 퇴적 지형 성장 조건이 보입니다."
        if landform_id in {"wave_cut_platform", "marine_terrace"} and val("wave_cut_efficiency") >= 0.1:
            return "파랑 에너지가 해수면 부근 평탄화로 전환되어 파식대와 해안 단구 형성 조건이 보입니다."
        if val("shoreline_process_focus") >= 0.45:
            return "파랑 침식이 해안선 부근에 집중되어 해식애 후퇴 조건이 강합니다."
        return "해안선 집중 침식이 약합니다. 파랑 에너지나 해수면 위치를 조정하세요."
    if landform_id == "barchan":
        if val("dune_transport_focus") >= 0.5:
            return "바람 이동과 퇴적이 하류 방향으로 집중되어 바르한 이동성이 큽니다."
        return "사구 이동 방향성이 약합니다. 풍속 조건을 높여 비교하세요."
    if landform_id in {"lava_dome", "shield_volcano", "stratovolcano", "lava_plateau", "maar", "cinder_cone"}:
        if landform_id in {"maar", "cinder_cone"} and val("explosive_excavation_ratio") >= 0.02:
            return "폭발성 분출과 화산쇄설물 퇴적이 함께 나타나 화산 지형의 폭발성 형성 조건이 보입니다."
        if landform_id in {"shield_volcano", "lava_plateau"} and val("lava_spread_efficiency") >= 0.3:
            return "점성 제약보다 용암 확산이 커서 넓게 퍼지는 화산 지형 성장 조건이 보입니다."
        if val("volcanic_core_focus") >= 0.5 and val("construction_erosion_ratio") >= 1.0:
            return "중앙 분출과 화산체 성장이 강해 용암돔·성층화산 계열의 성장 조건이 보입니다."
        return "화산체 성장 신호가 약합니다. 분출률, 점성, 냉각 조건을 조정해 비교하세요."
    if landform_id in {"karst_doline", "uvala", "polje", "karren", "tower_karst"}:
        if landform_id == "polje" and val("karst_flood_aggradation_ratio") > 0.0:
            return "지하수 배수와 계절 범람이 함께 나타나 카르스트 폴리에 바닥 변화 조건이 보입니다."
        if val("collapse_risk_index") > 0.0 and val("subsurface_drainage_ratio") > 0.0:
            return "용식과 지하수 배수가 연결되어 카르스트 함몰·붕괴 위험 조건이 보입니다."
        if val("karst_sink_focus") >= 0.45:
            return "중앙부 용식·지하수 작용이 집중되어 카르스트 함몰 지형 발달 조건이 보입니다."
        return "카르스트 용식 집중이 약합니다. 용식 강도와 지하수 흐름을 높여 비교하세요."
    return "지형 변화량과 작용장 분포를 함께 비교하세요."


def metric_cards(metrics: dict[str, float | str]) -> tuple[tuple[str, str, str], ...]:
    return (
        ("침식/퇴적", f"{float(metrics.get('erosion_deposition_ratio', 0.0)):.2f}", "1보다 크면 침식 우세"),
        ("퇴적 집중", f"{float(metrics.get('downstream_deposition_focus', 0.0)) * 100:.0f}%", "하류·말단부 퇴적 비율"),
        ("중심축 집중", f"{float(metrics.get('centerline_process_focus', 0.0)) * 100:.0f}%", "계곡·빙하 축 작용 비율"),
        ("활성 면적", f"{float(metrics.get('active_area_ratio', 0.0)) * 100:.0f}%", "강한 변화가 나타난 면적"),
    )


def process_field_cards(process_fields: dict[str, Any]) -> tuple[tuple[str, str, str], ...]:
    field_specs = (
        ("drainage_area", "집수면적", "DEM 경사로 누적한 물 흐름 집중도", "max"),
        ("transport_capacity", "하천 운반능력", "하천이 퇴적물을 더 운반할 수 있는 정도", "sum"),
        ("wave_energy", "파랑 에너지", "해수면 부근에 집중되는 파랑 작용", "sum"),
        ("shoreline_retreat", "해안선 후퇴", "파랑 침식으로 깎인 해안선 후퇴량", "sum"),
        ("wave_cut_platform", "파식대 평탄화", "해수면 근처에서 평탄화되는 파식대 작용", "sum"),
        ("beach_deposition", "해빈 퇴적", "파랑 에너지 저하 구간의 퇴적", "sum"),
        ("longshore_transport", "연안 표사 이동", "파랑이 해안선을 따라 이동시키는 퇴적물 flux", "sum"),
        ("wave_refraction", "파랑 굴절 집중", "해안선 굴곡과 경사 때문에 파랑 에너지가 집중되는 정도", "sum"),
        ("storm_runup", "폭풍 파상 침식", "높은 파랑이 평상시 해수면보다 위쪽까지 깎는 작용", "sum"),
        ("coastal_sediment_budget", "해안 퇴적 수지", "해빈 퇴적과 연안 이동, 해안 후퇴가 합쳐진 순 변화", "sum"),
        ("ice_thickness", "빙하 두께", "빙하가 축적된 두께장", "max"),
        ("glacial_velocity", "빙하 속도", "두께와 경사로 계산한 상대 속도", "max"),
        ("sand_flux", "모래 이동량", "바람에 의해 이동하는 모래 flux", "sum"),
        ("stoss_erosion", "풍상면 침식", "바람을 맞는 사면에서 깎인 양", "sum"),
        ("lee_deposition", "풍하면 퇴적", "바람 그늘 쪽에 쌓인 양", "sum"),
        ("wind_shear_stress", "바람 전단응력", "풍속과 사면 노출이 만든 모래 이동 가능 에너지", "sum"),
        ("sand_availability", "모래 공급 가능량", "바람이 실제로 운반할 수 있는 느슨한 모래의 공간 분포", "sum"),
        ("shelter_factor", "바람 그늘", "풍하면에서 풍속이 줄고 퇴적이 쉬워지는 정도", "sum"),
        ("dune_migration", "사구 이동 경향", "풍상면 침식과 풍하면 퇴적 차이로 본 이동 방향성", "sum"),
        ("volcanic_construction", "화산체 성장", "분출구 중심의 내적 성장량", "sum"),
        ("lava_flow", "용암 흐름", "점성과 확산에 따라 주변으로 흐른 용암", "sum"),
        ("explosion_energy", "폭발 에너지", "마그마와 물 접촉 또는 급격한 분출이 만든 폭발 강도", "sum"),
        ("ejecta_deposition", "분출물 퇴적", "폭발로 날아간 화산쇄설물이 주변에 쌓인 양", "sum"),
        ("crater_excavation", "분화구 굴착", "폭발이나 붕괴로 중심부가 파인 양", "sum"),
        ("pyroclastic_cone_growth", "화산쇄설 원추 성장", "스코리아·화산쇄설물이 화구 주변에 쌓인 양", "sum"),
        ("magma_water_contact", "마그마-물 접촉", "수증기 폭발을 강화하는 지하수 접촉 정도", "sum"),
        ("viscosity_resistance", "점성 저항", "용암 확산을 억제하는 상대 저항", "max"),
        ("cooling_limited_spread", "냉각 제한 확산", "냉각과 경사에 의해 제한된 용암 확산", "sum"),
        ("groundwater_flow", "지하수 흐름", "용식이 집중되는 지하수 흐름장", "sum"),
        ("solution_rate", "용식률", "석회암 용식에 의한 표면 저하량", "sum"),
        ("subsurface_drainage", "지하 배수", "지하 배수에 따른 침식·용식 작용", "sum"),
        ("collapse_risk", "붕괴 가능성", "용식과 지하 배수가 겹친 폐쇄 와지 위험도", "max"),
        ("fracture_density", "절리 밀도", "물이 스며들고 용식이 집중될 수 있는 균열 분포", "sum"),
        ("sinkhole_density", "싱크홀 밀도", "용식과 붕괴 위험이 겹쳐 폐쇄 와지가 생기기 쉬운 정도", "sum"),
        ("ponor_drainage", "포노르 배수", "폴리에 바닥에서 물이 지하로 빠져나가는 작용", "sum"),
        ("seasonal_flooding", "계절 침수", "배수가 늦어져 분지 바닥에 물이 머무는 정도", "sum"),
        ("polje_floor_aggradation", "폴리에 바닥 퇴적", "침수와 배수 반복으로 평탄한 바닥에 쌓이는 퇴적", "sum"),
    )
    cards: list[tuple[str, str, str]] = []
    for key, label, help_text, reducer in field_specs:
        value = process_fields.get(key)
        if value is None:
            continue
        array = np.nan_to_num(np.asarray(value, dtype=float), nan=0.0, posinf=0.0, neginf=0.0)
        magnitude = np.abs(array)
        if float(np.max(magnitude)) <= 1e-12:
            continue
        score = float(np.max(magnitude) if reducer == "max" else np.sum(magnitude))
        cards.append((label, f"{score:.2f}", help_text))
    return tuple(cards)


def _process_field_specs() -> tuple[tuple[str, str, str, str], ...]:
    return (
        ("drainage_area", "집수면적", "DEM 경사로 누적한 물 흐름 집중도", "max"),
        ("transport_capacity", "하천 운반능력", "하천이 퇴적물을 더 운반할 수 있는 정도", "sum"),
        ("wave_energy", "파랑 에너지", "해수면 부근에 집중되는 파랑 작용", "sum"),
        ("shoreline_retreat", "해안선 후퇴", "파랑 침식으로 깎인 해안선 후퇴량", "sum"),
        ("wave_cut_platform", "파식대 평탄화", "해수면 근처에서 평탄화되는 파식대 작용", "sum"),
        ("beach_deposition", "해빈 퇴적", "파랑 에너지 저하 구간의 퇴적", "sum"),
        ("longshore_transport", "연안 표사 이동", "파랑이 해안선을 따라 이동시키는 퇴적물 flux", "sum"),
        ("wave_refraction", "파랑 굴절 집중", "해안선 굴곡과 경사 때문에 파랑 에너지가 집중되는 정도", "sum"),
        ("storm_runup", "폭풍 파상 침식", "높은 파랑이 평상시 해수면보다 위쪽까지 깎는 작용", "sum"),
        ("coastal_sediment_budget", "해안 퇴적 수지", "해빈 퇴적과 연안 이동, 해안 후퇴가 합쳐진 순 변화", "sum"),
        ("ice_thickness", "빙하 두께", "빙하가 축적된 두께장", "max"),
        ("glacial_velocity", "빙하 속도", "두께와 경사로 계산한 상대 속도", "max"),
        ("sand_flux", "모래 이동량", "바람에 의해 이동하는 모래 flux", "sum"),
        ("stoss_erosion", "풍상면 침식", "바람을 맞는 사면에서 깎인 양", "sum"),
        ("lee_deposition", "풍하면 퇴적", "바람 그늘 쪽에 쌓인 양", "sum"),
        ("wind_shear_stress", "바람 전단응력", "풍속과 사면 노출이 만든 모래 이동 가능 에너지", "sum"),
        ("sand_availability", "모래 공급 가능량", "바람이 실제로 운반할 수 있는 느슨한 모래의 공간 분포", "sum"),
        ("shelter_factor", "바람 그늘", "풍하면에서 풍속이 줄고 퇴적이 쉬워지는 정도", "sum"),
        ("dune_migration", "사구 이동 경향", "풍상면 침식과 풍하면 퇴적 차이로 본 이동 방향성", "sum"),
        ("volcanic_construction", "화산체 성장", "분출구 중심의 내적 성장량", "sum"),
        ("lava_flow", "용암 흐름", "점성과 확산에 따라 주변으로 흐른 용암", "sum"),
        ("explosion_energy", "폭발 에너지", "마그마와 물 접촉 또는 급격한 분출이 만든 폭발 강도", "sum"),
        ("ejecta_deposition", "분출물 퇴적", "폭발로 날아간 화산쇄설물이 주변에 쌓인 양", "sum"),
        ("crater_excavation", "분화구 굴착", "폭발이나 붕괴로 중심부가 파인 양", "sum"),
        ("pyroclastic_cone_growth", "화산쇄설 원추 성장", "스코리아·화산쇄설물이 화구 주변에 쌓인 양", "sum"),
        ("magma_water_contact", "마그마-물 접촉", "수증기 폭발을 강화하는 지하수 접촉 정도", "sum"),
        ("viscosity_resistance", "점성 저항", "용암 확산을 억제하는 상대 저항", "max"),
        ("cooling_limited_spread", "냉각 제한 확산", "냉각과 경사에 의해 제한된 용암 확산", "sum"),
        ("groundwater_flow", "지하수 흐름", "용식이 집중되는 지하수 흐름장", "sum"),
        ("solution_rate", "용식률", "석회암 용식에 의한 표면 저하량", "sum"),
        ("subsurface_drainage", "지하 배수", "지하 배수에 따른 침식·용식 작용", "sum"),
        ("collapse_risk", "붕괴 가능성", "용식과 지하 배수가 겹친 폐쇄 와지 위험도", "max"),
        ("fracture_density", "절리 밀도", "물이 스며들고 용식이 집중될 수 있는 균열 분포", "sum"),
        ("sinkhole_density", "싱크홀 밀도", "용식과 붕괴 위험이 겹쳐 폐쇄 와지가 생기기 쉬운 정도", "sum"),
        ("ponor_drainage", "포노르 배수", "폴리에 바닥에서 물이 지하로 빠져나가는 작용", "sum"),
        ("seasonal_flooding", "계절 침수", "배수가 늦어져 분지 바닥에 물이 머무는 정도", "sum"),
        ("polje_floor_aggradation", "폴리에 바닥 퇴적", "침수와 배수 반복으로 평탄한 바닥에 쌓이는 퇴적", "sum"),
    )


def process_field_options(process_fields: dict[str, Any]) -> tuple[tuple[str, str], ...]:
    options: list[tuple[str, str]] = []
    for key, label, _help_text, _reducer in _process_field_specs():
        value = process_fields.get(key)
        if value is None:
            continue
        array = np.nan_to_num(np.asarray(value, dtype=float), nan=0.0, posinf=0.0, neginf=0.0)
        if float(np.max(np.abs(array))) > 1e-12:
            options.append((key, label))
    return tuple(options)


def normalize_process_field(process_fields: dict[str, Any], key: str) -> np.ndarray:
    value = process_fields.get(key)
    if value is None:
        return np.zeros((1, 1), dtype=float)
    array = np.nan_to_num(np.asarray(value, dtype=float), nan=0.0, posinf=0.0, neginf=0.0)
    magnitude = np.abs(array)
    peak = float(np.max(magnitude))
    if peak <= 1e-12:
        return np.zeros_like(magnitude, dtype=float)
    return magnitude / peak


def validation_cards(landform_id: str, metrics: dict[str, float | str]) -> tuple[tuple[str, str, str], ...]:
    def pct(key: str) -> str:
        return f"{float(metrics.get(key, 0.0)) * 100:.0f}%"

    def ratio(key: str) -> str:
        return f"{float(metrics.get(key, 0.0)):.2f}"

    common = (
        ("기복", f"{float(metrics.get('relief', 0.0)):.1f}", "최종 표면의 최고점-최저점 차이"),
        ("활성 면적", pct("active_area_ratio"), "강한 변화가 실제로 일어난 영역 비율"),
    )
    per_landform: dict[str, tuple[tuple[str, str, str], ...]] = {
        "v_valley": (
            ("V자 절개도", pct("valley_depth_index"), "계곡 양쪽 사면 대비 중심부가 얼마나 깊게 깎였는지"),
            ("중심 침식 집중", pct("centerline_process_focus"), "하천 작용이 계곡 축에 모인 정도"),
        ),
        "alluvial_fan": (
            ("선상 확산도", pct("fan_lateral_spread_index"), "출구부 퇴적물이 좌우로 퍼진 정도"),
            ("하류 퇴적 집중", pct("downstream_deposition_focus"), "말단부 퇴적 비율"),
        ),
        "delta": (
            ("전면 확장도", pct("delta_front_spread_index"), "하구 전면 퇴적체가 좌우로 성장한 정도"),
            ("퇴적/침식 비", ratio("deposition_erosion_ratio"), "1보다 크면 퇴적 우세"),
        ),
        "u_valley": (
            ("U자 바닥 폭", pct("u_floor_width_index"), "낮고 넓은 계곡 바닥이 형성된 정도"),
            ("빙하 축 집중", pct("centerline_process_focus"), "빙하 침식이 계곡 축에 모인 정도"),
        ),
        "coastal_cliff": (
            ("해안 급경사 지수", ratio("shoreline_gradient_index"), "해안선 부근 경사가 전체보다 얼마나 큰지"),
            ("파랑 집중", pct("shoreline_process_focus"), "파랑 침식이 해안선에 모인 정도"),
        ),
        "barchan": (
            ("사구 이동성", ratio("dune_migration_index"), "풍하측 퇴적과 풍상측 침식의 균형"),
            ("풍하 집중", pct("dune_transport_focus"), "바람 작용이 진행 방향으로 집중된 정도"),
        ),
        "lava_dome": (
            ("돔 대칭성", pct("dome_symmetry_index"), "중앙 분출 지형이 방사상으로 균형적인 정도"),
            ("분출 중심성", pct("volcanic_core_focus"), "성장이 중앙 분출구에 집중된 정도"),
        ),
        "karst_doline": (
            ("폐쇄 와지 깊이", pct("closed_depression_index"), "주변부 대비 중앙부가 낮아진 정도"),
            ("용식 집중", pct("karst_sink_focus"), "용식·지하수 작용이 중심부에 모인 정도"),
        ),
    }
    if landform_id in {"coastal_cliff", "wave_cut_platform", "spit_lagoon", "tombolo", "marine_terrace"}:
        coastal_cards = (
            ("해안 급경사 지수", ratio("shoreline_gradient_index"), "해안선 부근 경사가 전체보다 얼마나 큰지"),
            ("파랑 집중", pct("shoreline_process_focus"), "파랑 침식이 해안선에 모인 정도"),
            ("표사 이동 비율", ratio("longshore_transport_ratio"), "해빈 퇴적·해안 후퇴 대비 연안 표사 이동의 상대 크기"),
            ("파식 효율", ratio("wave_cut_efficiency"), "파랑 에너지가 파식대 평탄화로 전환되는 비율"),
        )
        return coastal_cards + common
    if landform_id in {"lava_dome", "shield_volcano", "stratovolcano", "lava_plateau", "maar", "cinder_cone"}:
        volcanic_cards = (
            ("돔 대칭성", pct("dome_symmetry_index"), "중앙 분출 지형이 방사상으로 균형적인 정도"),
            ("분출 중심성", pct("volcanic_core_focus"), "성장이 중앙 분출구에 집중된 정도"),
            ("용암 확산 효율", ratio("lava_spread_efficiency"), "화산체 성장 대비 용암류가 넓게 퍼지는 정도"),
            ("점성 제약", ratio("viscosity_constraint_index"), "점성이 용암 확산을 제한하는 상대 강도"),
        )
        return volcanic_cards + common
    if landform_id in {"karst_doline", "uvala", "polje", "karren", "tower_karst"}:
        karst_cards = (
            ("폐쇄 와지 지수", pct("closed_depression_index"), "주변부 대비 중앙부가 낮아진 정도"),
            ("용식 집중", pct("karst_sink_focus"), "용식·지하수 작용이 중앙부에 모인 정도"),
            ("지하수 집중", pct("groundwater_concentration_index"), "지하수 흐름과 지하 배수가 특정 함몰부에 모인 정도"),
            ("붕괴 위험", ratio("collapse_risk_index"), "용식과 배수가 겹쳐 표면 붕괴 가능성이 커진 정도"),
        )
        return karst_cards + common
    return per_landform.get(landform_id, ()) + common
