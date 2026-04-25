from app.services.animation_assets import (
    animation_quality_note_for_landform,
    is_student_recommended_landform,
    teaching_tags_for_landform,
)


def test_student_recommended_landforms_are_tagged():
    assert is_student_recommended_landform("v_valley")
    assert "학생 설명용 추천" in teaching_tags_for_landform("v_valley")


def test_quality_review_landforms_are_tagged():
    assert animation_quality_note_for_landform("lava_dome")
    assert "품질 점검 필요" in teaching_tags_for_landform("lava_dome")


def test_group_teaching_tags_remain_available_for_regular_assets():
    tags = teaching_tags_for_landform("tidal_flat")

    assert "파랑" in tags
    assert "해안 침식" in tags
