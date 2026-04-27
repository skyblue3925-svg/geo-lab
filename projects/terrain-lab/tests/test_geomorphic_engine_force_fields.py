import numpy as np

from app.services.geomorphic_engine import GeomorphicEngineParameters, run_geomorphic_engine


def _final_fields(params: GeomorphicEngineParameters) -> dict[str, np.ndarray]:
    result = run_geomorphic_engine(params)
    return result["process_history"][-1]


def _field_sum(fields: dict[str, np.ndarray], key: str) -> float:
    return float(np.sum(np.abs(fields[key])))


def test_marine_fields_are_active_only_under_marine_forcing():
    inactive = _final_fields(GeomorphicEngineParameters("coastal_cliff", grid_size=32, total_time_years=5_000))
    active = _final_fields(
        GeomorphicEngineParameters(
            "coastal_cliff",
            grid_size=32,
            total_time_years=5_000,
            marine=1.4,
            sediment=0.8,
            sea_level=0.0,
            wave_energy_scale=1.2,
        )
    )

    for key in ("wave_energy", "shoreline_retreat", "wave_cut_platform", "beach_deposition"):
        assert _field_sum(inactive, key) == 0.0
        assert _field_sum(active, key) > 0.0

    for key in ("longshore_transport", "wave_refraction", "storm_runup", "coastal_sediment_budget"):
        assert _field_sum(inactive, key) == 0.0
        assert _field_sum(active, key) > 0.0


def test_aeolian_fields_follow_wind_direction_and_sand_supply():
    fields = _final_fields(
        GeomorphicEngineParameters(
            "barchan",
            grid_size=32,
            total_time_years=5_000,
            aeolian=1.0,
            sediment=0.4,
            wind_direction_degrees=0.0,
            wind_speed=1.7,
            sand_supply=1.3,
        )
    )

    assert _field_sum(fields, "sand_flux") > 0.0
    assert _field_sum(fields, "stoss_erosion") > 0.0
    assert _field_sum(fields, "lee_deposition") > 0.0
    assert _field_sum(fields, "wind_shear_stress") > 0.0
    assert _field_sum(fields, "sand_availability") > 0.0
    assert _field_sum(fields, "shelter_factor") > 0.0
    assert _field_sum(fields, "dune_migration") > 0.0
    assert float(np.mean(fields["wind_vector_x"])) > 1.6
    assert abs(float(np.mean(fields["wind_vector_y"]))) < 1e-9


def test_volcanic_viscosity_changes_lava_spread():
    low_viscosity = _final_fields(
        GeomorphicEngineParameters(
            "lava_dome",
            grid_size=32,
            total_time_years=5_000,
            volcanic=1.2,
            eruption_rate=1.2,
            viscosity=0.15,
            lava_spread=1.4,
            cooling_rate=0.7,
        )
    )
    high_viscosity = _final_fields(
        GeomorphicEngineParameters(
            "lava_dome",
            grid_size=32,
            total_time_years=5_000,
            volcanic=1.2,
            eruption_rate=1.2,
            viscosity=0.9,
            lava_spread=1.4,
            cooling_rate=0.7,
        )
    )

    assert _field_sum(low_viscosity, "volcanic_construction") > 0.0
    assert _field_sum(low_viscosity, "lava_flow") > _field_sum(high_viscosity, "lava_flow")
    assert _field_sum(high_viscosity, "viscosity_resistance") > _field_sum(low_viscosity, "viscosity_resistance")


def test_karst_solution_responds_to_water_supply_and_solubility():
    weak = _final_fields(
        GeomorphicEngineParameters(
            "karst_doline",
            grid_size=32,
            total_time_years=5_000,
            karst=0.8,
            groundwater=0.4,
            water_supply=0.3,
            rock_solubility=0.6,
        )
    )
    strong = _final_fields(
        GeomorphicEngineParameters(
            "karst_doline",
            grid_size=32,
            total_time_years=5_000,
            karst=0.8,
            groundwater=0.4,
            water_supply=1.4,
            rock_solubility=1.8,
        )
    )

    assert _field_sum(strong, "groundwater_flow") > _field_sum(weak, "groundwater_flow")
    assert _field_sum(strong, "solution_rate") > _field_sum(weak, "solution_rate")
    assert _field_sum(strong, "collapse_risk") > 0.0


def test_maar_and_cinder_cone_expose_explosive_volcanic_fields():
    maar = _final_fields(
        GeomorphicEngineParameters(
            "maar",
            grid_size=32,
            total_time_years=5_000,
            volcanic=1.1,
            explosion_energy=1.5,
            magma_water_contact=1.3,
        )
    )
    cinder = _final_fields(
        GeomorphicEngineParameters(
            "cinder_cone",
            grid_size=32,
            total_time_years=5_000,
            volcanic=1.1,
            pyroclastic_supply=1.4,
        )
    )

    assert _field_sum(maar, "explosion_energy") > 0.0
    assert _field_sum(maar, "crater_excavation") > 0.0
    assert _field_sum(maar, "magma_water_contact") > 0.0
    assert _field_sum(cinder, "ejecta_deposition") > 0.0
    assert _field_sum(cinder, "pyroclastic_cone_growth") > 0.0


def test_polje_exposes_subsurface_drainage_and_floor_aggradation():
    fields = _final_fields(
        GeomorphicEngineParameters(
            "polje",
            grid_size=32,
            total_time_years=5_000,
            karst=1.2,
            groundwater=1.1,
            sediment=0.8,
            water_supply=1.2,
            rock_solubility=1.4,
            fracture_density=1.5,
            seasonal_flooding=1.3,
        )
    )

    assert _field_sum(fields, "fracture_density") > 0.0
    assert _field_sum(fields, "sinkhole_density") > 0.0
    assert _field_sum(fields, "ponor_drainage") > 0.0
    assert _field_sum(fields, "seasonal_flooding") > 0.0
    assert _field_sum(fields, "polje_floor_aggradation") > 0.0


def test_marine_wave_energy_scale_increases_shoreline_retreat():
    weak = _final_fields(
        GeomorphicEngineParameters(
            "coastal_cliff",
            grid_size=32,
            total_time_years=5_000,
            marine=1.0,
            sediment=0.6,
            wave_energy_scale=0.5,
            sea_level=0.0,
        )
    )
    strong = _final_fields(
        GeomorphicEngineParameters(
            "coastal_cliff",
            grid_size=32,
            total_time_years=5_000,
            marine=1.0,
            sediment=0.6,
            wave_energy_scale=1.8,
            sea_level=0.0,
        )
    )

    assert _field_sum(strong, "wave_energy") > _field_sum(weak, "wave_energy")
    assert _field_sum(strong, "shoreline_retreat") > _field_sum(weak, "shoreline_retreat")


def test_glacial_forcing_isolated_from_non_glacial_runs():
    inactive = _final_fields(GeomorphicEngineParameters("u_valley", grid_size=32, total_time_years=5_000))
    active = _final_fields(
        GeomorphicEngineParameters(
            "u_valley",
            grid_size=32,
            total_time_years=5_000,
            glacial=1.4,
            sediment=0.5,
        )
    )

    assert _field_sum(inactive, "ice_thickness") == 0.0
    assert _field_sum(inactive, "glacial_velocity") == 0.0
    assert _field_sum(active, "ice_thickness") > 0.0
    assert _field_sum(active, "glacial_velocity") > 0.0


def test_unrelated_force_fields_remain_inactive_for_single_process_runs():
    coastal = _final_fields(
        GeomorphicEngineParameters(
            "coastal_cliff",
            grid_size=32,
            total_time_years=5_000,
            marine=1.0,
            sediment=0.6,
            sea_level=0.0,
        )
    )
    dune = _final_fields(
        GeomorphicEngineParameters(
            "barchan",
            grid_size=32,
            total_time_years=5_000,
            aeolian=1.0,
            sediment=0.6,
            wind_speed=1.0,
            sand_supply=0.8,
        )
    )

    assert _field_sum(coastal, "sand_flux") == 0.0
    assert _field_sum(coastal, "volcanic_construction") == 0.0
    assert _field_sum(dune, "wave_energy") == 0.0
    assert _field_sum(dune, "solution_rate") == 0.0
