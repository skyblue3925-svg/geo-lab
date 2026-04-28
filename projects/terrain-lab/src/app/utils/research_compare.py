from __future__ import annotations

import csv
import json
from io import StringIO

import numpy as np


def align_reference_dem(target_elevation, reference_elevation):
    target = np.asarray(target_elevation, dtype=float)
    reference = np.asarray(reference_elevation, dtype=float)

    if target.shape == reference.shape:
        return reference

    from scipy.ndimage import zoom

    zoom_factors = (
        target.shape[0] / reference.shape[0],
        target.shape[1] / reference.shape[1],
    )
    return zoom(reference, zoom_factors, order=1)


def _safe_correlation(current: np.ndarray, reference: np.ndarray) -> float:
    current_flat = np.asarray(current, dtype=float).ravel()
    reference_flat = np.asarray(reference, dtype=float).ravel()
    valid = np.isfinite(current_flat) & np.isfinite(reference_flat)

    if np.count_nonzero(valid) < 2:
        return 0.0

    current_valid = current_flat[valid]
    reference_valid = reference_flat[valid]

    if np.allclose(current_valid, current_valid[0]) or np.allclose(reference_valid, reference_valid[0]):
        return 0.0

    corr = np.corrcoef(current_valid, reference_valid)[0, 1]
    if np.isnan(corr):
        return 0.0
    return float(corr)


def summarize_hypsometric_difference(hi_diff: float) -> str:
    hi_diff = float(hi_diff)
    if abs(hi_diff) < 0.02:
        return "\ub450 DEM\uc758 \uc0c1\ub300 \uace0\ub3c4-\uba74\uc801 \ubd84\ud3ec\uac00 \uac70\uc758 \uac19\uc2b5\ub2c8\ub2e4."
    if hi_diff > 0:
        return "\ud604\uc7ac DEM\uc774 \uae30\uc900 DEM\ubcf4\ub2e4 \uc0c1\ub300\uc801\uc73c\ub85c \ub192\uc740 \uc9c0\ub300 \ube44\uc911\uc774 \ub354 \ud07d\ub2c8\ub2e4."
    return "\ud604\uc7ac DEM\uc774 \uae30\uc900 DEM\ubcf4\ub2e4 \uc0c1\ub300\uc801\uc73c\ub85c \ub354 \uce68\uc2dd\ub418\uc5c8\uac70\ub098 \ub0ae\uc740 \uc9c0\ub300 \ube44\uc911\uc774 \ub354 \ud07d\ub2c8\ub2e4."


def compute_profile_error_stats(profile_current, profile_reference) -> dict[str, object]:
    error = np.asarray(profile_current.elevation, dtype=float) - np.asarray(profile_reference.elevation, dtype=float)
    reference_range = float(np.nanmax(profile_reference.elevation) - np.nanmin(profile_reference.elevation))
    normalized_rmse = float(np.sqrt(np.mean(error ** 2)) / reference_range) if reference_range > 0 else 0.0
    return {
        "error": error,
        "rmse": float(np.sqrt(np.mean(error ** 2))),
        "mae": float(np.mean(np.abs(error))),
        "peak_abs_error": float(np.max(np.abs(error))),
        "bias": float(np.mean(error)),
        "error_std": float(np.std(error)),
        "sample_count": int(error.size),
        "reference_range": reference_range,
        "normalized_rmse": normalized_rmse,
    }


def build_research_comparison_brief(summary: dict[str, object]) -> list[str]:
    rmse = float(summary["rmse"])
    normalized_rmse = float(summary.get("normalized_rmse", 0.0))
    mean_diff = float(summary["mean_diff"])
    correlation = float(summary["correlation"])
    cross_peak = float(summary["cross_profile_peak_abs_error"])
    long_peak = float(summary["long_profile_peak_abs_error"])
    hi_diff = float(summary["hi_diff"])
    current_range = float(summary.get("current_range", 0.0))
    reference_range = float(summary.get("reference_range", 0.0))

    if normalized_rmse < 0.05:
        rmse_message = "전체 오차가 작아 두 DEM의 형상이 전반적으로 잘 맞습니다."
    elif normalized_rmse < 0.15:
        rmse_message = "전체 형상은 유사하지만, 부분적으로 눈에 띄는 오차 구간이 있습니다."
    else:
        rmse_message = "전체 오차가 뚜렷해 차이 맵과 단면 오차를 함께 봐야 합니다."

    if mean_diff > 0.0:
        bias_message = "현재 DEM이 기준 DEM보다 전반적으로 더 높습니다."
    elif mean_diff < 0.0:
        bias_message = "현재 DEM이 기준 DEM보다 전반적으로 더 낮습니다."
    else:
        bias_message = "평균 고도 차이는 거의 없어 전반적 편향은 크지 않습니다."

    if correlation >= 0.9:
        corr_message = "고도 배치는 대체로 비슷해 국지적 차이를 집중적으로 보면 됩니다."
    elif correlation >= 0.75:
        corr_message = "고도 배치는 비슷한 편이지만, 비교 단면에서 구조 차이를 확인해야 합니다."
    else:
        corr_message = "고도 배치 상관성이 낮아 구조 자체가 다를 가능성이 큽니다."

    dominant_section = "\ud6a1\ub2e8\uba74" if cross_peak >= long_peak else "\uc885\ub2e8\uba74"
    section_message = f"가장 큰 단면 오차는 {dominant_section}에서 나타납니다."

    if current_range > 0 and reference_range > 0:
        scale_message = f"현재 DEM 기복량은 {current_range:.2f}m, 기준 DEM은 {reference_range:.2f}m입니다."
    else:
        scale_message = "기복량 기준 비교는 현재 데이터 범위가 작아 해석을 보수적으로 해야 합니다."

    hi_message = str(summary["hi_message"])
    if hi_diff > 0.0:
        hi_direction = "현재 DEM의 상대적 침식 단계가 기준 DEM보다 더 젊은 쪽입니다."
    elif hi_diff < 0.0:
        hi_direction = "현재 DEM의 상대적 침식 단계가 기준 DEM보다 더 성숙하거나 침식된 쪽입니다."
    else:
        hi_direction = "HI 차이가 거의 없어 전반적인 침식 단계는 비슷합니다."

    return [
        rmse_message,
        bias_message,
        f"{corr_message} {section_message}",
        f"{scale_message} {hi_message} {hi_direction}",
    ]


def export_profile_comparison_csv_bytes(
    *,
    cross_current,
    cross_reference,
    cross_error,
    long_current,
    long_reference,
    long_error,
) -> bytes:
    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["axis", "index", "distance_m", "current_elevation", "reference_elevation", "error"])

    for idx, (distance, current_value, reference_value, error_value) in enumerate(
        zip(cross_current.distance, cross_current.elevation, cross_reference.elevation, cross_error)
    ):
        writer.writerow(["cross", idx, float(distance), float(current_value), float(reference_value), float(error_value)])

    for idx, (distance, current_value, reference_value, error_value) in enumerate(
        zip(long_current.distance, long_current.elevation, long_reference.elevation, long_error)
    ):
        writer.writerow(["long", idx, float(distance), float(current_value), float(reference_value), float(error_value)])

    return buffer.getvalue().encode("utf-8")


def export_comparison_report_json_bytes(report: dict[str, object]) -> bytes:
    return json.dumps(report, indent=2, ensure_ascii=False).encode("utf-8")


def export_comparison_report_markdown_bytes(report: dict[str, object]) -> bytes:
    summary = report["summary"]
    interpretation = report["interpretation"]
    metrics = report["metrics"]
    sections = report["sections"]
    hypsometric = report["hypsometric"]
    limitations = report.get("limitations", [])

    lines = [
        "# Geo-lab DEM Comparison Report",
        "",
        "## Overview",
        f"- Reference DEM: {summary['reference_name']}",
        f"- Reference shape: {summary['reference_shape']}",
        f"- Reference cell size: {summary['reference_cell_size']:.3f} m",
        f"- Cross section row: {summary['cross_section_row']}",
        f"- Longitudinal column: {summary['longitudinal_col']}",
        "",
        "## Key Metrics",
    ]

    for label, value in metrics.items():
        lines.append(f"- {label}: {value}")

    lines.extend([
        "",
        "## Interpretation",
    ])
    for item in interpretation:
        lines.append(f"- {item}")

    lines.extend([
        "",
        "## Section Metrics",
    ])
    for section_name, section_metrics in sections.items():
        lines.append(f"### {section_name}")
        for label, value in section_metrics.items():
            lines.append(f"- {label}: {value}")

    lines.extend([
        "",
        "## Hypsometric",
        f"- Current HI: {hypsometric['current']:.3f}",
        f"- Reference HI: {hypsometric['reference']:.3f}",
        f"- HI difference: {hypsometric['difference']:+.3f}",
        f"- HI interpretation: {hypsometric['message']}",
    ])

    if limitations:
        lines.extend([
            "",
            "## Limitations",
        ])
        for item in limitations:
            lines.append(f"- {item}")

    return "\n".join(lines).encode("utf-8")


def build_alignment_limitations(
    *,
    current_shape,
    current_cell_size: float,
    reference_shape,
    reference_cell_size: float,
) -> list[str]:
    limitations = [
        "This comparison aligns the reference DEM by matching array shape with bilinear resampling. Extent and CRS are not reconciled automatically.",
    ]

    if tuple(current_shape) != tuple(reference_shape):
        limitations.append(
            f"Shape mismatch detected: current {tuple(current_shape)} vs reference {tuple(reference_shape)}. "
            "Reported errors are based on an internally resampled reference grid."
        )

    if abs(float(current_cell_size) - float(reference_cell_size)) > 1e-9:
        limitations.append(
            f"Cell size mismatch detected: current {float(current_cell_size):g} m vs reference {float(reference_cell_size):g} m."
        )

    return limitations


def build_research_comparison_summary(
    *,
    reference_name: str,
    reference_shape,
    reference_cell_size: float,
    stats_cmp: dict[str, float],
    current_hypso,
    reference_hypso,
    cross_stats: dict[str, object],
    long_stats: dict[str, object],
    compare_cross_row: int,
    compare_long_col: int,
) -> dict[str, object]:
    hi_diff = float(current_hypso.hypsometric_integral - reference_hypso.hypsometric_integral)
    hi_message = summarize_hypsometric_difference(hi_diff)
    current_range = float(stats_cmp.get("current_range", 0.0))
    reference_range = float(stats_cmp.get("reference_range", 0.0))

    summary = {
        "reference_name": reference_name,
        "reference_shape": list(reference_shape),
        "reference_cell_size": float(reference_cell_size),
        "mean_diff": float(stats_cmp["mean_diff"]),
        "rmse": float(stats_cmp["rmse"]),
        "mae": float(stats_cmp["mae"]),
        "normalized_rmse": float(stats_cmp.get("normalized_rmse", 0.0)),
        "correlation": float(stats_cmp["correlation"]),
        "bias": float(stats_cmp.get("bias", stats_cmp["mean_diff"])),
        "current_range": current_range,
        "reference_range": reference_range,
        "valid_ratio": float(stats_cmp.get("valid_ratio", 1.0)),
        "hi_current": float(current_hypso.hypsometric_integral),
        "hi_reference": float(reference_hypso.hypsometric_integral),
        "hi_diff": hi_diff,
        "hi_message": hi_message,
        "cross_section_row": int(compare_cross_row),
        "longitudinal_col": int(compare_long_col),
        "cross_profile_rmse": float(cross_stats["rmse"]),
        "cross_profile_mae": float(cross_stats["mae"]),
        "cross_profile_peak_abs_error": float(cross_stats["peak_abs_error"]),
        "cross_profile_bias": float(cross_stats.get("bias", 0.0)),
        "cross_profile_normalized_rmse": float(cross_stats.get("normalized_rmse", 0.0)),
        "long_profile_rmse": float(long_stats["rmse"]),
        "long_profile_mae": float(long_stats["mae"]),
        "long_profile_peak_abs_error": float(long_stats["peak_abs_error"]),
        "long_profile_bias": float(long_stats.get("bias", 0.0)),
        "long_profile_normalized_rmse": float(long_stats.get("normalized_rmse", 0.0)),
    }
    summary["brief"] = build_research_comparison_brief(summary)
    return summary


def build_research_comparison_report(
    *,
    summary: dict[str, object],
    stats_cmp: dict[str, float],
    current_hypso,
    reference_hypso,
    cross_stats: dict[str, object],
    long_stats: dict[str, object],
    current_shape,
    current_cell_size: float,
    reference_shape,
    reference_cell_size: float,
) -> dict[str, object]:
    limitations = build_alignment_limitations(
        current_shape=current_shape,
        current_cell_size=current_cell_size,
        reference_shape=reference_shape,
        reference_cell_size=reference_cell_size,
    )

    return {
        "summary": summary,
        "metrics": {
            "RMSE": f"{float(stats_cmp['rmse']):.3f} m",
            "MAE": f"{float(stats_cmp['mae']):.3f} m",
            "Bias": f"{float(stats_cmp.get('bias', stats_cmp['mean_diff'])):+.3f} m",
            "Correlation": f"{float(stats_cmp['correlation']):.3f}",
            "Normalized RMSE": f"{float(stats_cmp.get('normalized_rmse', 0.0)):.3f}",
            "Current range": f"{float(stats_cmp.get('current_range', 0.0)):.3f} m",
            "Reference range": f"{float(stats_cmp.get('reference_range', 0.0)):.3f} m",
            "Valid ratio": f"{float(stats_cmp.get('valid_ratio', 1.0)):.1%}",
        },
        "interpretation": list(summary.get("brief", [])),
        "sections": {
            "Cross section": {
                "Row": int(summary["cross_section_row"]),
                "RMSE": f"{float(cross_stats['rmse']):.3f} m",
                "MAE": f"{float(cross_stats['mae']):.3f} m",
                "Bias": f"{float(cross_stats.get('bias', 0.0)):+.3f} m",
                "Peak abs error": f"{float(cross_stats['peak_abs_error']):.3f} m",
                "Normalized RMSE": f"{float(cross_stats.get('normalized_rmse', 0.0)):.3f}",
            },
            "Longitudinal": {
                "Column": int(summary["longitudinal_col"]),
                "RMSE": f"{float(long_stats['rmse']):.3f} m",
                "MAE": f"{float(long_stats['mae']):.3f} m",
                "Bias": f"{float(long_stats.get('bias', 0.0)):+.3f} m",
                "Peak abs error": f"{float(long_stats['peak_abs_error']):.3f} m",
                "Normalized RMSE": f"{float(long_stats.get('normalized_rmse', 0.0)):.3f}",
            },
        },
        "hypsometric": {
            "current": float(current_hypso.hypsometric_integral),
            "reference": float(reference_hypso.hypsometric_integral),
            "difference": float(summary["hi_diff"]),
            "message": str(summary["hi_message"]),
        },
        "context": {
            "current_shape": list(current_shape),
            "current_cell_size": float(current_cell_size),
            "reference_shape": list(reference_shape),
            "reference_cell_size": float(reference_cell_size),
        },
        "limitations": limitations,
    }
