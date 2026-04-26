# Terrain Lab Agent Guide

## Scope

This project owns the terrain and landform learning product:

- Streamlit public app shell for Geo-Lab terrain pages
- Animation Studio, GIF gallery, high-school geography pages
- Geomorphic Lab physical modeling engine
- Terrain image, storyboard, frame, and GIF assets
- Terrain-specific Python tests and import scripts

## Current Source Locations

During migration, source still lives mostly at repository root:

- `app/`
- `pages/`
- `engine/`
- `assets/cinematic/`
- `assets/frames/`
- `scripts/*terrain*`, `scripts/*filmstrip*`, `scripts/*storyboard*`
- `tests/test_geomorphic_*`, `tests/test_physics_lab_*`, `tests/test_animation_*`, `tests/test_high_school_*`, `tests/test_image_sequence_*`
- `app.py`, `app_high_school.py`, `requirements.txt`, `pyproject.toml`

Do not assume all files have already moved under `projects/terrain-lab/`.

## Invariants

- Keep terrain work separate from Koppen climate and GIS work.
- Do not move large generated outputs, venvs, caches, or deployment worktrees into this project.
- Treat `assets/cinematic/image_sequence/` and `assets/frames/` as product assets, not temporary output.
- Preserve Streamlit route compatibility until deployment paths are explicitly changed.
- Lab physical modeling changes must keep the shared output contract:
  - `history`
  - `times`
  - `process_history`
  - `stats_history`
  - `kernel`
  - `config` or `parameters`

## Verification

For terrain work, prefer targeted checks first:

```powershell
.\.venv\Scripts\python.exe -m py_compile app\services\geomorphic_engine.py app\services\terrain_physics_lab.py "pages\3_🧪_Lab.py"
.\.venv\Scripts\python.exe -m pytest tests\test_geomorphic_engine_force_fields.py tests\test_geomorphic_engine_presets.py tests\test_physics_lab_metadata.py -q
```

For broader terrain regression:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_geomorphic_engine_force_fields.py tests\test_geomorphic_engine_presets.py tests\test_physics_lab_metadata.py tests\test_geomorphic_engine.py tests\test_morphometric_metrics.py tests\test_geomorphic_process_kernels.py tests\test_river_morphology_kernel.py tests\test_terrain_lab_catalog.py tests\test_page_syntax.py -q
```

If Streamlit is running locally, verify:

```powershell
Invoke-WebRequest -Uri http://127.0.0.1:8501/Lab -UseBasicParsing -TimeoutSec 20
```

