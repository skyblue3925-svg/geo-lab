# Cloudflare Pages Deploy for Koppen Climate Lab

This app should be deployed as a static site with Cloudflare Pages and Git integration.

## Current Status

- GitHub remote: `https://github.com/skyblue3925-svg/geo-lab.git`
- Production branch in this repo: `master`
- Latest app setup commit: `9f1438d`
- Cloudflare authentication has already been verified with Wrangler
- A Pages project for this app has not been created yet

## Why Pages Is Enough

- The app is static: HTML, CSS, JavaScript, GeoJSON, MJS, and BIN assets
- There is no login, database, secret key, or backend API for runtime
- The app only needs standard HTTP hosting for `fetch("./data/...")`

You do not need to build or manage a separate server for this version.

## Recommended Pages Settings

- Git provider: `GitHub`
- Repository: `skyblue3925-svg/geo-lab`
- Production branch: `master`
- Framework preset: `None`
- Root directory: `apps/koppen-climate-lab`
- Build command: leave blank
- Build output directory: `.`
- Environment variables: none

If the Cloudflare UI insists on a build command, use `exit 0`.

## Monorepo Recommendation

This repository contains many unrelated apps and files. Restrict Pages rebuilds to the Koppen app path.

- Build watch paths: `apps/koppen-climate-lab/*`

Set this in:

- `Workers & Pages`
- project
- `Settings`
- `Builds & deployments`
- `Build watch paths`

## Dashboard Steps

1. Open Cloudflare Dashboard.
2. Go to `Workers & Pages`.
3. Select `Create application`.
4. Select `Pages`.
5. Select `Connect to Git`.
6. Authorize GitHub if needed.
7. Choose repository `skyblue3925-svg/geo-lab`.
8. Enter these settings:

```text
Production branch: master
Framework preset: None
Root directory: apps/koppen-climate-lab
Build command: leave blank
Build output directory: .
Build watch paths: apps/koppen-climate-lab/*
```

9. Click `Save and Deploy`.

## Files Required In The Repo

These files must stay committed because the app loads them at runtime:

- `apps/koppen-climate-lab/index.html`
- `apps/koppen-climate-lab/app.js`
- `apps/koppen-climate-lab/styles.css`
- `apps/koppen-climate-lab/climate-model.mjs`
- `apps/koppen-climate-lab/lesson-data.mjs`
- `apps/koppen-climate-lab/world-map-data.mjs`
- `apps/koppen-climate-lab/data/koppen-geiger-1991-2020.mjs`
- `apps/koppen-climate-lab/data/koppen-geiger-1991-2020-0p1.bin`
- `apps/koppen-climate-lab/data/real-climate-data.mjs`
- `apps/koppen-climate-lab/data/world-land-110m.geojson`
- `apps/koppen-climate-lab/data/world-countries-110m.geojson`

## Files Excluded From Git

These raw source folders are intentionally excluded because they are only used for preprocessing:

- `apps/koppen-climate-lab/data/worldclim/raw/`
- `apps/koppen-climate-lab/data/koppen-official/`

## Local Verification

```powershell
cd "C:\Users\HANSOL\OneDrive\Desktop\Geo-lab\apps\koppen-climate-lab"
python -m http.server 8765
```

Open `http://127.0.0.1:8765`.

## Notes

- Do not open `index.html` by double-clicking. The app needs HTTP hosting because it uses `fetch("./data/...")`.
- Git integration is the right long-term choice for this app because every push to `master` can redeploy automatically.
- Cloudflare Pages also creates preview deploys for branches and pull requests.
