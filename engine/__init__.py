from pathlib import Path

_PROJECT_ENGINE = Path(__file__).resolve().parents[1] / "projects" / "terrain-lab" / "src" / "engine"
__path__ = [str(_PROJECT_ENGINE)]

