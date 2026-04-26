from app.services.river_morphology_kernel import RiverKernelParameters, run_river_morphology_model
from app.services.terrain_physics_lab import run_physics_lab_simulation


def test_river_kernel_returns_history_and_process_fields():
    result = run_river_morphology_model(
        RiverKernelParameters(
            landform_id="v_valley",
            grid_size=32,
            total_time_years=5_000,
            save_frames=8,
        )
    )

    assert result["kernel"] == "river_morphology_v1"
    assert len(result["history"]) >= 2
    assert result["history"][-1].shape == (32, 32)
    assert result["stats_history"][-1]["total_erosion"] > 0
    assert "deposition" in result["process_history"][-1]


def test_stronger_stream_power_increases_total_erosion():
    weak = run_river_morphology_model(
        RiverKernelParameters(
            landform_id="v_valley",
            grid_size=32,
            total_time_years=5_000,
            erodibility_k=0.00005,
            water_discharge_scale=0.7,
        )
    )
    strong = run_river_morphology_model(
        RiverKernelParameters(
            landform_id="v_valley",
            grid_size=32,
            total_time_years=5_000,
            erodibility_k=0.00032,
            water_discharge_scale=1.8,
        )
    )

    assert strong["stats_history"][-1]["total_erosion"] > weak["stats_history"][-1]["total_erosion"]


def test_lab_uses_river_kernel_for_river_landforms():
    result = run_physics_lab_simulation("alluvial_fan", 60, 55, 35, 40, 5_000, 32)

    assert result["kernel"] == "river_morphology_v1"
    assert result["dominant_process"]
    assert result["change"]["relief"] > 0
