from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Any

import numpy as np


@dataclass(frozen=True)
class ProcessKernelParameters:
    landform_id: str
    grid_size: int = 56
    total_time_years: int = 40_000
    dt_years: float = 250.0
    save_frames: int = 25
    force_scale: float = 1.0
    secondary_scale: float = 1.0
    uplift_rate: float = 0.0
    diffusion_d: float = 0.012
    base_level: float = 0.0


def _grid(grid_size: int) -> tuple[np.ndarray, np.ndarray]:
    y, x = np.indices((grid_size, grid_size), dtype=float)
    denom = max(grid_size - 1, 1)
    return x / denom, y / denom


def _normalize(field: np.ndarray) -> np.ndarray:
    arr = np.asarray(field, dtype=float)
    arr = np.nan_to_num(arr, nan=0.0, posinf=0.0, neginf=0.0)
    low = float(np.min(arr))
    high = float(np.max(arr))
    if high - low <= 1e-12:
        return np.zeros_like(arr)
    return (arr - low) / (high - low)


def _laplacian(z: np.ndarray) -> np.ndarray:
    return (
        np.roll(z, 1, axis=0)
        + np.roll(z, -1, axis=0)
        + np.roll(z, 1, axis=1)
        + np.roll(z, -1, axis=1)
        - 4.0 * z
    )


def _base_surface(landform_id: str, grid_size: int, base_level: float) -> np.ndarray:
    x, y = _grid(grid_size)
    if landform_id == "u_valley":
        valley = 95.0 * (1.0 - y) + 42.0 * np.abs(x - 0.5) ** 1.55
        trough = 28.0 * np.exp(-((x - 0.5) / 0.16) ** 4)
        return np.maximum(valley - trough, base_level)
    if landform_id == "coastal_cliff":
        land = 72.0 * (1.0 - x) + 10.0 * np.sin(2.0 * np.pi * y)
        sea = base_level + 2.0 * (x > 0.68)
        return np.maximum(np.where(x > 0.68, sea, land), base_level)
    if landform_id == "barchan":
        horn_left = np.exp(-(((x - 0.35) / 0.11) ** 2 + ((y - 0.62) / 0.23) ** 2))
        horn_right = np.exp(-(((x - 0.65) / 0.11) ** 2 + ((y - 0.62) / 0.23) ** 2))
        body = 42.0 * np.exp(-(((x - 0.5) / 0.18) ** 2 + ((y - 0.45) / 0.17) ** 2))
        return base_level + body + 18.0 * (horn_left + horn_right)
    if landform_id == "lava_dome":
        r = np.hypot(x - 0.5, y - 0.5)
        return base_level + 105.0 * np.exp(-((r / 0.22) ** 2)) + 8.0 * (1.0 - y)
    if landform_id == "karst_doline":
        upland = 42.0 + 10.0 * np.sin(2.5 * np.pi * x) * np.sin(2.0 * np.pi * y)
        doline = 24.0 * np.exp(-(((x - 0.5) / 0.18) ** 2 + ((y - 0.5) / 0.16) ** 2))
        return np.maximum(base_level, upland - doline)
    return np.zeros((grid_size, grid_size), dtype=float)


def _masks(landform_id: str, grid_size: int, secondary_scale: float) -> dict[str, np.ndarray]:
    x, y = _grid(grid_size)
    if landform_id == "u_valley":
        center = np.exp(-((x - 0.5) / (0.12 + 0.05 * secondary_scale)) ** 4)
        flow = np.clip(1.0 - y, 0.0, 1.0)
        return {"glacial": center * (0.35 + 0.65 * flow), "deposition": center * np.clip(y - 0.62, 0.0, 1.0)}
    if landform_id == "coastal_cliff":
        shore = np.exp(-((x - 0.66) / 0.045) ** 2)
        wave_focus = shore * (0.75 + 0.25 * np.sin(4.0 * np.pi * y) ** 2)
        platform = np.exp(-((x - 0.74) / 0.12) ** 2)
        return {"marine": wave_focus, "deposition": platform * np.clip(x - 0.68, 0.0, 1.0)}
    if landform_id == "barchan":
        wind_path = np.exp(-((x - 0.5) / 0.26) ** 2)
        lee = np.exp(-(((x - 0.5) / 0.22) ** 2 + ((y - 0.68) / 0.12) ** 2))
        stoss = np.exp(-(((x - 0.5) / 0.22) ** 2 + ((y - 0.35) / 0.16) ** 2))
        return {"aeolian": wind_path * (0.35 + y), "deposition": lee, "erosion": stoss}
    if landform_id == "lava_dome":
        r = np.hypot(x - 0.5, y - 0.5)
        vent = np.exp(-((r / 0.12) ** 2))
        apron = np.exp(-((r / 0.34) ** 2))
        return {"volcanic": vent, "deposition": apron * (1.0 - vent), "erosion": _normalize(r)}
    if landform_id == "karst_doline":
        sink = np.exp(-(((x - 0.5) / 0.21) ** 2 + ((y - 0.5) / 0.18) ** 2))
        groundwater = np.exp(-((y - 0.56) / (0.26 + 0.05 * secondary_scale)) ** 2)
        return {"karst": sink, "groundwater": groundwater * sink, "deposition": sink * np.clip(y - 0.55, 0.0, 1.0)}
    return {}


def _empty_process(z: np.ndarray) -> dict[str, np.ndarray]:
    zero = np.zeros_like(z)
    return {
        "erosion": zero,
        "deposition": zero,
        "diffusion": zero,
        "transport": zero,
        "tectonic": zero,
        "glacial": zero,
        "marine": zero,
        "aeolian": zero,
        "volcanic": zero,
        "karst": zero,
        "groundwater": zero,
        "moraine": zero,
        "total_erosion": zero,
    }


def _stats(z: np.ndarray, params: ProcessKernelParameters, fields: dict[str, np.ndarray]) -> dict[str, float]:
    dt = max(params.dt_years, 1e-9)
    erosion = fields.get("total_erosion", np.zeros_like(z))
    deposition = fields.get("deposition", np.zeros_like(z))
    diffusion = fields.get("diffusion", np.zeros_like(z))
    tectonic = fields.get("tectonic", np.zeros_like(z))
    return {
        "mean_elevation": float(np.mean(z)),
        "max_elevation": float(np.max(z)),
        "mean_erosion_rate": 0.0,
        "max_erosion_rate": 0.0,
        "mean_weathering_rate": 0.0,
        "mean_diffusion": float(np.mean(np.abs(diffusion)) / dt),
        "mean_deposition_rate": float(np.mean(deposition) / dt),
        "mean_lateral_erosion": 0.0,
        "mean_glacial": float(np.mean(fields.get("glacial", 0.0)) / dt),
        "mean_marine": float(np.mean(fields.get("marine", 0.0)) / dt),
        "mean_landslide": 0.0,
        "mean_faulting": 0.0,
        "mean_folding": 0.0,
        "mean_karst": float(np.mean(fields.get("karst", 0.0)) / dt),
        "mean_aeolian": float(np.mean(fields.get("aeolian", 0.0)) / dt),
        "mean_volcanic": float(np.mean(fields.get("volcanic", 0.0)) / dt),
        "mean_groundwater": float(np.mean(fields.get("groundwater", 0.0)) / dt),
        "mean_freeze_thaw": 0.0,
        "mean_moraine": float(np.mean(fields.get("moraine", 0.0)) / dt),
        "mean_uniform_uplift": max(float(params.uplift_rate), 0.0),
        "mean_subsidence": max(float(-params.uplift_rate), 0.0),
        "mean_soil_depth": float(np.mean(np.maximum(z - params.base_level, 0.0)) * 0.015),
        "total_erosion": float(np.sum(erosion)),
        "total_deposition": float(np.sum(deposition)),
        "total_weathering": 0.0,
        "total_uplift": float(np.sum(np.maximum(tectonic, 0.0))),
        "total_folding": 0.0,
        "total_subsidence": float(np.sum(np.maximum(-tectonic, 0.0))),
    }


def _step(z: np.ndarray, params: ProcessKernelParameters, masks: dict[str, np.ndarray]) -> tuple[np.ndarray, dict[str, np.ndarray], dict[str, float]]:
    diffusion = params.dt_years * params.diffusion_d * _laplacian(z) * 0.0007
    tectonic = np.full_like(z, params.uplift_rate * params.dt_years)
    deposition = np.zeros_like(z)
    erosion = np.zeros_like(z)
    construction = np.zeros_like(z)
    extra: dict[str, np.ndarray] = {}

    if params.landform_id == "u_valley":
        glacial = params.dt_years * 0.018 * params.force_scale * masks["glacial"]
        moraine = params.dt_years * 0.004 * params.secondary_scale * masks["deposition"]
        erosion = glacial
        deposition = moraine
        extra.update(glacial=glacial, moraine=moraine)
    elif params.landform_id == "coastal_cliff":
        marine = params.dt_years * 0.026 * params.force_scale * masks["marine"]
        beach = params.dt_years * 0.004 * params.secondary_scale * masks["deposition"]
        erosion = marine
        deposition = beach
        extra.update(marine=marine)
    elif params.landform_id == "barchan":
        aeolian = params.dt_years * 0.014 * params.force_scale * masks["aeolian"]
        erosion = aeolian * masks["erosion"]
        deposition = params.dt_years * 0.018 * params.secondary_scale * masks["deposition"]
        extra.update(aeolian=aeolian, transport=aeolian)
    elif params.landform_id == "lava_dome":
        volcanic = params.dt_years * 0.036 * params.force_scale * masks["volcanic"]
        lava_apron = params.dt_years * 0.006 * params.secondary_scale * masks["deposition"]
        flank_erosion = params.dt_years * 0.003 * masks["erosion"]
        construction = volcanic
        deposition = lava_apron
        erosion = flank_erosion
        extra.update(volcanic=volcanic)
    elif params.landform_id == "karst_doline":
        karst = params.dt_years * 0.016 * params.force_scale * masks["karst"]
        groundwater = params.dt_years * 0.006 * params.secondary_scale * masks["groundwater"]
        fill = params.dt_years * 0.002 * masks["deposition"]
        erosion = karst + groundwater
        deposition = fill
        extra.update(karst=karst, groundwater=groundwater)

    new_z = z + tectonic + diffusion + construction - erosion + deposition
    new_z = np.maximum(new_z, params.base_level)
    fields = _empty_process(z)
    fields.update(
        {
            "erosion": erosion,
            "deposition": deposition,
            "diffusion": diffusion,
            "tectonic": tectonic,
            "total_erosion": erosion,
        }
    )
    fields.update(extra)
    return new_z, fields, _stats(new_z, params, fields)


@lru_cache(maxsize=64)
def run_process_morphology_model(params: ProcessKernelParameters) -> dict[str, Any]:
    grid_size = int(np.clip(params.grid_size, 24, 96))
    total_time = int(np.clip(params.total_time_years, 2_500, 160_000))
    steps = max(int(total_time / max(params.dt_years, 1e-9)), 1)
    save_every = max(steps // max(params.save_frames - 1, 1), 1)
    z = _base_surface(params.landform_id, grid_size, params.base_level)
    masks = _masks(params.landform_id, grid_size, params.secondary_scale)

    history = [z.copy()]
    times = [0.0]
    process_history = [_empty_process(z)]
    stats_history = [_stats(z, params, process_history[0])]
    current_time = 0.0
    for step_idx in range(steps):
        z, fields, stats = _step(z, params, masks)
        current_time += params.dt_years
        if (step_idx + 1) % save_every == 0 or step_idx == steps - 1:
            history.append(z.copy())
            times.append(float(current_time))
            process_history.append({key: value.copy() for key, value in fields.items()})
            stats_history.append(dict(stats))

    return {
        "history": history,
        "times": times,
        "stats_history": stats_history,
        "process_history": process_history,
        "kernel": f"{params.landform_id}_process_v1",
        "parameters": params,
    }
