from app.services.animation_assets import KOREAN_TITLES
from app.services.terrain_simulation_payload import (
    build_simulation_terrain_3d_payload,
    is_simulation_terrain_supported,
)


def test_terrain_simulation_payload_has_no_unshipped_lab_model_dependency():
    source = "app/services/terrain_simulation_payload.py"
    with open(source, encoding="utf-8") as handle:
        module_source = handle.read()

    assert "app.utils.lab_model" not in module_source


def test_build_simulation_terrain_3d_payload_uses_simple_lem_history():
    payload = build_simulation_terrain_3d_payload(
        "v_valley",
        grid_size=12,
        frame_count=4,
    )

    assert payload is not None
    assert payload["modelSource"] == "simulation_history"
    assert payload["landformId"] == "v_valley"
    assert payload["gridSize"] == 12
    assert payload["surfaceFrameCount"] == 4
    assert len(payload["stageHistory"]) == 4
    assert sum(payload["erosionFrames"][1]) > 0.0


def test_all_animation_studio_landforms_have_simulation_scenarios():
    missing = [
        landform_id
        for landform_id in KOREAN_TITLES
        if not is_simulation_terrain_supported(landform_id)
    ]

    assert missing == []


def test_build_simulation_terrain_3d_payload_marks_proxy_landforms_with_caveat():
    payload = build_simulation_terrain_3d_payload("sea_arch", grid_size=12, frame_count=3)

    assert payload is not None
    assert payload["modelSource"] == "simulation_history"
    assert payload["simulationSupportLevel"] == "process_proxy"
    assert payload["terrainSurfaceSource"] == "ideal_landform:sea_arch"
    assert "근사" in payload["simulationCaveat"]
    assert len(payload["stageHistory"]) == 3
