from pathlib import Path

_PAGE = Path(__file__).resolve().parents[1] / "projects" / "terrain-lab" / "src" / "pages" / "10_GIF_Gallery.py"
exec(compile(_PAGE.read_text(encoding="utf-8"), str(_PAGE), "exec"))

