import numpy as np

from app.components.animation_renderer import (
    create_history_animation_embed_html,
    create_history_animation_figure,
    create_history_gif_bytes,
    get_next_history_frame,
)


def test_create_history_animation_figure_interpolates_dense_frames():
    history = [
        np.array([[0.0, 0.0], [0.0, 0.0]]),
        np.array([[3.0, 3.0], [3.0, 3.0]]),
    ]
    times = [0.0, 90.0]

    fig = create_history_animation_figure(
        history=history,
        times=times,
        interpolation_steps=3,
    )

    assert fig is not None
    assert len(fig.frames) == 4
    np.testing.assert_allclose(np.array(fig.frames[1].data[0].z), np.ones((2, 2)))
    assert len(fig.layout.sliders[0].steps) == 4
    assert fig.layout.updatemenus[0].buttons[0].args[0] == ("hist_000", "hist_001", "hist_002", "hist_003")


def test_create_history_animation_figure_applies_camera_motion():
    history = [
        np.array([[0.0, 0.0], [0.0, 0.0]]),
        np.array([[1.0, 2.0], [3.0, 4.0]]),
        np.array([[2.0, 3.0], [4.0, 5.0]]),
    ]
    times = [0.0, 50.0, 100.0]

    fig = create_history_animation_figure(
        history=history,
        times=times,
        interpolation_steps=1,
        landform_type="river",
        detailed_type="alluvial_fan",
        camera_motion="auto",
        cinematic_zoom=1.05,
    )

    assert fig is not None
    moved_camera = fig.frames[1].layout.scene.camera.to_plotly_json()
    initial_camera = fig.layout.scene.camera.to_plotly_json()
    assert moved_camera != initial_camera


def test_create_history_animation_figure_uses_front_facing_alluvial_fan_camera():
    history = [
        np.array([[0.0, 0.0], [0.0, 0.0]]),
        np.array([[1.0, 2.0], [3.0, 4.0]]),
    ]
    times = [0.0, 100.0]

    fig = create_history_animation_figure(
        history=history,
        times=times,
        interpolation_steps=1,
        landform_type="river",
        detailed_type="alluvial_fan",
        camera_motion="fixed",
    )

    assert fig is not None
    camera = fig.layout.scene.camera.to_plotly_json()
    assert camera["eye"]["y"] < 0
    assert -2.7 < camera["eye"]["y"] < -2.4
    assert 1.75 < camera["eye"]["z"] < 1.9
    assert abs(camera["eye"]["x"]) < 0.08


def test_create_history_animation_figure_uses_planform_camera_for_delta():
    history = [
        np.array([[0.0, 0.0], [0.0, 0.0]]),
        np.array([[1.0, 2.0], [3.0, 4.0]]),
    ]
    times = [0.0, 100.0]

    fig = create_history_animation_figure(
        history=history,
        times=times,
        interpolation_steps=1,
        landform_type="coastal",
        detailed_type="delta",
        camera_motion="fixed",
    )

    camera = fig.layout.scene.camera.to_plotly_json()
    assert camera["eye"]["y"] < 0
    assert -2.7 < camera["eye"]["y"] < -2.45
    assert 2.0 < camera["eye"]["z"] < 2.2
    assert 0.03 < camera["eye"]["x"] < 0.12


def test_create_history_animation_figure_uses_planform_camera_for_meander():
    history = [
        np.array([[0.0, 0.0], [0.0, 0.0]]),
        np.array([[1.0, 2.0], [3.0, 4.0]]),
    ]
    times = [0.0, 100.0]

    fig = create_history_animation_figure(
        history=history,
        times=times,
        interpolation_steps=1,
        landform_type="river",
        detailed_type="meander",
        camera_motion="fixed",
    )

    camera = fig.layout.scene.camera.to_plotly_json()
    assert camera["eye"]["y"] < 0
    assert camera["eye"]["z"] > 1.7
    assert abs(camera["eye"]["x"]) < 0.3


def test_create_history_animation_figure_uses_front_facing_camera_for_fjord():
    history = [
        np.array([[0.0, 0.0], [0.0, 0.0]]),
        np.array([[1.0, 2.0], [3.0, 4.0]]),
    ]
    times = [0.0, 100.0]

    fig = create_history_animation_figure(
        history=history,
        times=times,
        interpolation_steps=1,
        landform_type="glacial",
        detailed_type="fjord",
        camera_motion="fixed",
    )

    camera = fig.layout.scene.camera.to_plotly_json()
    assert camera["eye"]["y"] < 0
    assert -2.6 < camera["eye"]["y"] < -2.35
    assert 1.05 < camera["eye"]["z"] < 1.25
    assert 0.5 < camera["eye"]["x"] < 0.75


def test_create_history_animation_figure_uses_relief_camera_for_stratovolcano():
    history = [
        np.array([[0.0, 0.0], [0.0, 0.0]]),
        np.array([[1.0, 2.0], [3.0, 4.0]]),
    ]
    times = [0.0, 100.0]

    fig = create_history_animation_figure(
        history=history,
        times=times,
        interpolation_steps=1,
        landform_type="volcanic",
        detailed_type="stratovolcano",
        camera_motion="fixed",
    )

    camera = fig.layout.scene.camera.to_plotly_json()
    assert camera["eye"]["x"] > 1.7
    assert camera["eye"]["y"] < 0
    assert camera["eye"]["z"] > 0.75


def test_create_history_animation_figure_adds_process_overlay_trace():
    history = [
        np.array([[0.0, 0.0], [0.0, 0.0]]),
        np.array([[1.0, 2.0], [3.0, 4.0]]),
    ]
    times = [0.0, 100.0]
    process_history = [
        {
            "tectonic": np.array([[0.0, 0.0], [0.0, 0.0]]),
            "total_erosion": np.zeros((2, 2)),
            "deposition": np.zeros((2, 2)),
            "moraine": np.zeros((2, 2)),
        },
        {
            "tectonic": np.array([[0.0, 0.3], [0.6, 0.9]]),
            "total_erosion": np.zeros((2, 2)),
            "deposition": np.zeros((2, 2)),
            "moraine": np.zeros((2, 2)),
        },
    ]
    stage_history = [
        {"overlay_type": "tectonic"},
        {"overlay_type": "tectonic"},
    ]

    fig = create_history_animation_figure(
        history=history,
        times=times,
        process_history=process_history,
        stage_history=stage_history,
        interpolation_steps=1,
    )

    assert fig is not None
    assert len(fig.data) == 2
    assert len(fig.frames[0].data) == 2
    assert fig.frames[0].data[1].opacity == 0.48


def test_create_history_animation_embed_html_contains_plotly_autoplay_script():
    history = [
        np.array([[0.0, 0.0], [0.0, 0.0]]),
        np.array([[1.0, 1.0], [1.0, 1.0]]),
    ]
    times = [0.0, 100.0]

    fig = create_history_animation_figure(
        history=history,
        times=times,
        interpolation_steps=1,
        show_slider=False,
    )
    html = create_history_animation_embed_html(fig, frame_duration_ms=120, transition_duration_ms=60)

    assert "Plotly.animate" in html
    assert "hist_000" in html
    assert "hist_001" in html


def test_create_history_animation_figure_returns_none_for_empty_history():
    assert create_history_animation_figure(history=[], times=[]) is None


def test_create_history_gif_bytes_returns_gif_binary():
    history = [
        np.array([[0.0, 1.0], [1.0, 0.0]]),
        np.array([[1.0, 0.0], [0.0, 1.0]]),
    ]
    times = [0.0, 100.0]
    process_history = [
        {
            "tectonic": np.array([[0.0, 0.2], [0.1, 0.0]]),
            "total_erosion": np.zeros((2, 2)),
            "deposition": np.zeros((2, 2)),
        },
        {
            "tectonic": np.array([[0.0, 0.4], [0.3, 0.1]]),
            "total_erosion": np.zeros((2, 2)),
            "deposition": np.zeros((2, 2)),
        },
    ]
    stage_history = [
        {"title": "Stage 1", "overlay_type": "tectonic"},
        {"title": "Stage 2", "overlay_type": "tectonic"},
    ]

    gif_bytes = create_history_gif_bytes(
        history=history,
        times=times,
        process_history=process_history,
        stage_history=stage_history,
        overlay_type="tectonic",
        fps=2,
        landform_type="river",
        detailed_type="alluvial_fan",
    )

    assert gif_bytes[:6] in (b"GIF87a", b"GIF89a")
    assert len(gif_bytes) > 20


def test_get_next_history_frame_wraps_to_start():
    assert get_next_history_frame(0, 4) == 1
    assert get_next_history_frame(3, 4) == 0
    assert get_next_history_frame(2, 0) == 0
