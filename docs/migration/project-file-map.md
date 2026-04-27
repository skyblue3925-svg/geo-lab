# Geo-Lab Project Migration Map

## Current Structure

```text
Geo-lab/
  projects/
    terrain-lab/
      src/
        app/
        engine/
        pages/
    koppen-climate/
      app/
      static/
    school-gis/
      app/
  app/       # Streamlit compatibility wrapper
  engine/    # Terrain engine compatibility wrapper
  pages/     # Streamlit page wrappers
  assets/    # still shared, terrain-heavy
  scripts/   # still shared
  tests/     # still shared
  knowledge/
  docs/
  .deploy/
```

## Project Boundaries

### Terrain Lab

Owns landform education, terrain animation, and physical modeling.

Primary source:

- `projects/terrain-lab/src/app/`
- `projects/terrain-lab/src/engine/`
- `projects/terrain-lab/src/pages/`

Compatibility and shared runtime files:

- `app.py`
- `app/`
- `engine/`
- `pages/`
- `run_geo_lab.ps1`
- `requirements.txt`
- `pyproject.toml`

Still root-level for now:

- `assets/cinematic/`
- `assets/frames/`
- `scripts/build_storyboard_*`
- `scripts/import_filmstrip_sequence.py`
- `scripts/build_mobile_gif_gallery.py`
- `tests/test_geomorphic_*`
- `tests/test_physics_lab_*`
- `tests/test_animation_*`
- `tests/test_high_school_*`
- `tests/test_image_sequence_*`

### Koppen Climate

Owns the climate graph web app and climate data pipeline.

Primary source:

- `projects/koppen-climate/app/`
- `projects/koppen-climate/static/`
- `tests/koppen-climate-model.test.mjs`
- `tests/koppen-exam-spots.test.mjs`

Raw source datasets remain excluded from Git:

- `projects/koppen-climate/app/data/worldclim/`
- `projects/koppen-climate/app/data/koppen-official/`
- `projects/koppen-climate/app/data/beck-v2/`
- `projects/koppen-climate/app/data/etopo/`

### School GIS

Owns the school-neighborhood GIS app.

Primary source:

- `projects/school-gis/app/`
- `docs/SGIS_LOCAL_SETUP.md`
- `docs/CLOUDFLARE_PAGES_SCHOOL_GIS.md`
- `docs/SUPABASE_SCHOOL_GIS_SETUP.md`

### Shared / Root

Keep at root for now:

- `knowledge/`
- `.obsidian/`
- `AGENTS.md`
- root `.gitignore`, `.gitattributes`
- `.deploy/`
- local environment directories and caches

## Run Commands

Terrain Lab:

```powershell
.\run_geo_lab.ps1
```

Koppen Climate:

```powershell
cd projects\koppen-climate\app
python -m http.server 8765
```

School GIS:

```powershell
cd projects\school-gis\app
python -m http.server 8787
```

## Verification Commands

Terrain Lab:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_geomorphic_engine_force_fields.py tests\test_geomorphic_engine_presets.py tests\test_physics_lab_metadata.py tests\test_geomorphic_engine.py tests\test_morphometric_metrics.py tests\test_geomorphic_process_kernels.py tests\test_river_morphology_kernel.py tests\test_terrain_lab_catalog.py tests\test_page_syntax.py -q
```

Koppen Climate:

```powershell
npm.cmd run test:koppen
```

School GIS:

```powershell
npm.cmd run test:gis:syntax
```

## Deployment Paths

Terrain Lab:

- Streamlit/Hugging Face entrypoint: root `app.py`
- Deploy mirror: `.deploy/hf-space/`
- Mirror must include the root wrappers and `projects/terrain-lab/src/`.

Koppen Climate:

- Cloudflare Pages root: `projects/koppen-climate/static`
- Build command: blank
- Output directory: `.`

School GIS:

- Cloudflare Pages root: `projects/school-gis/app`
- Build command: blank
- Output directory: `.`

## Remaining Migration Work

1. Update `.deploy/` mirrors after local verification.
2. Decide whether terrain `assets/`, `scripts/`, and `tests/` should move under `projects/terrain-lab/`.
3. Add project-specific CI once deployment mirrors are stable.
4. Keep root wrappers until a deployment cutover confirms direct project-local execution is enough.
5. Document raw Koppen data regeneration/download flow.

