# School GIS Agent Guide

## Scope

This project owns the school-neighborhood GIS app:

- Local school/neighborhood spatial analysis UI
- GIS domain/application/infrastructure layers
- Sample layers and GIS data-processing scripts
- Cloudflare Pages or static deployment setup for GIS

## Current Source Locations

During migration, source already mostly lives at:

- `apps/school-neighborhood-gis/`
- `.deploy/school-neighborhood-gis-pages/` as deployment output/worktree
- GIS docs such as `docs/SGIS_LOCAL_SETUP.md`, `docs/CLOUDFLARE_PAGES_SCHOOL_GIS.md`, `docs/SUPABASE_SCHOOL_GIS_SETUP.md`
- GIS-related tests under `apps/school-neighborhood-gis/tests/` and possibly `tests/e2e/`

Do not mix GIS changes with terrain Lab or Koppen climate changes.

## Invariants

- Preserve the domain/application/infrastructure/presentation separation already present in the GIS app.
- Treat sample layers as source fixtures unless explicitly marked generated.
- Keep deployment output separate from source.
- Do not introduce Streamlit dependencies into this project unless intentionally building a bridge.

## Verification

Prefer the GIS app's own test/build commands after checking its `package.json` or README.

If no project-local script is available, inspect before adding new tooling:

```powershell
Get-Content apps\school-neighborhood-gis\package.json
Get-ChildItem apps\school-neighborhood-gis\tests
```

