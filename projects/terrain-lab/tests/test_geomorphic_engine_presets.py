import numpy as np

from app.services.geomorphic_engine import GeomorphicEngineParameters, run_geomorphic_engine
from app.services.terrain_physics_lab import run_physics_lab_simulation


def _initial_surface(preset_id: str) -> np.ndarray:
    result = run_geomorphic_engine(
        GeomorphicEngineParameters(
            preset_id=preset_id,
            grid_size=36,
            total_time_years=2_500,
            save_frames=3,
        )
    )
    return np.asarray(result["history"][0], dtype=float)


def _surface_distance(left: np.ndarray, right: np.ndarray) -> float:
    return float(np.mean(np.abs(left - right)))


def test_coastal_presets_have_distinct_initial_surfaces():
    baseline = _initial_surface("coastal_cliff")

    for preset_id in ["wave_cut_platform", "spit_lagoon", "tombolo", "marine_terrace"]:
        surface = _initial_surface(preset_id)
        assert surface.shape == baseline.shape
        assert _surface_distance(surface, baseline) > 4.0


def test_volcanic_presets_have_distinct_initial_surfaces():
    baseline = _initial_surface("lava_dome")

    for preset_id in ["stratovolcano", "shield_volcano", "lava_plateau", "maar", "cinder_cone"]:
        surface = _initial_surface(preset_id)
        assert surface.shape == baseline.shape
        assert _surface_distance(surface, baseline) > 4.0


def test_karst_presets_have_distinct_initial_surfaces():
    baseline = _initial_surface("karst_doline")

    for preset_id in ["tower_karst", "karren", "uvala", "polje"]:
        surface = _initial_surface(preset_id)
        assert surface.shape == baseline.shape
        assert _surface_distance(surface, baseline) > 2.0


def test_lab_routes_selected_landforms_to_distinct_presets():
    expected_presets = {
        "wave_cut_platform": "wave_cut_platform",
        "spit_lagoon": "spit_lagoon",
        "tombolo": "tombolo",
        "marine_terrace": "marine_terrace",
        "stratovolcano": "stratovolcano",
        "shield_volcano": "shield_volcano",
        "lava_plateau": "lava_plateau",
        "tower_karst": "tower_karst",
        "karren": "karren",
        "uvala": "uvala",
    }

    for landform_id, preset_id in expected_presets.items():
        result = run_physics_lab_simulation(landform_id, 55, 55, 35, 35, 5_000, 32)

        assert result["kernel"] == "geomorphic_engine_v2"
        assert result["config"].preset_id == preset_id
        assert result["change"]["relief"] > 0
