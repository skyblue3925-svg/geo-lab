from pathlib import Path

_PAGES_DIR = Path(__file__).resolve().parents[1] / "projects" / "terrain-lab" / "src" / "pages"
_PAGE = next(_PAGES_DIR.glob("4_*_Research.py"))
exec(compile(_PAGE.read_text(encoding="utf-8"), str(_PAGE), "exec"))
