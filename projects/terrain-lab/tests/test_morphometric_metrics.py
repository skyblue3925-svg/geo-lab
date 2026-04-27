from app.services.morphometric_metrics import (
    metric_cards,
    normalize_process_field,
    process_field_cards,
    process_field_options,
    validation_cards,
)
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
        "coastal_cliff": ("shoreline_gradient_index", "shoreline_process_focus", "wave_cut_efficiency"),
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


def test_coastal_metrics_expose_longshore_budget_and_refraction():
    for landform_id in ["coastal_cliff", "wave_cut_platform", "spit_lagoon", "tombolo", "marine_terrace"]:
        result = run_physics_lab_simulation(landform_id, 66, 62, 35, 35, 5_000, 32)
        metrics = result["metrics"]

        assert metrics["wave_refraction_focus"] >= 0.0
        assert metrics["longshore_transport_ratio"] > 0.0
        assert metrics["wave_cut_efficiency"] >= 0.0
        assert "해안" in metrics["diagnosis"] or "파랑" in metrics["diagnosis"] or "표사" in metrics["diagnosis"]

        labels = [card[0] for card in validation_cards(landform_id, metrics)]
        assert "표사 이동 비율" in labels
        assert "파식 효율" in labels


def test_volcanic_metrics_distinguish_lava_and_explosive_processes():
    for landform_id in ["lava_dome", "shield_volcano", "stratovolcano", "lava_plateau", "maar", "cinder_cone"]:
        result = run_physics_lab_simulation(landform_id, 66, 62, 35, 35, 5_000, 32)
        metrics = result["metrics"]

        assert metrics["lava_spread_efficiency"] >= 0.0
        assert metrics["viscosity_constraint_index"] >= 0.0
        assert metrics["explosive_excavation_ratio"] >= 0.0
        assert "화산" in metrics["diagnosis"] or "용암" in metrics["diagnosis"] or "분출" in metrics["diagnosis"]

        labels = [card[0] for card in validation_cards(landform_id, metrics)]
        assert "용암 확산 효율" in labels
        assert "점성 제약" in labels


def test_karst_metrics_expose_groundwater_drainage_and_collapse():
    for landform_id in ["karst_doline", "uvala", "polje", "karren", "tower_karst"]:
        result = run_physics_lab_simulation(landform_id, 66, 62, 35, 35, 5_000, 32)
        metrics = result["metrics"]

        assert metrics["groundwater_concentration_index"] >= 0.0
        assert metrics["subsurface_drainage_ratio"] >= 0.0
        assert metrics["collapse_risk_index"] >= 0.0
        assert "카르스트" in metrics["diagnosis"] or "용식" in metrics["diagnosis"] or "지하수" in metrics["diagnosis"]

        labels = [card[0] for card in validation_cards(landform_id, metrics)]
        assert "지하수 집중" in labels
        assert "붕괴 위험" in labels


def test_glacial_metrics_expose_ice_velocity_and_moraine_balance():
    for landform_id in ["u_valley", "moraine", "drumlin", "esker", "kettle_lake", "outwash_plain", "thermokarst"]:
        result = run_physics_lab_simulation(landform_id, 66, 62, 35, 35, 5_000, 32)
        metrics = result["metrics"]

        assert metrics["ice_accumulation_focus"] >= 0.0
        assert metrics["glacial_velocity_index"] >= 0.0
        assert metrics["moraine_deposition_ratio"] >= 0.0
        assert metrics["glacial_erosion_efficiency"] >= 0.0
        assert "빙하" in metrics["diagnosis"] or "모레인" in metrics["diagnosis"] or "융빙수" in metrics["diagnosis"]

        labels = [card[0] for card in validation_cards(landform_id, metrics)]
        assert "빙하 두께 집중" in labels
        assert "모레인 퇴적 비율" in labels


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


def test_process_field_options_and_normalized_overlay_support_lab_heatmap():
    result = run_physics_lab_simulation("coastal_cliff", 60, 55, 35, 35, 5_000, 32)
    fields = result["process_history"][-1]
    options = process_field_options(fields)

    assert ("wave_energy", "파랑 에너지") in options

    overlay = normalize_process_field(fields, "wave_energy")
    assert overlay.shape == result["history"][-1].shape
    assert float(overlay.max()) <= 1.0
    assert float(overlay.min()) >= 0.0
    assert float(overlay.max()) > 0.0
