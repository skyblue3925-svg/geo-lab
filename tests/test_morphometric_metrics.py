from app.services.morphometric_metrics import metric_cards
from app.services.terrain_physics_lab import run_physics_lab_simulation


def test_lab_results_include_metrics_and_diagnosis():
    result = run_physics_lab_simulation("v_valley", 70, 55, 45, 25, 5_000, 32)
    metrics = result["metrics"]

    assert metrics["relief"] > 0
    assert metrics["active_area_ratio"] > 0
    assert "V자곡" in metrics["diagnosis"] or "계곡" in metrics["diagnosis"]
    assert len(metric_cards(metrics)) == 4


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
