from app.services.terrain_simulation_payload import (
    build_simulation_terrain_3d_payload,
    is_simulation_terrain_supported,
)


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


def test_build_simulation_terrain_3d_payload_returns_none_for_unmapped_landforms():
    assert not is_simulation_terrain_supported("sea_arch")
    assert build_simulation_terrain_3d_payload("sea_arch", grid_size=12, frame_count=4) is None
