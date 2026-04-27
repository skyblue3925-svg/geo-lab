from app.services.terrain_physics_lab import (
    active_physics_lab_rows,
    get_physics_lab_theory,
    list_physics_lab_scenarios,
    planned_physics_lab_rows,
    run_physics_lab_simulation,
)


def test_active_lab_rows_expose_all_current_scenarios():
    scenarios = list_physics_lab_scenarios()
    rows = active_physics_lab_rows()

    assert len(scenarios) >= 50
    assert len(rows) == len(scenarios)
    assert {row["상태"] for row in rows} == {"실험 가능"}
    assert {row["지형"] for row in rows} == {scenario.title for scenario in scenarios}
    assert all(row["모델 계열"] for row in rows)
    assert "우각호" in {scenario.title for scenario in scenarios}
    assert "모레인" in {scenario.title for scenario in scenarios}
    assert "성층화산" in {scenario.title for scenario in scenarios}
    assert "폭포" in {scenario.title for scenario in scenarios}


def test_theory_notes_explain_equations_for_every_current_scenario():
    for scenario in list_physics_lab_scenarios():
        theory = get_physics_lab_theory(scenario.landform_id)

        assert theory.model_family
        assert theory.equations
        assert theory.assumptions
        assert theory.classroom_note


def test_planned_lab_rows_do_not_duplicate_active_animation_catalog():
    rows = planned_physics_lab_rows()
    active_titles = {scenario.title for scenario in list_physics_lab_scenarios()}

    assert "폭포" in active_titles
    assert "아레트" in active_titles
    assert "폭포" not in {row["지형"] for row in rows}
    assert "아레트" not in {row["지형"] for row in rows}


def test_new_catalog_scenarios_route_to_common_engine():
    for landform_id in ["oxbow_lake", "sea_cave_stack", "moraine", "maar", "polje", "waterfall", "stratovolcano"]:
        result = run_physics_lab_simulation(landform_id, 55, 50, 35, 35, 5_000, 32)

        assert result["kernel"] == "geomorphic_engine_v2"
        assert result["history"][-1].shape == (32, 32)
        assert result["dominant_process"]
        assert result["change"]["relief"] > 0


def test_lab_common_engine_exposes_process_force_fields():
    expected_fields = {
        "coastal_cliff": (
            "wave_energy",
            "shoreline_retreat",
            "wave_cut_platform",
            "beach_deposition",
            "longshore_transport",
            "wave_refraction",
            "storm_runup",
            "coastal_sediment_budget",
        ),
        "barchan": (
            "sand_flux",
            "stoss_erosion",
            "lee_deposition",
            "wind_vector_y",
            "wind_shear_stress",
            "sand_availability",
            "shelter_factor",
            "dune_migration",
        ),
        "lava_dome": ("volcanic_construction", "lava_flow", "viscosity_resistance", "cooling_limited_spread"),
        "maar": ("explosion_energy", "crater_excavation", "magma_water_contact", "ejecta_deposition"),
        "cinder_cone": ("ejecta_deposition", "pyroclastic_cone_growth"),
        "karst_doline": ("groundwater_flow", "solution_rate", "subsurface_drainage", "collapse_risk"),
        "polje": ("fracture_density", "sinkhole_density", "ponor_drainage", "seasonal_flooding", "polje_floor_aggradation"),
    }

    for landform_id, field_names in expected_fields.items():
        result = run_physics_lab_simulation(landform_id, 65, 60, 35, 35, 5_000, 32)
        process_fields = result["process_history"][-1]

        for field_name in field_names:
            assert field_name in process_fields
            assert float(abs(process_fields[field_name]).sum()) > 0.0
