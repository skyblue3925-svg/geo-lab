import numpy as np

from app.utils.lab_model import build_lab_stage_history


V_VALLEY = "V자곡 (하천침식)"
ALLUVIAL_FAN = "선상지 (급경사)"
FOLDED_RANGE = "습곡 산지 (구조운동)"

CENTER_EROSION = np.array(
    [
        [0.0, 0.6, 0.0],
        [0.1, 1.0, 0.1],
        [0.0, 0.7, 0.0],
    ]
)

FAN_DEPOSITION = np.array(
    [
        [0.0, 0.0, 0.0, 0.0],
        [0.1, 0.3, 0.3, 0.1],
        [0.2, 0.8, 0.8, 0.2],
        [0.2, 0.7, 0.7, 0.2],
    ]
)

FOLDING_BANDS = np.array(
    [
        [0.1, 0.1, 0.1, 0.1],
        [0.8, 0.8, 0.8, 0.8],
        [0.2, 0.2, 0.2, 0.2],
        [0.9, 0.9, 0.9, 0.9],
    ]
)

FOCUSED_EROSION_4 = np.array(
    [
        [0.0, 0.6, 0.6, 0.0],
        [0.1, 0.9, 0.9, 0.1],
        [0.1, 0.9, 0.9, 0.1],
        [0.0, 0.6, 0.6, 0.0],
    ]
)


def test_build_lab_stage_history_classifies_v_valley_by_process_thresholds():
    stage_history = build_lab_stage_history(
        V_VALLEY,
        stats_history=[
            {"mean_uniform_uplift": 0.5, "mean_erosion_rate": 0.1},
            {"mean_erosion_rate": 0.6, "mean_lateral_erosion": 0.1, "mean_diffusion": 0.15},
            {"mean_erosion_rate": 0.25, "mean_diffusion": 0.25, "mean_landslide": 0.2, "mean_weathering_rate": 0.1},
            {"mean_erosion_rate": 0.1, "mean_diffusion": 0.08, "mean_weathering_rate": 0.05},
        ],
        process_history=[
            {"tectonic": np.ones((3, 3)) * 0.3, "total_erosion": np.zeros((3, 3)), "deposition": np.zeros((3, 3))},
            {"tectonic": np.ones((3, 3)) * 0.2, "total_erosion": CENTER_EROSION, "deposition": np.zeros((3, 3))},
            {"tectonic": np.ones((3, 3)) * 0.1, "total_erosion": CENTER_EROSION * 0.8, "deposition": np.zeros((3, 3))},
            {"tectonic": np.ones((3, 3)) * 0.05, "total_erosion": CENTER_EROSION * 0.4, "deposition": np.zeros((3, 3))},
        ],
    )

    assert [item["stage_index"] for item in stage_history] == [0, 1, 2, 3]
    assert [item["overlay_type"] for item in stage_history] == ["tectonic", "erosion", "change", "change"]


def test_build_lab_stage_history_classifies_alluvial_fan_by_transport_then_deposition():
    stage_history = build_lab_stage_history(
        ALLUVIAL_FAN,
        stats_history=[
            {"mean_faulting": 0.4, "mean_landslide": 0.25, "mean_weathering_rate": 0.2},
            {"mean_erosion_rate": 0.45, "mean_lateral_erosion": 0.2, "mean_diffusion": 0.18, "mean_deposition_rate": 0.1},
            {"mean_deposition_rate": 0.6, "mean_diffusion": 0.12, "mean_erosion_rate": 0.25},
            {"mean_deposition_rate": 0.2, "mean_erosion_rate": 0.08, "mean_diffusion": 0.07},
        ],
        process_history=[
            {"tectonic": np.ones((4, 4)) * 0.4, "deposition": np.zeros((4, 4)), "total_erosion": np.zeros((4, 4))},
            {"tectonic": np.ones((4, 4)) * 0.25, "deposition": np.zeros((4, 4)), "total_erosion": np.ones((4, 4)) * 0.3},
            {"tectonic": np.ones((4, 4)) * 0.1, "deposition": FAN_DEPOSITION, "total_erosion": np.ones((4, 4)) * 0.15},
            {"tectonic": np.ones((4, 4)) * 0.05, "deposition": FAN_DEPOSITION * 0.4, "total_erosion": np.ones((4, 4)) * 0.05},
        ],
    )

    assert [item["stage_index"] for item in stage_history] == [0, 1, 2, 3]
    assert [item["overlay_type"] for item in stage_history] == ["change", "transport", "deposition", "change"]


def test_build_lab_stage_history_classifies_folded_range_by_tectonic_then_erosion():
    stage_history = build_lab_stage_history(
        FOLDED_RANGE,
        stats_history=[
            {"mean_folding": 0.6, "mean_uniform_uplift": 0.2},
            {"mean_folding": 0.45, "mean_erosion_rate": 0.18, "mean_weathering_rate": 0.08},
            {"mean_folding": 0.2, "mean_erosion_rate": 0.32, "mean_diffusion": 0.16, "mean_weathering_rate": 0.1},
            {"mean_folding": 0.05, "mean_erosion_rate": 0.1, "mean_diffusion": 0.08, "mean_weathering_rate": 0.04},
        ],
        process_history=[
            {"tectonic": FOLDING_BANDS, "folding": FOLDING_BANDS, "total_erosion": np.zeros((4, 4)), "deposition": np.zeros((4, 4))},
            {"tectonic": FOLDING_BANDS * 0.9, "folding": FOLDING_BANDS * 0.9, "total_erosion": FOCUSED_EROSION_4 * 0.4, "deposition": np.zeros((4, 4))},
            {"tectonic": FOLDING_BANDS * 0.6, "folding": FOLDING_BANDS * 0.6, "total_erosion": FOCUSED_EROSION_4 * 0.7, "deposition": np.zeros((4, 4))},
            {"tectonic": FOLDING_BANDS * 0.2, "folding": FOLDING_BANDS * 0.2, "total_erosion": FOCUSED_EROSION_4 * 0.1, "deposition": np.zeros((4, 4))},
        ],
    )

    assert [item["stage_index"] for item in stage_history] == [0, 1, 2, 3]
    assert [item["overlay_type"] for item in stage_history] == ["tectonic", "tectonic", "erosion", "change"]


def test_build_lab_stage_history_requires_sustained_signal_before_advancing():
    stage_history = build_lab_stage_history(
        V_VALLEY,
        stats_history=[
            {"mean_uniform_uplift": 0.5, "mean_erosion_rate": 0.1},
            {"mean_erosion_rate": 0.6, "mean_lateral_erosion": 0.1, "mean_diffusion": 0.15},
            {"mean_erosion_rate": 0.62, "mean_lateral_erosion": 0.1, "mean_diffusion": 0.15},
            {"mean_erosion_rate": 0.25, "mean_diffusion": 0.27, "mean_landslide": 0.2, "mean_weathering_rate": 0.1},
            {"mean_erosion_rate": 0.24, "mean_diffusion": 0.28, "mean_landslide": 0.2, "mean_weathering_rate": 0.1},
            {"mean_erosion_rate": 0.08, "mean_diffusion": 0.04, "mean_weathering_rate": 0.03},
            {"mean_erosion_rate": 0.07, "mean_diffusion": 0.04, "mean_weathering_rate": 0.03},
        ],
        process_history=[
            {"tectonic": np.ones((3, 3)) * 0.3, "total_erosion": np.zeros((3, 3)), "deposition": np.zeros((3, 3))},
            {"tectonic": np.ones((3, 3)) * 0.2, "total_erosion": CENTER_EROSION, "deposition": np.zeros((3, 3))},
            {"tectonic": np.ones((3, 3)) * 0.15, "total_erosion": CENTER_EROSION, "deposition": np.zeros((3, 3))},
            {"tectonic": np.ones((3, 3)) * 0.12, "total_erosion": CENTER_EROSION * 0.8, "deposition": np.zeros((3, 3))},
            {"tectonic": np.ones((3, 3)) * 0.1, "total_erosion": CENTER_EROSION * 0.8, "deposition": np.zeros((3, 3))},
            {"tectonic": np.ones((3, 3)) * 0.05, "total_erosion": CENTER_EROSION * 0.25, "deposition": np.zeros((3, 3))},
            {"tectonic": np.ones((3, 3)) * 0.05, "total_erosion": CENTER_EROSION * 0.2, "deposition": np.zeros((3, 3))},
        ],
    )

    assert [item["stage_index"] for item in stage_history] == [0, 0, 1, 1, 2, 2, 3]


def test_build_lab_stage_history_keeps_alluvial_fan_in_transport_without_outlet_deposition():
    stage_history = build_lab_stage_history(
        ALLUVIAL_FAN,
        stats_history=[
            {"mean_faulting": 0.4, "mean_landslide": 0.25, "mean_weathering_rate": 0.2},
            {"mean_erosion_rate": 0.45, "mean_lateral_erosion": 0.2, "mean_diffusion": 0.18, "mean_deposition_rate": 0.1},
            {"mean_deposition_rate": 0.7, "mean_diffusion": 0.12, "mean_erosion_rate": 0.25},
            {"mean_deposition_rate": 0.18, "mean_erosion_rate": 0.08, "mean_diffusion": 0.07},
        ],
        process_history=[
            {"tectonic": np.ones((4, 4)) * 0.4, "deposition": np.zeros((4, 4)), "total_erosion": np.zeros((4, 4))},
            {"tectonic": np.ones((4, 4)) * 0.25, "deposition": np.zeros((4, 4)), "total_erosion": np.ones((4, 4)) * 0.3},
            {"tectonic": np.ones((4, 4)) * 0.1, "deposition": np.flipud(FAN_DEPOSITION), "total_erosion": np.ones((4, 4)) * 0.15},
            {"tectonic": np.ones((4, 4)) * 0.05, "deposition": np.flipud(FAN_DEPOSITION) * 0.3, "total_erosion": np.ones((4, 4)) * 0.05},
        ],
    )

    assert [item["stage_index"] for item in stage_history] == [0, 1, 1, 1]
