import numpy as np

from app.services.terrain_3d_payload import build_terrain_3d_payload


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
