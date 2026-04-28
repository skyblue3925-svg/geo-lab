from app.services.geomorphic_process_kernels import (
    ProcessKernelParameters,
    run_process_morphology_model,
)
from app.services.terrain_physics_lab import run_physics_lab_simulation


def test_process_kernels_return_shared_output_contract():
    for landform_id in ["u_valley", "coastal_cliff", "barchan", "lava_dome", "karst_doline"]:
        result = run_process_morphology_model(
            ProcessKernelParameters(
                landform_id=landform_id,
                grid_size=32,
                total_time_years=5_000,
                save_frames=8,
            )
        )

        assert result["kernel"] == f"{landform_id}_process_v1"
        assert len(result["history"]) >= 2
        assert result["history"][-1].shape == (32, 32)
        assert "total_erosion" in result["process_history"][-1]
        assert "total_deposition" in result["stats_history"][-1]


def test_process_kernels_have_expected_dominant_activity():
    expectations = {
        "u_valley": "mean_glacial",
        "coastal_cliff": "mean_marine",
        "barchan": "mean_aeolian",
        "lava_dome": "mean_volcanic",
        "karst_doline": "mean_karst",
    }

    for landform_id, expected_key in expectations.items():
        result = run_process_morphology_model(
            ProcessKernelParameters(
                landform_id=landform_id,
                grid_size=32,
                total_time_years=5_000,
                force_scale=1.6,
                secondary_scale=1.2,
            )
        )
        final_stats = result["stats_history"][-1]

        assert final_stats[expected_key] > 0


def test_lab_uses_process_kernels_for_non_river_representatives():
    for landform_id in ["u_valley", "coastal_cliff", "barchan", "lava_dome", "karst_doline"]:
        result = run_physics_lab_simulation(landform_id, 60, 55, 35, 35, 5_000, 32)

        assert result["kernel"] == "geomorphic_engine_v2"
        assert result["dominant_process"]
        assert result["change"]["relief"] > 0
