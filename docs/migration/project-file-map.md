# Geo-Lab Project Migration Map

## Target Structure

```text
Geo-lab/
  projects/
    terrain-lab/
    koppen-climate/
    school-gis/
  knowledge/
  docs/
  .deploy/
```

## Project Boundaries

### Terrain Lab

Owns landform education, terrain animation, and physical modeling.

Current source candidates:

- `app/`
- `pages/`
- `engine/`
- `assets/cinematic/`
- `assets/frames/`
- `assets/reference/` when terrain-specific
- `scripts/build_storyboard_*`
- `scripts/import_filmstrip_sequence.py`
- `scripts/build_mobile_gif_gallery.py`
- `tests/test_geomorphic_*`
- `tests/test_physics_lab_*`
- `tests/test_animation_*`
- `tests/test_high_school_*`
- `tests/test_image_sequence_*`
- `app.py`
- `app_high_school.py`
- `renderer.py`
- root terrain specs: `00_Master_Integration_Plan.md`, `01_River_Landforms_Spec.md`, etc.

### Koppen Climate

Owns the climate graph web app and climate data pipeline.

Current source candidates:

- `apps/koppen-climate-lab/`
- `static/koppen-climate-lab/`
- `tests/koppen-climate-model.test.mjs`
- `tests/koppen-exam-spots.test.mjs`
- `package.json` entries related to Vitest and climate app tooling
- `.deploy/koppen-climate-lab-pages/` as deploy worktree/output, not source

### School GIS

Owns the school-neighborhood GIS app.

Current source candidates:

- `apps/school-neighborhood-gis/`
- `docs/SGIS_LOCAL_SETUP.md`
- `docs/CLOUDFLARE_PAGES_SCHOOL_GIS.md`
- `docs/SUPABASE_SCHOOL_GIS_SETUP.md`
- `.deploy/school-neighborhood-gis-pages/` as deploy worktree/output, not source

### Shared / Root

Keep at root for now:

- `knowledge/`
- `.obsidian/`
- `AGENTS.md`
- root `.gitignore`, `.gitattributes`
- `.deploy/`
- `.venv/`, `venv/`, `node_modules/` as local environment directories

## Migration Order

1. Stabilize and commit in-flight Terrain Lab work.
2. Create project-level `AGENTS.md` files and this migration map.
3. Move Koppen climate source first because it is already mostly isolated.
4. Move School GIS source second because it is already mostly isolated.
5. Move Terrain Lab source last because it owns the current Streamlit app root and has the highest import risk.
6. Update root README into a project index.
7. Update test/build commands per project.
8. Update deployment worktrees only after local project commands pass.

## Do Not Move Automatically

- `.deploy/`
- `.venv/`, `venv/`, `.tmp-venv/`
- `node_modules/`
- `.pytest_cache/`
- `.tmp-*`
- `tmp/`
- `test-results/`
- `output/` unless a file is explicitly product documentation

