from app.services.geomorphic_engine import GeomorphicEngineParameters, run_geomorphic_engine
from app.services.terrain_physics_lab import run_physics_lab_simulation


def test_common_engine_returns_shared_contract():
    result = run_geomorphic_engine(
        GeomorphicEngineParameters(
            preset_id="v_valley",
            grid_size=32,
            total_time_years=5_000,
            save_frames=8,
            fluvial=1.2,
            sediment=0.5,
            uplift_rate=0.00012,
            diffusion_d=0.02,
        )
    )

    assert result["kernel"] == "geomorphic_engine_v2"
    assert len(result["history"]) >= 2
    assert result["history"][-1].shape == (32, 32)
    assert "total_erosion" in result["process_history"][-1]
    assert "mean_erosion_rate" in result["stats_history"][-1]


def test_common_engine_combines_internal_and_external_processes():
    result = run_geomorphic_engine(
        GeomorphicEngineParameters(
            preset_id="lava_dome",
            grid_size=32,
            total_time_years=5_000,
            save_frames=8,
            volcanic=1.4,
            marine=0.4,
            diffusion_d=0.025,
            uplift_rate=0.0001,
        )
    )
    stats = result["stats_history"][-1]

    assert stats["mean_volcanic"] > 0
    assert stats["mean_marine"] > 0
    assert stats["mean_diffusion"] > 0
    assert stats["mean_uniform_uplift"] > 0


def test_lab_routes_representative_landforms_to_common_engine_v2():
    for landform_id in [
        "v_valley",
        "alluvial_fan",
        "delta",
        "u_valley",
        "coastal_cliff",
        "barchan",
        "lava_dome",
        "karst_doline",
    ]:
        result = run_physics_lab_simulation(landform_id, 60, 55, 35, 35, 5_000, 32)

        assert result["kernel"] == "geomorphic_engine_v2"
        assert result["dominant_process"]
        assert result["change"]["relief"] > 0
