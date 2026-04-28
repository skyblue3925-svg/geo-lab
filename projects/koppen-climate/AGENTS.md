# Koppen Climate Agent Guide

## Scope

This project owns the Koppen climate graph and climate-learning web app:

- Interactive Koppen climate graph UI
- Climate map/dashboard modules
- Climate data and exam spot data
- JavaScript unit tests for climate classification and UI state
- Static deployment assets for the climate app

## Current Source Locations

During migration, source still lives mostly at:

- `apps/koppen-climate-lab/`
- `static/koppen-climate-lab/`
- `tests/koppen-*.test.mjs`
- `tests/koppen-climate-model.test.mjs`
- root `package.json` and `package-lock.json` for shared JS tooling
- `.deploy/koppen-climate-lab-pages/` as deployment output/worktree

Do not mix Koppen changes with terrain Streamlit or GIS changes.

## Invariants

- Keep climate data files with the climate app.
- Keep browser/static assets separate from terrain `static/` assets unless a shared shell explicitly needs them.
- Do not move deployment worktree contents into source without checking whether they are generated.
- Prefer small ES module files over adding more logic to a single large `app.js`.

## Verification

Use JS tests for climate changes:

```powershell
npm.cmd run test:unit
```

When touching climate model code directly, run the specific tests if available:

```powershell
npx vitest run tests/koppen-climate-model.test.mjs
```

For local browser verification, serve or open the climate static app according to its project README after migration.

