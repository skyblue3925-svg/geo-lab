from app.services.morphometric_metrics import metric_cards, validation_cards
from app.services.terrain_physics_lab import run_physics_lab_simulation


def test_lab_results_include_metrics_and_diagnosis():
    result = run_physics_lab_simulation("v_valley", 70, 55, 45, 25, 5_000, 32)
    metrics = result["metrics"]

    assert metrics["relief"] > 0
    assert metrics["active_area_ratio"] > 0
    assert "V자곡" in metrics["diagnosis"] or "계곡" in metrics["diagnosis"]
    assert len(metric_cards(metrics)) == 4
    assert len(validation_cards("v_valley", metrics)) >= 4


def test_each_representative_landform_has_nonempty_metric_diagnosis():
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
        metrics = result["metrics"]

        assert metrics["diagnosis"]
        assert metrics["relief"] > 0
        assert validation_cards(landform_id, metrics)


def test_landform_specific_validation_metrics_are_present():
    expected_keys = {
        "v_valley": ("valley_depth_index", "centerline_process_focus"),
        "alluvial_fan": ("fan_lateral_spread_index", "downstream_deposition_focus"),
        "delta": ("delta_front_spread_index", "deposition_erosion_ratio"),
        "u_valley": ("u_floor_width_index", "centerline_process_focus"),
        "coastal_cliff": ("shoreline_gradient_index", "shoreline_process_focus"),
        "barchan": ("dune_migration_index", "dune_transport_focus"),
        "lava_dome": ("dome_symmetry_index", "volcanic_core_focus"),
        "karst_doline": ("closed_depression_index", "karst_sink_focus"),
    }

    for landform_id, keys in expected_keys.items():
        result = run_physics_lab_simulation(landform_id, 60, 55, 35, 35, 5_000, 32)
        metrics = result["metrics"]

        for key in keys:
            assert key in metrics
            assert float(metrics[key]) >= 0.0
