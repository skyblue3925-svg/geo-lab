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
    assert "drainage_area" in result["process_history"][-1]
    assert "transport_capacity" in result["process_history"][-1]
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


def test_fluvial_area_responds_to_dem_and_deposition_is_flux_limited():
    result = run_geomorphic_engine(
        GeomorphicEngineParameters(
            preset_id="v_valley",
            grid_size=32,
            total_time_years=5_000,
            save_frames=8,
            fluvial=1.6,
            sediment=1.2,
            uplift_rate=0.0002,
            diffusion_d=0.016,
        )
    )
    fields = result["process_history"][-1]
    drainage = fields["drainage_area"]
    deposition = fields["deposition"]
    transport = fields["transport"]

    assert float(drainage.max()) > float(drainage.mean())
    assert float(drainage[-6:, :].mean()) > float(drainage[:6, :].mean())
    assert float(deposition.sum()) <= float(transport.sum()) + 1e-9


def test_glacial_process_uses_ice_thickness_and_velocity_fields():
    result = run_geomorphic_engine(
        GeomorphicEngineParameters(
            preset_id="u_valley",
            grid_size=32,
            total_time_years=5_000,
            save_frames=8,
            glacial=1.7,
            sediment=0.8,
            diffusion_d=0.014,
        )
    )
    fields = result["process_history"][-1]
    stats = result["stats_history"][-1]

    assert "ice_thickness" in fields
    assert "glacial_velocity" in fields
    assert float(fields["ice_thickness"].max()) > float(fields["ice_thickness"].mean())
    assert float(fields["glacial_velocity"].max()) > 0
    assert stats["total_ice_volume"] > 0
    assert stats["max_glacial_velocity"] > 0
    assert stats["mean_glacial"] > 0


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
