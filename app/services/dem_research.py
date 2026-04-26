from __future__ import annotations

import csv
from io import StringIO

import numpy as np


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
