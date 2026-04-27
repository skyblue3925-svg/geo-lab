from app.services.terrain_lab_catalog import (
    GROUP_LABELS_KO,
    build_lab_experiment_design_summary,
    format_parameter_multiplier_lines,
    get_additional_lab_scenario,
    list_additional_lab_scenarios,
    list_additional_lab_scenarios_by_group,
    missing_process_factor_definitions,
    process_factor_definitions_for_scenario,
    scenario_slider_defaults,
)


def test_additional_lab_catalog_contains_eighteen_scenarios():
    scenarios = list_additional_lab_scenarios()

    assert len(scenarios) == 18
    assert get_additional_lab_scenario("oxbow_lake").title_ko == "우각호"
    assert get_additional_lab_scenario("lava_dome").formation_steps_ko[-1] == "급경사 돔 안정화"
    assert get_additional_lab_scenario("esker").simulation_family == "glacial"
    assert get_additional_lab_scenario("polje").group == "karst"


def test_additional_lab_catalog_groups_and_factors_are_complete():
    assert not missing_process_factor_definitions()

    for scenario in list_additional_lab_scenarios():
        assert scenario.group in GROUP_LABELS_KO
        definitions = process_factor_definitions_for_scenario(scenario.landform_id)
        defaults = scenario_slider_defaults(scenario.landform_id)

        assert len(definitions) == len(scenario.process_factors)
        assert set(defaults) == set(scenario.process_factors)


def test_additional_lab_catalog_group_filtering():
    river_scenarios = list_additional_lab_scenarios_by_group("river")
    coastal_scenarios = list_additional_lab_scenarios_by_group("coastal")

    assert {scenario.landform_id for scenario in river_scenarios} == {
        "oxbow_lake",
        "floodplain_natural_levee",
        "river_terrace",
    }
    assert {scenario.landform_id for scenario in coastal_scenarios} == {
        "sea_cave_stack",
        "wave_cut_platform",
        "barrier_island",
        "marine_terrace",
        "tidal_flat",
    }


def test_lab_experiment_design_summary_links_factors_to_model_multipliers():
    summary = build_lab_experiment_design_summary(
        "floodplain_natural_levee",
        {"flood_frequency": 80, "settling_velocity": 50},
        {"water_scale": 1.6, "deposition_scale": 1.2, "k_scale": 1.0},
    )

    assert summary["title"] == "범람원과 자연제방 실험 설계"
    assert summary["group"] == "하천 지형"
    assert summary["formation_steps"]
    assert any("홍수 빈도: 80" in line for line in summary["factor_lines"])
    assert "물/수위 조건 x1.60" in summary["multiplier_lines"]
    assert "침식 반응 x1.00" not in summary["multiplier_lines"]


def test_format_parameter_multiplier_lines_reports_neutral_conditions():
    assert format_parameter_multiplier_lines({"k_scale": 1.0}) == ("기본값에 가까운 조건입니다.",)
