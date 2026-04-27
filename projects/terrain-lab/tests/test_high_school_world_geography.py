import numpy as np

from app.utils.high_school_world_geography import (
    build_high_school_process_fields,
    get_high_school_world_group,
    get_high_school_world_groups,
    get_high_school_world_topic,
    get_high_school_world_topics,
)


def test_high_school_world_groups_cover_core_curriculum_units():
    groups = get_high_school_world_groups()
    group_ids = {group["group_id"] for group in groups}

    assert {"river", "delta", "glacial", "volcanic", "karst", "arid", "coastal"} <= group_ids


def test_high_school_world_topics_cover_grouped_atlas_not_reduced_subset():
    topics = get_high_school_world_topics()
    topic_ids = {topic["topic_id"] for topic in topics}

    assert len(topics) >= 35
    assert {
        "v_valley",
        "alluvial_fan",
        "delta",
        "free_meander",
        "fjord",
        "tower_karst",
        "coastal_cliff",
        "shield_volcano",
        "barchan",
        "spit_lagoon",
    } <= topic_ids


def test_group_filter_returns_only_requested_curriculum_unit():
    river_group = get_high_school_world_group("river")
    river_topics = get_high_school_world_topics("river")

    assert river_group is not None
    assert river_group["default_topic_id"] == "v_valley"
    assert river_topics
    assert all(topic["group_id"] == "river" for topic in river_topics)


def test_high_school_world_topic_includes_world_case_stage_and_camera_standard():
    topic = get_high_school_world_topic("alluvial_fan")

    assert topic is not None
    assert topic["title"] == "선상지"
    assert topic["world_case"]["case_id"] == "death_valley_alluvial_fan"
    assert "산지 출구" in topic["classroom_goal"]
    assert topic["primary_overlay"] == "deposition"
    assert topic["camera_profile"] == "planform_front"
    assert topic["recommended_view"] == "정면 평면도"
    assert len(topic["stages"]) == 4
    assert topic["stages"][0]["title"] == "산지 공급"


def test_build_high_school_process_fields_populates_selected_overlay_signal():
    elevation = np.array(
        [
            [4.0, 4.0, 4.0],
            [3.0, 2.0, 3.0],
            [1.0, 0.5, 1.0],
        ]
    )

    fan_fields = build_high_school_process_fields("alluvial_fan", elevation)
    volcano_fields = build_high_school_process_fields("shield_volcano", elevation)

    assert fan_fields["deposition"].shape == elevation.shape
    assert float(fan_fields["deposition"].max()) > 0.0
    assert float(volcano_fields["tectonic"].max()) > 0.0
