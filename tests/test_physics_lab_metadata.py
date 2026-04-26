from app.services.terrain_physics_lab import (
    active_physics_lab_rows,
    get_physics_lab_theory,
    list_physics_lab_scenarios,
    planned_physics_lab_rows,
)


def test_active_lab_rows_expose_all_current_scenarios():
    scenarios = list_physics_lab_scenarios()
    rows = active_physics_lab_rows()

    assert len(rows) == len(scenarios)
    assert {row["상태"] for row in rows} == {"실험 가능"}
    assert {row["지형"] for row in rows} == {scenario.title for scenario in scenarios}
    assert all(row["모델 계열"] for row in rows)


def test_theory_notes_explain_equations_for_every_current_scenario():
    for scenario in list_physics_lab_scenarios():
        theory = get_physics_lab_theory(scenario.landform_id)

        assert theory.landform_id == scenario.landform_id
        assert theory.model_family
        assert theory.equations
        assert theory.assumptions
        assert theory.classroom_note


def test_planned_lab_rows_include_locked_catalog_candidates():
    rows = planned_physics_lab_rows()

    assert rows
    assert {row["상태"] for row in rows} == {"프리셋 예정"}
    assert "우각호" in {row["지형"] for row in rows}
    assert "모레인" in {row["지형"] for row in rows}
