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
    aeolian = _field(fields, "aeolian", shape)
    volcanic = _field(fields, "volcanic", shape)
    karst = _field(fields, "karst", shape)
    groundwater = _field(fields, "groundwater", shape)

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
        "dune_transport_focus": _lower_half_fraction(aeolian),
        "volcanic_core_focus": _radial_concentration(volcanic, 0.18),
        "karst_sink_focus": _radial_concentration(karst + groundwater, 0.24),
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
    if landform_id == "coastal_cliff":
        if val("shoreline_process_focus") >= 0.45:
            return "파랑 침식이 해안선 부근에 집중되어 해식애 후퇴 조건이 강합니다."
        return "해안선 집중 침식이 약합니다. 파랑 에너지나 해수면 위치를 조정하세요."
    if landform_id == "barchan":
        if val("dune_transport_focus") >= 0.5:
            return "바람 이동과 퇴적이 하류 방향으로 집중되어 바르한 이동성이 큽니다."
        return "사구 이동 방향성이 약합니다. 풍속 조건을 높여 비교하세요."
    if landform_id == "lava_dome":
        if val("volcanic_core_focus") >= 0.5 and val("construction_erosion_ratio") >= 1.0:
            return "중앙 분출·성장 신호가 강해 용암돔 발달 조건이 뚜렷합니다."
        return "분출 중심 성장이 약합니다. 분출률을 높이거나 확산을 낮춰 보세요."
    if landform_id == "karst_doline":
        if val("karst_sink_focus") >= 0.45:
            return "중앙부 용식·지하수 작용이 집중되어 돌리네 발달 조건이 보입니다."
        return "용식 집중이 약합니다. 용식 강도와 지하수 흐름을 높여 보세요."
    return "지형 변화량과 작용장 분포를 함께 비교하세요."


def metric_cards(metrics: dict[str, float | str]) -> tuple[tuple[str, str, str], ...]:
    return (
        ("침식/퇴적", f"{float(metrics.get('erosion_deposition_ratio', 0.0)):.2f}", "1보다 크면 침식 우세"),
        ("퇴적 집중", f"{float(metrics.get('downstream_deposition_focus', 0.0)) * 100:.0f}%", "하류·말단부 퇴적 비율"),
        ("중심축 집중", f"{float(metrics.get('centerline_process_focus', 0.0)) * 100:.0f}%", "계곡·빙하 축 작용 비율"),
        ("활성 면적", f"{float(metrics.get('active_area_ratio', 0.0)) * 100:.0f}%", "강한 변화가 나타난 면적"),
    )
