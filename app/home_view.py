from pathlib import Path

_MODULE = Path(__file__).resolve().parents[1] / "projects" / "terrain-lab" / "src" / "app" / "home_view.py"
exec(compile(_MODULE.read_text(encoding="utf-8"), str(_MODULE), "exec"))

