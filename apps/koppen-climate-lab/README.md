# Koppen Climate Lab

Static classroom web app for exploring Koppen climate regions on a world map.

Created for teaching use by Hanbaek High School teacher Kim Hansol.

## App Files

- `index.html`
- `app.js`
- `climate-model.mjs`
- `styles.css`
- `lesson-data.mjs`
- `world-map-data.mjs`

## Data Sources

- Map classification layer: Beck et al. Koppen-Geiger v2, `1991-2020`, `0.1 deg`
- Monthly chart data: WorldClim 2.1 climate normals, `1970-2000`

## Included Deploy Assets

- `data/koppen-geiger-1991-2020.mjs`
- `data/koppen-geiger-1991-2020-0p1.bin`
- `data/real-climate-data.mjs`
- `data/world-land-110m.geojson`
- `data/world-countries-110m.geojson`

## Excluded Source Assets

These raw source folders are not needed for runtime or Cloudflare Pages deploys:

- `data/worldclim/raw/`
- `data/koppen-official/`

## Local Run

```powershell
cd "C:\Users\HANSOL\OneDrive\Desktop\Geo-lab\apps\koppen-climate-lab"
python -m http.server 8765
```

Open `http://127.0.0.1:8765`.

## Cloudflare Pages

Recommended Git-connected Pages settings:

- Framework preset: `None`
- Root directory: `apps/koppen-climate-lab`
- Build command: leave blank
- Build output directory: `.`
- Build watch paths: `apps/koppen-climate-lab/*`

If the dashboard insists on a build command, use `exit 0`.

See [CLOUDFLARE_PAGES_KOPPEN.md](C:\Users\HANSOL\OneDrive\Desktop\Geo-lab\docs\CLOUDFLARE_PAGES_KOPPEN.md) for the full setup.
