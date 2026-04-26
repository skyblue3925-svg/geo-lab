from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Any

import numpy as np


@dataclass(frozen=True)
class GeomorphicEngineParameters:
    preset_id: str
    grid_size: int = 56
    total_time_years: int = 40_000
    dt_years: float = 250.0
    save_frames: int = 25
    fluvial: float = 0.0
    sediment: float = 0.0
    marine: float = 0.0
    glacial: float = 0.0
    aeolian: float = 0.0
    volcanic: float = 0.0
    karst: float = 0.0
    groundwater: float = 0.0
    uplift_rate: float = 0.0
    diffusion_d: float = 0.012
    base_level: float = 0.0
    sea_level: float | None = None
    wave_energy_scale: float = 1.0
    wind_direction_degrees: float = 90.0
    wind_speed: float | None = None
    sand_supply: float | None = None
    eruption_rate: float | None = None
    viscosity: float | None = None
    lava_spread: float = 1.0
    cooling_rate: float = 1.0
    rock_solubility: float = 1.0
    water_supply: float | None = None


def _grid(grid_size: int) -> tuple[np.ndarray, np.ndarray]:
    y, x = np.indices((grid_size, grid_size), dtype=float)
    denom = max(grid_size - 1, 1)
    return x / denom, y / denom


def _normalize(field: np.ndarray) -> np.ndarray:
    arr = np.nan_to_num(np.asarray(field, dtype=float), nan=0.0, posinf=0.0, neginf=0.0)
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
    return np.maximum(out, base_level)


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
        "wave_energy": zero,
        "shoreline_retreat": zero,
        "wave_cut_platform": zero,
        "beach_deposition": zero,
        "longshore_transport": zero,
        "wave_refraction": zero,
        "storm_runup": zero,
        "coastal_sediment_budget": zero,
        "wind_vector_x": zero,
        "wind_vector_y": zero,
        "sand_flux": zero,
        "stoss_erosion": zero,
        "lee_deposition": zero,
        "wind_shear_stress": zero,
        "sand_availability": zero,
        "shelter_factor": zero,
        "dune_migration": zero,
        "volcanic_construction": zero,
        "lava_flow": zero,
        "viscosity_resistance": zero,
        "cooling_limited_spread": zero,
        "groundwater_flow": zero,
        "solution_rate": zero,
        "subsurface_drainage": zero,
        "collapse_risk": zero,
        "ice_thickness": zero,
        "glacial_velocity": zero,
        "fluvial_erosion": zero,
        "drainage_area": zero,
        "transport_capacity": zero,
        "total_erosion": zero,
    }


def _initial_surface(preset_id: str, grid_size: int, base_level: float) -> np.ndarray:
    x, y = _grid(grid_size)
    downstream_slope = 130.0 * (1.0 - y) + base_level
    valley_sides = 38.0 * np.abs(x - 0.5) ** 1.45
    channel = np.exp(-(((x - 0.5 - 0.06 * np.sin(2.5 * np.pi * y)) / (0.04 + 0.09 * y)) ** 2))

    if preset_id == "alluvial_fan":
        apex = np.exp(-(((x - 0.5) / 0.18) ** 2 + ((y - 0.18) / 0.08) ** 2))
        surface = downstream_slope * 0.72 + 28.0 * apex + 18.0 * np.abs(x - 0.5)
    elif preset_id == "delta":
        marine_plain = base_level + 9.0 * (1.0 - y)
        river_plain = downstream_slope * 0.35 + 14.0
        surface = np.where(y > 0.52, marine_plain, river_plain)
    elif preset_id == "u_valley":
        surface = 95.0 * (1.0 - y) + 42.0 * np.abs(x - 0.5) ** 1.55
        surface -= 28.0 * np.exp(-((x - 0.5) / 0.16) ** 4)
    elif preset_id == "coastal_cliff":
        land = 72.0 * (1.0 - x) + 10.0 * np.sin(2.0 * np.pi * y)
        sea = base_level + 2.0 * (x > 0.68)
        surface = np.where(x > 0.68, sea, land)
    elif preset_id == "barchan":
        horn_left = np.exp(-(((x - 0.35) / 0.11) ** 2 + ((y - 0.62) / 0.23) ** 2))
        horn_right = np.exp(-(((x - 0.65) / 0.11) ** 2 + ((y - 0.62) / 0.23) ** 2))
        body = 42.0 * np.exp(-(((x - 0.5) / 0.18) ** 2 + ((y - 0.45) / 0.17) ** 2))
        surface = base_level + body + 18.0 * (horn_left + horn_right)
    elif preset_id == "lava_dome":
        r = np.hypot(x - 0.5, y - 0.5)
        surface = base_level + 105.0 * np.exp(-((r / 0.22) ** 2)) + 8.0 * (1.0 - y)
    elif preset_id == "karst_doline":
        upland = 42.0 + 10.0 * np.sin(2.5 * np.pi * x) * np.sin(2.0 * np.pi * y)
        surface = upland - 24.0 * np.exp(-(((x - 0.5) / 0.18) ** 2 + ((y - 0.5) / 0.16) ** 2))
    else:
        surface = downstream_slope + valley_sides - 18.0 * channel

    return _fixed_boundaries(surface, base_level)


def _drainage_area(z: np.ndarray) -> np.ndarray:
    rows, cols = z.shape
    receivers = np.full((rows, cols, 2), -1, dtype=int)
    for row in range(rows):
        for col in range(cols):
            steepest_drop = 0.0
            receiver = (-1, -1)
            current = float(z[row, col])
            for d_row in (-1, 0, 1):
                for d_col in (-1, 0, 1):
                    if d_row == 0 and d_col == 0:
                        continue
                    n_row = row + d_row
                    n_col = col + d_col
                    if n_row < 0 or n_row >= rows or n_col < 0 or n_col >= cols:
                        continue
                    distance = float(np.hypot(d_row, d_col))
                    drop = (current - float(z[n_row, n_col])) / max(distance, 1e-9)
                    if drop > steepest_drop:
                        steepest_drop = drop
                        receiver = (n_row, n_col)
            receivers[row, col] = receiver

    area = np.ones_like(z, dtype=float)
    flat_indices = np.argsort(z, axis=None)[::-1]
    for flat_index in flat_indices:
        row, col = np.unravel_index(int(flat_index), z.shape)
        n_row, n_col = receivers[row, col]
        if n_row >= 0:
            area[n_row, n_col] += area[row, col]
    return _normalize(area)


def _process_masks(preset_id: str, grid_size: int) -> dict[str, np.ndarray]:
    x, y = _grid(grid_size)
    centerline = np.exp(-(((x - 0.5 - 0.06 * np.sin(2.5 * np.pi * y)) / (0.04 + 0.09 * y)) ** 2))
    downstream = np.clip((y - 0.35) / 0.65, 0.0, 1.0)
    lower = np.clip(y - 0.5, 0.0, 1.0)
    r = np.hypot(x - 0.5, y - 0.5)

    fan_spread = np.clip((y - 0.18) / 0.82, 0.0, 1.0)
    fan_width = 0.035 + 0.42 * fan_spread
    fan = np.exp(-((np.abs(x - 0.5) / (fan_width + 1e-6)) ** 2)) * fan_spread

    mouth = np.clip((y - 0.48) / 0.52, 0.0, 1.0)
    delta = mouth * np.exp(-((x - 0.5) / (0.18 + 0.25 * mouth)) ** 2)

    glacial = np.exp(-((x - 0.5) / 0.16) ** 4) * (0.35 + 0.65 * (1.0 - y))
    shore = np.exp(-((x - 0.66) / 0.045) ** 2)
    platform = np.exp(-((x - 0.74) / 0.12) ** 2) * np.clip(x - 0.68, 0.0, 1.0)
    aeolian_path = np.exp(-((x - 0.5) / 0.26) ** 2) * (0.35 + y)
    lee = np.exp(-(((x - 0.5) / 0.22) ** 2 + ((y - 0.68) / 0.12) ** 2))
    stoss = np.exp(-(((x - 0.5) / 0.22) ** 2 + ((y - 0.35) / 0.16) ** 2))
    vent = np.exp(-((r / 0.12) ** 2))
    lava_apron = np.exp(-((r / 0.34) ** 2)) * (1.0 - vent)
    sink = np.exp(-(((x - 0.5) / 0.21) ** 2 + ((y - 0.5) / 0.18) ** 2))
    groundwater = sink * np.exp(-((y - 0.56) / 0.28) ** 2)

    fluvial_deposition = centerline * lower
    if preset_id == "alluvial_fan":
        centerline = fan
        fluvial_deposition = fan
    elif preset_id == "delta":
        centerline = np.maximum(centerline * (y < 0.62), delta)
        fluvial_deposition = delta

    return {
        "channel": np.clip(centerline, 0.0, 1.0),
        "fluvial_deposition": np.clip(fluvial_deposition, 0.0, 1.0),
        "glacial": np.clip(glacial, 0.0, 1.0),
        "moraine": np.clip(glacial * downstream, 0.0, 1.0),
        "shore": np.clip(shore, 0.0, 1.0),
        "platform": np.clip(platform, 0.0, 1.0),
        "aeolian": np.clip(aeolian_path, 0.0, 1.0),
        "lee": np.clip(lee, 0.0, 1.0),
        "stoss": np.clip(stoss, 0.0, 1.0),
        "vent": np.clip(vent, 0.0, 1.0),
        "lava_apron": np.clip(lava_apron, 0.0, 1.0),
        "flank": np.clip(_normalize(r), 0.0, 1.0),
        "sink": np.clip(sink, 0.0, 1.0),
        "groundwater": np.clip(groundwater, 0.0, 1.0),
    }


def _fluvial_process(
    z: np.ndarray,
    params: GeomorphicEngineParameters,
    masks: dict[str, np.ndarray],
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    if params.fluvial <= 0.0:
        zero = np.zeros_like(z)
        return zero, zero, zero, zero, zero
    gy, gx = np.gradient(z)
    slope = np.hypot(gx, gy)
    slope_norm = _normalize(slope)
    _x, y = _grid(z.shape[0])
    drainage = _drainage_area(z)
    channel_weight = np.clip(0.65 * drainage + 0.35 * masks["channel"], 0.0, 1.0)
    area = 0.08 + np.power(channel_weight, 1.35)
    stream_power = 0.00018 * params.fluvial * np.power(area, 0.5) * np.power(slope + 1e-6, 1.0)
    erosion = params.dt_years * stream_power * (0.22 + 1.55 * channel_weight)
    transport_capacity = params.dt_years * 0.0012 * params.fluvial * np.power(area + 1e-6, 0.7) * np.power(slope + 1e-6, 0.9)
    sediment_flux = params.sediment * (0.82 * erosion + 0.18 * area * channel_weight)
    if params.preset_id == "alluvial_fan":
        erosion *= 0.55
        sediment_flux *= 1.65
        transport_capacity *= 0.35
    elif params.preset_id == "delta":
        erosion *= 0.25
        sediment_flux *= 2.5
        transport_capacity *= 0.18
    elif params.preset_id == "v_valley":
        sediment_flux *= 0.65
    low_energy_excess = np.maximum(sediment_flux - transport_capacity, 0.0)
    depositional_window = np.clip(0.5 * masks["fluvial_deposition"] + 0.5 * y, 0.0, 1.0)
    deposition = 0.55 * low_energy_excess * (1.0 - slope_norm) * depositional_window
    deposition = np.minimum(deposition, sediment_flux)
    return erosion, deposition, sediment_flux, drainage, transport_capacity


def _glacial_process(
    z: np.ndarray,
    params: GeomorphicEngineParameters,
    masks: dict[str, np.ndarray],
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    if params.glacial <= 0.0:
        zero = np.zeros_like(z)
        return zero, zero, zero, zero
    gy, gx = np.gradient(z)
    surface_slope = _normalize(np.hypot(gx, gy))
    altitude = _normalize(z)
    accumulation = np.clip(0.55 * altitude + 0.45 * masks["glacial"], 0.0, 1.0)
    thickness = params.glacial * accumulation * masks["glacial"]
    velocity = _normalize(np.power(thickness + 1e-9, 3.0) * (0.18 + surface_slope))
    basal_sliding = thickness * (0.35 + 0.65 * velocity)
    erosion = params.dt_years * 0.014 * params.glacial * basal_sliding

    thickness_gradient = np.maximum(thickness - np.roll(thickness, -1, axis=0), 0.0)
    terminus = masks["moraine"] * (0.45 + 0.55 * _normalize(thickness_gradient))
    moraine = params.dt_years * 0.0045 * params.glacial * max(params.sediment, 0.15) * terminus
    return erosion, moraine, thickness, velocity


def _marine_process(
    z: np.ndarray,
    params: GeomorphicEngineParameters,
    masks: dict[str, np.ndarray],
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    if params.marine <= 0.0:
        zero = np.zeros_like(z)
        return zero, zero, zero, zero, zero, zero, zero, zero, zero
    sea_level = params.base_level if params.sea_level is None else float(params.sea_level)
    gy, gx = np.gradient(z)
    cliff_gradient = _normalize(np.abs(gx))
    alongshore_gradient = _normalize(np.abs(gy))
    tidal_window = np.clip(1.0 - np.abs(z - sea_level) / 48.0, 0.0, 1.0)
    nearshore_window = np.clip(1.0 - np.abs(z - sea_level) / 24.0, 0.0, 1.0)
    wave_refraction = masks["shore"] * (0.35 + 0.65 * alongshore_gradient)
    wave_energy = (
        params.marine
        * max(params.wave_energy_scale, 0.0)
        * masks["shore"]
        * (0.30 + 0.40 * tidal_window + 0.18 * cliff_gradient + 0.12 * wave_refraction)
    )
    shoreline_retreat = params.dt_years * 0.026 * wave_energy
    storm_runup = params.dt_years * 0.0032 * params.marine * max(params.wave_energy_scale, 0.0) * masks["shore"] * np.clip(
        1.0 - np.abs(z - (sea_level + 6.0)) / 36.0,
        0.0,
        1.0,
    )
    wave_cut_platform = (
        params.dt_years
        * 0.010
        * params.marine
        * max(params.wave_energy_scale, 0.0)
        * masks["platform"]
        * nearshore_window
        * (0.45 + 0.55 * (1.0 - cliff_gradient))
    )
    beach_deposition = (
        params.dt_years
        * 0.0048
        * params.marine
        * max(params.sediment, 0.15)
        * masks["platform"]
        * np.clip(1.0 - wave_energy, 0.15, 1.0)
    )
    longshore_transport = params.dt_years * 0.006 * params.marine * max(params.sediment, 0.15) * masks["platform"] * wave_refraction
    coastal_sediment_budget = beach_deposition - 0.35 * longshore_transport - 0.20 * shoreline_retreat
    return (
        shoreline_retreat,
        wave_cut_platform,
        beach_deposition,
        wave_energy,
        shoreline_retreat,
        longshore_transport,
        wave_refraction,
        storm_runup,
        coastal_sediment_budget,
    )


def _aeolian_process(
    z: np.ndarray,
    params: GeomorphicEngineParameters,
    masks: dict[str, np.ndarray],
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    if params.aeolian <= 0.0:
        zero = np.zeros_like(z)
        return zero, zero, zero, zero, zero, zero, zero, zero, zero, zero
    wind_speed = params.aeolian if params.wind_speed is None else max(float(params.wind_speed), 0.0)
    sand_supply = max(params.sediment if params.sand_supply is None else float(params.sand_supply), 0.15)
    angle = np.deg2rad(params.wind_direction_degrees)
    wind_x = float(np.cos(angle))
    wind_y = float(np.sin(angle))
    gy, gx = np.gradient(z)
    windward_slope = gx * wind_x + gy * wind_y
    stoss_exposure = _normalize(np.maximum(windward_slope, 0.0))
    lee_exposure = _normalize(np.maximum(-windward_slope, 0.0))
    stoss_mask = np.clip(0.70 * masks["stoss"] + 0.30 * stoss_exposure, 0.0, 1.0)
    shelter_factor = np.clip(0.55 * masks["lee"] + 0.45 * lee_exposure, 0.0, 1.0)
    lee_mask = np.clip(0.70 * masks["lee"] + 0.30 * shelter_factor, 0.0, 1.0)
    wind_vector_x = np.full_like(z, wind_speed * wind_x)
    wind_vector_y = np.full_like(z, wind_speed * wind_y)
    wind_shear_stress = np.square(wind_speed) * masks["aeolian"] * (0.45 + 0.55 * stoss_exposure)
    sand_availability = sand_supply * masks["aeolian"]
    sand_flux = params.dt_years * 0.014 * wind_shear_stress * sand_availability
    stoss_erosion = sand_flux * stoss_mask
    lee_deposition = params.dt_years * 0.018 * wind_speed * sand_supply * lee_mask
    dune_migration = lee_deposition - stoss_erosion
    return (
        sand_flux,
        stoss_erosion,
        lee_deposition,
        wind_vector_x,
        wind_vector_y,
        sand_flux,
        wind_shear_stress,
        sand_availability,
        shelter_factor,
        dune_migration,
    )


def _volcanic_process(
    z: np.ndarray,
    params: GeomorphicEngineParameters,
    masks: dict[str, np.ndarray],
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    if params.volcanic <= 0.0:
        zero = np.zeros_like(z)
        return zero, zero, zero, zero, zero
    eruption_rate = params.volcanic if params.eruption_rate is None else max(float(params.eruption_rate), 0.0)
    default_viscosity = np.clip(1.0 - params.diffusion_d / 0.06, 0.05, 1.0)
    viscosity = np.clip(default_viscosity if params.viscosity is None else float(params.viscosity), 0.05, 1.0)
    lava_spread = max(float(params.lava_spread), 0.05)
    cooling_rate = max(float(params.cooling_rate), 0.05)
    slope_drag = np.clip(1.0 - _normalize(np.hypot(*np.gradient(z))), 0.0, 1.0)
    viscosity_resistance = viscosity * masks["vent"]
    volcanic_construction = params.dt_years * 0.036 * eruption_rate * masks["vent"] * (0.65 + 0.35 * viscosity)
    lava_flow = (
        params.dt_years
        * 0.0075
        * eruption_rate
        * lava_spread
        * (1.05 - viscosity)
        * masks["lava_apron"]
    )
    cooling_limited_spread = lava_flow * slope_drag * np.clip(1.15 - cooling_rate * masks["flank"], 0.05, 1.0)
    flank_erosion = params.dt_years * 0.0022 * eruption_rate * masks["flank"]
    return volcanic_construction, lava_flow, viscosity_resistance, cooling_limited_spread, flank_erosion


def _karst_process(
    z: np.ndarray,
    params: GeomorphicEngineParameters,
    masks: dict[str, np.ndarray],
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    if params.karst <= 0.0 and params.groundwater <= 0.0:
        zero = np.zeros_like(z)
        return zero, zero, zero, zero, zero
    gy, gx = np.gradient(z)
    water_supply = params.groundwater if params.water_supply is None else max(float(params.water_supply), 0.0)
    rock_solubility = max(float(params.rock_solubility), 0.0)
    groundwater_flow = water_supply * masks["groundwater"] * (0.35 + 0.65 * _normalize(np.hypot(gx, gy)))
    solution_rate = params.dt_years * 0.016 * params.karst * rock_solubility * (0.35 + 0.65 * water_supply) * masks["sink"]
    subsurface_drainage = params.dt_years * 0.006 * groundwater_flow
    collapse_risk = _normalize(solution_rate + subsurface_drainage) * masks["sink"]
    sink_fill = params.dt_years * 0.002 * params.sediment * masks["sink"] * np.clip(_grid(z.shape[0])[1] - 0.55, 0.0, 1.0)
    return solution_rate, subsurface_drainage, groundwater_flow, collapse_risk, sink_fill


def _step(z: np.ndarray, params: GeomorphicEngineParameters, masks: dict[str, np.ndarray]) -> tuple[np.ndarray, dict[str, np.ndarray], dict[str, float]]:
    fluvial_erosion, fluvial_deposition, transport, drainage, transport_capacity = _fluvial_process(z, params, masks)
    diffusion = params.dt_years * params.diffusion_d * _laplacian(z) * 0.00068
    tectonic = np.full_like(z, params.uplift_rate * params.dt_years)

    glacial, moraine, ice_thickness, glacial_velocity = _glacial_process(z, params, masks)
    (
        marine,
        wave_cut_platform,
        beach,
        wave_energy,
        shoreline_retreat,
        longshore_transport,
        wave_refraction,
        storm_runup,
        coastal_sediment_budget,
    ) = _marine_process(z, params, masks)
    (
        aeolian,
        dune_erosion,
        dune_deposition,
        wind_vector_x,
        wind_vector_y,
        sand_flux,
        wind_shear_stress,
        sand_availability,
        shelter_factor,
        dune_migration,
    ) = _aeolian_process(z, params, masks)
    volcanic, lava_apron, viscosity_resistance, cooling_limited_spread, flank_erosion = _volcanic_process(z, params, masks)
    karst, groundwater, groundwater_flow, collapse_risk, sink_fill = _karst_process(z, params, masks)

    erosion = fluvial_erosion + glacial + marine + wave_cut_platform + storm_runup + dune_erosion + flank_erosion + karst + groundwater
    deposition = fluvial_deposition + moraine + beach + np.maximum(coastal_sediment_budget, 0.0) + dune_deposition + lava_apron + sink_fill
    construction = volcanic
    new_z = z + tectonic + diffusion + construction - erosion + deposition
    new_z = _fixed_boundaries(new_z, params.base_level)

    fields = _empty_process(z)
    fields.update(
        {
            "erosion": erosion,
            "deposition": deposition,
            "diffusion": diffusion,
            "transport": transport + aeolian,
            "tectonic": tectonic,
            "glacial": glacial,
            "marine": marine,
            "aeolian": aeolian,
            "volcanic": volcanic,
            "karst": karst,
            "groundwater": groundwater,
            "moraine": moraine,
            "wave_energy": wave_energy,
            "shoreline_retreat": shoreline_retreat,
            "wave_cut_platform": wave_cut_platform,
            "beach_deposition": beach,
            "longshore_transport": longshore_transport,
            "wave_refraction": wave_refraction,
            "storm_runup": storm_runup,
            "coastal_sediment_budget": coastal_sediment_budget,
            "wind_vector_x": wind_vector_x,
            "wind_vector_y": wind_vector_y,
            "sand_flux": sand_flux,
            "stoss_erosion": dune_erosion,
            "lee_deposition": dune_deposition,
            "wind_shear_stress": wind_shear_stress,
            "sand_availability": sand_availability,
            "shelter_factor": shelter_factor,
            "dune_migration": dune_migration,
            "volcanic_construction": volcanic,
            "lava_flow": lava_apron,
            "viscosity_resistance": viscosity_resistance,
            "cooling_limited_spread": cooling_limited_spread,
            "groundwater_flow": groundwater_flow,
            "solution_rate": karst,
            "subsurface_drainage": groundwater,
            "collapse_risk": collapse_risk,
            "ice_thickness": ice_thickness,
            "glacial_velocity": glacial_velocity,
            "fluvial_erosion": fluvial_erosion,
            "drainage_area": drainage,
            "transport_capacity": transport_capacity,
            "total_erosion": erosion,
        }
    )
    return new_z, fields, _stats(new_z, params, fields)


def _stats(z: np.ndarray, params: GeomorphicEngineParameters, fields: dict[str, np.ndarray]) -> dict[str, float]:
    dt = max(params.dt_years, 1e-9)
    tectonic = fields.get("tectonic", np.zeros_like(z))
    return {
        "mean_elevation": float(np.mean(z)),
        "max_elevation": float(np.max(z)),
        "mean_erosion_rate": float(np.mean(fields["fluvial_erosion"]) / dt),
        "max_erosion_rate": float(np.max(fields["fluvial_erosion"]) / dt),
        "mean_weathering_rate": 0.0,
        "mean_diffusion": float(np.mean(np.abs(fields["diffusion"])) / dt),
        "mean_deposition_rate": float(np.mean(fields["deposition"]) / dt),
        "mean_lateral_erosion": 0.0,
        "mean_glacial": float(np.mean(fields["glacial"]) / dt),
        "mean_ice_thickness": float(np.mean(fields["ice_thickness"])),
        "max_glacial_velocity": float(np.max(fields["glacial_velocity"])),
        "mean_marine": float(np.mean(fields["marine"]) / dt),
        "mean_landslide": 0.0,
        "mean_faulting": 0.0,
        "mean_folding": 0.0,
        "mean_karst": float(np.mean(fields["karst"]) / dt),
        "mean_aeolian": float(np.mean(fields["aeolian"]) / dt),
        "mean_volcanic": float(np.mean(fields["volcanic"]) / dt),
        "mean_groundwater": float(np.mean(fields["groundwater"]) / dt),
        "mean_freeze_thaw": 0.0,
        "mean_moraine": float(np.mean(fields["moraine"]) / dt),
        "mean_uniform_uplift": max(float(params.uplift_rate), 0.0),
        "mean_subsidence": max(float(-params.uplift_rate), 0.0),
        "mean_soil_depth": float(np.mean(np.maximum(z - params.base_level, 0.0)) * 0.016),
        "total_erosion": float(np.sum(fields["total_erosion"])),
        "total_deposition": float(np.sum(fields["deposition"])),
        "total_fluvial_erosion": float(np.sum(fields["fluvial_erosion"])),
        "total_ice_volume": float(np.sum(fields["ice_thickness"])),
        "total_shoreline_retreat": float(np.sum(fields["shoreline_retreat"])),
        "total_wave_cut_platform": float(np.sum(fields["wave_cut_platform"])),
        "total_longshore_transport": float(np.sum(fields["longshore_transport"])),
        "total_storm_runup": float(np.sum(fields["storm_runup"])),
        "total_coastal_sediment_budget": float(np.sum(fields["coastal_sediment_budget"])),
        "total_sand_flux": float(np.sum(fields["sand_flux"])),
        "total_stoss_erosion": float(np.sum(fields["stoss_erosion"])),
        "total_lee_deposition": float(np.sum(fields["lee_deposition"])),
        "total_wind_shear_stress": float(np.sum(fields["wind_shear_stress"])),
        "total_dune_migration": float(np.sum(fields["dune_migration"])),
        "total_lava_flow": float(np.sum(fields["lava_flow"])),
        "total_volcanic_construction": float(np.sum(fields["volcanic_construction"])),
        "total_solution": float(np.sum(fields["solution_rate"])),
        "total_subsurface_drainage": float(np.sum(fields["subsurface_drainage"])),
        "total_transport_capacity": float(np.sum(fields["transport_capacity"])),
        "total_sediment_flux": float(np.sum(fields["transport"])),
        "total_weathering": 0.0,
        "total_uplift": float(np.sum(np.maximum(tectonic, 0.0))),
        "total_folding": 0.0,
        "total_subsidence": float(np.sum(np.maximum(-tectonic, 0.0))),
    }


@lru_cache(maxsize=96)
def run_geomorphic_engine(params: GeomorphicEngineParameters) -> dict[str, Any]:
    grid_size = int(np.clip(params.grid_size, 24, 96))
    total_time = int(np.clip(params.total_time_years, 2_500, 160_000))
    steps = max(int(total_time / max(params.dt_years, 1e-9)), 1)
    save_every = max(steps // max(params.save_frames - 1, 1), 1)
    z = _initial_surface(params.preset_id, grid_size, params.base_level)
    masks = _process_masks(params.preset_id, grid_size)

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
        "kernel": "geomorphic_engine_v2",
        "parameters": params,
    }
