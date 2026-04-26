from app.services.morphometric_metrics import metric_cards, process_field_cards, validation_cards
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


def test_process_field_cards_expose_active_engine_fields_for_lab_ui():
    expectations = {
        "coastal_cliff": "파랑 에너지",
        "barchan": "모래 이동량",
        "lava_dome": "용암 흐름",
        "karst_doline": "용식률",
        "u_valley": "빙하 두께",
    }

    for landform_id, expected_label in expectations.items():
        result = run_physics_lab_simulation(landform_id, 60, 55, 35, 35, 5_000, 32)
        cards = process_field_cards(result["process_history"][-1])

        assert any(card[0] == expected_label for card in cards)
        assert all(float(card[1]) >= 0.0 for card in cards)


def test_process_field_cards_do_not_show_fluvial_area_for_non_fluvial_presets():
    for landform_id in ["barchan", "lava_dome", "karst_doline", "u_valley"]:
        result = run_physics_lab_simulation(landform_id, 60, 55, 35, 35, 5_000, 32)
        labels = [card[0] for card in process_field_cards(result["process_history"][-1])]

        assert "집수면적" not in labels
