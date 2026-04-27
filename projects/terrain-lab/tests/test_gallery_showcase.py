from app.utils.gallery_showcase import (
    apply_gallery_showcase_preset,
    build_lab_showcase_preset,
    consume_gallery_showcase_preset,
    get_gallery_showcase_preset,
    queue_gallery_showcase_preset,
)


RIVER = "\ud558\ucc9c"
DELTA = "\uc0bc\uac01\uc8fc"
ALLUVIAL_FAN = "\uc120\uc0c1\uc9c0"
FRONT_VIEW = "\uc815\uba74 (Y-)"
SCENARIO_MOUNTAIN_RIVER = "\U0001f3d4\ufe0f \uc0b0\uc9c0/\ud558\ucc9c"
STEEP_FAN = "\uc120\uc0c1\uc9c0 (\uae09\uacbd\uc0ac)"
TEACHER_MODE = "\uc218\uc5c5\uc6a9 \uce74\ud0c8\ub85c\uadf8"
COASTAL = "\ud574\uc548"


def test_get_gallery_showcase_preset_applies_landform_override():
    preset = get_gallery_showcase_preset(RIVER, "alluvial_fan")

    assert preset["title"] == ALLUVIAL_FAN
    assert preset["camera_view"] == FRONT_VIEW
    assert preset["landform_key"] == "alluvial_fan"
    assert preset["category"] == RIVER
    assert "\ubd80\ucc44\uaf34" in preset["lesson_focus"]
    assert "\ucc3e\uc544\ubcf4\uc138\uc694" in preset["observation_prompt"]
    assert preset["world_case"]["case_id"] == "death_valley_alluvial_fan"
    assert "\ub370\uc2a4\ubc38\ub9ac" in preset["world_case_label"]


def test_apply_gallery_showcase_preset_sets_gallery_session_keys():
    state = {}
    preset = get_gallery_showcase_preset(DELTA, "delta")

    apply_gallery_showcase_preset(state, preset)

    assert state["gallery_cat"] == DELTA
    assert state["landform_select"] == "delta"
    assert state["gallery_render_style"] == preset["render_style_label"]
    assert state["gallery_camera_motion"] == preset["camera_motion_label"]


def test_build_lab_showcase_preset_maps_gallery_card_to_lab():
    preset = build_lab_showcase_preset(RIVER, "alluvial_fan")

    assert preset is not None
    assert preset["source"] == "gallery_showcase"
    assert preset["scenario_category"] == SCENARIO_MOUNTAIN_RIVER
    assert preset["selected_landform"] == STEEP_FAN
    assert preset["auto_run"] is True
    assert preset["world_case"]["case_id"] == "death_valley_alluvial_fan"


def test_build_lab_showcase_preset_returns_none_when_no_mapping_exists():
    assert build_lab_showcase_preset(COASTAL, "sea_arch") is None


def test_queue_and_consume_gallery_showcase_preset_delays_widget_key_mutation():
    state = {}
    preset = get_gallery_showcase_preset(RIVER, "alluvial_fan")

    queue_gallery_showcase_preset(state, preset)

    assert state["gallery_pending_preset"]["landform_key"] == "alluvial_fan"

    consume_gallery_showcase_preset(state)

    assert state["gallery_mode"] == TEACHER_MODE
    assert state["gallery_cat"] == RIVER
    assert "gallery_pending_preset" not in state
