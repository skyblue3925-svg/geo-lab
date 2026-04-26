from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
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


SCENARIOS: tuple[PhysicsLabScenario, ...] = (
    PhysicsLabScenario("v_valley", "V자곡", "하천 지형", "V자곡", "하천 침식력", "강수량", 60, 45, 25, 45_000),
    PhysicsLabScenario("alluvial_fan", "선상지", "하천 지형", "선상지", "퇴적물 공급", "경사 완화", 55, 35, 40, 35_000),
    PhysicsLabScenario("delta", "삼각주", "하구·삼각주", "삼각주", "퇴적물 공급", "해수면 안정성", 50, 20, 35, 35_000),
    PhysicsLabScenario("u_valley", "U자곡", "빙하 지형", "U자곡", "빙하 침식력", "빙하 두께", 65, 25, 20, 55_000),
    PhysicsLabScenario("coastal_cliff", "해식애", "해안 지형", "해식애", "파랑 에너지", "해수면 위치", 60, 20, 30, 40_000),
    PhysicsLabScenario("barchan", "바르한", "건조 지형", "바르한", "풍속", "모래 공급", 58, 10, 25, 30_000),
    PhysicsLabScenario("lava_dome", "용암돔", "화산 지형", "용암돔", "분출률", "점성/확산", 62, 35, 28, 28_000),
    PhysicsLabScenario("karst_doline", "돌리네", "카르스트 지형", "카르스트 돌리네", "용식 강도", "지하수 흐름", 52, 5, 22, 45_000),
)


def list_physics_lab_scenarios() -> tuple[PhysicsLabScenario, ...]:
    return SCENARIOS


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
        "dominant_process": format_process_summary(stats_history[-1] if stats_history else None),
        "kernel": raw["kernel"],
        "kernel_notes": (
            "Stream Power Law(E=K A^m S^n), 사면 확산, 퇴적물 운반/퇴적, "
            "기저면 조건을 결합한 하천 지형 커널 v1입니다."
        ),
    }


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
    if scenario.landform_id in {"v_valley", "alluvial_fan", "delta"}:
        return _run_river_kernel_scenario(
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

    return {
        "scenario": scenario,
        "config": config,
        "history": [_normalize_surface(frame) for frame in history],
        "times": list(times),
        "stats_history": list(lem.stats_history),
        "process_history": list(lem.process_history),
        "stage_history": stage_history,
        "final_stage": final_stage,
        "change": _change_summary(history[0], history[-1]),
        "dominant_process": format_process_summary(lem.stats_history[-1] if lem.stats_history else None),
        "kernel": "simple_lem",
        "kernel_notes": "기존 SimpleLEM 기반 실험 경로입니다. 계열별 전용 커널로 순차 교체할 예정입니다.",
    }
