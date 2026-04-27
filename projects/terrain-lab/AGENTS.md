# Terrain Lab Agent Guide

## Scope

This project owns the terrain and landform learning product:

- Streamlit public app shell for Geo-Lab terrain pages
- Animation Studio, GIF Gallery, and high-school geography pages
- Geomorphic Lab physical modeling engine
- Terrain image, storyboard, frame, and GIF assets
- Terrain-specific Python tests and import scripts

## Current Source Locations

Primary source now lives under this project:

- `projects/terrain-lab/src/app/`
- `projects/terrain-lab/src/pages/`
- `projects/terrain-lab/src/engine/`

The repository root still keeps compatibility wrappers for Streamlit and deployment:

- `app/`
- `pages/`
- `engine/`
- `app.py`

Terrain assets and scripts still live at repository root for now:

- `assets/cinematic/`
- `assets/frames/`
- `scripts/*terrain*`, `scripts/*filmstrip*`, `scripts/*storyboard*`
- `requirements.txt`
- `pyproject.toml`

Terrain tests now live in `projects/terrain-lab/tests/`.
Do not assume `assets/` or `scripts/` have already moved under `projects/terrain-lab/`.

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
.\.venv\Scripts\python.exe -m py_compile projects\terrain-lab\src\app\services\geomorphic_engine.py projects\terrain-lab\src\app\services\terrain_physics_lab.py "projects\terrain-lab\src\pages\3_🧪_Lab.py"
powershell -ExecutionPolicy Bypass -File .\projects\terrain-lab\test.ps1 -Fast
```

For broader terrain regression:

```powershell
powershell -ExecutionPolicy Bypass -File .\projects\terrain-lab\test.ps1
```

If Streamlit is running locally, verify:

```powershell
Invoke-WebRequest -Uri http://127.0.0.1:8501/Lab -UseBasicParsing -TimeoutSec 20
```
