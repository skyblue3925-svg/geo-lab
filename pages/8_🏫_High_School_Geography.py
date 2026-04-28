from pathlib import Path

_PAGE = Path(__file__).resolve().parents[1] / "projects" / "terrain-lab" / "src" / "pages" / "8_🏫_High_School_Geography.py"
exec(compile(_PAGE.read_text(encoding="utf-8"), str(_PAGE), "exec"))

