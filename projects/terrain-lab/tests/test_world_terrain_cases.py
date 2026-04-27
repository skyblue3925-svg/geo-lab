from app.utils.world_terrain_cases import (
    extract_selected_world_case_id,
    get_all_world_cases,
    get_featured_world_case,
    get_featured_world_cases,
    get_world_case,
    get_world_cases_for_category,
)


def test_get_featured_world_case_returns_expected_case_for_alluvial_fan():
    case = get_featured_world_case("alluvial_fan")

    assert case is not None
    assert case["case_id"] == "death_valley_alluvial_fan"
    assert case["category"] == "하천"
    assert case["recommended_view"] == "정면 (Y-)"
    assert case["latitude"] > 0
    assert case["longitude"] < 0


def test_get_world_cases_for_category_returns_multiple_river_examples():
    river_cases = get_world_cases_for_category("하천")
    case_ids = {case["case_id"] for case in river_cases}

    assert "death_valley_alluvial_fan" in case_ids
    assert "alpine_v_valley" in case_ids
    assert "mississippi_meander_plain" in case_ids


def test_get_world_case_can_lookup_specific_case():
    case = get_world_case("norway_fjord")

    assert case is not None
    assert case["landform_key"] == "fjord"
    assert "빙하 침식" in case["process_focus"]


def test_get_featured_world_cases_can_limit_case_count():
    cases = get_featured_world_cases(limit=4)

    assert len(cases) == 4
    assert cases[0]["case_id"] == "death_valley_alluvial_fan"


def test_all_world_cases_have_required_teaching_fields():
    cases = get_all_world_cases()

    assert len(cases) >= 8
    for case in cases:
        assert case["title"]
        assert case["location_label"]
        assert case["classroom_hook"]
        assert case["student_question"]
        assert case["teacher_note"]
        assert case["overlay_priority"]
        assert -90 <= case["latitude"] <= 90
        assert -180 <= case["longitude"] <= 180


def test_extract_selected_world_case_id_reads_streamlit_plotly_event_shape():
    event_data = {
        "selection": {
            "points": [
                {
                    "customdata": "death_valley_alluvial_fan",
                }
            ]
        }
    }

    assert extract_selected_world_case_id(event_data) == "death_valley_alluvial_fan"


def test_extract_selected_world_case_id_handles_customdata_sequence():
    event_data = {
        "selection": {
            "points": [
                {
                    "customdata": ["alpine_v_valley", "ignored"],
                }
            ]
        }
    }

    assert extract_selected_world_case_id(event_data) == "alpine_v_valley"
