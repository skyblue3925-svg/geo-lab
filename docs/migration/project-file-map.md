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
- `projects/terrain-lab/tests/`
- `projects/terrain-lab/tests/e2e/`

### Koppen Climate

Owns the climate graph web app and climate data pipeline.

Primary source:

- `projects/koppen-climate/app/`
- `projects/koppen-climate/static/`
- `projects/koppen-climate/tests/`
- `projects/koppen-climate/package.json`

Raw source datasets remain excluded from Git:

- `projects/koppen-climate/app/data/worldclim/`
- `projects/koppen-climate/app/data/koppen-official/`
- `projects/koppen-climate/app/data/beck-v2/`
- `projects/koppen-climate/app/data/etopo/`

### School GIS

Owns the school-neighborhood GIS app.

Primary source:

- `projects/school-gis/app/`
- `projects/school-gis/app/package.json`
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
.\.venv\Scripts\python.exe -m pytest projects\terrain-lab\tests\test_geomorphic_engine_force_fields.py projects\terrain-lab\tests\test_geomorphic_engine_presets.py projects\terrain-lab\tests\test_physics_lab_metadata.py projects\terrain-lab\tests\test_geomorphic_engine.py projects\terrain-lab\tests\test_morphometric_metrics.py projects\terrain-lab\tests\test_geomorphic_process_kernels.py projects\terrain-lab\tests\test_river_morphology_kernel.py projects\terrain-lab\tests\test_terrain_lab_catalog.py projects\terrain-lab\tests\test_page_syntax.py -q
```

or:

```powershell
powershell -ExecutionPolicy Bypass -File .\projects\terrain-lab\test.ps1
```

Koppen Climate:

```powershell
npm.cmd run test:koppen
```

or:

```powershell
cd projects\koppen-climate
npm.cmd test
```

School GIS:

```powershell
npm.cmd run test:gis:syntax
```

or:

```powershell
cd projects\school-gis\app
npm.cmd run test:syntax
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
2. Decide whether terrain `assets/` and `scripts/` should move under `projects/terrain-lab/`.
3. Clean up root-level test/deploy references that still assume `tests/`.
4. Add project-specific CI once deployment mirrors are stable.
5. Keep root wrappers until a deployment cutover confirms direct project-local execution is enough.
6. Document raw Koppen data regeneration/download flow.
