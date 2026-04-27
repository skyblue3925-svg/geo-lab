import numpy as np
import pytest

from engine.simple_lem import SimpleLEM


def test_run_persists_process_stats_history_for_saved_frames():
    lem = SimpleLEM(
        grid_size=24,
        cell_size=50.0,
        K=0.0002,
        D=0.01,
        U=-0.0002,
        enable_sediment_transport=True,
        enable_lateral_erosion=True,
        enable_glacial=True,
        enable_marine=True,
        enable_landslides=True,
        enable_faulting=True,
        enable_karst=True,
        enable_aeolian=True,
        enable_volcanic=True,
        enable_groundwater=True,
        enable_freeze_thaw=True,
        enable_glacial_deposit=True,
    )
    lem.glacier_ela = 10.0
    lem.sea_level = 5.0
    lem.freeze_elevation = 8.0
    lem.water_table = 15.0
    lem.create_initial_mountain(peak_height=40.0, noise_amp=0.5, initial_soil=1.0)

    history, times = lem.run(total_time=300.0, dt=100.0, save_interval=1, verbose=False)

    assert len(history) == len(times)
    assert len(lem.stats_history) == len(history)
    assert len(lem.process_history) == len(history)

    sample = lem.stats_history[1]
    process_sample = lem.process_history[1]
    assert sample["mean_subsidence"] == pytest.approx(0.0002)
    assert sample["mean_faulting"] > 0.0
    assert sample["mean_diffusion"] >= 0.0
    assert sample["mean_karst"] >= 0.0
    assert sample["mean_aeolian"] >= 0.0
    assert sample["mean_volcanic"] >= 0.0
    assert sample["mean_groundwater"] >= 0.0
    assert sample["mean_freeze_thaw"] >= 0.0
    assert "total_subsidence" in sample
    assert process_sample["tectonic"].shape == history[0].shape
    assert process_sample["erosion"].shape == history[0].shape
    assert process_sample["deposition"].shape == history[0].shape
    assert process_sample["total_erosion"].shape == history[0].shape
    assert float(process_sample["tectonic"].sum()) != 0.0
    assert float(np.abs(process_sample["total_erosion"]).sum()) > 0.0


def test_step_reports_folding_when_structural_uplift_is_enabled():
    lem = SimpleLEM(
        grid_size=24,
        cell_size=50.0,
        K=0.0002,
        D=0.01,
        U=0.0,
    )
    lem.enable_folding = True
    lem.fold_rate = 0.0005
    lem.fold_wavelength = 0.25
    lem.create_initial_mountain(peak_height=30.0, noise_amp=0.2, initial_soil=1.0)

    stats = lem.step(dt=100.0)

    assert stats["mean_folding"] > 0.0
    assert stats["total_folding"] > 0.0
    assert lem.last_process_fields["folding"].shape == lem.elevation.shape
    assert float(np.abs(lem.last_process_fields["folding"]).sum()) > 0.0
