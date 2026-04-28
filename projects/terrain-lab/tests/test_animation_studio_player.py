from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


def test_image_sequence_player_crops_filmstrip_cells_with_canvas():
    source = (ROOT / "projects" / "terrain-lab" / "src" / "pages" / "9_Animation_Studio.py").read_text(
        encoding="utf-8"
    )

    assert "filmstrip-canvas" in source
    assert "drawImage(filmstripImage" in source
    assert "cellTrimPx" in source
    assert "backgroundPosition" not in source
    assert "background-size:500% 600%" not in source


def test_animation_studio_does_not_render_prompt_body_publicly():
    source = (ROOT / "projects" / "terrain-lab" / "src" / "pages" / "9_Animation_Studio.py").read_text(
        encoding="utf-8"
    )

    assert "st.code(prompt_text" not in source
    assert "read_prompt_text(selected_asset)" not in source
    assert "has_prompt" in source
