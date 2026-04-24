from types import SimpleNamespace

from app.components import babylon_renderer, threejs_renderer


class ExistingPath:
    def exists(self) -> bool:
        return True


def _sample_payload() -> dict:
    cells = [0.0, 0.2, 0.4, 0.6]
    return {
        "gridSize": 2,
        "surfaceFrames": [cells],
        "elevationFrames": [cells],
        "waterDepthFrames": [[0.0, 0.0, 0.3, 0.5]],
        "erosionFrames": [[0.1, 0.2, 0.8, 0.3]],
        "depositionFrames": [[0.0, 0.4, 0.7, 0.2]],
        "flowFrames": [{"x": [0.0, 1.0, 0.0, 1.0], "y": [1.0, 0.0, 1.0, 0.0]}],
        "surfaceFrameCount": 1,
        "heightScale": 18.0,
        "processLabels": ["하방 침식", "퇴적"],
        "cameraProfile": {"mode": "plan"},
        "teachingAnnotations": [{"frame": 0, "label": "하방 침식", "text": "확인"}],
    }


def _patch_renderer_dependencies(monkeypatch, module):
    monkeypatch.setattr(
        module,
        "get_landform_asset_bundle",
        lambda landform_id: {
            "filmstrip_path": ExistingPath(),
            "image_sequence_entry": {"frame_count": 1, "fps": 8},
        },
    )
    monkeypatch.setattr(module, "read_image_data_uri", lambda path: "data:image/png;base64,abc")
    monkeypatch.setattr(module, "build_terrain_3d_payload", lambda *args, **kwargs: _sample_payload())


def test_babylon_viewer_embeds_shared_physics_payload(monkeypatch):
    _patch_renderer_dependencies(monkeypatch, babylon_renderer)
    asset = SimpleNamespace(landform_id="v_valley", title="V자곡")

    html = babylon_renderer.create_babylon_terrain_viewer_html(asset, grid_size=2, surface_frames=1)

    assert html is not None
    assert '"waterDepthFrames"' in html
    assert '"erosionFrames"' in html
    assert '"depositionFrames"' in html
    assert '"flowFrames"' in html
    assert "하방 침식" in html


def test_threejs_viewer_embeds_shared_physics_payload(monkeypatch):
    _patch_renderer_dependencies(monkeypatch, threejs_renderer)
    asset = SimpleNamespace(landform_id="v_valley", title="V자곡")

    html = threejs_renderer.create_threejs_terrain_viewer_html(asset, grid_size=2, surface_frames=1)

    assert html is not None
    assert '"waterDepthFrames"' in html
    assert '"erosionFrames"' in html
    assert '"depositionFrames"' in html
    assert '"flowFrames"' in html
    assert "하방 침식" in html
