from app.high_school_geography_view import build_high_school_animation_figure
from app.utils.high_school_world_geography import get_high_school_world_topic


def test_high_school_animation_figure_has_playback_controls():
    topic = get_high_school_world_topic("v_valley")

    figure = build_high_school_animation_figure(topic, grid_size=32, num_frames=6)

    assert figure is not None
    assert len(figure.frames) == 6

    buttons = [
        button
        for menu in (figure.layout.updatemenus or [])
        for button in (menu.buttons or [])
    ]
    assert any(getattr(button, "method", None) == "animate" for button in buttons)
