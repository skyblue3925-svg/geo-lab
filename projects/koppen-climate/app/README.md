# Koppen Climate Lab

제작자: 한백고등학교 김한솔

쾨펜 기후 구분을 세계지도와 기후 그래프로 탐구하는 정적 웹앱입니다.

## 앱 경로

- 앱 소스: `projects/koppen-climate/app/`
- 정적 배포 사본: `projects/koppen-climate/static/`
- 테스트: 루트 `tests/koppen-climate-model.test.mjs`, `tests/koppen-exam-spots.test.mjs`

## 주요 파일

- `index.html`
- `app.js`
- `climate-model.mjs`
- `styles.css`
- `lesson-data.mjs`
- `world-map-data.mjs`

## 포함된 런타임 데이터

- `data/koppen-geiger-1991-2020.mjs`
- `data/koppen-geiger-1991-2020-0p1.bin`
- `data/real-climate-data.mjs`
- `data/real-elevation-data.mjs`
- `data/world-land-110m.geojson`
- `data/world-countries-110m.geojson`

## Git에서 제외할 원자료

다음 원자료 폴더는 런타임이나 Cloudflare Pages 배포에 직접 필요하지 않습니다.

- `data/worldclim/`
- `data/koppen-official/`
- `data/beck-v2/`
- `data/etopo/`

## 로컬 실행

```powershell
cd "C:\Users\HANSOL\OneDrive\Desktop\Geo-lab\projects\koppen-climate\app"
python -m http.server 8765
```

브라우저에서 `http://127.0.0.1:8765`를 엽니다.

## 검증

```powershell
cd "C:\Users\HANSOL\OneDrive\Desktop\Geo-lab"
npm.cmd run test:koppen
```

## Cloudflare Pages

권장 설정:

- Framework preset: `None`
- Root directory: `projects/koppen-climate/static`
- Build command: 비움
- Build output directory: `.`

소스 앱을 직접 배포할 때는 root directory를 `projects/koppen-climate/app`으로 잡을 수 있습니다. 다만 공개 배포 기준은 `static` 사본으로 맞춥니다.
