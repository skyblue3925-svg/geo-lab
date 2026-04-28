import numpy as np

from app.services.terrain_3d_payload import build_terrain_3d_payload, build_terrain_3d_payload_from_history


def test_build_terrain_3d_payload_exposes_common_renderer_contract_for_v_valley():
    payload = build_terrain_3d_payload("v_valley", grid_size=16, frame_count=5)

    assert payload["landformId"] == "v_valley"
    assert payload["family"] == "river_delta"
    assert payload["gridSize"] == 16
    assert payload["surfaceFrameCount"] == 5
    assert payload["surfaceFrames"] == payload["elevationFrames"]

    expected_cell_count = 16 * 16
    for field_name in ("elevationFrames", "waterDepthFrames", "erosionFrames", "depositionFrames"):
        frames = payload[field_name]
        assert len(frames) == 5
        assert all(len(frame) == expected_cell_count for frame in frames)

    assert len(payload["flowFrames"]) == 5
    assert all(len(frame["x"]) == expected_cell_count for frame in payload["flowFrames"])
    assert all(len(frame["y"]) == expected_cell_count for frame in payload["flowFrames"])

    erosion_total = sum(float(np.sum(frame)) for frame in payload["erosionFrames"])
    water_total = sum(float(np.sum(frame)) for frame in payload["waterDepthFrames"])
    assert erosion_total > 0.0
    assert water_total > 0.0
    assert "하방 침식" in " ".join(payload["processLabels"])
    assert payload["cameraProfile"]["mode"] in {"valley_follow", "low_oblique", "plan"}
    assert payload["teachingAnnotations"]


def test_build_terrain_3d_payload_marks_delta_deposition_and_plan_camera():
    payload = build_terrain_3d_payload("delta", grid_size=18, frame_count=6)

    deposition_total = sum(float(np.sum(frame)) for frame in payload["depositionFrames"])
    water_total = sum(float(np.sum(frame)) for frame in payload["waterDepthFrames"])

    assert payload["family"] == "river_delta"
    assert deposition_total > 0.0
    assert water_total > 0.0
    assert payload["cameraProfile"]["mode"] == "plan"
    assert any("퇴적" in label for label in payload["processLabels"])
    assert any(annotation["frame"] == 0 for annotation in payload["teachingAnnotations"])


def test_build_terrain_3d_payload_recovers_karren_small_grid_sequence():
    payload = build_terrain_3d_payload("karren", grid_size=16, frame_count=5)

    frames = np.array(payload["surfaceFrames"], dtype=float)
    assert payload["gridSize"] == 16
    assert payload["surfaceFrameCount"] == 5
    assert float(np.mean(np.abs(frames[-1] - frames[0]))) > 0.02
    assert sum(float(np.sum(frame)) for frame in payload["erosionFrames"]) > 0.0


def test_build_terrain_3d_payload_makes_static_pedestal_formation_visible():
    payload = build_terrain_3d_payload("pedestal_rock", grid_size=24, frame_count=5)

    frames = np.array(payload["surfaceFrames"], dtype=float)
    assert float(np.mean(np.abs(frames[-1] - frames[0]))) > 0.02
    assert payload["surfaceFrameCount"] == 5


def test_build_terrain_3d_payload_from_history_uses_simulation_process_fields():
    history = [
        np.array([[4.0, 3.0], [2.0, 1.0]]),
        np.array([[3.5, 2.5], [2.0, 1.2]]),
    ]
    process_history = [
        {
            "total_erosion": np.array([[0.0, 0.0], [0.0, 0.0]]),
            "deposition": np.array([[0.0, 0.0], [0.0, 0.0]]),
        },
        {
            "total_erosion": np.array([[0.7, 0.4], [0.0, 0.0]]),
            "deposition": np.array([[0.0, 0.0], [0.2, 0.5]]),
        },
    ]

    payload = build_terrain_3d_payload_from_history(
        "v_valley",
        history=history,
        process_history=process_history,
    )

    assert payload["modelSource"] == "simulation_history"
    assert payload["gridSize"] == 2
    assert payload["surfaceFrameCount"] == 2
    assert len(payload["elevationFrames"]) == 2
    assert payload["erosionFrames"][1] == [0.0, 0.0, 1.0, 0.57143]
    assert payload["depositionFrames"][1] == [0.4, 1.0, 0.0, 0.0]
    assert sum(payload["waterDepthFrames"][1]) > 0.0
    assert payload["flowFrames"][1]["x"]
