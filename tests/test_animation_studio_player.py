from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def test_image_sequence_player_crops_filmstrip_cells_with_canvas():
    source = (ROOT / "pages" / "9_Animation_Studio.py").read_text(encoding="utf-8")

    assert "filmstrip-canvas" in source
    assert "drawImage(filmstripImage" in source
    assert "cellTrimPx" in source
    assert "backgroundPosition" not in source
    assert "background-size:500% 600%" not in source
