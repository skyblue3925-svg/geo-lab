import pytest

from app.utils.lab_model import (
    describe_lab_process_stage,
    get_lab_scenario_config,
    get_lab_teaching_notes,
)


FOLDED_RANGE = "습곡 산지 (구조운동)"


def test_folded_range_scenario_enables_folding_and_custom_surface():
    config = get_lab_scenario_config(FOLDED_RANGE)

    assert config.detailed_type == "folded_range"
    assert config.custom_surface == "folded_range"
    assert config.enable_folding is True
    assert config.fold_rate == pytest.approx(0.00045)
    assert config.fold_wavelength == pytest.approx(0.22)


def test_folded_range_stage_description_surfaces_folding_process():
    stage = describe_lab_process_stage(
        FOLDED_RANGE,
        progress=0.1,
        stats={
            "mean_folding": 0.3,
            "mean_weathering_rate": 0.1,
        },
    )

    assert "습곡" in stage["title"] or "습곡" in stage["summary"]
    assert "습곡" in stage["process_order"]
    assert "습곡" in stage["dominant_summary"]
    assert "내적 작용" in stage["balance_summary"]


def test_folded_range_teaching_notes_explain_internal_vs_external_roles():
    notes = get_lab_teaching_notes(FOLDED_RANGE)

    assert "습곡" in notes["concept"]
    assert "내적 작용" in notes["takeaway"]
