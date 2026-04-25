import numpy as np
import pytest

from app.utils.lab_model import (
    LAB_THEORY_EXAMPLE_TEXT,
    apply_lab_theory_example,
    configure_lab_scenario,
    create_lab_simple_lem,
    describe_lab_process_stage,
    get_lab_scenario_config,
    get_lab_teaching_notes,
    summarize_process_stats,
)
from engine.ideal_landforms import IDEAL_LANDFORM_GENERATORS


ALLUVIAL_FAN = "선상지"
DELTA = "삼각주"
MEANDER = "곡류"
COASTAL_CLIFF = "해식애"
BARCHAN = "바르한"
VOLCANO = "화산"
PLAIN = "평원"
FOLDED_RANGE = "습곡 산지 (구조운동)"


def build_test_lem():
    return create_lab_simple_lem(
        grid_size=32,
        K=0.001,
        D=0.01,
        U=0.0001,
        enable_isostasy=False,
        enable_karst=False,
        enable_exner=False,
        enable_slope_stability=False,
    )


def test_create_lab_simple_lem_maps_legacy_flags_to_supported_engine_flags():
    lem = create_lab_simple_lem(
        grid_size=32,
        K=0.001,
        D=0.01,
        U=0.0001,
        enable_isostasy=True,
        enable_karst=True,
        enable_exner=True,
        enable_slope_stability=True,
    )

    assert lem.enable_flexure is True
    assert lem.enable_karst is True
    assert lem.enable_landslides is True
    assert lem.enable_isostasy is True
    assert lem.enable_exner is True
    assert lem.enable_slope_stability is True


def test_apply_lab_theory_example_updates_session_state():
    state = {}

    apply_lab_theory_example(state)

    assert state["lab_theory_text"] == LAB_THEORY_EXAMPLE_TEXT


@pytest.mark.parametrize(
    ("selected_landform", "expected_generator", "expected_landform_type", "expected_detailed_type"),
    [
        (ALLUVIAL_FAN, "alluvial_fan", "river", "alluvial_fan"),
        (MEANDER, "meander", "river", "meander"),
        (COASTAL_CLIFF, "coastal_cliff", "coastal", "coastal_cliff"),
        (BARCHAN, "barchan", "arid", "barchan"),
        (VOLCANO, "stratovolcano", "volcanic", "stratovolcano"),
    ],
)
def test_get_lab_scenario_config_maps_named_landforms(
    selected_landform,
    expected_generator,
    expected_landform_type,
    expected_detailed_type,
):
    config = get_lab_scenario_config(selected_landform)

    assert config.generator_key == expected_generator
    assert config.landform_type == expected_landform_type
    assert config.detailed_type == expected_detailed_type


def test_configure_lab_scenario_uses_alluvial_fan_surface_and_process_flags():
    lem = build_test_lem()

    config = configure_lab_scenario(
        lem,
        selected_landform=ALLUVIAL_FAN,
        grid_size=32,
    )

    expected = IDEAL_LANDFORM_GENERATORS["alluvial_fan"](32)

    assert config.detailed_type == "alluvial_fan"
    assert np.allclose(lem.elevation, expected)
    assert lem.enable_sediment_transport is True
    assert lem.enable_lateral_erosion is True
    assert lem.K == pytest.approx(0.001 * 0.2)
    assert lem.U == pytest.approx(0.0001 * 0.1)
    assert lem.Vs == pytest.approx(2.5)


def test_get_lab_scenario_config_marks_plain_as_custom_surface():
    config = get_lab_scenario_config(PLAIN)

    assert config.custom_surface == "fluvial_plain"
    assert config.generator_key is None
    assert config.enable_sediment_transport is True


def test_get_lab_teaching_notes_returns_landform_specific_prompts():
    notes = get_lab_teaching_notes(ALLUVIAL_FAN)

    assert "선상지" in notes["concept"]
    assert "에너지 감소" in notes["takeaway"]
    assert "퇴적" in notes["question"]


def test_get_lab_teaching_notes_uses_high_school_world_case_metadata():
    notes = get_lab_teaching_notes(DELTA)

    assert "하구" in notes["concept"]
    assert "새로운 땅" in notes["question"]
    assert notes["world_case"] == "나일 삼각주"


def test_get_lab_scenario_config_exposes_internal_and_external_process_flags():
    fan = get_lab_scenario_config(ALLUVIAL_FAN)
    delta = get_lab_scenario_config("삼각주")
    karst = get_lab_scenario_config("카르스트")
    folded = get_lab_scenario_config(FOLDED_RANGE)

    assert fan.enable_faulting is True
    assert fan.enable_landslides is True
    assert fan.fault_rate == pytest.approx(0.00035)
    assert delta.u_scale < 0
    assert karst.enable_groundwater is True
    assert karst.water_table == pytest.approx(30.0)
    assert folded.enable_folding is True
    assert folded.fold_rate == pytest.approx(0.00045)
    assert folded.custom_surface == "folded_range"


def test_summarize_process_stats_returns_ranked_grouped_processes():
    dominant = summarize_process_stats(
        {
            "mean_deposition_rate": 0.5,
            "mean_faulting": 0.2,
            "mean_erosion_rate": 0.3,
            "mean_subsidence": 0.1,
        },
        top_n=3,
    )

    assert [item["label"] for item in dominant] == ["퇴적", "하천 침식", "단층 운동"]
    assert [item["group"] for item in dominant] == ["외적", "외적", "내적"]


def test_describe_lab_process_stage_uses_landform_specific_story_and_dominant_processes():
    stage = describe_lab_process_stage(
        ALLUVIAL_FAN,
        progress=0.55,
        stats={
            "mean_deposition_rate": 0.4,
            "mean_faulting": 0.2,
            "mean_landslide": 0.1,
        },
    )

    assert "출구" in stage["title"] or "선상지" in stage["summary"]
    assert "공급" in stage["process_order"] or "퇴적" in stage["process_order"]
    assert "퇴적" in stage["dominant_summary"]
    assert "외적 작용" in stage["balance_summary"]


def test_describe_lab_process_stage_uses_high_school_standard_for_delta():
    stage = describe_lab_process_stage(
        DELTA,
        progress=0.55,
        stats={
            "mean_deposition_rate": 0.45,
            "mean_erosion_rate": 0.2,
            "mean_lateral_erosion": 0.08,
        },
    )

    assert stage["title"] == "수로 분기"
    assert stage["overlay_type"] == "transport"
    assert stage["world_case_title"] == "나일 삼각주"
    assert "하구" in stage["classroom_goal"]
