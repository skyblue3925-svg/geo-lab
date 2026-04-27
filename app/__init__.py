from pathlib import Path

_PROJECT_APP = Path(__file__).resolve().parents[1] / "projects" / "terrain-lab" / "src" / "app"
__path__ = [str(_PROJECT_APP)]

