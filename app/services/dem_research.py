from __future__ import annotations

import csv
from io import StringIO

import numpy as np

DEM_LAYER_LABELS = {
    "slope": "경사 강도",
    "curvature": "곡률",
    "drainage_area": "배수 집중",
}


def load_csv_dem(content: str | bytes) -> np.ndarray:
    text = content.decode("utf-8") if isinstance(content, bytes) else content
    rows: list[list[float]] = []
    for row in csv.reader(StringIO(text.strip())):
        parsed: list[float] = []
        for cell in row:
            value = cell.strip()
            if value == "" or value.lower() in {"nan", "nodata", "null"}:
                parsed.append(float("nan"))
            else:
                parsed.append(float(value))
        if parsed:
            rows.append(parsed)
    if not rows:
        raise ValueError("DEM CSV is empty.")
    width = len(rows[0])
    if any(len(row) != width for row in rows):
        raise ValueError("DEM CSV rows must have the same number of columns.")
    return np.asarray(rows, dtype=float)


def _fill_nan_with_mean(dem: np.ndarray) -> np.ndarray:
    array = np.asarray(dem, dtype=float)
    if not np.isnan(array).any():
        return array.copy()
    fill = float(np.nanmean(array)) if not np.isnan(array).all() else 0.0
    return np.nan_to_num(array, nan=fill, posinf=fill, neginf=fill)


def resample_dem(dem: np.ndarray, target_size: int) -> np.ndarray:
    source = _fill_nan_with_mean(dem)
    target_size = int(np.clip(target_size, 16, 128))
    src_rows, src_cols = source.shape
    y_coords = np.linspace(0, src_rows - 1, target_size)
    x_coords = np.linspace(0, src_cols - 1, target_size)
    y0 = np.floor(y_coords).astype(int)
    x0 = np.floor(x_coords).astype(int)
    y1 = np.clip(y0 + 1, 0, src_rows - 1)
    x1 = np.clip(x0 + 1, 0, src_cols - 1)
    y_weight = y_coords - y0
    x_weight = x_coords - x0

    out = np.zeros((target_size, target_size), dtype=float)
    for row_idx, (a0, a1, wy) in enumerate(zip(y0, y1, y_weight, strict=False)):
        top = source[a0, x0] * (1.0 - x_weight) + source[a0, x1] * x_weight
        bottom = source[a1, x0] * (1.0 - x_weight) + source[a1, x1] * x_weight
        out[row_idx, :] = top * (1.0 - wy) + bottom * wy
    return out


def _normalize(field: np.ndarray) -> np.ndarray:
    array = np.nan_to_num(np.asarray(field, dtype=float), nan=0.0, posinf=0.0, neginf=0.0)
    low = float(np.min(array))
    high = float(np.max(array))
    if high - low <= 1e-12:
        return np.zeros_like(array)
    return (array - low) / (high - low)


def _drainage_area(dem: np.ndarray) -> np.ndarray:
    z = _fill_nan_with_mean(dem)
    rows, cols = z.shape
    receivers = np.full((rows, cols, 2), -1, dtype=int)
    for row in range(rows):
        for col in range(cols):
            receiver = (-1, -1)
            steepest_drop = 0.0
            current = float(z[row, col])
            for d_row in (-1, 0, 1):
                for d_col in (-1, 0, 1):
                    if d_row == 0 and d_col == 0:
                        continue
                    n_row = row + d_row
                    n_col = col + d_col
                    if n_row < 0 or n_row >= rows or n_col < 0 or n_col >= cols:
                        continue
                    drop = (current - float(z[n_row, n_col])) / max(float(np.hypot(d_row, d_col)), 1e-9)
                    if drop > steepest_drop:
                        steepest_drop = drop
                        receiver = (n_row, n_col)
            receivers[row, col] = receiver

    area = np.ones_like(z, dtype=float)
    for flat_index in np.argsort(z, axis=None)[::-1]:
        row, col = np.unravel_index(int(flat_index), z.shape)
        n_row, n_col = receivers[row, col]
        if n_row >= 0:
            area[n_row, n_col] += area[row, col]
    return _normalize(area)


def analyze_dem_surface(dem: np.ndarray) -> dict[str, np.ndarray | dict[str, float]]:
    z = _fill_nan_with_mean(dem)
    gy, gx = np.gradient(z)
    slope = np.hypot(gx, gy)
    curvature = (
        np.roll(z, 1, axis=0)
        + np.roll(z, -1, axis=0)
        + np.roll(z, 1, axis=1)
        + np.roll(z, -1, axis=1)
        - 4.0 * z
    )
    drainage = _drainage_area(z)
    return {
        "slope": slope,
        "curvature": curvature,
        "drainage_area": drainage,
        "summary": {
            "relief": float(np.max(z) - np.min(z)),
            "mean_elevation": float(np.mean(z)),
            "mean_slope": float(np.mean(slope)),
            "max_drainage_area": float(np.max(drainage)),
        },
    }


def dem_research_cards(
    analysis: dict[str, np.ndarray | dict[str, float]],
) -> tuple[tuple[str, str, str], ...]:
    summary = analysis["summary"]
    assert isinstance(summary, dict)
    return (
        ("기복", f"{summary['relief']:.2f}", "최고점과 최저점의 차이입니다."),
        ("평균 고도", f"{summary['mean_elevation']:.2f}", "DEM 전체 평균 고도입니다."),
        ("평균 경사", f"{summary['mean_slope']:.3f}", "값이 클수록 사면 작용과 절개 가능성이 큽니다."),
        ("배수 집중", f"{summary['max_drainage_area']:.2f}", "1에 가까울수록 흐름이 특정 경로에 모입니다."),
    )


def normalize_dem_layer(
    analysis: dict[str, np.ndarray | dict[str, float]],
    key: str,
) -> np.ndarray:
    if key not in DEM_LAYER_LABELS:
        raise KeyError(f"Unknown DEM layer: {key}")
    layer = analysis[key]
    assert isinstance(layer, np.ndarray)
    return _normalize(layer)


def process_hints_from_dem(
    analysis: dict[str, np.ndarray | dict[str, float]],
) -> tuple[str, ...]:
    summary = analysis["summary"]
    assert isinstance(summary, dict)
    slope = analysis["slope"]
    curvature = analysis["curvature"]
    drainage = analysis["drainage_area"]
    assert isinstance(slope, np.ndarray)
    assert isinstance(curvature, np.ndarray)
    assert isinstance(drainage, np.ndarray)

    hints: list[str] = []
    if float(summary["max_drainage_area"]) > 0.9 and float(summary["mean_slope"]) > 0.2:
        hints.append("배수 집중과 경사가 함께 나타나 하천 침식/운반 작용 후보가 큽니다.")
    if float(np.percentile(slope, 90)) > max(float(summary["mean_slope"]) * 1.4, 0.1):
        hints.append("상위 경사 구간이 뚜렷해 사면 붕괴, 절벽, 빙식 경계 같은 급경사 작용을 점검할 수 있습니다.")
    curvature_spread = float(np.percentile(curvature, 95) - np.percentile(curvature, 5))
    if curvature_spread > max(float(summary["relief"]) * 0.04, 0.05):
        hints.append("곡률 변화가 커서 볼록/오목 지형 경계와 침식·퇴적 전환대를 비교하기 좋습니다.")
    if not hints:
        hints.append("현재 DEM은 변화가 완만합니다. 기복이 작은 평탄면, 퇴적면, 저에너지 환경 후보로 먼저 해석하세요.")
    return tuple(hints)
