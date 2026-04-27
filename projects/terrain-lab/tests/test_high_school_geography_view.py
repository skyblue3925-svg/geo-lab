from app.high_school_geography_view import resolve_high_school_camera_spec


def test_resolve_high_school_camera_spec_uses_textbook_override_for_key_landforms():
    camera_profile, recommended_view = resolve_high_school_camera_spec(
        {
            "topic_id": "alluvial_fan",
            "camera_profile": "planform_front",
            "recommended_view": "default",
        }
    )

    assert camera_profile == "fan_textbook"
    assert "선상지" in recommended_view


def test_resolve_high_school_camera_spec_falls_back_for_other_landforms():
    camera_profile, recommended_view = resolve_high_school_camera_spec(
        {
            "topic_id": "tower_karst",
            "camera_profile": "relief_oblique",
            "recommended_view": "입체 지형 사선뷰",
        }
    )

    assert camera_profile == "relief_oblique"
    assert recommended_view == "입체 지형 사선뷰"
