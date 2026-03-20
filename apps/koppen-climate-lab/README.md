# Koppen Climate Map

쾨펜 기후 구분 지도를 수업용으로 보여 주는 정적 웹앱입니다.

## App Path

- `apps/koppen-climate-lab/index.html`
- `apps/koppen-climate-lab/app.js`
- `apps/koppen-climate-lab/climate-model.mjs`
- `apps/koppen-climate-lab/styles.css`

## Current Data Model

- 지도 레이어: Beck et al. `Koppen-Geiger v2`, `1991-2020`, `0.1°`
- 월별 기온·강수 차트: `WorldClim 2.1`, `1970-2000`
- 지도는 공식 분류를 그대로 쓰고, 차트는 월별 기후 정상값으로 설명을 보강합니다.

## Included Deploy Assets

- `data/koppen-geiger-1991-2020.mjs`
- `data/koppen-geiger-1991-2020-0p1.bin`
- `data/real-climate-data.mjs`
- `data/world-land-110m.geojson`
- `data/world-countries-110m.geojson`

## Excluded Source Assets

원본 다운로드 파일은 저장소에 올리지 않습니다.

- `data/worldclim/raw/`
- `data/koppen-official/`

이 폴더들은 전처리용 원본 보관소입니다. 앱 실행과 Cloudflare Pages 배포에는 필요하지 않습니다.

## Local Run

정적 앱이라 간단한 로컬 서버만 있으면 됩니다.

```powershell
cd "C:\Users\HANSOL\OneDrive\Desktop\Geo-lab\apps\koppen-climate-lab"
python -m http.server 8765
```

브라우저에서 `http://127.0.0.1:8765` 를 열면 됩니다.

## Cloudflare Pages

Git 연동 기준 권장 설정:

- Framework preset: `None`
- Root directory: `apps/koppen-climate-lab`
- Build command: `exit 0`
- Build output directory: `.`

자세한 절차는 [docs/CLOUDFLARE_PAGES_KOPPEN.md](C:/Users/HANSOL/OneDrive/Desktop/Geo-lab/docs/CLOUDFLARE_PAGES_KOPPEN.md) 를 보면 됩니다.
