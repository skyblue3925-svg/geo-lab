import numpy as np

from app.components.renderer import render_terrain_plotly


def test_render_terrain_plotly_adds_overlay_surface_for_process_fields():
    elevation = np.array([[0.0, 1.0], [2.0, 3.0]])
    process_fields = {
        "tectonic": np.array([[0.0, 0.5], [1.0, 0.2]]),
        "total_erosion": np.zeros((2, 2)),
        "deposition": np.zeros((2, 2)),
        "lateral": np.zeros((2, 2)),
        "glacial": np.zeros((2, 2)),
        "marine": np.zeros((2, 2)),
        "diffusion": np.zeros((2, 2)),
        "landslide": np.zeros((2, 2)),
    }

    fig = render_terrain_plotly(
        elevation,
        "Overlay test",
        add_water=False,
        process_fields=process_fields,
        overlay_type="tectonic",
    )

    assert fig is not None
    assert len(fig.data) == 2
    assert fig.data[1].opacity == 0.46


def test_render_terrain_plotly_uses_front_facing_camera_for_alluvial_fan():
    elevation = np.array([[0.0, 1.0], [2.0, 3.0]])

    fig = render_terrain_plotly(
        elevation,
        "Camera test",
        add_water=False,
        landform_type="river",
        detailed_type="alluvial_fan",
    )

    assert fig is not None
    camera = fig.layout.scene.camera.to_plotly_json()
    assert camera["eye"]["y"] < 0
    assert -2.7 < camera["eye"]["y"] < -2.4
    assert 1.75 < camera["eye"]["z"] < 1.9
    assert abs(camera["eye"]["x"]) < 0.08


def test_render_terrain_plotly_uses_valley_profile_camera_for_v_valley():
    elevation = np.array([[0.0, 1.0], [2.0, 3.0]])

    fig = render_terrain_plotly(
        elevation,
        "Valley camera test",
        add_water=False,
        landform_type="river",
        detailed_type="v_valley",
    )

    camera = fig.layout.scene.camera.to_plotly_json()
    assert camera["eye"]["x"] > 2.0
    assert camera["eye"]["y"] < 0
    assert camera["eye"]["z"] < 1.0


def test_render_terrain_plotly_uses_coastal_front_camera_for_coastal_cliff():
    elevation = np.array([[0.0, 1.0], [2.0, 3.0]])

    fig = render_terrain_plotly(
        elevation,
        "Coastal camera test",
        add_water=False,
        landform_type="coastal",
        detailed_type="coastal_cliff",
    )

    camera = fig.layout.scene.camera.to_plotly_json()
    assert camera["eye"]["y"] < 0
    assert -2.05 < camera["eye"]["y"] < -1.8
    assert 0.82 < camera["eye"]["z"] < 0.95
    assert 0.85 < camera["eye"]["x"] < 1.05


def test_render_terrain_plotly_uses_planform_camera_for_meander():
    elevation = np.array([[0.0, 1.0], [2.0, 3.0]])

    fig = render_terrain_plotly(
        elevation,
        "Meander camera test",
        add_water=False,
        landform_type="river",
        detailed_type="meander",
    )

    camera = fig.layout.scene.camera.to_plotly_json()
    assert camera["eye"]["y"] < 0
    assert camera["eye"]["z"] > 1.7
    assert abs(camera["eye"]["x"]) < 0.3


def test_render_terrain_plotly_uses_basin_camera_for_karst_doline():
    elevation = np.array([[0.0, 1.0], [2.0, 3.0]])

    fig = render_terrain_plotly(
        elevation,
        "Karst camera test",
        add_water=False,
        landform_type="karst",
        detailed_type="karst_doline",
    )

    camera = fig.layout.scene.camera.to_plotly_json()
    assert camera["eye"]["y"] < 0
    assert camera["eye"]["z"] > 1.6
    assert abs(camera["eye"]["x"]) < 0.7


def test_render_terrain_plotly_uses_relief_camera_for_folded_range():
    elevation = np.array([[0.0, 1.0], [2.0, 3.0]])

    fig = render_terrain_plotly(
        elevation,
        "Folded range camera test",
        add_water=False,
        landform_type="tectonic",
        detailed_type="folded_range",
    )

    camera = fig.layout.scene.camera.to_plotly_json()
    assert camera["eye"]["x"] > 1.8
    assert camera["eye"]["y"] < 0
    assert camera["eye"]["z"] > 0.8


def test_render_terrain_plotly_respects_camera_profile_override():
    elevation = np.array([[0.0, 1.0], [2.0, 3.0]])

    fig = render_terrain_plotly(
        elevation,
        "Camera override test",
        add_water=False,
        landform_type="river",
        detailed_type="alluvial_fan",
        camera_profile="relief_oblique",
    )

    camera = fig.layout.scene.camera.to_plotly_json()
    assert camera["eye"]["x"] > 1.8
    assert camera["eye"]["y"] < -1.0
    assert camera["eye"]["z"] < 1.0


def test_render_terrain_plotly_respects_fjord_textbook_camera_profile():
    elevation = np.array([[0.0, 1.0], [2.0, 3.0]])

    fig = render_terrain_plotly(
        elevation,
        "Fjord textbook camera",
        add_water=False,
        landform_type="glacial",
        detailed_type="fjord",
        camera_profile="fjord_textbook",
    )

    camera = fig.layout.scene.camera.to_plotly_json()
    assert 0.5 < camera["eye"]["x"] < 0.75
    assert -2.6 < camera["eye"]["y"] < -2.35
    assert 1.05 < camera["eye"]["z"] < 1.25
