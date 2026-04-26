from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Any

import numpy as np


@dataclass(frozen=True)
class RiverKernelParameters:
    landform_id: str
    grid_size: int = 56
    total_time_years: int = 40_000
    dt_years: float = 250.0
    save_frames: int = 25
    erodibility_k: float = 0.00018
    diffusion_d: float = 0.018
    uplift_rate: float = 0.00012
    water_discharge_scale: float = 1.0
    sediment_supply_scale: float = 1.0
    deposition_rate: float = 0.42
    base_level: float = 0.0
    stream_power_m: float = 0.5
    stream_power_n: float = 1.0


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


def _fixed_boundaries(z: np.ndarray, base_level: float) -> np.ndarray:
    out = z.copy()
    out[0, :] = out[1, :]
    out[:, 0] = out[:, 1]
    out[:, -1] = out[:, -2]
    out[-1, :] = np.minimum(out[-2, :], base_level + 2.0)
    return out


def _grid(grid_size: int) -> tuple[np.ndarray, np.ndarray]:
    y, x = np.indices((grid_size, grid_size), dtype=float)
    denom = max(grid_size - 1, 1)
    return x / denom, y / denom


def _channel_masks(landform_id: str, grid_size: int) -> dict[str, np.ndarray]:
    x, y = _grid(grid_size)
    if landform_id == "alluvial_fan":
        apex = 0.18
        spread = np.clip((y - apex) / max(1.0 - apex, 1e-6), 0.0, 1.0)
        center = 0.5
        distance = np.abs(x - center)
        fan_width = 0.035 + 0.42 * spread
        channel = np.exp(-((distance / fan_width) ** 2)) * (y >= apex)
        depositional_zone = np.exp(-((distance / (fan_width * 1.25 + 1e-6)) ** 2)) * spread
    elif landform_id == "delta":
        trunk = np.exp(-((x - 0.5) / 0.045) ** 2) * (y < 0.58)
        mouth = np.clip((y - 0.48) / 0.52, 0.0, 1.0)
        distributary_left = np.exp(-((x - (0.5 - 0.28 * mouth)) / 0.055) ** 2)
        distributary_right = np.exp(-((x - (0.5 + 0.28 * mouth)) / 0.055) ** 2)
        distributary_mid = np.exp(-((x - 0.5) / (0.06 + 0.09 * mouth)) ** 2)
        channel = np.maximum(trunk, np.maximum(distributary_left, distributary_right) * (y >= 0.45))
        channel = np.maximum(channel, distributary_mid * (y >= 0.52))
        depositional_zone = mouth * np.exp(-((x - 0.5) / (0.18 + 0.25 * mouth)) ** 2)
    else:
        meander = 0.06 * np.sin(2.5 * np.pi * y)
        center = 0.5 + meander
        valley_width = 0.035 + 0.09 * y
        channel = np.exp(-(((x - center) / valley_width) ** 2))
        depositional_zone = np.exp(-(((x - center) / (valley_width * 1.7)) ** 2)) * np.clip(y - 0.45, 0, 1)

    return {
        "channel": np.clip(channel, 0.0, 1.0),
        "depositional_zone": np.clip(depositional_zone, 0.0, 1.0),
    }


def _initial_surface(landform_id: str, grid_size: int, base_level: float) -> np.ndarray:
    x, y = _grid(grid_size)
    downstream_slope = 130.0 * (1.0 - y) + base_level
    ridge = 38.0 * (np.abs(x - 0.5) ** 1.45)
    masks = _channel_masks(landform_id, grid_size)
    channel = masks["channel"]

    if landform_id == "alluvial_fan":
        apex = np.exp(-(((x - 0.5) / 0.18) ** 2 + ((y - 0.18) / 0.08) ** 2))
        surface = downstream_slope * 0.72 + 28.0 * apex + 18.0 * np.abs(x - 0.5)
    elif landform_id == "delta":
        marine_plain = base_level + 9.0 * (1.0 - y)
        river_plain = downstream_slope * 0.35 + 14.0
        surface = np.where(y > 0.52, marine_plain, river_plain)
    else:
        surface = downstream_slope + ridge - 18.0 * channel

    return _fixed_boundaries(np.maximum(surface, base_level), base_level)


def _drainage_area(landform_id: str, channel: np.ndarray, water_scale: float) -> np.ndarray:
    _x, y = _grid(channel.shape[0])
    downstream_growth = 0.08 + np.power(np.clip(y, 0.0, 1.0), 1.65)
    if landform_id == "delta":
        downstream_growth = 0.15 + np.power(np.clip(y, 0.0, 1.0), 1.25)
    return water_scale * downstream_growth * (0.28 + 1.45 * channel)


def _step(z: np.ndarray, params: RiverKernelParameters, masks: dict[str, np.ndarray]) -> tuple[np.ndarray, dict[str, np.ndarray], dict[str, float]]:
    channel = masks["channel"]
    depositional_zone = masks["depositional_zone"]
    gy, gx = np.gradient(z)
    slope = np.hypot(gx, gy)
    slope_norm = _normalize(slope)
    area = _drainage_area(params.landform_id, channel, params.water_discharge_scale)

    stream_power = params.erodibility_k * np.power(area, params.stream_power_m) * np.power(slope + 1e-6, params.stream_power_n)
    erosion = params.dt_years * stream_power * (0.22 + 1.55 * channel)
    diffusion = params.dt_years * params.diffusion_d * _laplacian(z) * 0.00065

    low_slope = 1.0 - slope_norm
    outlet_bias = np.clip((_grid(z.shape[0])[1] - 0.35) / 0.65, 0.0, 1.0)
    sediment_flux = params.sediment_supply_scale * (0.65 * erosion + 0.35 * area * channel)
    deposition = params.dt_years * params.deposition_rate * sediment_flux * low_slope * depositional_zone * outlet_bias * 0.018

    if params.landform_id == "v_valley":
        deposition *= 0.34
    elif params.landform_id == "alluvial_fan":
        deposition *= 1.55
        erosion *= 0.78
    elif params.landform_id == "delta":
        deposition *= 1.85
        erosion *= 0.58

    uplift = np.full_like(z, params.uplift_rate * params.dt_years)
    if params.landform_id in {"alluvial_fan", "delta"}:
        uplift *= 0.45

    new_z = z + uplift + diffusion - erosion + deposition
    new_z = np.maximum(new_z, params.base_level)
    new_z = _fixed_boundaries(new_z, params.base_level)

    process_fields = {
        "erosion": erosion,
        "deposition": deposition,
        "diffusion": diffusion,
        "transport": sediment_flux,
        "tectonic": uplift,
        "total_erosion": erosion,
    }
    stats = {
        "mean_elevation": float(np.mean(new_z)),
        "max_elevation": float(np.max(new_z)),
        "mean_erosion_rate": float(np.mean(erosion) / max(params.dt_years, 1e-9)),
        "max_erosion_rate": float(np.max(erosion) / max(params.dt_years, 1e-9)),
        "mean_diffusion": float(np.mean(np.abs(diffusion)) / max(params.dt_years, 1e-9)),
        "mean_deposition_rate": float(np.mean(deposition) / max(params.dt_years, 1e-9)),
        "mean_weathering_rate": 0.0,
        "mean_lateral_erosion": 0.0,
        "mean_glacial": 0.0,
        "mean_marine": 0.0,
        "mean_landslide": 0.0,
        "mean_faulting": 0.0,
        "mean_folding": 0.0,
        "mean_karst": 0.0,
        "mean_aeolian": 0.0,
        "mean_volcanic": 0.0,
        "mean_groundwater": 0.0,
        "mean_freeze_thaw": 0.0,
        "mean_moraine": 0.0,
        "mean_uniform_uplift": max(float(params.uplift_rate), 0.0),
        "mean_subsidence": max(float(-params.uplift_rate), 0.0),
        "mean_soil_depth": float(np.mean(np.maximum(new_z - params.base_level, 0.0)) * 0.02),
        "total_erosion": float(np.sum(erosion)),
        "total_deposition": float(np.sum(deposition)),
        "total_weathering": 0.0,
        "total_uplift": float(np.sum(np.maximum(uplift, 0.0))),
        "total_folding": 0.0,
        "total_subsidence": float(np.sum(np.maximum(-uplift, 0.0))),
    }
    return new_z, process_fields, stats


@lru_cache(maxsize=64)
def run_river_morphology_model(params: RiverKernelParameters) -> dict[str, Any]:
    grid_size = int(np.clip(params.grid_size, 24, 96))
    total_time = int(np.clip(params.total_time_years, 2_500, 160_000))
    steps = max(int(total_time / max(params.dt_years, 1e-9)), 1)
    save_every = max(steps // max(params.save_frames - 1, 1), 1)
    masks = _channel_masks(params.landform_id, grid_size)
    z = _initial_surface(params.landform_id, grid_size, params.base_level)

    history = [z.copy()]
    times = [0.0]
    process_history = [
        {
            "erosion": np.zeros_like(z),
            "deposition": np.zeros_like(z),
            "diffusion": np.zeros_like(z),
            "transport": np.zeros_like(z),
            "tectonic": np.zeros_like(z),
            "total_erosion": np.zeros_like(z),
        }
    ]
    stats_history = [
        {
            "mean_elevation": float(np.mean(z)),
            "max_elevation": float(np.max(z)),
            "mean_erosion_rate": 0.0,
            "max_erosion_rate": 0.0,
            "mean_diffusion": 0.0,
            "mean_deposition_rate": 0.0,
            "mean_weathering_rate": 0.0,
            "mean_uniform_uplift": max(float(params.uplift_rate), 0.0),
            "mean_subsidence": max(float(-params.uplift_rate), 0.0),
            "mean_soil_depth": 0.0,
            "total_erosion": 0.0,
            "total_deposition": 0.0,
            "total_weathering": 0.0,
            "total_uplift": 0.0,
            "total_subsidence": 0.0,
        }
    ]

    current_time = 0.0
    for step_idx in range(steps):
        z, process_fields, stats = _step(z, params, masks)
        current_time += params.dt_years
        if (step_idx + 1) % save_every == 0 or step_idx == steps - 1:
            history.append(z.copy())
            times.append(float(current_time))
            process_history.append({key: value.copy() for key, value in process_fields.items()})
            stats_history.append(dict(stats))

    return {
        "history": history,
        "times": times,
        "stats_history": stats_history,
        "process_history": process_history,
        "kernel": "river_morphology_v1",
        "parameters": params,
    }
