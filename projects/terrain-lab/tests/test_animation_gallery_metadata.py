from app.services.animation_assets import (
    animation_quality_note_for_landform,
    animation_reinforced_note_for_landform,
    is_student_recommended_landform,
    teaching_tags_for_landform,
)


def test_student_recommended_landforms_are_tagged():
    assert is_student_recommended_landform("v_valley")
    assert "학생 설명용 추천" in teaching_tags_for_landform("v_valley")


def test_reinforced_landforms_are_tagged_after_quality_pass():
    assert animation_quality_note_for_landform("lava_dome") is None
    assert animation_reinforced_note_for_landform("lava_dome")
    assert "보강 완료" in teaching_tags_for_landform("lava_dome")


def test_group_teaching_tags_remain_available_for_regular_assets():
    tags = teaching_tags_for_landform("tidal_flat")

    assert "파랑" in tags
    assert "해안 침식" in tags
