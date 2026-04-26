# Geo-Lab Projects

Geo-Lab is being split into three project domains.

## 1. Terrain Lab

Path: `projects/terrain-lab/`

Current source is still mostly in root-level `app/`, `pages/`, `engine/`, `assets/`, `scripts/`, and terrain tests. See `projects/terrain-lab/AGENTS.md`.

## 2. Koppen Climate

Path: `projects/koppen-climate/`

Current source is mostly in `apps/koppen-climate-lab/` and `static/koppen-climate-lab/`. See `projects/koppen-climate/AGENTS.md`.

## 3. School GIS

Path: `projects/school-gis/`

Current source is mostly in `apps/school-neighborhood-gis/`. See `projects/school-gis/AGENTS.md`.

## Migration Rule

Move one project at a time. For each project:

1. Create or update project-local instructions.
2. Move source files.
3. Update imports, script paths, and tests.
4. Run project-local verification.
5. Commit before moving the next project.

The root `knowledge/` vault remains shared project memory, not a product source tree.

